"""Config Entry Data for Zaparoo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from custom_components.zaparoo.websocket_client import ZaparooWebSocket

    from .coordinator import ZaparooCoordinator


type ZaparooDataConfigEntry = ConfigEntry[ZaparooData]


@dataclass
class ZaparooData:
    """Data for the Zaproo integration."""

    client: ZaparooWebSocket
    coordinator: ZaparooCoordinator
    integration: Integration
