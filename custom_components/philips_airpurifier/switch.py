"""Philips Air Purifier switch platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import ATTR_DEVICE_CLASS, CONF_ENTITY_CATEGORY

from .const import SWITCH_OFF, SWITCH_ON, SWITCH_TYPES, FanAttributes
from .entity import PhilipsAirPurifierEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .__init__ import PhilipsAirPurifierConfigEntry
    from .coordinator import PhilipsAirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsAirPurifierConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    coordinator = entry.runtime_data
    model_config = coordinator.model_config

    async_add_entities(PhilipsSwitch(coordinator, kind) for kind in SWITCH_TYPES if kind in model_config.switches)


class PhilipsSwitch(PhilipsAirPurifierEntity, SwitchEntity):
    """Philips AirPurifier switch."""

    _attr_is_on: bool | None = False

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
        kind: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)

        self._description = SWITCH_TYPES[kind]
        self._on = self._description.get(SWITCH_ON)
        self._off = self._description.get(SWITCH_OFF)
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_translation_key = self._description.get(FanAttributes.LABEL)
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)
        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{kind.lower()}"
        self.kind = kind

    @property
    def is_on(self) -> bool:
        """Return if switch is on."""
        return self._device_status.get(self.kind) != self._off

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self.coordinator.async_set_control_value(self.kind, self._on)
        self._device_status[self.kind] = self._on
        self._handle_coordinator_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self.coordinator.async_set_control_value(self.kind, self._off)
        self._device_status[self.kind] = self._off
        self._handle_coordinator_update()
