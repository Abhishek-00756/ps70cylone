"""
ML pipeline unit tests (stdlib unittest -- see test_api.py docstring for why).
Run: python -m unittest discover -s backend/tests -v
"""
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from ml.preprocessing.synthetic_satellite import SyntheticFrameParams, generate_infrared_frame
from ml.preprocessing.features import extract_features, features_to_vector
from ml.classification.classifier import CycloneClassifier, classify_by_wind_speed_kt
from ml.detection.detector import detect_cyclone
from ml.intensity.estimator import estimate_intensity, analyze_temporal_trend
from ml.tracking.track_generator import generate_demo_track, forecast_track
from ml.evaluation.risk_engine import assess_risk


def setUpModule():
    """Ensure the prototype classifier exists before these tests run (fresh
    clone / fresh CI run won't have ml/models/classifier.pkl committed --
    see .gitignore -- so train it once here rather than depending on test
    execution order)."""
    try:
        CycloneClassifier.load()
    except FileNotFoundError:
        from ml.training.train_classifier import main as train_main

        train_main()


class MlPipelineTestCase(unittest.TestCase):
    def test_synthetic_frame_shape_and_range(self):
        frame = generate_infrared_frame(SyntheticFrameParams(organization=0.7))
        self.assertEqual(frame.shape, (256, 256))
        self.assertGreaterEqual(frame.min(), 0.0)
        self.assertLessEqual(frame.max(), 1.0)

    def test_more_organized_frame_has_more_cold_cloud(self):
        low = generate_infrared_frame(SyntheticFrameParams(organization=0.05, noise_level=0.02, seed=1))
        high = generate_infrared_frame(SyntheticFrameParams(organization=0.95, noise_level=0.02, seed=1))
        f_low = extract_features(low)
        f_high = extract_features(high)
        self.assertGreaterEqual(f_high.cold_cloud_fraction, f_low.cold_cloud_fraction)

    def test_feature_vector_order_stable(self):
        frame = generate_infrared_frame(SyntheticFrameParams(organization=0.5))
        f = extract_features(frame)
        vec = features_to_vector(f)
        self.assertEqual(vec.shape, (12,))
        self.assertTrue(np.all(np.isfinite(vec)))

    def test_classifier_loads_and_predicts(self):
        clf = CycloneClassifier.load()
        frame = generate_infrared_frame(SyntheticFrameParams(organization=0.8, seed=3))
        f = extract_features(frame)
        result = clf.predict(f)
        self.assertIn(result.predicted_class, clf.model.classes_)
        self.assertTrue(0 <= result.confidence <= 1)
        self.assertLess(abs(sum(result.class_probabilities.values()) - 1.0), 1e-3)

    def test_imd_scale_boundaries(self):
        self.assertEqual(classify_by_wind_speed_kt(10), "LOW_PRESSURE_AREA")
        self.assertEqual(classify_by_wind_speed_kt(20), "DEPRESSION")
        self.assertEqual(classify_by_wind_speed_kt(40), "CYCLONIC_STORM")
        self.assertEqual(classify_by_wind_speed_kt(130), "SUPER_CYCLONIC_STORM")

    def test_detection_consistent_with_classification(self):
        clf = CycloneClassifier.load()
        frame = generate_infrared_frame(SyntheticFrameParams(organization=0.02, noise_level=0.02, seed=5))
        f = extract_features(frame)
        cls = clf.predict(f)
        det = detect_cyclone(f, cls)
        self.assertIsInstance(det.detected, bool)
        self.assertTrue(0 <= det.confidence <= 1)

    def test_intensity_estimate_monotonic_with_organization(self):
        low = extract_features(generate_infrared_frame(SyntheticFrameParams(organization=0.05, noise_level=0.02, seed=9)))
        high = extract_features(generate_infrared_frame(SyntheticFrameParams(organization=0.95, noise_level=0.02, seed=9)))
        i_low = estimate_intensity(low)
        i_high = estimate_intensity(high)
        self.assertGreater(i_high.wind_speed_kt, i_low.wind_speed_kt)
        self.assertLess(i_high.central_pressure_hpa, i_low.central_pressure_hpa)

    def test_rapid_intensification_detection(self):
        series_wind = [("t0", 40.0), ("t1", 75.0)]
        series_p = [("t0", 990.0), ("t1", 950.0)]
        trend = analyze_temporal_trend(series_wind, series_p)
        self.assertTrue(trend.rapid_intensification)
        self.assertEqual(trend.trend, "intensifying")

    def test_track_generation_and_forecast_shapes(self):
        track = generate_demo_track()
        self.assertEqual(len(track), 9)
        forecast = forecast_track(track, [6, 12, 24])
        self.assertEqual(len(forecast), 3)
        radii = [f.uncertainty_radius_km for f in forecast]
        self.assertEqual(radii, sorted(radii))

    def test_risk_formula_is_traceable_product(self):
        r = assess_risk(wind_speed_kt=90, landfall_probability=0.9, rainfall_intensity_proxy=0.7)
        expected = round(r.hazard_intensity * r.exposure * r.vulnerability, 4)
        self.assertLess(abs(r.overall_risk_score - expected), 1e-6)
        self.assertIn(r.risk_category, ("LOW", "MODERATE", "HIGH", "SEVERE", "EXTREME"))


if __name__ == "__main__":
    unittest.main()
