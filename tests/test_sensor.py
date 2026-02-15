"""Tests for Philips AirPurifier sensor platform."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.const import PhilipsApi
from custom_components.philips_airpurifier.sensor import (
    PhilipsFilterSensor,
    PhilipsSensor,
    _format_duration,
    _format_filter_capacity,
    _format_time_remaining,
    _pluralize,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er


async def test_sensor_setup(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test sensor entities are created correctly."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    sensor_entries = [entry for entry in entries if entry.domain == "sensor"]

    # AC3858/51 Gen1 has 5 sensor types + 3 filter sensors
    assert len(sensor_entries) >= 8

    # Check sensor entity unique_ids match expected format
    sensor_unique_ids = {entry.unique_id for entry in sensor_entries}
    expected_sensors = {
        "AC3858/51-aabbccddeeff-pm25",
        "AC3858/51-aabbccddeeff-iaql",
        "AC3858/51-aabbccddeeff-rh",
        "AC3858/51-aabbccddeeff-temp",
        "AC3858/51-aabbccddeeff-runtime",
        "AC3858/51-aabbccddeeff-pre_filter",
        "AC3858/51-aabbccddeeff-hepa_filter",
        "AC3858/51-aabbccddeeff-active_carbon_filter",
    }
    assert expected_sensors.issubset(sensor_unique_ids)


async def test_sensor_runtime_value(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test runtime sensor value conversion and metadata."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    runtime_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-runtime")
    state = hass.states.get(runtime_entry.entity_id)

    assert state is not None
    assert state.state == "2.0"
    assert state.attributes.get("unit_of_measurement") == "h"
    assert state.attributes.get("device_class") == "duration"
    assert state.attributes.get("state_class") == "total"
    assert runtime_entry.entity_category == "diagnostic"


async def test_sensor_pm25_value(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test PM2.5 sensor value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Find PM2.5 sensor by unique_id
    pm25_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-pm25")
    state = hass.states.get(pm25_entry.entity_id)

    assert state is not None
    assert state.state == "12"
    assert state.attributes.get("unit_of_measurement") == "μg/m³"
    assert state.attributes.get("device_class") == "pm25"
    assert state.attributes.get("state_class") == "measurement"


async def test_sensor_iaql_value(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test Indoor Allergen Index sensor value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Find IAQL sensor by unique_id
    iaql_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-iaql")
    state = hass.states.get(iaql_entry.entity_id)

    assert state is not None
    assert state.state == "3"
    assert state.attributes.get("state_class") == "measurement"


async def test_sensor_humidity_value(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test humidity sensor value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Find humidity sensor by unique_id
    humidity_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-rh")
    state = hass.states.get(humidity_entry.entity_id)

    assert state is not None
    assert state.state == "50"
    assert state.attributes.get("unit_of_measurement") == "%"
    assert state.attributes.get("device_class") == "humidity"
    assert state.attributes.get("state_class") == "measurement"


async def test_sensor_temperature_value(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test temperature sensor value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Find temperature sensor by unique_id
    temp_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-temp")
    state = hass.states.get(temp_entry.entity_id)

    assert state is not None
    assert state.state == "22"
    assert state.attributes.get("unit_of_measurement") == "°C"
    assert state.attributes.get("device_class") == "temperature"
    assert state.attributes.get("state_class") == "measurement"


async def test_filter_sensor_pre_filter(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test pre-filter sensor value and percentage calculation."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Find pre-filter sensor by unique_id
    pre_filter_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-pre_filter")
    state = hass.states.get(pre_filter_entry.entity_id)

    assert state is not None
    # 200/2400 * 100 = 8.333... → round = 8
    assert state.state == "8"
    assert state.attributes.get("unit_of_measurement") == "%"
    # Entity category is stored in the entity registry, not state attributes
    assert pre_filter_entry.entity_category == "diagnostic"


async def test_filter_sensor_hepa_filter(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test HEPA filter sensor value and percentage calculation."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Find HEPA filter sensor by unique_id
    hepa_filter_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-hepa_filter")
    state = hass.states.get(hepa_filter_entry.entity_id)

    assert state is not None
    # 1000/4800 * 100 = 20.833... → round = 21
    assert state.state == "21"
    assert state.attributes.get("unit_of_measurement") == "%"
    # Entity category is stored in the entity registry, not state attributes
    assert hepa_filter_entry.entity_category == "diagnostic"


async def test_filter_sensor_active_carbon(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test active carbon filter sensor value and percentage calculation."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Find active carbon filter sensor by unique_id
    carbon_filter_entry = next(
        entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-active_carbon_filter"
    )
    state = hass.states.get(carbon_filter_entry.entity_id)

    assert state is not None
    # 500/2400 * 100 = 20.833... → round = 21
    assert state.state == "21"
    assert state.attributes.get("unit_of_measurement") == "%"
    # Entity category is stored in the entity registry, not state attributes
    assert carbon_filter_entry.entity_category == "diagnostic"


async def test_filter_sensor_extra_state_attributes(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test filter sensor extra state attributes."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Test pre-filter attributes
    pre_filter_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-pre_filter")
    state = hass.states.get(pre_filter_entry.entity_id)

    assert state is not None
    # Pre-filter has no type in MOCK_STATUS_GEN1 (fltt0 is not included)
    # But has fltt1="A3" and fltt2="C7"

    # Check that total capacity and remaining life are formatted
    assert "Total Filter Capacity" in state.attributes
    assert "Filter Life Remaining" in state.attributes
    assert "Filter Life Percentage" in state.attributes
    assert "Replacement Status" in state.attributes

    # 200/2400 = 8.33% → rounds to 8%
    assert state.attributes["Filter Life Percentage"] == "8%"
    # 8% is ≤15%, so should be "Replace soon"
    assert state.attributes["Replacement Status"] == "Replace soon"

    # Test HEPA filter with filter type
    hepa_filter_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-hepa_filter")
    state = hass.states.get(hepa_filter_entry.entity_id)

    assert state is not None
    # HEPA filter has fltt1="A3"
    assert state.attributes.get("Filter Type") == "A3"
    # 1000/4800 = 20.83% → rounds to 21%
    assert state.attributes["Filter Life Percentage"] == "21%"
    # 21% is >15% and ≤30%, so should be "Monitor closely"
    assert state.attributes["Replacement Status"] == "Monitor closely"

    # Test active carbon filter with filter type
    carbon_filter_entry = next(
        entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-active_carbon_filter"
    )
    state = hass.states.get(carbon_filter_entry.entity_id)

    assert state is not None
    # Active carbon filter has fltt2="C7"
    assert state.attributes.get("Filter Type") == "C7"
    # 500/2400 = 20.83% → rounds to 21%
    assert state.attributes["Filter Life Percentage"] == "21%"
    # 21% is >15% and ≤30%, so should be "Monitor closely"
    assert state.attributes["Replacement Status"] == "Monitor closely"


async def test_sensor_entity_category(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that filter sensors have diagnostic entity category."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Filter sensors should be diagnostic
    filter_entries = [entry for entry in entries if "filter" in entry.unique_id and entry.domain == "sensor"]

    for entry in filter_entries:
        # entity_category is stored in the entity registry, not state attributes
        assert entry.entity_category == "diagnostic"


async def test_sensor_device_info(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test sensor entities have correct device info."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    sensor_entries = [entry for entry in entries if entry.domain == "sensor"]

    for entry in sensor_entries:
        # All sensors should have device_id set
        assert entry.device_id is not None
        # Verify entity belongs to the correct config entry
        assert entry.config_entry_id == init_integration.entry_id


async def test_sensor_unique_ids(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test sensor unique IDs follow the correct format."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    sensor_entries = [entry for entry in entries if entry.domain == "sensor"]

    # All sensor unique IDs should start with "AC3858/51-aabbccddeeff-"
    for entry in sensor_entries:
        assert entry.unique_id.startswith("AC3858/51-aabbccddeeff-")


async def test_sensor_icon_mapping(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test sensor icons are set correctly based on value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)

    # Temperature sensor has icon mapping
    temp_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-temp")
    state = hass.states.get(temp_entry.entity_id)

    assert state is not None
    # Temp is 22, which is >= 17 and < 23, so should use "mdi:thermometer"
    assert state.attributes.get("icon") == "mdi:thermometer"

    # Filter sensors have icon mapping based on percentage
    pre_filter_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-pre_filter")
    state = hass.states.get(pre_filter_entry.entity_id)

    assert state is not None
    # Pre-filter is at 8%, which is < 72%, so should show replacement icon
    # Icon map: {0: ICON.FILTER_REPLACEMENT, 72: "mdi:dots-grid"}
    # At 8%, should use the 0 threshold icon
    assert state.attributes.get("icon") == "mdi:air-filter"


async def test_sensor_icon_none_value_returns_default(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test sensor icon falls back when native value is None."""
    coordinator = init_integration.runtime_data
    coordinator.data["temp"] = None
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    temp_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-temp")
    entity = hass.data["entity_components"]["sensor"].get_entity(temp_entry.entity_id)

    assert entity.icon == "mdi:thermometer-low"


