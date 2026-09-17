"""
Cyclone detection: is there an organized tropical system present at all?

Prototype approach (documented, not claimed as CNN-based): combines the
feature classifier's P(not NO_CYCLONE) with a simple structural check
(cloud coverage + symmetry) into a single detection confidence. This keeps
detection consistent with classification instead of being an independent
random number.
"""
from __future__ import annotations

from dataclasses import dataclass

from ml.classification.classifier import CycloneClassifier, ClassificationResult
from ml.preprocessing.features import CycloneFeatures


@dataclass
class DetectionResult:
    detected: bool
    confidence: float
    method: str


def detect_cyclone(features: CycloneFeatures, classification: ClassificationResult) -> DetectionResult:
    structural_score = min(1.0, 0.5 * features.cloud_coverage + 0.5 * features.symmetry_score)
    p_no_cyclone = classification.class_probabilities.get("NO_CYCLONE", 0.0)
    p_cyclone = 1.0 - p_no_cyclone
    confidence = round(0.6 * p_cyclone + 0.4 * structural_score, 4)
    return DetectionResult(
        detected=confidence >= 0.5,
        confidence=confidence,
        method="prototype_feature_and_classifier_fusion",
    )
