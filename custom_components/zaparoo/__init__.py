"""Zaparoo integration init."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.loader import async_get_loaded_integration

from custom_components.zaparoo.coordinator import ZaparooCoordinator
from custom_components.zaparoo.data import ZaparooData, ZaparooDataConfigEntry
from custom_components.zaparoo.services import async_register_services
from custom_components.zaparoo.websocket_client import ZaparooWebSocket

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
PLATFORMS = [Platform.SENSOR, Platform.EVENT]


async def async_setup_entry(hass: HomeAssistant, entry: ZaparooDataConfigEntry) -> bool:
    """Set up a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Store host/port
    hass.data[DOMAIN][entry.entry_id] = {
        "host": entry.data["host"],
        "port": entry.data["port"],
    }

    coordinator = ZaparooCoordinator(
        hass=hass,
    )

    entry.runtime_data = ZaparooData(
        client=ZaparooWebSocket(
            host=entry.data["host"],
            port=entry.data["port"],
            coordinator=coordinator,
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )
    await entry.runtime_data.client.start()
    # Load the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_register_services(hass)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ZaparooDataConfigEntry
) -> bool:
    """Unload a config entry."""
    await entry.runtime_data.client.stop()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
