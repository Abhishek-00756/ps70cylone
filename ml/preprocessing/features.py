"""
Feature extraction from a (synthetic, demo-labelled) satellite frame.

These features are computed once per frame and reused by every downstream
component (classification, intensity estimation, rapid-intensification
detection, risk scoring, AI-reasoning explanations) so the system is
internally consistent rather than having each page invent its own numbers.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np


@dataclass
class CycloneFeatures:
    mean_intensity: float          # overall brightness/coldness proxy [0,1]
    std_intensity: float           # texture / variability
    cold_cloud_fraction: float     # fraction of pixels colder than threshold
    symmetry_score: float          # 0..1, radial symmetry of the cloud field
    circularity: float             # 0..1, how circular the dense-cloud mask is
    spiral_band_strength: float    # 0..1, strength of angular banding
    eye_probability: float         # 0..1, likelihood of a clear eye
    cloud_coverage: float          # fraction of frame covered by dense cloud
    sst_proxy: float               # 0..1 synthetic sea-surface-temperature proxy
    wind_shear_proxy: float        # 0..1 (0 = low shear/favorable, 1 = high shear)
    vorticity_proxy: float         # 0..1 low-level vorticity proxy
    moisture_proxy: float          # 0..1 mid-level moisture proxy

    def to_dict(self) -> dict:
        return {k: round(float(v), 4) for k, v in asdict(self).items()}


def _radial_profile(frame: np.ndarray, n_bins: int = 24) -> np.ndarray:
    h, w = frame.shape
    cy, cx = h / 2.0, w / 2.0
    ys, xs = np.mgrid[0:h, 0:w]
    r = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2)
    r_max = r.max()
    bins = (r / r_max * (n_bins - 1)).astype(int)
    profile = np.zeros(n_bins, dtype=np.float64)
    counts = np.zeros(n_bins, dtype=np.float64)
    np.add.at(profile, bins, frame)
    np.add.at(counts, bins, 1)
    counts[counts == 0] = 1
    return profile / counts


def extract_features(
    ir_frame: np.ndarray,
    *,
    env_sst_proxy: float | None = None,
    env_wind_shear_proxy: float | None = None,
    rng_seed: int = 0,
) -> CycloneFeatures:
    """Extract a fixed feature vector from an infrared demo frame.

    env_sst_proxy / env_wind_shear_proxy let the caller inject a slowly
    varying environmental context (used by the demo track generator so a
    time series tells a coherent physical story); if omitted they are
    derived deterministically from the frame itself.
    """
    h, w = ir_frame.shape
    mean_intensity = float(ir_frame.mean())
    std_intensity = float(ir_frame.std())

    cold_threshold = 0.6
    cold_cloud_fraction = float((ir_frame > cold_threshold).mean())
    cloud_coverage = float((ir_frame > 0.35).mean())

    # Symmetry: compare frame to its 180-degree rotation. High similarity => symmetric.
    rotated = np.rot90(ir_frame, 2)
    diff = np.abs(ir_frame - rotated)
    symmetry_score = float(np.clip(1.0 - diff.mean() / (ir_frame.mean() + 1e-6), 0, 1))

    # Circularity of the dense-cloud mask via area/perimeter-style proxy.
    mask = ir_frame > 0.5
    area = mask.sum()
    if area > 10:
        ys, xs = np.nonzero(mask)
        cy, cx = ys.mean(), xs.mean()
        radii = np.sqrt((ys - cy) ** 2 + (xs - cx) ** 2)
        circularity = float(np.clip(1.0 - (radii.std() / (radii.mean() + 1e-6)), 0, 1))
    else:
        circularity = 0.0

    # Spiral band strength: variance of the angular profile at mid-radius.
    profile = _radial_profile(ir_frame)
    mid = profile[len(profile) // 3 : 2 * len(profile) // 3]
    spiral_band_strength = float(np.clip(mid.std() * 4.0, 0, 1))

    # Eye probability: a local minimum surrounded by a much colder ring near the center.
    cy_i, cx_i = h // 2, w // 2
    patch = ir_frame[max(cy_i - 6, 0): cy_i + 6, max(cx_i - 6, 0): cx_i + 6]
    ring = ir_frame[max(cy_i - 24, 0): cy_i + 24, max(cx_i - 24, 0): cx_i + 24]
    center_val = float(patch.mean()) if patch.size else 0.0
    ring_val = float(ring.mean()) if ring.size else 0.0
    eye_probability = float(np.clip((ring_val - center_val) * 2.2, 0, 1))

    sst_proxy = float(np.clip(env_sst_proxy if env_sst_proxy is not None else 0.55 + 0.2 * mean_intensity, 0, 1))
    wind_shear_proxy = float(
        np.clip(env_wind_shear_proxy if env_wind_shear_proxy is not None else 0.5 - 0.3 * symmetry_score, 0, 1)
    )
    vorticity_proxy = float(np.clip(0.3 + 0.6 * circularity, 0, 1))
    moisture_proxy = float(np.clip(0.4 + 0.5 * cloud_coverage, 0, 1))

    return CycloneFeatures(
        mean_intensity=mean_intensity,
        std_intensity=std_intensity,
        cold_cloud_fraction=cold_cloud_fraction,
        symmetry_score=symmetry_score,
        circularity=circularity,
        spiral_band_strength=spiral_band_strength,
        eye_probability=eye_probability,
        cloud_coverage=cloud_coverage,
        sst_proxy=sst_proxy,
        wind_shear_proxy=wind_shear_proxy,
        vorticity_proxy=vorticity_proxy,
        moisture_proxy=moisture_proxy,
    )


FEATURE_ORDER = [
    "mean_intensity", "std_intensity", "cold_cloud_fraction", "symmetry_score",
    "circularity", "spiral_band_strength", "eye_probability", "cloud_coverage",
    "sst_proxy", "wind_shear_proxy", "vorticity_proxy", "moisture_proxy",
]


def features_to_vector(f: CycloneFeatures) -> np.ndarray:
    d = f.to_dict()
    return np.array([d[name] for name in FEATURE_ORDER], dtype=np.float32)
