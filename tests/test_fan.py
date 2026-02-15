"""Tests for the Philips AirPurifier fan platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.const import (
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_STATUS,
    DOMAIN,
)
from custom_components.philips_airpurifier.coordinator import (
    PhilipsAirPurifierCoordinator,
)
from custom_components.philips_airpurifier.fan import PhilipsFan
from custom_components.philips_airpurifier.model import DeviceInformation
from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
    SERVICE_SET_PRESET_MODE,
    FanEntityFeature,
)
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import TEST_DEVICE_ID, TEST_MODEL

if TYPE_CHECKING:
    from collections.abc import Generator

ENTITY_ID = "fan.living_room"


async def test_fan_setup(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan entity is created."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON


async def test_fan_is_on(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan is_on property."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON


async def test_fan_turn_on(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning on the fan."""
    # First turn it off
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )
    mock_coap_client.reset_mock()

    # Now turn it on
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "1"})


async def test_fan_turn_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning off the fan."""
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "0"})


async def test_fan_preset_modes(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan preset modes list."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None

    preset_modes = state.attributes.get("preset_modes")
    assert preset_modes is not None
    assert isinstance(preset_modes, list)
    # AC3858/51 has 6 preset modes
    assert len(preset_modes) == 6
    assert "auto" in preset_modes
    assert "sleep" in preset_modes
    assert "allergy_sleep" in preset_modes
    assert "speed_1" in preset_modes
    assert "speed_2" in preset_modes
    assert "turbo" in preset_modes


async def test_fan_preset_mode_auto(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan preset mode is auto when mode=AG."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None

    # MOCK_STATUS_GEN1 has pwr="1", mode="AG" which corresponds to auto preset
    preset_mode = state.attributes.get("preset_mode")
    assert preset_mode == "auto"


async def test_fan_set_preset_mode(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting preset mode."""
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_PRESET_MODE: "sleep",
        },
        blocking=True,
    )

    # Sleep preset for AC3858/51: pwr="1", mode="S", om="s"
    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "1", "mode": "S", "om": "s"})


async def test_fan_turn_on_with_preset(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning on fan with preset mode."""
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_PRESET_MODE: "turbo",
        },
        blocking=True,
    )

    # Turbo preset for AC3858/51: pwr="1", mode="T", om="t"
    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "1", "mode": "T", "om": "t"})


async def test_fan_speed_count(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan speed count."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None

    # AC3858/51 has 4 speeds: sleep, speed_1, speed_2, turbo
    # percentage_step = 100 / 4 = 25.0
    assert state.attributes.get("percentage_step") == 25.0


async def test_fan_percentage(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan percentage calculation."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None

    # MOCK_STATUS_GEN1 has pwr="1", mode="AG", om="a" which doesn't match any speed
    # Auto preset is different from speeds, so percentage should be None
    percentage = state.attributes.get("percentage")
    assert percentage is None


async def test_fan_set_percentage(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting fan percentage."""
    # Set to 50% (should map to speed_1 or speed_2)
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_PERCENTAGE: 50,
        },
        blocking=True,
    )

    # With 4 speeds, 50% maps to speed_1 (2nd of 4 speeds)
    # speed_1 for AC3858/51: pwr="1", mode="M", om="1"
    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "1", "mode": "M", "om": "1"})


async def test_fan_set_percentage_zero(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting fan percentage to zero turns off the fan."""
    # Reset mock to clear any previous calls
    mock_coap_client.reset_mock()

    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PERCENTAGE,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_PERCENTAGE: 0,
        },
        blocking=True,
    )

    # Setting to 0% should turn off the fan via set_control_values
    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "0"})


async def test_fan_supported_features(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan supported features."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None

    supported_features = state.attributes.get("supported_features")
    assert supported_features is not None

    # AC3858/51 should support: PRESET_MODE, TURN_OFF, TURN_ON, SET_SPEED
    # No OSCILLATE support for this model
    expected_features = (
        FanEntityFeature.PRESET_MODE | FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON | FanEntityFeature.SET_SPEED
    )
    assert supported_features == expected_features

    # Verify no oscillate feature
    assert not (supported_features & FanEntityFeature.OSCILLATE)


async def test_fan_unique_id(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan unique ID format."""
    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get(ENTITY_ID)

    assert entry is not None
    assert entry.unique_id == f"{TEST_MODEL}-{TEST_DEVICE_ID}"


async def test_fan_turn_on_with_percentage(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning on fan with percentage."""
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_PERCENTAGE: 100,
        },
        blocking=True,
    )

    # 100% should map to turbo (last speed)
    # turbo for AC3858/51: pwr="1", mode="T", om="t"
    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "1", "mode": "T", "om": "t"})


async def test_fan_set_preset_mode_allergy_sleep(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting allergy_sleep preset mode."""
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {
            ATTR_ENTITY_ID: ENTITY_ID,
            ATTR_PRESET_MODE: "allergy_sleep",
        },
        blocking=True,
    )

    # allergy_sleep preset for AC3858/51: pwr="1", mode="AS", om="as"
    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "1", "mode": "AS", "om": "as"})


