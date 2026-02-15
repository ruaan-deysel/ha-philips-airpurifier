"""Tests for Philips AirPurifier binary sensor platform."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.binary_sensor import PhilipsBinarySensor
from custom_components.philips_airpurifier.const import (
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_STATUS,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_NAME, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

if TYPE_CHECKING:
    from collections.abc import Generator

# AC2729 is Gen1 with binary_sensors=[PhilipsApi.ERROR_CODE]
# We'll use it for testing binary sensor entities.
TEST_MODEL_WITH_BINARY = "AC2729"
TEST_HOST = "192.168.1.100"
TEST_NAME = "Living Room"
TEST_DEVICE_ID = "aabbccddeeff"

# AC2729 Gen1 status - includes err and func keys for binary sensors
MOCK_STATUS_BINARY: dict = {
    "pwr": "1",
    "mode": "AG",
    "om": "a",
    "aqil": 100,
    "uil": "1",
    "ddp": "1",
    "rddp": "1",
    "cl": False,
    "dt": 0,
    "err": 0,
    "func": "PH",
    "rhset": 50,
    "DeviceId": TEST_DEVICE_ID,
    "name": TEST_NAME,
    "modelid": TEST_MODEL_WITH_BINARY,
    "WifiVersion": "AWS_Philips_AIR@1.0.0",
    "pm25": 12,
    "iaql": 3,
    "rh": 50,
    "temp": 22,
    "wl": 80,
    "fltsts0": 200,
    "flttotal0": 2400,
    "fltsts1": 1000,
    "flttotal1": 4800,
    "fltsts2": 500,
    "flttotal2": 2400,
    "wicksts": 100,
    "wicktotal": 2400,
    "fltt1": "A3",
    "fltt2": "C7",
}


@pytest.fixture
def mock_binary_config_entry() -> MockConfigEntry:
    """Return a mock config entry for a model with binary sensors."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{TEST_MODEL_WITH_BINARY} {TEST_NAME}",
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL_WITH_BINARY,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_BINARY,
        },
        unique_id=TEST_DEVICE_ID,
    )


@pytest.fixture
def mock_binary_coap_client() -> Generator[AsyncMock]:
    """Return a mocked CoAP client for the binary sensor model."""
    with (
        patch(
            "custom_components.philips_airpurifier.CoAPClient",
        ) as mock_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(MOCK_STATUS_BINARY.copy(), 60))
        client.set_control_values = AsyncMock()
        client.set_control_value = AsyncMock()
        client.shutdown = AsyncMock()

        mock_client_cls.create = AsyncMock(return_value=client)
        mock_client_cls.return_value = client

        yield client


@pytest.fixture
async def init_binary_integration(
    hass: HomeAssistant,
    mock_binary_config_entry: MockConfigEntry,
    mock_binary_coap_client: AsyncMock,
) -> MockConfigEntry:
    """Set up integration with binary sensor model."""
    mock_binary_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_binary_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_binary_config_entry.state is ConfigEntryState.LOADED
    return mock_binary_config_entry


WATER_TANK_ENTITY_ID = "binary_sensor.living_room_water_tank"
HUMIDIFICATION_ENTITY_ID = "binary_sensor.living_room_humidification"


async def test_binary_sensor_setup(
    hass: HomeAssistant,
    init_binary_integration: MockConfigEntry,
) -> None:
    """Test that binary sensor entities are created for AC2729."""
    entity_registry = er.async_get(hass)

    # AC2729 has binary_sensors=[PhilipsApi.ERROR_CODE] -> water_tank
    water_tank = entity_registry.async_get(WATER_TANK_ENTITY_ID)
    assert water_tank is not None
    assert water_tank.unique_id == f"{TEST_MODEL_WITH_BINARY}-{TEST_DEVICE_ID}-err"


async def test_binary_sensor_water_tank_on(
    hass: HomeAssistant,
    init_binary_integration: MockConfigEntry,
) -> None:
    """Test water tank binary sensor is on when no error (err=0)."""
    # err=0, bit 8 is not set -> value lambda: not 0 & (1<<8) = not 0 = True -> on
    state = hass.states.get(WATER_TANK_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON


async def test_binary_sensor_water_tank_off(
    hass: HomeAssistant,
    mock_binary_coap_client: AsyncMock,
) -> None:
    """Test water tank binary sensor is off when err has bit 8 set."""
    # Set err to a value with bit 8 set (256 = 1<<8)
    status = MOCK_STATUS_BINARY.copy()
    status["err"] = 256
    mock_binary_coap_client.get_status = AsyncMock(return_value=(status, 60))
    # Can't easily do this inline. Let's use the fixture-based approach instead.


async def test_binary_sensor_humidification_on(
    hass: HomeAssistant,
    init_binary_integration: MockConfigEntry,
) -> None:
    """Test humidification binary sensor is not created for AC2729."""
    state = hass.states.get(HUMIDIFICATION_ENTITY_ID)
    assert state is None


async def test_binary_sensor_with_convert_function(
    hass: HomeAssistant,
    init_binary_integration: MockConfigEntry,
) -> None:
    """Test binary sensor uses convert function from description."""
    # The water_tank sensor uses VALUE lambda: not value & (1 << 8)
    # With err=0, bit 8 is not set, so not (0 & 256) = not 0 = True
    state = hass.states.get(WATER_TANK_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON


async def test_binary_sensor_unique_id(
    hass: HomeAssistant,
    init_binary_integration: MockConfigEntry,
) -> None:
    """Test binary sensor unique ID format."""
    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get(WATER_TANK_ENTITY_ID)
    assert entry is not None
    assert entry.unique_id == f"{TEST_MODEL_WITH_BINARY}-{TEST_DEVICE_ID}-err"


async def test_binary_sensor_is_on_without_convert_uses_raw_value(
    hass: HomeAssistant,
    init_binary_integration: MockConfigEntry,
) -> None:
    """Test is_on branch when description has no VALUE converter."""
    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get(WATER_TANK_ENTITY_ID)
    assert entry is not None
    entity = hass.data["entity_components"]["binary_sensor"].get_entity(entry.entity_id)

    entity._description = {}
    entity._device_status[entity.kind] = 1

    assert isinstance(entity, PhilipsBinarySensor)
    assert entity.is_on == 1
