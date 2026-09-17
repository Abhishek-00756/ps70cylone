"""
Demo cyclone track (Bay of Bengal, fictional "CYCLONE DEMO-01") generator.

Produces a non-linear, curving historical trajectory with a believable
formation -> intensification -> peak -> weakening story, at 3-hourly steps.
Everything downstream (satellite frames, features, intensity, risk) is keyed
off this same time series so the whole dashboard stays internally
consistent.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone


@dataclass
class TrackPoint:
    timestamp: str
    lat: float
    lon: float
    organization: float  # 0..1, drives synthetic imagery + features
    sst_proxy: float
    wind_shear_proxy: float

    def to_dict(self):
        return asdict(self)


def generate_demo_track(
    n_hist_points: int = 9,
    n_future_points: int = 0,
    step_hours: int = 3,
    start_time: datetime | None = None,
) -> list[TrackPoint]:
    """9 points at 3h spacing = 24h of history ending at 'now' (t-24h..t)."""
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(hours=step_hours * (n_hist_points - 1))

    # Base curving trajectory over the Bay of Bengal: starts SE of the
    # eventual track and curves NW toward the Indian east coast, a common
    # real-world recurvature pattern for Bay of Bengal systems.
    start_lat, start_lon = 12.5, 88.0
    points: list[TrackPoint] = []
    total = n_hist_points + n_future_points
    for i in range(total):
        t = i / max(total - 1, 1)  # 0..1 progress along the whole story
        lat = start_lat + 6.5 * t + 1.2 * math.sin(t * math.pi * 1.3)
        lon = start_lon - 4.0 * t - 0.8 * math.sin(t * math.pi * 0.8)

        # Organization story: slow formation, then intensification, peak near t=0.75, slight weakening near landfall.
        organization = max(0.0, min(1.0, 0.15 + 0.9 * math.sin(min(t, 0.85) / 0.85 * math.pi / 2) ** 1.4))
        if t > 0.85:
            organization *= max(0.4, 1 - (t - 0.85) * 3)  # weakening approaching coast

        sst_proxy = max(0.4, min(0.9, 0.55 + 0.3 * math.sin(t * math.pi)))
        wind_shear_proxy = max(0.05, min(0.7, 0.45 - 0.35 * math.sin(t * math.pi)))

        ts = (start_time + timedelta(hours=step_hours * i)).isoformat()
        points.append(TrackPoint(ts, round(lat, 3), round(lon, 3), round(organization, 3), round(sst_proxy, 3), round(wind_shear_proxy, 3)))
    return points


@dataclass
class ForecastPoint:
    horizon_hours: int
    timestamp: str
    lat: float
    lon: float
    uncertainty_radius_km: float


def forecast_track(history: list[TrackPoint], horizons_hours: list[int]) -> list[ForecastPoint]:
    """Prototype Forecast Model: extrapolates recent bearing + speed + gentle
    curvature (fit from the last 4 historical points via simple linear
    regression on lat/lon vs time), then grows an uncertainty cone with
    horizon -- this is NOT an operational NWP model.
    """
    if len(history) < 3:
        raise ValueError("Need at least 3 historical points to forecast.")

    recent = history[-4:] if len(history) >= 4 else history
    times_h = [i * 3.0 for i in range(len(recent))]  # relative hours, 3h spacing assumed
    lats = [p.lat for p in recent]
    lons = [p.lon for p in recent]

    def linfit(x, y):
        n = len(x)
        mean_x, mean_y = sum(x) / n, sum(y) / n
        num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        den = sum((xi - mean_x) ** 2 for xi in x) or 1e-6
        slope = num / den
        intercept = mean_y - slope * mean_x
        return slope, intercept

    lat_slope, lat_intercept = linfit(times_h, lats)
    lon_slope, lon_intercept = linfit(times_h, lons)

    last_t = times_h[-1]
    last_ts = datetime.fromisoformat(history[-1].timestamp)

    forecasts = []
    for h in horizons_hours:
        t_future = last_t + h
        lat = lat_intercept + lat_slope * t_future
        lon = lon_intercept + lon_slope * t_future
        # Uncertainty grows roughly linearly with horizon (prototype, not IMD's official cone).
        uncertainty_km = 25 + 1.8 * h
        forecasts.append(
            ForecastPoint(
                horizon_hours=h,
                timestamp=(last_ts + timedelta(hours=h)).isoformat(),
                lat=round(lat, 3),
                lon=round(lon, 3),
                uncertainty_radius_km=round(uncertainty_km, 1),
            )
        )
    return forecasts
