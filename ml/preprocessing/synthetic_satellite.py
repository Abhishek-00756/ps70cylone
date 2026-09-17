"""
Synthetic satellite image generator.

IMPORTANT: This produces DEMO / SYNTHETIC imagery only. It is used because a
full operational INSAT/MOSDAC satellite feed is not available in this
hackathon prototype. Nothing generated here should ever be presented to a
user as real satellite imagery — the API layer tags every image produced by
this module with `"source": "SYNTHETIC_DEMO"`.

The generator builds a plausible tropical-cyclone-like cloud structure
(spiral rain bands, central dense overcast, optional eye) parameterised by
an "organization" value in [0, 1] so that a time series of increasing
organization can be rendered to tell a coherent formation -> intensification
-> peak story, which the rest of the pipeline (feature extraction,
classification, intensity) reads back out.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class SyntheticFrameParams:
    """Parameters describing one synthetic cyclone frame.

    organization: 0 (disorganized cluster) -> 1 (extremely severe, clear eye)
    size_km: rough radius of dense cloud shield, used only to vary visual size
    rotation_deg: spiral phase, advanced over time to imply rotation
    noise_level: amount of speckle/sensor noise to add
    seed: RNG seed for reproducibility (same seed + params => same image)
    """

    organization: float
    size_km: float = 400.0
    rotation_deg: float = 0.0
    noise_level: float = 0.06
    seed: int = 0


def _radial_grid(n: int):
    ys, xs = np.mgrid[0:n, 0:n]
    cx = cy = n / 2.0
    dx = xs - cx
    dy = ys - cy
    r = np.sqrt(dx**2 + dy**2)
    theta = np.arctan2(dy, dx)
    return r, theta


def generate_infrared_frame(params: SyntheticFrameParams, size: int = 256) -> np.ndarray:
    """Generate a synthetic infrared cloud-top-temperature-proxy frame.

    Returns a float32 array in [0, 1] where higher values ~ colder cloud tops
    (i.e. brighter = colder, matching common IR cyclone imagery conventions).
    """
    rng = np.random.default_rng(params.seed)
    r, theta = _radial_grid(size)
    max_r = size / 2.0
    org = float(np.clip(params.organization, 0.0, 1.0))

    # Central dense overcast: as organization increases the cold-cloud
    # shield both intensifies and expands (consistent with real CDO growth
    # during intensification), while also becoming more sharply bounded.
    core_radius = max_r * (0.35 + 0.20 * org)
    sharpness = 1.3 + 1.2 * org
    core = np.exp(-((r / max(core_radius, 1e-3)) ** sharpness))
    core = core * (0.55 + 0.45 * org)  # overall coldness/peak also rises with organization

    # Spiral rain bands: sinusoidal modulation in angle+radius, phase advances
    # with rotation_deg to simulate a rotating system over time.
    n_bands = 3
    phase = math.radians(params.rotation_deg)
    spiral = 0.5 + 0.5 * np.sin(n_bands * theta + r / (12.0 + 4.0 * (1 - org)) + phase)
    band_strength = 0.25 + 0.35 * org
    field = core * (1 - band_strength) + core * spiral * band_strength

    # Eye: only appears once organization is high enough (severe cyclonic storm+)
    if org > 0.55:
        eye_strength = (org - 0.55) / 0.45
        eye_radius = max_r * 0.06 * (1.0 + (1 - org))
        eye = np.exp(-((r / max(eye_radius, 1e-3)) ** 2))
        field = field * (1 - 0.85 * eye_strength * eye)

    # Background environment (warmer / lower values) with gentle large-scale texture
    bg_texture = 0.08 * np.sin(theta * 2 + r / 40.0)
    field = np.clip(field + bg_texture * (1 - core), 0, 1)

    noise = rng.normal(0, params.noise_level, size=(size, size))
    field = np.clip(field + noise, 0.0, 1.0)
    return field.astype(np.float32)


def generate_visible_frame(ir_frame: np.ndarray, seed: int = 0) -> np.ndarray:
    """Derive a synthetic 'visible' channel from the IR frame (cloud brightness)."""
    rng = np.random.default_rng(seed + 1)
    vis = np.clip(ir_frame * 0.9 + rng.normal(0, 0.03, ir_frame.shape), 0, 1)
    return vis.astype(np.float32)


def generate_water_vapor_frame(ir_frame: np.ndarray, seed: int = 0) -> np.ndarray:
    """Derive a synthetic water-vapour channel (smoother, broader moisture plume)."""
    rng = np.random.default_rng(seed + 2)
    n = ir_frame.shape[0]
    r, theta = _radial_grid(n)
    plume = np.exp(-(r / (n * 0.4)) ** 2)
    wv = np.clip(0.5 * ir_frame + 0.5 * plume + rng.normal(0, 0.04, ir_frame.shape), 0, 1)
    return wv.astype(np.float32)


def frame_to_png_bytes(frame: np.ndarray, colormap: str = "ir") -> bytes:
    """Render a [0,1] float frame to PNG bytes using a simple colormap, no external deps beyond PIL."""
    from PIL import Image

    # NOTE: do all arithmetic in int16 before the final uint8 cast -- doing
    # it directly in uint8 silently wraps around (e.g. 255+20 -> 19) instead
    # of clipping, which corrupted the rendered colors.
    img = (np.clip(frame, 0, 1) * 255).astype(np.int16)
    if colormap == "ir":
        # Classic inverted-grayscale IR look: cold (high value) -> white/light
        r = np.clip(255 - img, 0, 255)
        g = np.clip(255 - img, 0, 255)
        b = np.clip(255 - img + 20, 0, 255)
        rgb = np.stack([r, g, b], axis=-1).astype(np.uint8)
    elif colormap == "wv":
        # Blue-toned water vapour look
        rgb = np.stack([img // 3, img // 2, img], axis=-1).astype(np.uint8)
    else:  # visible
        rgb = np.stack([img, img, img], axis=-1).astype(np.uint8)
    return_bytes = Image.fromarray(rgb, mode="RGB")
    from io import BytesIO

    buf = BytesIO()
    return_bytes.save(buf, format="PNG")
    return buf.getvalue()
