"""Tests for Philips AirPurifier climate (heater) platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.climate import PhilipsHeater
from custom_components.philips_airpurifier.const import (
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_STATUS,
    DOMAIN,
)
from custom_components.philips_airpurifier.coordinator import (
    PhilipsAirPurifierCoordinator,
)
from custom_components.philips_airpurifier.model import DeviceInformation
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    DOMAIN as CLIMATE_DOMAIN,
    SWING_OFF,
    SWING_ON,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_HOST,
    CONF_NAME,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er

if TYPE_CHECKING:
    from collections.abc import Generator

# CX3120 is a heater model with oscillation support
HEATER_MODEL = "CX3120"
HEATER_DEVICE_ID = "heater_device_01"
HEATER_NAME = "Living Room"

# Gen3 status for CX3120 heater
MOCK_STATUS_HEATER: dict = {
    "D03102": 1,  # NEW2_POWER (on)
    "D0310A": 3,  # NEW2_MODE_A
    "D0310C": 0,  # NEW2_MODE_B (auto_plus)
    "D03224": 22,  # NEW2_TEMPERATURE (current temp)
    "D0310E": 25,  # NEW2_TARGET_TEMP (target temp)
    "D0320F": 0,  # NEW2_OSCILLATION (off)
    "D03103": 0,  # NEW2_CHILD_LOCK (off)
    "DeviceId": HEATER_DEVICE_ID,
    "name": HEATER_NAME,
    "modelid": HEATER_MODEL,
    # Sensors
    "D03125": 50,  # humidity
    "temp": 22,
}


@pytest.fixture
def mock_heater_config_entry() -> MockConfigEntry:
    """Return a mock config entry for a heater model."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{HEATER_MODEL} {HEATER_NAME}",
        data={
            CONF_HOST: "192.168.1.101",
            CONF_MODEL: HEATER_MODEL,
            CONF_NAME: HEATER_NAME,
            CONF_DEVICE_ID: HEATER_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_HEATER,
        },
        unique_id=HEATER_DEVICE_ID,
    )


@pytest.fixture
def mock_heater_coap_client() -> Generator[AsyncMock]:
    """Return a mocked CoAP client for heater tests."""
    with (
        patch(
            "custom_components.philips_airpurifier.CoAPClient",
        ) as mock_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(MOCK_STATUS_HEATER.copy(), 60))
        client.set_control_values = AsyncMock()
        client.set_control_value = AsyncMock()
        client.shutdown = AsyncMock()

        mock_client_cls.create = AsyncMock(return_value=client)
        mock_client_cls.return_value = client

        yield client


