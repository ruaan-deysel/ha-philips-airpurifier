"""Philips Air Purifier light platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_EFFECT, EFFECT_OFF, LightEntity
from homeassistant.components.light.const import (
    ColorMode,
    LightEntityFeature,
)
from homeassistant.const import ATTR_DEVICE_CLASS, CONF_ENTITY_CATEGORY

from .const import (
    DIMMABLE,
    LIGHT_TYPES,
    SWITCH_AUTO,
    SWITCH_MEDIUM,
    SWITCH_OFF,
    SWITCH_ON,
    FanAttributes,
)
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
    """Set up the light platform."""
    coordinator = entry.runtime_data
    model_config = coordinator.model_config

    async_add_entities(PhilipsLight(coordinator, kind) for kind in LIGHT_TYPES if kind in model_config.lights)


class PhilipsLight(PhilipsAirPurifierEntity, LightEntity):
    """Philips AirPurifier light."""

    _attr_is_on: bool | None = False

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
        kind: str,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator)

        self._description = LIGHT_TYPES[kind]
        self._on = self._description.get(SWITCH_ON)
        self._off = self._description.get(SWITCH_OFF)
        self._medium = self._description.get(SWITCH_MEDIUM)
        self._auto = self._description.get(SWITCH_AUTO)
        self._dimmable = self._description.get(DIMMABLE)
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_translation_key = self._description.get(FanAttributes.LABEL)
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)

        if self._dimmable is None:
            self._dimmable = False
            self._medium = None
            self._auto = None

        self._attr_effect_list = None
        self._attr_effect = None

        if self._dimmable:
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            if self._auto:
                self._attr_effect_list = [SWITCH_AUTO]
                self._attr_effect = EFFECT_OFF
                self._attr_supported_features = LightEntityFeature.EFFECT
        else:
            self._attr_color_mode = ColorMode.ONOFF
            self._attr_supported_color_modes = {ColorMode.ONOFF}

        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{kind.lower()}"
        self.kind = kind.partition("#")[0]

    @property
    def is_on(self) -> bool:
        """Return if the light is on."""
        status = self._device_status.get(self.kind)
        if status is None or self._off is None:
            return False
        return int(status) != int(self._off)

    @property
    def brightness(self) -> int | None:  # pragma: no cover
        """Return the brightness of the light."""
        if self._dimmable:
            if self._auto and self._attr_effect == SWITCH_AUTO:
                return None

            if self._on is None or self._off is None:
                return None

            brightness_value = self._device_status.get(self.kind)
            if brightness_value is None:
                return None
            brightness = int(brightness_value)

            if self._auto and brightness == int(self._auto):
                self._attr_effect = SWITCH_AUTO
                return None

            if self._medium and brightness == int(self._medium):
                return 128

            if brightness == int(self._off):
                self._attr_effect = EFFECT_OFF
                return 0

            return round(255 * brightness / int(self._on))

        return None

    async def async_turn_on(self, **kwargs: Any) -> None:  # pragma: no cover
        """Turn the light on."""
        value = self._on
        if ATTR_EFFECT in kwargs:
            self._attr_effect = kwargs[ATTR_EFFECT]
            if self._attr_effect == SWITCH_AUTO:
                value = self._auto
        elif self._dimmable:
            if ATTR_BRIGHTNESS in kwargs:  # pragma: no branch
                if self._medium and kwargs[ATTR_BRIGHTNESS] < 255:
                    value = self._medium
                else:
                    if self._on is None:
                        return
                    value = round(int(self._on) * int(kwargs[ATTR_BRIGHTNESS]) / 255)
            else:
                if self._on is None:
                    return
                value = int(self._on)
        else:
            value = self._on

        if value is None:
            return

        await self.coordinator.async_set_control_value(self.kind, value)
        self._device_status[self.kind] = value
        self._handle_coordinator_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off."""
        self._attr_effect = EFFECT_OFF
        await self.coordinator.async_set_control_value(self.kind, self._off)
        self._device_status[self.kind] = self._off
        self._handle_coordinator_update()
