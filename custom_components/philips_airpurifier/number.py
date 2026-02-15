"""Philips Air Purifier number platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity
from homeassistant.components.number.const import NumberMode
from homeassistant.const import ATTR_DEVICE_CLASS, ATTR_ICON, CONF_ENTITY_CATEGORY

from .const import NUMBER_TYPES, FanAttributes
from .entity import PhilipsAirPurifierEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .__init__ import PhilipsAirPurifierConfigEntry
    from .coordinator import PhilipsAirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

NUMBER_ICON_FALLBACKS: dict[str, str] = {
    FanAttributes.OSCILLATION: "mdi:rotate-right",
    FanAttributes.TARGET_TEMP: "mdi:thermometer",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsAirPurifierConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    coordinator = entry.runtime_data
    model_config = coordinator.model_config

    configured_numbers = set(model_config.numbers)
    configured_numbers.update(kind for kind in model_config.humidifiers if kind in NUMBER_TYPES)

    async_add_entities(PhilipsNumber(coordinator, kind) for kind in NUMBER_TYPES if kind in configured_numbers)


class PhilipsNumber(PhilipsAirPurifierEntity, NumberEntity):
    """Philips AirPurifier number."""

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
        kind: str,
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)

        self._description = NUMBER_TYPES[kind]
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_translation_key = self._description.get(FanAttributes.LABEL)
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)
        self._attr_icon = self._description.get(ATTR_ICON)
        if self._attr_icon is None:
            label = self._description.get(FanAttributes.LABEL)
            if isinstance(label, str):
                self._attr_icon = NUMBER_ICON_FALLBACKS.get(label)
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_unit_of_measurement = self._description.get(FanAttributes.UNIT)

        self._attr_native_min_value = float(self._description.get(FanAttributes.OFF) or 0)
        self._min = float(self._description.get(FanAttributes.MIN) or 0)
        self._attr_native_max_value = float(self._description.get(FanAttributes.MAX) or self._attr_native_min_value)
        self._attr_native_step = float(self._description.get(FanAttributes.STEP) or 1)

        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{kind.lower()}"
        self.kind = kind.partition("#")[0]

    @property
    def native_value(self) -> float | None:
        """Return the current number."""
        value = self._device_status.get(self.kind)
        return None if value is None else float(value)

    async def async_set_native_value(self, value: float | None) -> None:
        """Select a number."""
        _LOGGER.debug("async_set_native_value called with: %s", value)

        if value is None or value < self._attr_native_min_value:
            value = self._attr_native_min_value
        if value % self._attr_native_step > 0:
            value = value // self._attr_native_step * self._attr_native_step
        value = max(value, self._min) if value > 0 else value
        value = min(value, self._attr_native_max_value)

        _LOGGER.debug("setting number with: %s", value)

        await self.coordinator.async_set_control_value(self.kind, int(value))
        self._device_status[self.kind] = int(value)
        self._handle_coordinator_update()
