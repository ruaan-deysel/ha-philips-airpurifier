"""Philips Air Purifier event platform.

Exposes device notifications (error / warning codes reported by the purifier) as
a Home Assistant event entity. The entity reads the status published by the
``philips-airctrl`` library through the coordinator; it never talks to the
device directly.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.event import EventEntity
from homeassistant.const import EntityCategory
from homeassistant.core import callback

from .const import PhilipsApi
from .entity import PhilipsAirPurifierEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .__init__ import PhilipsAirPurifierConfigEntry
    from .coordinator import PhilipsAirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

# Status keys that carry a device error/notification code, across API
# generations. The first key present in the status payload is used.
_ERROR_CODE_KEYS: tuple[str, ...] = (
    PhilipsApi.ERROR_CODE,  # Gen1 "err"
    PhilipsApi.NEW2_ERROR_CODE,  # Gen3 "D03240"
)

# Out-of-water is encoded in bit 9 of the error code on the models that report
# it; surfacing it as a distinct event makes automations easier to write.
_OUT_OF_WATER_BIT = 1 << 8

EVENT_ERROR = "error"
EVENT_OUT_OF_WATER = "out_of_water"
EVENT_CLEARED = "cleared"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsAirPurifierConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the event platform."""
    coordinator = entry.runtime_data
    status = coordinator.data or {}

    if any(key in status for key in _ERROR_CODE_KEYS):
        async_add_entities([PhilipsNotificationEvent(coordinator)])


class PhilipsNotificationEvent(PhilipsAirPurifierEntity, EventEntity):
    """Event entity that fires when the device raises or clears a notification."""

    _attr_translation_key = "notification"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_event_types = [EVENT_ERROR, EVENT_OUT_OF_WATER, EVENT_CLEARED]

    def __init__(self, coordinator: PhilipsAirPurifierCoordinator) -> None:
        """Initialize the notification event entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-notification"
        # Seeded on the first refresh so an already-present code at startup does
        # not fire a spurious event.
        self._last_code: int | None = None

    def _read_code(self) -> tuple[str | None, int]:
        """Return the active error-code key and its integer value."""
        status = self._device_status or {}
        for key in _ERROR_CODE_KEYS:
            if key in status:
                try:
                    return key, int(status[key])
                except TypeError, ValueError:
                    return key, 0
        return None, 0

    @callback
    def _handle_coordinator_update(self) -> None:
        """Fire an event when the device's notification code changes."""
        source_key, code = self._read_code()

        if self._last_code is None:
            # First update after startup: record the baseline without firing.
            self._last_code = code
        elif code != self._last_code:
            details: dict[str, Any] = {"code": code, "source": source_key}
            if code == 0:
                event_type = EVENT_CLEARED
            elif code & _OUT_OF_WATER_BIT:
                event_type = EVENT_OUT_OF_WATER
            else:
                event_type = EVENT_ERROR
            self._trigger_event(event_type, details)
            self._last_code = code

        super()._handle_coordinator_update()
