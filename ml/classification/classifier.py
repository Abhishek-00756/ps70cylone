"""
Cyclone classification.

Two layers are used, and the UI must always say which one produced a value:

1. IMD_SCALE: the real, public India Meteorological Department wind-speed
   classification scale (documented below with citation of the thresholds).
   This is deterministic and not a "model" -- it is just the official
   category boundaries applied to an estimated wind speed.

2. FeatureClassifier: a lightweight scikit-learn RandomForest trained on
   *synthetic* demo images (see ml/training/train_classifier.py) that maps
   extracted cloud-structure features -> a coarse category
   (NO_CYCLONE / DEPRESSION / CYCLONIC_STORM / SEVERE_CYCLONIC_STORM). This
   stands in for the CNN specified in the brief: no GPU-training framework
   (PyTorch) or internet access was available in the build environment, so a
   CNN could not actually be trained here. The interface
   (`CycloneClassifier`) is designed so a real CNN can be dropped in later
   without changing any caller.

Both layers are clearly labelled "Prototype / Synthetic" wherever the API
returns them.
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ml.preprocessing.features import CycloneFeatures, features_to_vector

# --- Real IMD wind-speed classification scale (public IMD criteria, in knots) ---
IMD_SCALE = [
    ("LOW_PRESSURE_AREA", 0, 17),
    ("DEPRESSION", 17, 28),
    ("DEEP_DEPRESSION", 28, 34),
    ("CYCLONIC_STORM", 34, 48),
    ("SEVERE_CYCLONIC_STORM", 48, 64),
    ("VERY_SEVERE_CYCLONIC_STORM", 64, 90),
    ("EXTREMELY_SEVERE_CYCLONIC_STORM", 90, 120),
    ("SUPER_CYCLONIC_STORM", 120, 10_000),
]

MODEL_CLASSES = ["NO_CYCLONE", "DEPRESSION", "CYCLONIC_STORM", "SEVERE_CYCLONIC_STORM"]

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "classifier.pkl"


def classify_by_wind_speed_kt(wind_kt: float) -> str:
    """Deterministic mapping using the real IMD scale. Not a model prediction."""
    for name, lo, hi in IMD_SCALE:
        if lo <= wind_kt < hi:
            return name
    return IMD_SCALE[-1][0]


@dataclass
class ClassificationResult:
    predicted_class: str
    confidence: float
    class_probabilities: dict
    method: str  # "prototype_feature_classifier"


class CycloneClassifier:
    """Interface: swap in a real CNN later by implementing `.predict(features)`."""

    def __init__(self, model: RandomForestClassifier | None = None):
        self.model = model

    @classmethod
    def load(cls, path: Path = DEFAULT_MODEL_PATH) -> "CycloneClassifier":
        if not path.exists():
            raise FileNotFoundError(
                f"No trained classifier at {path}. Run `python -m ml.training.train_classifier` first."
            )
        with open(path, "rb") as f:
            model = pickle.load(f)
        return cls(model=model)

    def save(self, path: Path = DEFAULT_MODEL_PATH) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.model, f)

    def fit(self, X: np.ndarray, y: Sequence[str]) -> None:
        self.model = RandomForestClassifier(
            n_estimators=120, max_depth=8, random_state=42, class_weight="balanced"
        )
        self.model.fit(X, y)

    def predict(self, features: CycloneFeatures) -> ClassificationResult:
        if self.model is None:
            raise RuntimeError("Classifier not loaded/fitted.")
        vec = features_to_vector(features).reshape(1, -1)
        proba = self.model.predict_proba(vec)[0]
        classes = list(self.model.classes_)
        probs = {c: round(float(p), 4) for c, p in zip(classes, proba)}
        best_idx = int(np.argmax(proba))
        return ClassificationResult(
            predicted_class=classes[best_idx],
            confidence=round(float(proba[best_idx]), 4),
            class_probabilities=probs,
            method="prototype_feature_classifier",
        )
