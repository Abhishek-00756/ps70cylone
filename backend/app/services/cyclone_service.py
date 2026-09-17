"""
Orchestrates the full pipeline (track -> synthetic imagery -> features ->
detection -> classification -> intensity -> temporal trend -> forecast ->
risk -> alerts) for the demo cyclone, computed ONCE at process start and
cached, so every API call returns consistent, already-computed values
instead of recomputing (and potentially re-randomizing) on every request.

This module is the single source of truth the API layer reads from -- the
frontend never invents numbers independently.
"""
from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from ml.classification.classifier import CycloneClassifier
from ml.detection.detector import detect_cyclone
from ml.evaluation.risk_engine import assess_risk
from ml.intensity.estimator import analyze_temporal_trend, estimate_intensity
from ml.preprocessing.features import extract_features
from ml.preprocessing.synthetic_satellite import SyntheticFrameParams, generate_infrared_frame
from ml.tracking.track_generator import generate_demo_track, forecast_track

CYCLONE_ID = "DEMO-01"
CYCLONE_NAME = "CYCLONE DEMO-01"
METRICS_PATH = Path(__file__).resolve().parents[3] / "data" / "demo" / "metadata" / "model_metrics.json"

_lock = Lock()
_cache: dict = {}


def _build() -> dict:
    track = generate_demo_track()
    try:
        classifier = CycloneClassifier.load()
    except FileNotFoundError:
        # First run on a fresh clone: the trained .pkl is gitignored (small
        # but regenerable), so train it once automatically instead of
        # requiring a manual step before the API can serve anything.
        from ml.training.train_classifier import build_dataset

        classifier = CycloneClassifier()
        X, y = build_dataset()
        classifier.fit(X, y)
        classifier.save()

    steps = []
    wind_series, pressure_series = [], []
    for i, point in enumerate(track):
        frame = generate_infrared_frame(
            SyntheticFrameParams(organization=point.organization, rotation_deg=i * 25, seed=i)
        )
        features = extract_features(frame, env_sst_proxy=point.sst_proxy, env_wind_shear_proxy=point.wind_shear_proxy)
        classification = classifier.predict(features)
        detection = detect_cyclone(features, classification)
        intensity = estimate_intensity(features)

        wind_series.append((point.timestamp, intensity.wind_speed_kt))
        pressure_series.append((point.timestamp, intensity.central_pressure_hpa))

        steps.append(
            {
                "index": i,
                "point": point,
                "features": features,
                "classification": classification,
                "detection": detection,
                "intensity": intensity,
            }
        )

    trend = analyze_temporal_trend(wind_series, pressure_series)
    forecast = forecast_track(track, [6, 12, 24, 48, 72])

    latest = steps[-1]
    # Landfall probability: heuristic from how close the 72h forecast point's
    # longitude is to the Indian east coast (~80°E in this stretch) relative
    # to the current position -- a documented prototype heuristic, not a
    # trained landfall model.
    landfall_point = forecast[-1]
    landfall_probability = round(min(1.0, max(0.3, 1.0 - abs(landfall_point.lon - 80.0) / 10.0)), 2)

    rainfall_proxy = min(1.0, 0.4 + 0.6 * latest["features"].moisture_proxy)
    risk = assess_risk(latest["intensity"].wind_speed_kt, landfall_probability, rainfall_proxy)

    alerts = _generate_alerts(steps, trend, risk, landfall_probability)

    metrics = None
    if METRICS_PATH.exists():
        with open(METRICS_PATH) as f:
            metrics = json.load(f)

    return {
        "track": track,
        "steps": steps,
        "trend": trend,
        "forecast": forecast,
        "landfall_probability": landfall_probability,
        "risk": risk,
        "alerts": alerts,
        "metrics": metrics,
    }


