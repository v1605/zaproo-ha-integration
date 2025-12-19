"""Coordinator that stores push-state and broadcasts events to event-entities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
)

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import ZaparooDataConfigEntry

_LOGGER = logging.getLogger(__name__)


class ZaparooCoordinator(DataUpdateCoordinator):
    """Stores state pushed from websocket."""

    config_entry: ZaparooDataConfigEntry

    def __init__(self, hass: HomeAssistant) -> None:
        """Init the cooridnator base state."""
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.data = {
            "media": None,
            "indexing": None,
            "readers": {},
            "last_token": None,
            "playtime": None,
            "connected": False,
        }

    def handle_ws_event(self, method: str, params: dict) -> None:
        """Call when websocket_client wevent occurs."""
        if method == "media.started":
            self.data["media"] = params
        elif method == "media.stopped":
            self.data["media"] = None
        elif method == "media.indexing":
            self.data["indexing"] = params
        elif method == "readers.added":
            self.data["readers"][params["path"]] = params
        elif method == "readers.removed":
            self.data["readers"].pop(params["path"], None)
        elif method == "tokens.added":
            self.data["last_token"] = params
        elif method == "tokens.removed":
            self.data["last_token"] = None
        elif method.startswith("playtime.limit"):
            self.data["playtime"] = params

        self.data["last_event_method"] = method
        self.data["last_event_params"] = params

        self.async_set_updated_data(self.data)

    def disconnected(self) -> None:
        """Set connected to false."""
        self.data["connected"] = False
        self.data["last_event_method"] = None
        self.data["last_event_params"] = None
        self.async_set_updated_data(self.data)

    def connected(self) -> None:
        """Set connected to true."""
        self.data["connected"] = True
        self.async_set_updated_data(self.data)