async def test_sensor_icon_non_numeric_value_returns_default(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    monkeypatch,
) -> None:
    """Test sensor icon falls back when native value cannot be converted to int."""
    monkeypatch.setattr(PhilipsSensor, "native_value", property(lambda _self: "invalid"))

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    temp_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-temp")
    entity = hass.data["entity_components"]["sensor"].get_entity(temp_entry.entity_id)

    assert entity.icon == "mdi:thermometer-low"


async def test_filter_sensor_icon_none_native_value_returns_default(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    monkeypatch,
) -> None:
    """Test filter sensor icon fallback when native value is None."""
    monkeypatch.setattr(PhilipsFilterSensor, "native_value", property(lambda _self: None))

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    pre_filter_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-pre_filter")
    entity = hass.data["entity_components"]["sensor"].get_entity(pre_filter_entry.entity_id)

    assert entity.icon == "mdi:air-filter"


async def test_filter_sensor_icon_non_numeric_native_value_returns_default(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    monkeypatch,
) -> None:
    """Test filter sensor icon fallback when native value cannot be converted to int."""
    monkeypatch.setattr(PhilipsFilterSensor, "native_value", property(lambda _self: "invalid"))

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    pre_filter_entry = next(entry for entry in entries if entry.unique_id == "AC3858/51-aabbccddeeff-pre_filter")
    entity = hass.data["entity_components"]["sensor"].get_entity(pre_filter_entry.entity_id)

    assert entity.icon == "mdi:air-filter"


