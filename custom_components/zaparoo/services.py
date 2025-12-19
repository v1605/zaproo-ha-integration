"""Exposed user services."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

import voluptuous as vol
from homeassistant.core import SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from custom_components.zaparoo.data import ZaparooDataConfigEntry

    from .websocket_client import ZaparooWebSocket

SERVICE_LAUNCH = "launch"
SERVICE_STOP = "stop"
SERVICE_MEDIA = "media"

_LOGGER = logging.getLogger(__name__)


LAUNCH_SCHEMA = vol.Schema(
    {
        vol.Optional("type"): str,
        vol.Optional("text"): str,
        vol.Optional("data"): str,
        vol.Optional("unsafe", default=False): bool,
        vol.Optional("device_id"): object,
        vol.Optional("area_id"): object,
    }
)

NO_BODY_SCHEMA = vol.Schema(
    {
        vol.Optional("device_id"): object,
        vol.Optional("area_id"): object,
    }
)


def _device_ids_from_target(call: ServiceCall) -> list[str]:
    """Extract device IDs from HA service call."""
    device_ids = call.data.get("device_id")
    if not device_ids:
        msg = "No target devices specified"
        raise HomeAssistantError(msg)
    if isinstance(device_ids, str):
        return [device_ids]
    if isinstance(device_ids, list):
        return device_ids
    msg = "Invalid device_id type"
    raise HomeAssistantError(msg)


async def async_launch_service(call: ServiceCall) -> None:
    """Call to launch a token."""
    hass = call.hass
    _LOGGER.info("Service Data Payload: %s", call.data)

    device_ids = _device_ids_from_target(call)

    if not any(call.data.get(k) for k in ("text", "data")):
        msg = "One of 'text' or 'data' is required"
        raise HomeAssistantError(msg)

    params = {
        k: v
        for k, v in {
            "type": call.data.get("type"),
            "text": call.data.get("text"),
            "data": call.data.get("data"),
            "unsafe": call.data.get("unsafe"),
        }.items()
        if v is not None
    }

    for device_id in device_ids:
        ws = _get_ws_for_device(hass, device_id)

        try:
            response = await ws.send_jsonrpc("run", params)
        except Exception as err:
            msg = f"Launch failed: {err}"
            raise HomeAssistantError(msg) from err

        if isinstance(response, dict) and "error" in response:
            raise HomeAssistantError(response["error"])

        result = response.get("result") if isinstance(response, dict) else None
        if result not in (None, {}, []):
            msg = "Non-empty result from Zaparoo run(): %s"
            raise HomeAssistantError(msg, result)


async def async_stop_service(call: ServiceCall) -> None:
    """Call to stop the current running game."""
    hass = call.hass
    device_ids = _device_ids_from_target(call)

    for device_id in device_ids:
        ws = _get_ws_for_device(hass, device_id)

        try:
            response = await ws.send_jsonrpc("stop")
        except Exception as err:
            msg = f"Stop failed: {err}"
            raise HomeAssistantError(msg) from err

        if isinstance(response, dict) and "error" in response:
            raise HomeAssistantError(response["error"])

        result = response.get("result") if isinstance(response, dict) else None
        if result not in (None, {}, []):
            msg = "Non-empty result from Zaparoo stop(): %s"
            raise HomeAssistantError(msg, result)


async def async_media_service(call: ServiceCall) -> Any:
    """Call to return the currently running game."""
    hass = call.hass
    device_ids = _device_ids_from_target(call)
    device_id = device_ids[0]
    ws = _get_ws_for_device(hass, device_id)

    try:
        response = await ws.send_jsonrpc("media")
    except Exception as err:
        msg = f"Media query failed: {err}"
        raise HomeAssistantError(msg) from err

    if isinstance(response, dict) and "error" in response:
        raise HomeAssistantError(response["error"])

    return response.get("result") if isinstance(response, dict) else None


def async_register_services(hass: HomeAssistant) -> None:
    """Register all the above services."""
    hass.services.async_register(
        DOMAIN,
        SERVICE_LAUNCH,
        async_launch_service,
        schema=LAUNCH_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP,
        async_stop_service,
        schema=NO_BODY_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_MEDIA,
        async_media_service,
        schema=NO_BODY_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


def _get_ws_for_device(hass: HomeAssistant, device_id: str) -> ZaparooWebSocket:
    device_reg = dr.async_get(hass)
    device = device_reg.async_get(device_id)

    if device is None:
        msg = f"Device not found: {device_id}"
        raise HomeAssistantError(msg)

    for entry_id in device.config_entries:
        entry = hass.config_entries.async_get_entry(entry_id)

        if entry is None or entry.domain != DOMAIN:
            continue

        zap_entry = cast("ZaparooDataConfigEntry", entry)
        ws = zap_entry.runtime_data.client

        if ws is None:
            msg = "Zaparoo is not connected"
            raise HomeAssistantError(msg)

        return ws

    msg = "Zaparoo device not linked to config entry"
    raise HomeAssistantError(msg)