@pytest.fixture
async def init_heater_integration(
    hass: HomeAssistant,
    mock_heater_config_entry: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> MockConfigEntry:
    """Set up the heater integration for testing."""
    mock_heater_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_heater_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_heater_config_entry.state is ConfigEntryState.LOADED

    return mock_heater_config_entry


def _get_climate_entity_id(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
) -> str:
    """Get the climate entity ID from the entity registry."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    climate_entries = [e for e in entries if e.domain == CLIMATE_DOMAIN]
    assert len(climate_entries) >= 1
    return climate_entries[0].entity_id


async def test_climate_setup(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test climate entity is created for a heater model."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_heater_integration.entry_id)
    climate_entries = [e for e in entries if e.domain == CLIMATE_DOMAIN]

    assert len(climate_entries) == 1
    entry = climate_entries[0]
    assert HEATER_MODEL in entry.unique_id
    assert HEATER_DEVICE_ID in entry.unique_id


async def test_climate_hvac_mode_auto(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test climate HVAC mode reports HEAT for CX3120 auto_plus preset."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    # CX3120 uses auto_plus (not auto), and hvac_mode maps only PresetMode.AUTO to AUTO.
    assert state.state == HVACMode.HEAT


async def test_climate_hvac_mode_off(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test climate HVAC mode reports OFF when device is off."""
    coordinator = init_heater_integration.runtime_data
    # Set power off
    coordinator.data["D03102"] = 0
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == HVACMode.OFF


async def test_climate_hvac_mode_fan_only(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test climate HVAC mode reports FAN_ONLY for ventilation preset."""
    coordinator = init_heater_integration.runtime_data
    # Set ventilation preset: D0310A=1, D0310C=-127
    coordinator.data["D03102"] = 1
    coordinator.data["D0310A"] = 1
    coordinator.data["D0310C"] = -127
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == HVACMode.FAN_ONLY


async def test_climate_hvac_mode_heat(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test climate HVAC mode reports HEAT for non-auto/non-ventilation presets."""
    coordinator = init_heater_integration.runtime_data
    # Set LOW preset: D0310A=3, D0310C=66
    coordinator.data["D03102"] = 1
    coordinator.data["D0310A"] = 3
    coordinator.data["D0310C"] = 66
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == HVACMode.HEAT


async def test_climate_set_hvac_mode_off(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting HVAC mode to OFF turns off the device."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.assert_called_with(data={"D03102": 0})


async def test_climate_set_hvac_mode_auto(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting HVAC mode to AUTO is a no-op when model has no auto preset."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)

    # First turn off so setting auto is a change
    coordinator = init_heater_integration.runtime_data
    coordinator.data["D03102"] = 0
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.AUTO},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.assert_not_called()


async def test_climate_set_hvac_mode_fan_only(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting HVAC mode to FAN_ONLY sets ventilation preset."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.FAN_ONLY},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Ventilation preset for CX3120: D03102=1, D0310A=1, D0310C=-127
    mock_heater_coap_client.set_control_values.assert_called_with(data={"D03102": 1, "D0310A": 1, "D0310C": -127})


async def test_climate_set_hvac_mode_heat(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting HVAC mode to HEAT sets LOW preset."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    await hass.async_block_till_done()

    # LOW preset for CX3120: D03102=1, D0310A=3, D0310C=66
    mock_heater_coap_client.set_control_values.assert_called_with(data={"D03102": 1, "D0310A": 3, "D0310C": 66})


async def test_climate_preset_mode(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test climate preset mode property."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    # Status matches auto_plus preset: D0310A=3, D0310C=0
    assert state.attributes.get("preset_mode") == "auto_plus"


async def test_climate_set_preset_mode(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting a preset mode."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_preset_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_PRESET_MODE: "low"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.assert_called_with(data={"D03102": 1, "D0310A": 3, "D0310C": 66})


async def test_climate_set_preset_mode_invalid(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting an invalid preset mode does nothing."""
    mock_heater_coap_client.set_control_values.reset_mock()

    # Directly call the entity method with an invalid preset
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_heater_integration.entry_id)
    climate_entry = next(e for e in entries if e.domain == CLIMATE_DOMAIN)
    entity = hass.data["entity_components"][CLIMATE_DOMAIN].get_entity(climate_entry.entity_id)
    await entity.async_set_preset_mode("nonexistent_preset")

    mock_heater_coap_client.set_control_values.assert_not_called()


async def test_climate_preset_mode_none(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test preset_mode returns None when no preset matches."""
    coordinator = init_heater_integration.runtime_data
    # Set a mode_b value that doesn't match any preset
    coordinator.data["D0310C"] = 999
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("preset_mode") is None


async def test_climate_swing_mode(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test climate swing mode property (CX3120 has oscillation)."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    # D0320F=0 maps to SWITCH_OFF in OSCILLATION_MAP3 -> SWING_OFF
    assert state.attributes.get("swing_mode") == SWING_OFF


async def test_climate_swing_mode_on(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test climate swing mode returns ON when oscillation is active."""
    coordinator = init_heater_integration.runtime_data
    # OSCILLATION_MAP3: SWITCH_ON=45
    coordinator.data["D0320F"] = 45
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("swing_mode") == SWING_ON


async def test_climate_set_swing_mode_on(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting swing mode to ON."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_swing_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_SWING_MODE: SWING_ON},
        blocking=True,
    )
    await hass.async_block_till_done()

    # CX3120 OSCILLATION_MAP3: SWITCH_ON=45
    mock_heater_coap_client.set_control_values.assert_called_with(data={"D0320F": 45})


async def test_climate_set_swing_mode_off(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting swing mode to OFF."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)

    # First set oscillation on
    coordinator = init_heater_integration.runtime_data
    coordinator.data["D0320F"] = 45
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_swing_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_SWING_MODE: SWING_OFF},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.assert_called_with(data={"D0320F": 0})


async def test_climate_turn_on(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test turning on the heater."""
    # First turn off
    coordinator = init_heater_integration.runtime_data
    coordinator.data["D03102"] = 0
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.assert_called_with(data={"D03102": 1})


async def test_climate_turn_off(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test turning off the heater."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.assert_called_with(data={"D03102": 0})


async def test_climate_set_temperature(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting the target temperature."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_temperature",
        {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 30},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_heater_coap_client.set_control_values.assert_called_with(data={"D0310E": 30})


async def test_climate_set_temperature_clamped_high(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting temperature above max is clamped."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            "set_temperature",
            {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 50},
            blocking=True,
        )

    mock_heater_coap_client.set_control_values.assert_not_called()


async def test_climate_set_temperature_clamped_low(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test setting temperature below min is clamped."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    mock_heater_coap_client.set_control_values.reset_mock()

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            "set_temperature",
            {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: -5},
            blocking=True,
        )

    mock_heater_coap_client.set_control_values.assert_not_called()


async def test_climate_target_temperature(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test target temperature property."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert float(state.attributes.get("temperature")) == 25.0


async def test_climate_is_on(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test is_on property."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    # Device is on (D03102=1), so state should not be OFF
    assert state is not None
    assert state.state != HVACMode.OFF


async def test_climate_supported_features(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
) -> None:
    """Test supported features include temperature, preset, swing, turn on/off."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    features = state.attributes.get("supported_features")
    assert features is not None

    # Check swing modes are present since CX3120 has oscillation
    assert state.attributes.get("swing_modes") is not None
    assert SWING_ON in state.attributes["swing_modes"]
    assert SWING_OFF in state.attributes["swing_modes"]


async def test_climate_no_entities_for_non_heater_model(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that no climate entities are created for a non-heater model (AC3858/51)."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    climate_entries = [e for e in entries if e.domain == CLIMATE_DOMAIN]

    assert len(climate_entries) == 0


async def test_climate_set_hvac_mode_unsupported_noop(
    hass: HomeAssistant,
    init_heater_integration: MockConfigEntry,
    mock_heater_coap_client: AsyncMock,
) -> None:
    """Test unsupported HVAC mode does not trigger device updates."""
    entity_id = _get_climate_entity_id(hass, init_heater_integration)
    entity = hass.data["entity_components"][CLIMATE_DOMAIN].get_entity(entity_id)

    mock_heater_coap_client.set_control_values.reset_mock()
    await entity.async_set_hvac_mode("dry")

    mock_heater_coap_client.set_control_values.assert_not_called()


async def test_climate_no_oscillation_model_swing_paths(hass: HomeAssistant) -> None:
    """Test swing properties are no-op when model has no oscillation config."""
    device_info = DeviceInformation(
        model="CX5120",
        name="No Osc",
        device_id="no-osc-id",
        host="192.168.1.120",
    )
    coordinator = PhilipsAirPurifierCoordinator(hass, AsyncMock(), "192.168.1.120", device_info)
    coordinator.data = {
        "D03102": 1,
        "D0310E": 22,
        "temp": 21,
        "D0310A": 3,
        "D0310C": 0,
    }

    entity = PhilipsHeater(coordinator, "D0310E")
    entity._oscillation_key = None
    assert entity.swing_mode is None

    coordinator.async_set_control_value = AsyncMock()
    await entity.async_set_swing_mode(SWING_ON)
    coordinator.async_set_control_value.assert_not_called()
