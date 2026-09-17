"""
Risk & Impact engine.

Documented formula (kept intentionally simple and transparent for a
prototype -- exact conceptual form requested in the brief):

    risk_score = hazard_intensity * exposure * vulnerability

Where, in this prototype:
  hazard_intensity in [0,1]: derived from estimated wind speed (normalized
      against the IMD Super Cyclonic Storm threshold of 120kt) and forecast
      landfall proximity.
  exposure in [0,1]: DEMO layer -- a fixed illustrative population/
      infrastructure density for the predicted landfall stretch of coast.
      Clearly labelled DEMO DATA; a real deployment would use gridded
      census + infrastructure datasets.
  vulnerability in [0,1]: DEMO layer -- a fixed illustrative coastal
      vulnerability index (e.g. low-lying delta terrain increases this).

None of these are fabricated "AI outputs" -- they are declared inputs
multiplied together per the stated formula, so risk_score is fully
traceable.
"""
from __future__ import annotations

from dataclasses import dataclass

IMD_MAX_SCALE_KT = 120.0

# DEMO exposure/vulnerability layers for the fictional landfall stretch used
# in the demo track (illustrative only, not real census/infrastructure data).
DEMO_EXPOSURE = 0.72
DEMO_VULNERABILITY = 0.68


@dataclass
class RiskAssessment:
    hazard_intensity: float
    exposure: float
    vulnerability: float
    overall_risk_score: float
    risk_category: str
    wind_risk: str
    rainfall_risk: str
    storm_surge_risk: str
    method: str = "hazard_x_exposure_x_vulnerability (demo exposure/vulnerability layers)"


def _bucket(score: float) -> str:
    if score < 0.15:
        return "LOW"
    if score < 0.35:
        return "MODERATE"
    if score < 0.55:
        return "HIGH"
    if score < 0.75:
        return "SEVERE"
    return "EXTREME"


def assess_risk(wind_speed_kt: float, landfall_probability: float, rainfall_intensity_proxy: float) -> RiskAssessment:
    hazard_intensity = max(0.0, min(1.0, (wind_speed_kt / IMD_MAX_SCALE_KT) * (0.4 + 0.6 * landfall_probability)))
    overall = round(hazard_intensity * DEMO_EXPOSURE * DEMO_VULNERABILITY, 4)

    wind_risk = _bucket(hazard_intensity)
    rainfall_risk = _bucket(max(0.0, min(1.0, rainfall_intensity_proxy)))
    surge_risk = _bucket(max(0.0, min(1.0, hazard_intensity * (0.5 + 0.5 * landfall_probability))))

    return RiskAssessment(
        hazard_intensity=round(hazard_intensity, 4),
        exposure=DEMO_EXPOSURE,
        vulnerability=DEMO_VULNERABILITY,
        overall_risk_score=overall,
        risk_category=_bucket(overall),
        wind_risk=wind_risk,
        rainfall_risk=rainfall_risk,
        storm_surge_risk=surge_risk,
    )
