"""
Computes REAL metrics for the prototype classifier -- but only ever on the
synthetic dataset it was trained/tested against. Results are written to
data/demo/metadata/model_metrics.json and explicitly tagged
"Prototype / Synthetic Dataset Evaluation" so the frontend cannot present
them as real-world operational performance.

Run: python -m ml.evaluation.evaluate
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score, precision_recall_fscore_support

from ml.classification.classifier import CycloneClassifier, MODEL_CLASSES
from ml.training.train_classifier import build_dataset

OUTPUT_PATH = Path(__file__).resolve().parents[2] / "data" / "demo" / "metadata" / "model_metrics.json"


def main():
    X, y = build_dataset(n_per_class=40, seed=99)  # independent synthetic eval set (different seed)
    clf = CycloneClassifier.load()
    preds = clf.model.predict(X)

    acc = accuracy_score(y, preds)
    precision, recall, f1, support = precision_recall_fscore_support(
        y, preds, labels=MODEL_CLASSES, zero_division=0
    )
    cm = confusion_matrix(y, preds, labels=MODEL_CLASSES)

    metrics = {
        "dataset": "PROTOTYPE_SYNTHETIC_DATASET_EVALUATION",
        "disclaimer": "Computed entirely on synthetically generated demo imagery. Not indicative of real-world operational accuracy.",
        "n_samples": int(len(y)),
        "classes": MODEL_CLASSES,
        "accuracy": round(float(acc), 4),
        "per_class": [
            {
                "class": c,
                "precision": round(float(p), 4),
                "recall": round(float(r), 4),
                "f1": round(float(f), 4),
                "support": int(s),
            }
            for c, p, r, f, s in zip(MODEL_CLASSES, precision, recall, f1, support)
        ],
        "confusion_matrix": cm.tolist(),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))
    print(f"\nWritten to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
