"""
Intensity estimation.

Documented prototype formula (loosely inspired by the structure of the
Dvorak technique -- organized cold, symmetric, deep convection with an eye
implies higher intensity -- but this is a simplified, NOT operationally
calibrated, mapping for demo purposes):

    T_number_proxy = 1 + 7 * (
        0.30 * cold_cloud_fraction +
        0.25 * symmetry_score +
        0.20 * circularity +
        0.15 * eye_probability +
        0.10 * spiral_band_strength
    )

    wind_kt = 12 + 14 * T_number_proxy           (roughly 26kt..~124kt across the T1-8 range)
    pressure_hpa = 1010 - 0.75 * (wind_kt - 12)  (rough, monotonic wind-pressure relation,
                                                   loosely calibrated so Cyclonic Storm (34kt)
                                                   ~ 993hPa and Super Cyclonic Storm (120kt) ~ 929hPa)

Rapid Intensification (RI) is flagged using the operational-style
definition: a wind-speed increase of >= 30 kt in 24 hours (the same
threshold used operationally for RI, e.g. NHC), computed from the demo
time series' own estimated wind speeds rather than asserted independently.
"""
from __future__ import annotations

from dataclasses import dataclass

from ml.preprocessing.features import CycloneFeatures

RI_THRESHOLD_KT_PER_24H = 30.0


@dataclass
class IntensityEstimate:
    wind_speed_kt: float
    wind_speed_kmh: float
    central_pressure_hpa: float
    t_number_proxy: float
    method: str


def estimate_intensity(features: CycloneFeatures) -> IntensityEstimate:
    t_number = 1 + 7 * (
        0.30 * features.cold_cloud_fraction
        + 0.25 * features.symmetry_score
        + 0.20 * features.circularity
        + 0.15 * features.eye_probability
        + 0.10 * features.spiral_band_strength
    )
    t_number = max(1.0, min(8.0, t_number))
    wind_kt = 12 + 14 * t_number
    pressure_hpa = 1010 - 0.75 * (wind_kt - 12)
    return IntensityEstimate(
        wind_speed_kt=round(wind_kt, 1),
        wind_speed_kmh=round(wind_kt * 1.852, 1),
        central_pressure_hpa=round(pressure_hpa, 1),
        t_number_proxy=round(t_number, 2),
        method="prototype_dvorak_inspired_formula",
    )


@dataclass
class TemporalTrend:
    trend: str  # "intensifying" | "weakening" | "stable"
    delta_wind_kt_24h: float
    delta_pressure_hpa_24h: float
    rapid_intensification: bool
    ri_threshold_kt_per_24h: float = RI_THRESHOLD_KT_PER_24H


def analyze_temporal_trend(wind_series_kt: list[tuple[str, float]], pressure_series_hpa: list[tuple[str, float]]) -> TemporalTrend:
    """wind_series_kt / pressure_series_hpa: list of (iso_timestamp, value), oldest first."""
    if len(wind_series_kt) < 2:
        return TemporalTrend("stable", 0.0, 0.0, False)

    # Approximate 24h delta using the earliest and latest available points
    # (demo series are generated at fixed 3h spacing covering >=24h).
    first_wind = wind_series_kt[0][1]
    last_wind = wind_series_kt[-1][1]
    first_p = pressure_series_hpa[0][1]
    last_p = pressure_series_hpa[-1][1]

    delta_wind = round(last_wind - first_wind, 1)
    delta_pressure = round(last_p - first_p, 1)

    if delta_wind > 5:
        trend = "intensifying"
    elif delta_wind < -5:
        trend = "weakening"
    else:
        trend = "stable"

    ri = delta_wind >= RI_THRESHOLD_KT_PER_24H
    return TemporalTrend(trend, delta_wind, delta_pressure, ri)
