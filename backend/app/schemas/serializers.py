from __future__ import annotations


def serialize_track_point(p) -> dict:
    return p.to_dict()


def serialize_step_summary(step: dict) -> dict:
    p = step["point"]
    return {
        "timestamp": p.timestamp,
        "lat": p.lat,
        "lon": p.lon,
        "classification": step["classification"].predicted_class,
        "classification_confidence": step["classification"].confidence,
        "detected": step["detection"].detected,
        "detection_confidence": step["detection"].confidence,
        "wind_speed_kt": step["intensity"].wind_speed_kt,
        "central_pressure_hpa": step["intensity"].central_pressure_hpa,
    }


def serialize_cyclone_summary(cyclone_id: str, name: str, state: dict) -> dict:
    latest = state["steps"][-1]
    return {
        "id": cyclone_id,
        "name": name,
        "basin": "North Indian Ocean - Bay of Bengal",
        "status": "ACTIVE_DEMO",
        "latest": serialize_step_summary(latest),
        "trend": latest["classification"].predicted_class,
        "movement_direction_deg": _bearing(state["track"][-2], state["track"][-1]) if len(state["track"]) > 1 else None,
        "last_updated": latest["point"].timestamp,
    }


def _bearing(p1, p2) -> float:
    import math

    lat1, lon1, lat2, lon2 = map(math.radians, [p1.lat, p1.lon, p2.lat, p2.lon])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    brng = (math.degrees(math.atan2(x, y)) + 360) % 360
    return round(brng, 1)
