"""
Backend API tests.

Uses stdlib `unittest` rather than pytest: pytest is not installed in the
build/verification sandbox and could not be fetched (no network access), so
unittest guarantees these tests can actually be run and verified here.
pytest works fine too if installed (`pip install pytest && pytest backend/tests -v`).

Run: python -m unittest discover -s backend/tests -v
"""
import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(REPO_ROOT))

from app import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_health(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "ok")

    def test_system_status(self):
        r = self.client.get("/api/system/status")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertIn(body["mode"], ("DEMO", "LIVE"))
        self.assertIn("ai_engine", body["components"])

    def test_cyclone_list_and_detail(self):
        r = self.client.get("/api/cyclones")
        self.assertEqual(r.status_code, 200)
        cyclones = r.get_json()["cyclones"]
        self.assertEqual(len(cyclones), 1)
        cid = cyclones[0]["id"]

        r2 = self.client.get(f"/api/cyclones/{cid}")
        self.assertEqual(r2.status_code, 200)
        self.assertIn("history", r2.get_json())

    def test_track_has_history_and_forecast(self):
        r = self.client.get("/api/cyclones/DEMO-01/track")
        body = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(body["history"]), 5)
        self.assertEqual(len(body["forecast"]), 5)
        horizons = [f["horizon_hours"] for f in body["forecast"]]
        self.assertEqual(horizons, sorted(horizons))

    def test_intensity_series_values_physical(self):
        r = self.client.get("/api/cyclones/DEMO-01/intensity")
        body = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(body["series"]), 5)
        for point in body["series"]:
            self.assertGreater(point["wind_speed_kt"], 0)
            self.assertLess(point["central_pressure_hpa"], 1013)

    def test_features_endpoint(self):
        r = self.client.get("/api/cyclones/DEMO-01/features")
        body = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertTrue(0 <= body["features"]["symmetry_score"] <= 1)
        self.assertIn("reasoning", body)

    def test_risk_endpoint_formula_traceable(self):
        r = self.client.get("/api/cyclones/DEMO-01/risk")
        body = r.get_json()
        self.assertEqual(r.status_code, 200)
        expected = round(body["hazard_intensity"] * body["exposure"] * body["vulnerability"], 4)
        self.assertLess(abs(body["overall_risk_score"] - expected), 1e-3)

    def test_satellite_frame_returns_png(self):
        r = self.client.get("/api/cyclones/DEMO-01/satellite/frame?channel=infrared")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, "image/png")
        self.assertEqual(r.data[:8], b"\x89PNG\r\n\x1a\n")

    def test_satellite_frame_all_channels(self):
        for channel in ["infrared", "visible", "water_vapor"]:
            r = self.client.get(f"/api/cyclones/DEMO-01/satellite/frame?channel={channel}")
            self.assertEqual(r.status_code, 200, channel)

    def test_alerts_endpoint(self):
        r = self.client.get("/api/alerts")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.get_json()["alerts"], list)

    def test_data_sources_labelled_correctly(self):
        r = self.client.get("/api/data-sources")
        sources = r.get_json()["sources"]
        demo_sources = [s for s in sources if s["status"] == "DEMO"]
        self.assertGreaterEqual(len(demo_sources), 1)
        for s in demo_sources:
            self.assertEqual(s["source"], "SYNTHETIC_DEMO")

    def test_analyze_and_predict_endpoints(self):
        r = self.client.post("/api/analyze")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["pipeline_status"]["classification"], "done")

        r2 = self.client.post("/api/predict", json={"horizons_hours": [6, 24]})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(len(r2.get_json()["forecast"]), 2)


if __name__ == "__main__":
    unittest.main()
