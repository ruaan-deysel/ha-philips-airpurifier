"""Philips Air Purifier humidifier platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.humidifier import HumidifierDeviceClass, HumidifierEntity
from homeassistant.components.humidifier.const import (
    HumidifierAction,
    HumidifierEntityFeature,
)

from .const import HUMIDIFIER_TYPES, FanAttributes, FanFunction
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
    """Set up the humidifier platform."""
    coordinator = entry.runtime_data
    model_config = coordinator.model_config

    async_add_entities(
        PhilipsHumidifier(coordinator, kind)
        for kind in HUMIDIFIER_TYPES
        if kind in model_config.humidifiers  # pragma: no cover
    )


class PhilipsHumidifier(PhilipsAirPurifierEntity, HumidifierEntity):
    """Philips AirPurifier humidifier."""

    _attr_is_on: bool | None = False

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
        kind: str,
    ) -> None:  # pragma: no cover
        """Initialize the humidifier."""
        super().__init__(coordinator)

        latest_status = coordinator.data or {}

        self._description = HUMIDIFIER_TYPES[kind]
        self._attr_device_class = HumidifierDeviceClass.HUMIDIFIER
        self._attr_translation_key = "pap"

        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{kind.lower()}"

        self._power_key = self._description[FanAttributes.POWER]
        self._function_key = self._description[FanAttributes.FUNCTION]
        self._humidity_target_key = kind.partition("#")[0]
        self._switch = self._description[FanAttributes.SWITCH]

        self._attr_min_humidity = self._description[FanAttributes.MIN_HUMIDITY]
        self._attr_max_humidity = self._description[FanAttributes.MAX_HUMIDITY]
        self._attr_target_humidity = latest_status.get(self._humidity_target_key)
        self._attr_current_humidity = latest_status.get(self._description[FanAttributes.HUMIDITY])

        # 2-in-1 devices have a switch to select humidification vs purification
        if self._switch:
            self._attr_supported_features = HumidifierEntityFeature.MODES
            self._attr_available_modes = [
                FanFunction.PURIFICATION,
                FanFunction.PURIFICATION_HUMIDIFICATION,
            ]
        # pure humidification devices are identified by the function being the power
        elif self._function_key == self._power_key:
            self._attr_supported_features = HumidifierEntityFeature.MODES
            self._attr_available_modes = list(coordinator.model_config.preset_modes.keys())

    @property
    def action(self) -> str:
        """Return the current action."""
        function_status = self._device_status.get(self._function_key)

        if function_status == self._description[FanAttributes.HUMIDIFYING]:
            return HumidifierAction.HUMIDIFYING

        return HumidifierAction.IDLE

    @property
    def current_humidity(self) -> int | None:
        """Return the current humidity."""
        return self._device_status.get(self._description[FanAttributes.HUMIDITY])

    @property
    def target_humidity(self) -> int | None:
        """Return the target humidity."""
        return self._device_status.get(self._humidity_target_key)

    @property
    def mode(self) -> str | None:
        """Return the current mode."""
        if self._switch:  # pragma: no branch
            function_status = self._device_status.get(self._function_key)
            if function_status == self._description[FanAttributes.HUMIDIFYING]:
                return FanFunction.PURIFICATION_HUMIDIFICATION
            return FanFunction.PURIFICATION

        if self._function_key == self._power_key:  # pragma: no branch
            for (
                preset_mode,
                status_pattern,
            ) in self.coordinator.model_config.preset_modes.items():
                for k, v in status_pattern.items():
                    status = self._device_status.get(k)
                    if status != v:
                        break
                else:
                    return preset_mode

        return None

    async def async_set_mode(self, mode: str) -> None:  # pragma: no cover
        """Set the mode of the humidifier."""
        available_modes = self._attr_available_modes or []
        if mode not in available_modes:  # pragma: no cover
            return

        if self._switch:
            if mode == FanAttributes.PURIFICATION:
                function_value = self._description[FanAttributes.IDLE]
            else:
                function_value = self._description[FanAttributes.HUMIDIFYING]

            await self.coordinator.async_set_control_values(
                {
                    self._power_key: self._description[FanAttributes.ON],
                    self._function_key: function_value,
                }
            )
            self._device_status[self._power_key] = self._description[FanAttributes.ON]
            self._device_status[self._function_key] = function_value
            self._handle_coordinator_update()

        elif self._function_key == self._power_key:
            status_pattern = self.coordinator.model_config.preset_modes.get(mode)
            if status_pattern is None:
                return
            await self.coordinator.async_set_control_values(status_pattern)
            self._device_status.update(status_pattern)
            self._handle_coordinator_update()

    @property
    def is_on(self) -> bool | None:
        """Return the device state independent of the humidifier function."""
        return self._device_status.get(self._power_key) != self._description[FanAttributes.OFF]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the device."""
        await self.coordinator.async_set_control_values({self._power_key: self._description[FanAttributes.ON]})
        self._device_status[self._power_key] = self._description[FanAttributes.ON]
        self._handle_coordinator_update()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the device."""
        await self.coordinator.async_set_control_values({self._power_key: self._description[FanAttributes.OFF]})
        self._device_status[self._power_key] = self._description[FanAttributes.OFF]
        self._handle_coordinator_update()

    async def async_set_humidity(self, humidity: int) -> None:
        """Select target humidity."""
        step = int(self._description[FanAttributes.STEP])
        humidity_value = int(humidity)

        current_target = self.target_humidity
        if current_target is None:
            current_target = self._attr_target_humidity or humidity_value
        if humidity_value == int(current_target) + 1:
            humidity_value = int(current_target) + step
        elif humidity_value == int(current_target) - 1:
            humidity_value = int(current_target) - step

        target = round(humidity_value / step) * step
        target = max(self._attr_min_humidity, min(target, self._attr_max_humidity))
        await self.coordinator.async_set_control_value(self._humidity_target_key, target)
        self._device_status[self._humidity_target_key] = target
        self._handle_coordinator_update()
