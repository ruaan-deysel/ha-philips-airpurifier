"""Philips Air Purifier sensor platform."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any, cast

from homeassistant.components.sensor import ATTR_STATE_CLASS, SensorEntity
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    CONF_ENTITY_CATEGORY,
    PERCENTAGE,
    EntityCategory,
    UnitOfTime,
)

from .const import FILTER_TYPES, SENSOR_TYPES, FanAttributes
from .entity import PhilipsAirPurifierEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback
    from homeassistant.helpers.typing import StateType

    from .__init__ import PhilipsAirPurifierConfigEntry
    from .coordinator import PhilipsAirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsAirPurifierConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data
    model_config = coordinator.model_config
    status = coordinator.data or {}

    entities: list[SensorEntity] = [
        PhilipsSensor(coordinator, kind)
        for kind in SENSOR_TYPES
        if kind in status and kind not in model_config.unavailable_sensors
    ]
    entities.extend(
        PhilipsFilterSensor(coordinator, kind)
        for kind in FILTER_TYPES
        if kind in status and kind not in model_config.unavailable_filters
    )

    async_add_entities(entities)


class PhilipsSensor(PhilipsAirPurifierEntity, SensorEntity):
    """Philips AirPurifier sensor."""

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
        kind: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._description = SENSOR_TYPES[kind]
        self._icon_map = self._description.get(FanAttributes.ICON_MAP)
        self._norm_icon = next(iter(self._icon_map.items()))[1] if self._icon_map is not None else None
        self._attr_state_class = self._description.get(ATTR_STATE_CLASS)
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)
        self._attr_translation_key = self._description.get(FanAttributes.LABEL)
        self._attr_native_unit_of_measurement = self._description.get(FanAttributes.UNIT)

        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{kind.lower()}"
        self.kind = kind

    @property
    def native_value(self) -> StateType:
        """Return the native value of the sensor."""
        value = self._device_status.get(self.kind)
        convert = self._description.get(FanAttributes.VALUE)
        if convert:
            value = convert(value, self._device_status)
        return cast("StateType", value)

    @property
    def icon(self) -> str | None:
        """Return the icon of the sensor."""
        icon = self._norm_icon
        if not self._icon_map:
            return icon

        native_value = self.native_value
        if native_value is None:
            return icon
        try:
            value = int(native_value)
        except (TypeError, ValueError):
            return icon

        for level_value, level_icon in self._icon_map.items():
            if value >= level_value:
                icon = level_icon
        return icon


class PhilipsFilterSensor(PhilipsAirPurifierEntity, SensorEntity):
    """Philips AirPurifier filter sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
        kind: str,
    ) -> None:
        """Initialize the filter sensor."""
        super().__init__(coordinator)

        self._description = FILTER_TYPES[kind]
        self._icon_map = self._description.get(FanAttributes.ICON_MAP)
        self._norm_icon = next(iter(self._icon_map.items()))[1] if self._icon_map is not None else None

        self._value_key = kind
        self._total_key = self._description[FanAttributes.TOTAL]
        self._type_key = self._description[FanAttributes.TYPE]
        self._attr_translation_key = self._description.get(FanAttributes.LABEL)

        if self._has_total:
            self._attr_native_unit_of_measurement = PERCENTAGE
        else:
            self._attr_native_unit_of_measurement = UnitOfTime.HOURS

        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{self._description[FanAttributes.LABEL]}"

    @property
    def _has_total(self) -> bool:
        return self._total_key in (self._device_status or {})

    @property
    def _value(self) -> int:
        return self._device_status[self._value_key]

    @property
    def _total(self) -> int:
        return self._device_status[self._total_key]

    @property
    def _percentage(self) -> float:
        return round(100.0 * self._value / self._total)

    @property
    def _time_remaining(self) -> str:
        return str(round(timedelta(hours=self._value) / timedelta(hours=1)))

    @property
    def native_value(self) -> StateType:
        """Return the native value of the filter sensor."""
        if self._has_total:
            return self._percentage
        return self._time_remaining

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the extra state attributes of the filter sensor."""
        attrs: dict[str, Any] = {}

        if self._type_key in self._device_status:
            filter_type = self._device_status[self._type_key]
            if filter_type:
                attrs["Filter Type"] = filter_type

        if self._has_total:
            total_hours = self._total
            remaining_hours = self._value
            percentage = round(100.0 * remaining_hours / total_hours)

            attrs["Total Filter Capacity"] = _format_filter_capacity(total_hours)
            attrs["Filter Life Remaining"] = _format_time_remaining(remaining_hours)
            attrs["Filter Life Percentage"] = f"{percentage}%"

            if percentage <= 5:
                attrs["Replacement Status"] = "Replace immediately"
            elif percentage <= 15:
                attrs["Replacement Status"] = "Replace soon"
            elif percentage <= 30:
                attrs["Replacement Status"] = "Monitor closely"
            else:
                attrs["Replacement Status"] = "Good condition"
        else:
            remaining_hours = self._value
            attrs["Filter Life Remaining"] = _format_time_remaining(remaining_hours)

            if remaining_hours <= 24:
                attrs["Replacement Status"] = "Replace immediately"
            elif remaining_hours <= 72:
                attrs["Replacement Status"] = "Replace soon"
            elif remaining_hours <= 168:
                attrs["Replacement Status"] = "Monitor closely"
            else:
                attrs["Replacement Status"] = "Good condition"

        return attrs

    @property
    def icon(self) -> str | None:
        """Return the icon of the sensor."""
        icon = self._norm_icon
        if not self._icon_map:
            return icon

        native_value = self.native_value
        if native_value is None:
            return icon
        try:
            value = int(native_value)
        except (TypeError, ValueError):
            return icon

        for level_value, level_icon in self._icon_map.items():
            if value >= level_value:
                icon = level_icon
        return icon


def _pluralize(value: int, unit: str) -> str:
    """Return unit with 's' suffix when value != 1."""
    return f"{value} {unit}{'s' if value != 1 else ''}"


def _format_duration(hours: int, suffix: str) -> str:  # noqa: PLR0911  # pragma: no cover
    """Format a duration in hours with the given suffix (e.g. 'remaining', 'capacity')."""
    if hours <= 0:
        return "Replace immediately"

    days = hours // 24
    remaining_hours = hours % 24

    if days >= 365:
        years = days // 365
        remaining_days = days % 365
        base = _pluralize(years, "year")
        if remaining_days == 0:
            return f"{base} {suffix}"  # pragma: no cover
        return f"{base}, {_pluralize(remaining_days, 'day')} {suffix}"

    if days >= 30:
        months = days // 30
        remaining_days = days % 30
        base = _pluralize(months, "month")
        if remaining_days == 0:
            return f"{base} {suffix}"
        return f"{base}, {_pluralize(remaining_days, 'day')} {suffix}"

    if days >= 7:
        weeks = days // 7
        remaining_days = days % 7
        base = _pluralize(weeks, "week")
        if remaining_days == 0:
            return f"{base} {suffix}"
        return f"{base}, {_pluralize(remaining_days, 'day')} {suffix}"

    if days > 0:
        base = _pluralize(days, "day")
        if remaining_hours == 0:
            return f"{base} {suffix}"
        return f"{base}, {_pluralize(remaining_hours, 'hour')} {suffix}"

    return f"{_pluralize(hours, 'hour')} {suffix}"


def _format_time_remaining(hours: int) -> str:
    """Format time remaining in a user-friendly way."""
    return _format_duration(hours, "remaining")


def _format_filter_capacity(hours: int) -> str:
    """Format total filter capacity in a user-friendly way."""
    return _format_duration(hours, "capacity")
