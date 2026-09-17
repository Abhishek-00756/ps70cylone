from __future__ import annotations

from ml.preprocessing.synthetic_satellite import (
    SyntheticFrameParams,
    generate_infrared_frame,
    generate_visible_frame,
    generate_water_vapor_frame,
    frame_to_png_bytes,
)

from app.providers.base import SatelliteDataProvider


class DemoSatelliteProvider(SatelliteDataProvider):
    """Generates synthetic, clearly-labelled demo imagery locally.

    Frame content is looked up by (cyclone_id, timestamp) against the demo
    track store so every channel/timestamp combination stays consistent with
    the rest of the dashboard.
    """

    name = "Demo Synthetic Provider"
    status = "DEMO"

    def __init__(self, track_lookup):
        # track_lookup(cyclone_id, timestamp) -> TrackPoint-like object with
        # .organization / rotation seed info, supplied by the cyclone service.
        self._track_lookup = track_lookup

    def describe(self) -> dict:
        return {
            "source": "SYNTHETIC_DEMO",
            "status": self.status,
            "name": self.name,
            "data_type": "Synthetically generated cloud-structure imagery",
            "purpose": "Stand-in for INSAT/MOSDAC imagery when no live feed is configured",
        }

    def get_frame_png(self, cyclone_id: str, timestamp: str, channel: str) -> bytes:
        point, index = self._track_lookup(cyclone_id, timestamp)
        params = SyntheticFrameParams(
            organization=point.organization,
            rotation_deg=index * 25,
            noise_level=0.06,
            seed=index,
        )
        ir = generate_infrared_frame(params)
        if channel == "infrared":
            return frame_to_png_bytes(ir, colormap="ir")
        if channel == "visible":
            vis = generate_visible_frame(ir, seed=index)
            return frame_to_png_bytes(vis, colormap="visible")
        if channel == "water_vapor":
            wv = generate_water_vapor_frame(ir, seed=index)
            return frame_to_png_bytes(wv, colormap="wv")
        raise ValueError(f"Unknown channel: {channel}")


class IMDSatelliteProvider(SatelliteDataProvider):
    """Placeholder for a real IMD satellite product integration.

    Not implemented: IMD does not currently expose a public, credential-free
    satellite imagery API suitable for this prototype. Wire this up by
    implementing get_frame_png() against the real product endpoint and
    setting SATELLITE_PROVIDER=imd with IMD_API_KEY configured.
    """

    name = "IMD Satellite (not configured)"
    status = "UNAVAILABLE"

    def describe(self) -> dict:
        return {
            "source": "IMD",
            "status": self.status,
            "name": self.name,
            "data_type": "INSAT-3D/3DR satellite products",
            "purpose": "Real operational imagery (requires credentials, not available in this prototype)",
        }

    def get_frame_png(self, cyclone_id: str, timestamp: str, channel: str) -> bytes:
        from app.providers.base import ProviderUnavailableError

        raise ProviderUnavailableError("IMD live provider is not configured in this prototype.")


class MOSDACProvider(SatelliteDataProvider):
    """Placeholder for a real ISRO MOSDAC data integration. See IMDSatelliteProvider docstring."""

    name = "MOSDAC (not configured)"
    status = "UNAVAILABLE"

    def describe(self) -> dict:
        return {
            "source": "MOSDAC",
            "status": self.status,
            "name": self.name,
            "data_type": "SST, OLR, QPE, Cloud Motion Vectors",
            "purpose": "Real multi-source environmental data (requires credentials, not available in this prototype)",
        }

    def get_frame_png(self, cyclone_id: str, timestamp: str, channel: str) -> bytes:
        from app.providers.base import ProviderUnavailableError

        raise ProviderUnavailableError("MOSDAC live provider is not configured in this prototype.")
