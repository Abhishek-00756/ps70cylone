# ML / AI Pipeline

This document explains what every model/formula in this prototype actually
does, how it was built, and — most importantly — what its real limitations
are. Nothing here is presented as more accurate or more "real" than it is.

## 1. Synthetic satellite imagery (`ml/preprocessing/synthetic_satellite.py`)

No real INSAT/MOSDAC imagery was available in the build environment, so a
generator produces cyclone-like cloud structures parameterised by an
`organization` value in `[0, 1]`:

- A central dense overcast (radial Gaussian-like falloff) that both
  intensifies **and** expands as organization increases.
- Spiral rain bands via an angular sinusoidal modulation.
- An eye that appears only once organization exceeds ~0.55, growing more
  defined toward 1.0.
- Sensor-style speckle noise.

Every image the API serves is tagged `"source": "SYNTHETIC_DEMO"` end to
end (provider → API → frontend banner). **This is not real satellite data
and should never be mistaken for it.**

## 2. Feature extraction (`ml/preprocessing/features.py`)

12 features are computed per frame and reused identically by every
downstream component (classification, intensity, risk, AI-reasoning
explanations), so the system doesn't invent inconsistent numbers per page:

`mean_intensity, std_intensity, cold_cloud_fraction, symmetry_score,
circularity, spiral_band_strength, eye_probability, cloud_coverage,
sst_proxy, wind_shear_proxy, vorticity_proxy, moisture_proxy`

These are genuine image-processing computations (radial profiles, rotational
symmetry comparison, mask-based circularity, etc.) — not random numbers —
but they are proxies computed from *synthetic* imagery, not calibrated
against real meteorological measurements.

## 3. Classification (`ml/classification/classifier.py`)

Two distinct, clearly-labelled layers:

1. **IMD wind-speed scale** — the real, public 8-tier India Meteorological
   Department classification (Low Pressure Area through Super Cyclonic
   Storm), applied deterministically to the estimated wind speed. This is
   not a model output.
2. **Prototype feature classifier** — a scikit-learn `RandomForestClassifier`
   (120 trees, max depth 8) trained on the 12-dim feature vector extracted
   from synthetically generated images at various organization levels, over
   4 coarse classes (`NO_CYCLONE / DEPRESSION / CYCLONIC_STORM /
   SEVERE_CYCLONIC_STORM`). The brief calls for a CNN; no GPU/PyTorch was
   available in the build sandbox, so this stands in via the same
   `CycloneClassifier` interface a CNN would implement.

Trained via `python -m ml.training.train_classifier`. Achieves ~95-98%
accuracy **on a held-out split of the same synthetic distribution it was
trained on** — this measures whether the pipeline mechanics work, not
real-world skill.

## 4. Detection (`ml/detection/detector.py`)

Fuses `P(not NO_CYCLONE)` from the classifier with a structural score
(cloud coverage + symmetry) into one detection confidence, so detection
stays consistent with classification instead of being computed
independently.

## 5. Intensity estimation (`ml/intensity/estimator.py`)

A documented, simplified formula loosely inspired by the *structure* of the
Dvorak technique (organized, cold, symmetric, deep convection with an eye →
higher intensity) — explicitly **not** an operationally calibrated Dvorak
implementation:

```
T_number_proxy = 1 + 7 * (0.30*cold_cloud_fraction + 0.25*symmetry_score
                          + 0.20*circularity + 0.15*eye_probability
                          + 0.10*spiral_band_strength)
wind_kt = 12 + 14 * T_number_proxy
pressure_hpa = 1010 - 0.75 * (wind_kt - 12)
```

**Rapid Intensification** is flagged using the same magnitude threshold
used operationally (e.g. by NHC): a wind-speed increase of ≥30kt within the
analysed ~24h window, computed from the pipeline's own estimated wind
series (not asserted independently).

## 6. Track generation & forecasting (`ml/tracking/track_generator.py`)

The demo historical track is a smooth, curving, non-linear trajectory over
the Bay of Bengal (recurving toward the Indian east coast, a common
real-world pattern for this basin) with an organization story: slow
formation → intensification → peak → slight weakening near the coast.

Forecasting is a **prototype extrapolation model**: linear regression of
the last 3–4 historical lat/lon points against time, projected to each
requested horizon, with an uncertainty radius that grows linearly with
horizon (`25 + 1.8*hours` km). This is explicitly **not** an operational
numerical weather prediction (NWP) model or IMD's official cone of
uncertainty — it exists to demonstrate the forecasting *interface*
(`TrackPredictor`), which a real NWP-driven or ML (LSTM/GRU) model could
replace without changing any caller.

## 7. Risk engine (`ml/evaluation/risk_engine.py`)

Implements exactly the documented conceptual formula:

```
risk_score = hazard_intensity × exposure × vulnerability
```

`hazard_intensity` is derived from the estimated wind speed and forecast
landfall probability. `exposure` and `vulnerability` are **fixed,
illustrative DEMO values** (not real census/infrastructure/vulnerability
datasets) — the UI labels both explicitly as DEMO so this can never be
mistaken for a real risk assessment.

## 8. Model evaluation (`ml/evaluation/evaluate.py`)

Computes **real** accuracy, per-class precision/recall/F1, and a confusion
matrix — but only ever against an independently-seeded synthetic evaluation
set. Output is written to `data/demo/metadata/model_metrics.json` tagged
`"PROTOTYPE_SYNTHETIC_DATASET_EVALUATION"` and the frontend's Model
Performance page displays that disclaimer prominently. These numbers must
never be read as real-world operational accuracy.

## Honest summary of limitations

- No real satellite imagery, no real historical IMD best-track data, no
  real population/infrastructure/vulnerability datasets were available or
  used anywhere in this build.
- The classifier is a RandomForest over engineered features, not a trained
  CNN, due to no PyTorch/GPU access in the build sandbox.
- Track forecasting is simple extrapolation, not NWP or a trained
  sequence model.
- All formulas (intensity, risk) are documented and internally consistent,
  but are not fitted/calibrated against real historical outcomes.
- **This system is a hackathon prototype and must not be used, or
  represented, as an operational cyclone forecasting or warning tool.**
