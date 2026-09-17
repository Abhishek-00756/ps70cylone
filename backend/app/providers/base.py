"""
SatelliteDataProvider abstraction so the application is never tightly
coupled to one data source. Real providers (IMD/MOSDAC) can be added later
by implementing this interface -- nothing else in the codebase needs to
change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class SatelliteDataProvider(ABC):
    name: str = "base"
    status: str = "UNAVAILABLE"  # CONNECTED | DEMO | UNAVAILABLE

    @abstractmethod
    def get_frame_png(self, cyclone_id: str, timestamp: str, channel: str) -> bytes:
        """Return PNG bytes for the given channel ('infrared'|'visible'|'water_vapor')."""
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> dict:
        raise NotImplementedError


class ProviderUnavailableError(RuntimeError):
    """Raised when LIVE_DATA mode is requested but no real provider is configured."""