def test_pluralize() -> None:
    """Test pluralization helper."""
    assert _pluralize(1, "hour") == "1 hour"
    assert _pluralize(2, "hour") == "2 hours"


def test_format_duration_zero() -> None:
    """Test duration formatting for zero values."""
    assert _format_duration(0, "remaining") == "Replace immediately"


def test_format_duration_year_month_week_day_hour_paths() -> None:
    """Test duration formatting across all unit conversion branches."""
    assert "year" in _format_duration(24 * 365, "remaining")
    assert "month" in _format_duration(24 * 45, "remaining")
    assert "week" in _format_duration(24 * 10, "remaining")
    assert "day" in _format_duration(30, "remaining")
    assert "hour" in _format_duration(5, "remaining")


def test_format_wrapper_helpers() -> None:
    """Test wrapper helpers for remaining/capacity."""
    assert _format_time_remaining(48).endswith("remaining")
    assert _format_filter_capacity(48).endswith("capacity")


async def test_filter_sensor_without_total_uses_hour_remaining_branches(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test filter sensor branch behavior when total key is missing."""
    coordinator = init_integration.runtime_data
    original = dict(coordinator.data)
    try:
        coordinator.data[PhilipsApi.FILTER_WICK] = 20
        coordinator.data.pop(PhilipsApi.FILTER_WICK_TOTAL, None)
        coordinator.data[PhilipsApi.FILTER_WICK_TYPE] = ""

        sensor = PhilipsFilterSensor(coordinator, PhilipsApi.FILTER_WICK)
        assert sensor.native_value == "20"
        attrs = sensor.extra_state_attributes
        assert attrs["Replacement Status"] == "Replace immediately"
        assert "Filter Type" not in attrs

        coordinator.data[PhilipsApi.FILTER_WICK] = 60
        assert sensor.extra_state_attributes["Replacement Status"] == "Replace soon"

        coordinator.data[PhilipsApi.FILTER_WICK] = 120
        assert sensor.extra_state_attributes["Replacement Status"] == "Monitor closely"

        coordinator.data[PhilipsApi.FILTER_WICK] = 200
        assert sensor.extra_state_attributes["Replacement Status"] == "Good condition"

        sensor._icon_map = None
        assert sensor.icon == sensor._norm_icon
    finally:
        coordinator.data.clear()
        coordinator.data.update(original)


async def test_filter_sensor_total_percentage_replace_immediately_branch(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test <=5% replacement branch for total-based filter sensors."""
    coordinator = init_integration.runtime_data
    original = dict(coordinator.data)
    try:
        coordinator.data[PhilipsApi.FILTER_PRE] = 1
        coordinator.data[PhilipsApi.FILTER_PRE_TOTAL] = 100
        sensor = PhilipsFilterSensor(coordinator, PhilipsApi.FILTER_PRE)
        assert sensor.extra_state_attributes["Replacement Status"] == "Replace immediately"

        coordinator.data[PhilipsApi.FILTER_PRE] = 50
        coordinator.data[PhilipsApi.FILTER_PRE_TOTAL] = 100
        assert sensor.extra_state_attributes["Replacement Status"] == "Good condition"
    finally:
        coordinator.data.clear()
        coordinator.data.update(original)


def test_format_duration_exact_zero_remainder_branches() -> None:
    """Test exact branches where remaining days/hours equal zero."""
    assert _format_duration(24 * 365, "remaining") == "1 year remaining"
    assert _format_duration(24 * 30, "remaining") == "1 month remaining"
    assert _format_duration(24 * 7, "remaining") == "1 week remaining"
    assert _format_duration(24, "remaining") == "1 day remaining"
