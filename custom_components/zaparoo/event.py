"""Event entities for Zaparoo notifications."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.event import EventEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import EVENT_METHOD_MAP, TRIGGER_TYPES

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ZaparooCoordinator
    from .data import ZaparooDataConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Required
    entry: ZaparooDataConfigEntry,
    add_entities: AddEntitiesCallback,
) -> None:
    """Set the config entry."""
    coordinator = entry.runtime_data.coordinator
    add_entities([ZaparooEventEntity(entry, coordinator)])


class ZaparooEventEntity(CoordinatorEntity, EventEntity):
    """Event entity that fires when Zaparoo pushes an event."""

    _attr_has_entity_name = True
    _attr_name = "Zaparoo Events"
    _attr_icon = "mdi:bell-ring"

    def __init__(
        self, entry: ZaparooDataConfigEntry, coordinator: ZaparooCoordinator
    ) -> None:
        """Init the actual config entry."""
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_event_stream"

    @property
    def event_types(self) -> list[str]:
        """List of all possible event types this entity can emit."""
        return TRIGGER_TYPES

    @property
    def _event_data(self) -> Any:
        """Return last event data from coordinator."""
        return self.coordinator.data.get("last_event_params")

    @property
    def _event_type(self) -> str | None:
        """Return last event type from coordinator."""
        method = self.coordinator.data.get("last_event_method")
        if not method:
            return None

        event_type = EVENT_METHOD_MAP.get(method)
        if not event_type:
            _LOGGER.debug("Unknown Zaparoo event method: %s", method)
            return None

        return event_type

    def _handle_coordinator_update(self) -> None:
        """Coordinator pushes new data."""
        event_type = self._event_type
        event_data = self._event_data

        if event_type:
            _LOGGER.debug("Firing HA event entity: %s | %s", event_type, event_data)
            self._trigger_event(event_type, event_data)

        super()._handle_coordinator_update()
