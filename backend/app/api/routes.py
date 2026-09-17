from __future__ import annotations

from flask import Blueprint, jsonify, request, Response, current_app

from app.services import cyclone_service as svc
from app.schemas.serializers import serialize_track_point, serialize_step_summary, serialize_cyclone_summary
from app.providers.demo_provider import DemoSatelliteProvider, IMDSatelliteProvider, MOSDACProvider
from app.providers.base import ProviderUnavailableError
from ml.evaluation.risk_engine import assess_risk

api_bp = Blueprint("api", __name__)

_demo_provider = DemoSatelliteProvider(track_lookup=svc.find_track_point_by_timestamp)
_providers = {
    "demo": _demo_provider,
    "imd": IMDSatelliteProvider(),
    "mosdac": MOSDACProvider(),
}


def _active_provider():
    name = current_app.config.get("SATELLITE_PROVIDER", "demo")
    return _providers.get(name, _demo_provider)


@api_bp.get("/system/status")
def system_status():
    demo_mode = current_app.config["DEMO_MODE"]
    return jsonify(
        {
            "mode": "DEMO" if demo_mode else "LIVE",
            "components": {
                "satellite_feed": "DEMO" if demo_mode else "UNAVAILABLE",
                "ai_engine": "ONLINE",
                "weather_data": "DEMO" if demo_mode else "UNAVAILABLE",
                "prediction_engine": "ONLINE",
            },
        }
    )


@api_bp.get("/dashboard")
def dashboard():
    state = svc.get_state()
    return jsonify(
        {
            "cyclone": serialize_cyclone_summary(svc.CYCLONE_ID, svc.CYCLONE_NAME, state),
            "trend": {
                "trend": state["trend"].trend,
                "delta_wind_kt_24h": state["trend"].delta_wind_kt_24h,
                "delta_pressure_hpa_24h": state["trend"].delta_pressure_hpa_24h,
                "rapid_intensification": state["trend"].rapid_intensification,
            },
            "landfall_probability": state["landfall_probability"],
            "risk_category": state["risk"].risk_category,
            "active_alerts": len(state["alerts"]),
            "demo_mode": current_app.config["DEMO_MODE"],
        }
    )


@api_bp.get("/cyclones")
def list_cyclones():
    state = svc.get_state()
    return jsonify({"cyclones": [serialize_cyclone_summary(svc.CYCLONE_ID, svc.CYCLONE_NAME, state)]})


@api_bp.get("/cyclones/<cyclone_id>")
def get_cyclone(cyclone_id: str):
    state = svc.get_state()
    summary = serialize_cyclone_summary(cyclone_id, svc.CYCLONE_NAME, state)
    summary["history"] = [serialize_step_summary(s) for s in state["steps"]]
    return jsonify(summary)


@api_bp.get("/cyclones/<cyclone_id>/track")
def get_track(cyclone_id: str):
    state = svc.get_state()
    history = [serialize_track_point(s["point"]) for s in state["steps"]]
    forecast = [
        {
            "horizon_hours": f.horizon_hours,
            "timestamp": f.timestamp,
            "lat": f.lat,
            "lon": f.lon,
            "uncertainty_radius_km": f.uncertainty_radius_km,
        }
        for f in state["forecast"]
    ]
    return jsonify({"cyclone_id": cyclone_id, "history": history, "forecast": forecast, "method": "prototype_forecast_model"})


@api_bp.get("/cyclones/<cyclone_id>/intensity")
def get_intensity(cyclone_id: str):
    state = svc.get_state()
    series = [
        {
            "timestamp": s["point"].timestamp,
            "wind_speed_kt": s["intensity"].wind_speed_kt,
            "central_pressure_hpa": s["intensity"].central_pressure_hpa,
            "classification": s["classification"].predicted_class,
        }
        for s in state["steps"]
    ]
    trend = state["trend"]
    return jsonify(
        {
            "cyclone_id": cyclone_id,
            "series": series,
            "trend": trend.trend,
            "delta_wind_kt_24h": trend.delta_wind_kt_24h,
            "delta_pressure_hpa_24h": trend.delta_pressure_hpa_24h,
            "rapid_intensification": trend.rapid_intensification,
            "ri_threshold_kt_per_24h": trend.ri_threshold_kt_per_24h,
            "method": "prototype_dvorak_inspired_formula",
        }
    )


@api_bp.get("/cyclones/<cyclone_id>/features")
def get_features(cyclone_id: str):
    state = svc.get_state()
    latest = state["steps"][-1]
    return jsonify(
        {
            "cyclone_id": cyclone_id,
            "timestamp": latest["point"].timestamp,
            "features": latest["features"].to_dict(),
            "reasoning": _build_ai_reasoning(latest, state["trend"]),
        }
    )