async def test_fan_attributes(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test fan entity attributes."""
    state = hass.states.get(ENTITY_ID)
    assert state is not None

    # Verify all expected attributes are present
    assert "preset_modes" in state.attributes
    assert "preset_mode" in state.attributes
    assert "percentage_step" in state.attributes
    assert "supported_features" in state.attributes


@pytest.fixture
def mock_no_fan_coap_client() -> Generator[AsyncMock]:
    """Return mocked client for a model that should not create fan entity."""
    status = {
        "D03102": 1,
        "D0310C": 0,
        "D03125": 45,
        "D03128": 50,
        "D0312A": "0",
        "D0312D": 100,
        "D03103": 0,
        "DeviceId": "nofan-device",
        "name": "No Fan",
        "modelid": "HU1510",
    }
    with (
        patch("custom_components.philips_airpurifier.CoAPClient") as mock_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(status, 60))
        client.set_control_values = AsyncMock()
        client.shutdown = AsyncMock()
        mock_client_cls.create = AsyncMock(return_value=client)
        yield client


async def test_no_fan_entity_when_model_disables_fan(
    hass: HomeAssistant,
    mock_no_fan_coap_client: AsyncMock,
) -> None:
    """Test no fan entity is created when create_fan is False."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="HU1510 No Fan",
        data={
            "host": "192.168.1.111",
            CONF_MODEL: "HU1510",
            "name": "No Fan",
            CONF_DEVICE_ID: "nofan-device",
            CONF_STATUS: {
                "D03102": 1,
                "D0310C": 0,
                "D03125": 45,
                "D03128": 50,
                "D0312A": "0",
                "D0312D": 100,
                "D03103": 0,
            },
        },
        unique_id="nofan-device",
    )
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, entry.entry_id)
    assert all(entity.domain != FAN_DOMAIN for entity in entries)


def _make_fan_entity(model: str, data: dict[str, str | int]) -> tuple[PhilipsFan, PhilipsAirPurifierCoordinator]:
    """Create fan entity for direct branch testing."""
    coordinator = PhilipsAirPurifierCoordinator(
        AsyncMock(),
        AsyncMock(),
        "192.168.1.140",
        DeviceInformation(
            model=model,
            name="Fan Branch",
            device_id="fan-branch-id",
            host="192.168.1.140",
        ),
    )
    coordinator.data = data
    coordinator.async_set_control_value = AsyncMock()
    coordinator.async_set_control_values = AsyncMock()
    return PhilipsFan(coordinator), coordinator


async def test_fan_invalid_preset_mode_noop() -> None:
    """Test invalid preset mode does not call coordinator."""
    entity, coordinator = _make_fan_entity("AC3858/51", {"pwr": "1", "mode": "AG", "om": "a"})

    await entity.async_set_preset_mode("invalid")

    coordinator.async_set_control_values.assert_not_called()


async def test_fan_oscillating_status_none_branch() -> None:
    """Test oscillating returns None when oscillation key is missing in status."""
    entity, _ = _make_fan_entity("CX3120", {"D03102": 1, "D0310A": 3, "D0310C": 0})
    assert entity.oscillating is None


async def test_fan_oscillating_none_when_no_oscillation_config() -> None:
    """Test oscillating returns None for models without oscillation support."""
    entity, _ = _make_fan_entity("AC3858/51", {"pwr": "1", "mode": "AG", "om": "a"})
    assert entity.oscillating is None


async def test_fan_oscillate_branches() -> None:
    """Test oscillate updates control value for models with oscillation."""
    entity, coordinator = _make_fan_entity(
        "CX3120",
        {"D03102": 1, "D0310A": 3, "D0310C": 0, "D0320F": 0},
    )
    entity._handle_coordinator_update = lambda: None

    await entity.async_oscillate(True)
    coordinator.async_set_control_value.assert_awaited_with("D0320F", 45)

    coordinator.async_set_control_value.reset_mock()
    await entity.async_oscillate(False)
    coordinator.async_set_control_value.assert_awaited_with("D0320F", 0)


async def test_fan_oscillate_noop_without_oscillation() -> None:
    """Test oscillate is a no-op when model has no oscillation map."""
    entity, coordinator = _make_fan_entity("AC3858/51", {"pwr": "1", "mode": "AG", "om": "a"})
    await entity.async_oscillate(True)
    coordinator.async_set_control_value.assert_not_called()