def _generate_alerts(steps, trend, risk, landfall_probability) -> list[dict]:
    alerts = []
    latest = steps[-1]
    first_detected_idx = next((s["index"] for s in steps if s["detection"].detected), None)

    if first_detected_idx is not None:
        alerts.append(
            {
                "id": "ALERT-FORMATION",
                "type": "FORMATION_DETECTED",
                "severity": "ADVISORY",
                "timestamp": steps[first_detected_idx]["point"].timestamp,
                "affected_region": "Bay of Bengal (central)",
                "reason": "AI detection pipeline identified an organized convective system with sustained circulation.",
                "confidence": steps[first_detected_idx]["detection"].confidence,
                "recommended_action": "Continue monitoring; no coastal action required yet.",
            }
        )

    if trend.trend == "intensifying":
        alerts.append(
            {
                "id": "ALERT-INTENSIFICATION",
                "type": "INTENSIFICATION",
                "severity": "WATCH",
                "timestamp": latest["point"].timestamp,
                "affected_region": "Bay of Bengal (central-west)",
                "reason": f"Estimated wind speed increased {trend.delta_wind_kt_24h:+.1f}kt over the analysed window.",
                "confidence": latest["classification"].confidence,
                "recommended_action": "Increase monitoring frequency; prepare coastal advisories.",
            }
        )

    if trend.rapid_intensification:
        alerts.append(
            {
                "id": "ALERT-RI",
                "type": "RAPID_INTENSIFICATION",
                "severity": "WARNING",
                "timestamp": latest["point"].timestamp,
                "affected_region": "Bay of Bengal (central-west)",
                "reason": f"Wind speed increase of {trend.delta_wind_kt_24h:.1f}kt meets/exceeds the {trend.ri_threshold_kt_per_24h:.0f}kt/24h rapid intensification threshold.",
                "confidence": latest["classification"].confidence,
                "recommended_action": "Escalate to disaster-management authorities; issue coastal warnings.",
            }
        )

    if landfall_probability >= 0.6:
        alerts.append(
            {
                "id": "ALERT-LANDFALL",
                "type": "LANDFALL_RISK",
                "severity": "WARNING" if landfall_probability >= 0.75 else "WATCH",
                "timestamp": latest["point"].timestamp,
                "affected_region": "Odisha - Andhra Pradesh coast (prototype demo estimate)",
                "reason": f"Prototype forecast model estimates {landfall_probability*100:.0f}% landfall probability along the analysed coastal stretch within 72h.",
                "confidence": landfall_probability,
                "recommended_action": "Coordinate with district disaster management authorities; review evacuation readiness.",
            }
        )

    if risk.wind_risk in ("HIGH", "SEVERE", "EXTREME"):
        alerts.append(
            {
                "id": "ALERT-WIND",
                "type": "HIGH_WIND_RISK",
                "severity": risk.wind_risk,
                "timestamp": latest["point"].timestamp,
                "affected_region": "Coastal districts along forecast track",
                "reason": f"Estimated sustained wind {latest['intensity'].wind_speed_kt}kt classified as {risk.wind_risk} wind risk.",
                "confidence": latest["classification"].confidence,
                "recommended_action": "Secure loose structures; restrict fishing and coastal activity.",
            }
        )

    if risk.rainfall_risk in ("HIGH", "SEVERE", "EXTREME"):
        alerts.append(
            {
                "id": "ALERT-RAIN",
                "type": "HEAVY_RAINFALL_RISK",
                "severity": risk.rainfall_risk,
                "timestamp": latest["point"].timestamp,
                "affected_region": "Coastal and near-coastal districts along forecast track",
                "reason": "Moisture-proxy feature indicates high rainfall potential in the system's inflow bands.",
                "confidence": 0.6,
                "recommended_action": "Alert local authorities to flood-prone low-lying areas.",
            }
        )

    return alerts


def get_state() -> dict:
    with _lock:
        if not _cache:
            _cache.update(_build())
        return _cache


def reset_cache() -> None:
    with _lock:
        _cache.clear()


def find_track_point_by_timestamp(cyclone_id: str, timestamp: str):
    state = get_state()
    for i, s in enumerate(state["steps"]):
        if s["point"].timestamp == timestamp:
            return s["point"], i
    # default to latest if not found
    return state["steps"][-1]["point"], len(state["steps"]) - 1