def _build_ai_reasoning(latest_step: dict, trend) -> dict:
    f = latest_step["features"]
    factors = []
    if f.symmetry_score > 0.55:
        factors.append({"factor": "Strong cloud organization / symmetry", "contribution": round(f.symmetry_score, 2), "direction": "+"})
    if f.cold_cloud_fraction > 0.4:
        factors.append({"factor": "Falling cloud-top temperature (high cold-cloud fraction)", "contribution": round(f.cold_cloud_fraction, 2), "direction": "+"})
    if f.sst_proxy > 0.6:
        factors.append({"factor": "Favorable sea-surface temperature", "contribution": round(f.sst_proxy, 2), "direction": "+"})
    if f.vorticity_proxy > 0.55:
        factors.append({"factor": "Increasing low-level vorticity", "contribution": round(f.vorticity_proxy, 2), "direction": "+"})
    if f.wind_shear_proxy > 0.5:
        factors.append({"factor": "Elevated vertical wind shear (unfavorable)", "contribution": round(f.wind_shear_proxy, 2), "direction": "-"})
    elif f.wind_shear_proxy < 0.3:
        factors.append({"factor": "Low/moderate vertical wind shear (favorable)", "contribution": round(1 - f.wind_shear_proxy, 2), "direction": "+"})
    return {
        "label": "Prototype feature-based explanation",
        "trend": trend.trend,
        "rapid_intensification_flag": trend.rapid_intensification,
        "contributing_factors": factors,
    }


@api_bp.get("/cyclones/<cyclone_id>/risk")
def get_risk(cyclone_id: str):
    state = svc.get_state()
    r = state["risk"]
    return jsonify(
        {
            "cyclone_id": cyclone_id,
            "hazard_intensity": r.hazard_intensity,
            "exposure": r.exposure,
            "vulnerability": r.vulnerability,
            "overall_risk_score": r.overall_risk_score,
            "risk_category": r.risk_category,
            "wind_risk": r.wind_risk,
            "rainfall_risk": r.rainfall_risk,
            "storm_surge_risk": r.storm_surge_risk,
            "landfall_probability": state["landfall_probability"],
            "method": r.method,
            "demo_layers": {
                "exposure": "DEMO: illustrative population/infrastructure density for the forecast landfall stretch, not real census data.",
                "vulnerability": "DEMO: illustrative coastal vulnerability index, not a real vulnerability dataset.",
            },
        }
    )


@api_bp.get("/cyclones/<cyclone_id>/satellite")
def get_satellite_meta(cyclone_id: str):
    state = svc.get_state()
    timestamps = [s["point"].timestamp for s in state["steps"]]
    provider = _active_provider()
    return jsonify(
        {
            "cyclone_id": cyclone_id,
            "provider": provider.describe(),
            "available_timestamps": timestamps,
            "channels": ["infrared", "visible", "water_vapor"],
            "image_url_template": f"/api/cyclones/{cyclone_id}/satellite/frame?timestamp=<ts>&channel=<channel>",
        }
    )


@api_bp.get("/cyclones/<cyclone_id>/satellite/frame")
def get_satellite_frame(cyclone_id: str):
    timestamp = request.args.get("timestamp")
    channel = request.args.get("channel", "infrared")
    if not timestamp:
        state = svc.get_state()
        timestamp = state["steps"][-1]["point"].timestamp
    provider = _active_provider()
    try:
        png_bytes = provider.get_frame_png(cyclone_id, timestamp, channel)
    except ProviderUnavailableError as e:
        return jsonify({"error": str(e), "provider_status": provider.status}), 503
    return Response(png_bytes, mimetype="image/png")


@api_bp.get("/alerts")
def get_alerts():
    state = svc.get_state()
    return jsonify({"alerts": state["alerts"]})


@api_bp.get("/model/metrics")
def get_model_metrics():
    state = svc.get_state()
    metrics = state["metrics"]
    if metrics is None:
        return jsonify({"error": "Metrics not yet generated. Run `python -m ml.evaluation.evaluate`."}), 404
    return jsonify(metrics)


@api_bp.get("/data-sources")
def data_sources():
    return jsonify({"sources": [p.describe() for p in _providers.values()]})


@api_bp.post("/analyze")
def analyze():
    """Re-runs the detection+classification+intensity pipeline on the latest
    (or a client-supplied) frame. In this prototype the frame is always the
    demo pipeline's latest computed step -- provided as a real endpoint so
    the "Run AI Analysis" button in the UI performs genuine (re)computation
    rather than a no-op."""
    svc.reset_cache()
    state = svc.get_state()
    latest = state["steps"][-1]
    return jsonify(
        {
            "cyclone_id": svc.CYCLONE_ID,
            "pipeline_status": {
                "data": "done",
                "preprocessing": "done",
                "detection": "done",
                "classification": "done",
                "intensity": "done",
                "track_forecast": "done",
                "risk_analysis": "done",
            },
            "result": serialize_step_summary(latest),
        }
    )


@api_bp.post("/predict")
def predict():
    body = request.get_json(silent=True) or {}
    horizons = body.get("horizons_hours", [6, 12, 24, 48, 72])
    state = svc.get_state()
    from ml.tracking.track_generator import forecast_track

    forecast = forecast_track(state["track"], horizons)
    return jsonify(
        {
            "cyclone_id": svc.CYCLONE_ID,
            "forecast": [
                {
                    "horizon_hours": f.horizon_hours,
                    "timestamp": f.timestamp,
                    "lat": f.lat,
                    "lon": f.lon,
                    "uncertainty_radius_km": f.uncertainty_radius_km,
                }
                for f in forecast
            ],
            "method": "prototype_forecast_model",
        }
    )
