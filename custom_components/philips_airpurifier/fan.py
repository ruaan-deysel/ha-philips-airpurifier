"""Philips Air Purifier fan platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from .const import SWITCH_OFF, SWITCH_ON
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
    """Set up the fan platform."""
    coordinator = entry.runtime_data
    model_config = coordinator.model_config

    if model_config.create_fan:
        async_add_entities([PhilipsFan(coordinator)])


class PhilipsFan(PhilipsAirPurifierEntity, FanEntity):  # pragma: no cover
    """Philips AirPurifier fan entity."""

    _attr_translation_key = "pap"
    _attr_name = None

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
    ) -> None:  # pragma: no cover
        """Initialize the fan."""
        super().__init__(coordinator)

        model_config = coordinator.model_config

        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}"

        self._power_key = model_config.power_key
        self._power_on = model_config.power_on
        self._power_off = model_config.power_off

        self._preset_modes_map = model_config.preset_modes
        self._speeds_map = model_config.speeds
        self._speeds_list = list(self._speeds_map.keys())
        self._oscillation = model_config.oscillation

        # Set supported features
        self._attr_supported_features = (
            FanEntityFeature.PRESET_MODE | FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON
        )

        if self._speeds_list:
            self._attr_supported_features |= FanEntityFeature.SET_SPEED

        if self._oscillation is not None:
            self._attr_supported_features |= FanEntityFeature.OSCILLATE

    @property
    def is_on(self) -> bool:
        """Return if the fan is on."""
        return self._device_status.get(self._power_key) == self._power_on

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:  # pragma: no cover
        """Turn the fan on."""
        if preset_mode:  # pragma: no branch
            await self.async_set_preset_mode(preset_mode)
            return

        if percentage:
            await self.async_set_percentage(percentage)
            return

        await self.coordinator.async_set_control_value(self._power_key, self._power_on)
        self._device_status[self._power_key] = self._power_on
        self._handle_coordinator_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the fan off."""
        await self.coordinator.async_set_control_value(self._power_key, self._power_off)
        self._device_status[self._power_key] = self._power_off
        self._handle_coordinator_update()

    @property
    def preset_modes(self) -> list[str]:
        """Return the supported preset modes."""
        return list(self._preset_modes_map.keys())

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        for preset_mode, status_pattern in self._preset_modes_map.items():
            for k, v in status_pattern.items():
                if self._device_status.get(k) != v:
                    break
            else:
                return preset_mode
        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        status_pattern = self._preset_modes_map.get(preset_mode)
        if status_pattern:
            await self.coordinator.async_set_control_values(status_pattern)
            self._device_status.update(status_pattern)
            self._handle_coordinator_update()

    @property
    def speed_count(self) -> int:
        """Return the number of speed options."""
        return len(self._speeds_list)

    @property
    def percentage(self) -> int | None:
        """Return the current speed as a percentage."""
        for speed, status_pattern in self._speeds_map.items():
            for k, v in status_pattern.items():
                if self._device_status.get(k) != v:
                    break
            else:
                return ordered_list_item_to_percentage(self._speeds_list, speed)
        return None

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed percentage."""
        if percentage == 0:
            await self.async_turn_off()
            return

        speed = percentage_to_ordered_list_item(self._speeds_list, percentage)
        status_pattern = self._speeds_map.get(speed)
        if status_pattern:
            await self.coordinator.async_set_control_values(status_pattern)
            self._device_status.update(status_pattern)
            self._handle_coordinator_update()

    @property
    def oscillating(self) -> bool | None:  # pragma: no cover
        """Return if the fan is oscillating."""
        if self._oscillation is None:  # pragma: no cover
            return None

        key = next(iter(self._oscillation))
        values = self._oscillation[key]
        off = values[SWITCH_OFF]
        status = self._device_status.get(key)

        if status is None:  # pragma: no cover
            return None

        return status != off

    async def async_oscillate(self, oscillating: bool) -> None:  # pragma: no cover
        """Set the oscillation of the fan."""
        if self._oscillation is None:
            return

        key = next(iter(self._oscillation))
        values = self._oscillation[key]
        value = values[SWITCH_ON] if oscillating else values[SWITCH_OFF]

        await self.coordinator.async_set_control_value(key, value)
        self._device_status[key] = value
        self._handle_coordinator_update()
