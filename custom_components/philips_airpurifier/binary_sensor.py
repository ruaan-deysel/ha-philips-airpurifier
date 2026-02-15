"""Philips Air Purifier binary sensor platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import ATTR_DEVICE_CLASS, CONF_ENTITY_CATEGORY

from .const import BINARY_SENSOR_TYPES, FanAttributes
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
    """Set up binary sensor entities."""
    coordinator = entry.runtime_data
    model_config = coordinator.model_config
    status = coordinator.data or {}

    async_add_entities(
        PhilipsBinarySensor(coordinator, kind)
        for kind in BINARY_SENSOR_TYPES
        if kind in model_config.binary_sensors and kind in status
    )


class PhilipsBinarySensor(PhilipsAirPurifierEntity, BinarySensorEntity):
    """Philips AirPurifier binary sensor."""

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
        kind: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)

        self._description = BINARY_SENSOR_TYPES[kind]
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)
        self._attr_translation_key = self._description.get(FanAttributes.LABEL)
        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{kind.lower()}"
        self.kind = kind

    @property
    def is_on(self) -> bool:
        """Return the state of the binary sensor."""
        value = self._device_status[self.kind]
        convert = self._description.get(FanAttributes.VALUE)
        if convert:
            value = convert(value)
        return cast("bool", value)
