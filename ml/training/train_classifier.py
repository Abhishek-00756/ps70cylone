"""
Builds a synthetic labelled dataset (organization level -> coarse class) and
trains the prototype RandomForest feature-classifier described in
ml/classification/classifier.py.

This is intentionally a SYNTHETIC / PROTOTYPE training run: labels come from
the same generator that produced the images (by construction), so this
demonstrates the pipeline mechanics, not real-world skill. Real skill can
only be measured once genuine labelled satellite data is used -- see
docs/ml_pipeline.md for the honest limitations section.

Run: python -m ml.training.train_classifier
"""
from __future__ import annotations

import numpy as np

from ml.classification.classifier import CycloneClassifier, MODEL_CLASSES
from ml.preprocessing.features import extract_features, features_to_vector
from ml.preprocessing.synthetic_satellite import SyntheticFrameParams, generate_infrared_frame


def organization_to_label(org: float) -> str:
    if org < 0.12:
        return "NO_CYCLONE"
    if org < 0.35:
        return "DEPRESSION"
    if org < 0.6:
        return "CYCLONIC_STORM"
    return "SEVERE_CYCLONIC_STORM"


def build_dataset(n_per_class: int = 60, seed: int = 7):
    rng = np.random.default_rng(seed)
    X, y = [], []
    # Sample organization values densely enough to cover every class boundary.
    org_ranges = {
        "NO_CYCLONE": (0.0, 0.12),
        "DEPRESSION": (0.12, 0.35),
        "CYCLONIC_STORM": (0.35, 0.6),
        "SEVERE_CYCLONIC_STORM": (0.6, 1.0),
    }
    for label, (lo, hi) in org_ranges.items():
        for _ in range(n_per_class):
            org = float(rng.uniform(lo, hi))
            rot = float(rng.uniform(0, 360))
            noise = float(rng.uniform(0.03, 0.1))
            frame = generate_infrared_frame(
                SyntheticFrameParams(organization=org, rotation_deg=rot, noise_level=noise, seed=int(rng.integers(0, 1_000_000)))
            )
            feats = extract_features(frame)
            X.append(features_to_vector(feats))
            y.append(label)
    return np.array(X), np.array(y)


def main():
    X, y = build_dataset()
    n = len(X)
    idx = np.random.default_rng(0).permutation(n)
    split = int(n * 0.8)
    train_idx, test_idx = idx[:split], idx[split:]

    clf = CycloneClassifier()
    clf.fit(X[train_idx], y[train_idx])
    clf.save()

    # quick train-set sanity check (full evaluation lives in ml/evaluation)
    preds = clf.model.predict(X[test_idx])
    acc = float((preds == y[test_idx]).mean())
    print(f"Trained prototype classifier on {len(train_idx)} synthetic samples.")
    print(f"Held-out synthetic accuracy: {acc:.3f} (SYNTHETIC DATA -- not a real-world metric)")
    print(f"Classes: {MODEL_CLASSES}")


if __name__ == "__main__":
    main()
