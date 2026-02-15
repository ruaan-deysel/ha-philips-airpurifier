"""Tests for Philips AirPurifier humidifier platform."""

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
    FanFunction,
)
from homeassistant.components.humidifier.const import (
    ATTR_HUMIDITY,
    DOMAIN as HUMIDIFIER_DOMAIN,
)
from homeassistant.components.number import ATTR_VALUE, DOMAIN as NUMBER_DOMAIN
from homeassistant.components.number.const import SERVICE_SET_VALUE
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
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

TEST_MODEL = "AC2729"
TEST_HOST = "192.168.1.110"
TEST_NAME = "Hum Room"
TEST_DEVICE_ID = "humidifier-device-01"

MOCK_STATUS_HUMIDIFIER: dict = {
    "pwr": "1",
    "mode": "AG",
    "om": "a",
    "func": "PH",
    "rhset": 50,
    "rh": 47,
    "aqil": 100,
    "uil": "1",
    "ddp": "1",
    "rddp": "1",
    "cl": False,
    "dt": 0,
    "err": 0,
    "DeviceId": TEST_DEVICE_ID,
    "name": TEST_NAME,
    "modelid": TEST_MODEL,
}


HU_MODEL = "HU1510"
HU_STATUS: dict = {
    "D03102": 1,
    "D0310C": 0,
    "D03125": 50,
    "D03128": 50,
    "D0312D": 100,
    "D03103": 0,
    "DeviceId": "hu-device-01",
    "name": "HU Room",
    "modelid": HU_MODEL,
}


@pytest.fixture
def mock_humidifier_config_entry() -> MockConfigEntry:
    """Return a mock config entry for a model with humidifier support."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{TEST_MODEL} {TEST_NAME}",
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_HUMIDIFIER,
        },
        unique_id=TEST_DEVICE_ID,
    )


@pytest.fixture
def mock_humidifier_coap_client() -> Generator[AsyncMock]:
    """Return a mocked CoAP client for humidifier tests."""
    with (
        patch("custom_components.philips_airpurifier.CoAPClient") as mock_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(MOCK_STATUS_HUMIDIFIER.copy(), 60))
        client.set_control_values = AsyncMock()
        client.set_control_value = AsyncMock()
        client.shutdown = AsyncMock()

        mock_client_cls.create = AsyncMock(return_value=client)
        mock_client_cls.return_value = client

        yield client


@pytest.fixture
async def init_humidifier_integration(
    hass: HomeAssistant,
    mock_humidifier_config_entry: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> MockConfigEntry:
    """Set up integration with humidifier model."""
    mock_humidifier_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_humidifier_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_humidifier_config_entry.state is ConfigEntryState.LOADED
    return mock_humidifier_config_entry


def _get_humidifier_entity_id(hass: HomeAssistant, config_entry: MockConfigEntry) -> str:
    """Return humidifier entity ID."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    humidifier_entry = next(e for e in entries if e.domain == HUMIDIFIER_DOMAIN)
    return humidifier_entry.entity_id


def _get_humidity_target_number_entity_id(hass: HomeAssistant, config_entry: MockConfigEntry) -> str:
    """Return humidity target number entity ID."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    number_entry = next(e for e in entries if e.domain == NUMBER_DOMAIN and "humidity_target" in e.entity_id)
    return number_entry.entity_id


async def test_humidifier_setup(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
) -> None:
    """Test humidifier entity is created."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("current_humidity") == 47
    assert state.attributes.get("humidity") == 50


async def test_humidifier_action_and_mode_humidifying(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
) -> None:
    """Test humidifier action/mode when function is humidifying."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("action") == "humidifying"
    assert state.attributes.get("mode") == FanFunction.PURIFICATION_HUMIDIFICATION


async def test_humidifier_mode_purification_when_idle(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
) -> None:
    """Test humidifier mode/action when function is idle purification."""
    coordinator = init_humidifier_integration.runtime_data
    coordinator.data["func"] = "P"
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)
    state = hass.states.get(entity_id)

    assert state is not None
    assert state.attributes.get("action") == "idle"
    assert state.attributes.get("mode") == FanFunction.PURIFICATION


async def test_humidifier_set_mode_humidification(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test setting humidifier mode to purification+humidification."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        "set_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_MODE: FanFunction.PURIFICATION_HUMIDIFICATION},
        blocking=True,
    )

    mock_humidifier_coap_client.set_control_values.assert_called_with(data={"pwr": "1", "func": "PH"})


async def test_humidifier_set_mode_purification(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test setting humidifier mode to purification."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        "set_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_MODE: FanFunction.PURIFICATION},
        blocking=True,
    )

    mock_humidifier_coap_client.set_control_values.assert_called_with(data={"pwr": "1", "func": "P"})


async def test_humidity_target_number_set_value(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test humidity target number entity updates rhset value."""
    entity_id = _get_humidity_target_number_entity_id(hass, init_humidifier_integration)

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, ATTR_VALUE: 60},
        blocking=True,
    )

    mock_humidifier_coap_client.set_control_values.assert_called_with(data={"rhset": 60})

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "60.0"


async def test_humidifier_set_mode_invalid_no_call(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test invalid humidifier mode is ignored."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)
    mock_humidifier_coap_client.set_control_values.reset_mock()

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        "set_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_MODE: "invalid_mode"},
        blocking=True,
    )

    mock_humidifier_coap_client.set_control_values.assert_not_called()


async def test_humidifier_turn_on_turn_off(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test humidifier turn on/off actions."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert mock_humidifier_coap_client.set_control_values.await_args_list[-2].kwargs == {"data": {"pwr": "0"}}
    assert mock_humidifier_coap_client.set_control_values.await_args_list[-1].kwargs == {"data": {"pwr": "1"}}


async def test_humidifier_set_humidity_plus_one_uses_step(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test setting target humidity +1 increments by configured step."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        "set_humidity",
        {ATTR_ENTITY_ID: entity_id, ATTR_HUMIDITY: 51},
        blocking=True,
    )

    mock_humidifier_coap_client.set_control_values.assert_called_with(data={"rhset": 60})


async def test_humidifier_set_humidity_clamped_max(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test target humidity is clamped to max."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            HUMIDIFIER_DOMAIN,
            "set_humidity",
            {ATTR_ENTITY_ID: entity_id, ATTR_HUMIDITY: 90},
            blocking=True,
        )

    mock_humidifier_coap_client.set_control_values.assert_not_called()


@pytest.fixture
def mock_hu_config_entry() -> MockConfigEntry:
    """Return mock config entry for HU1510 humidifier branch paths."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{HU_MODEL} HU Room",
        data={
            CONF_HOST: "192.168.1.111",
            CONF_MODEL: HU_MODEL,
            CONF_NAME: "HU Room",
            CONF_DEVICE_ID: "hu-device-01",
            CONF_STATUS: HU_STATUS,
        },
        unique_id="hu-device-01",
    )


@pytest.fixture
def mock_hu_coap_client() -> Generator[AsyncMock]:
    """Return mocked CoAP client for HU1510."""
    with (
        patch("custom_components.philips_airpurifier.CoAPClient") as mock_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(HU_STATUS.copy(), 60))
        client.set_control_values = AsyncMock()
        client.set_control_value = AsyncMock()
        client.shutdown = AsyncMock()
        mock_client_cls.create = AsyncMock(return_value=client)
        yield client


@pytest.fixture
async def init_hu_integration(
    hass: HomeAssistant,
    mock_hu_config_entry: MockConfigEntry,
    mock_hu_coap_client: AsyncMock,
) -> MockConfigEntry:
    """Set up HU1510 integration."""
    mock_hu_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_hu_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_hu_config_entry


async def test_humidifier_function_equals_power_mode_branch(
    hass: HomeAssistant,
    init_hu_integration: MockConfigEntry,
    mock_hu_coap_client: AsyncMock,
) -> None:
    """Test mode handling when function key equals power key."""
    entity_id = _get_humidifier_entity_id(hass, init_hu_integration)

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        "set_mode",
        {ATTR_ENTITY_ID: entity_id, ATTR_MODE: "sleep"},
        blocking=True,
    )

    mock_hu_coap_client.set_control_values.assert_called_with(data={"D03102": 1, "D0310C": 17})


async def test_humidifier_set_humidity_minus_one_uses_step(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test setting target humidity -1 decrements by step."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        "set_humidity",
        {ATTR_ENTITY_ID: entity_id, ATTR_HUMIDITY: 49},
        blocking=True,
    )

    mock_humidifier_coap_client.set_control_values.assert_called_with(data={"rhset": 40})


async def test_humidifier_mode_none_when_no_preset_match(
    hass: HomeAssistant,
    init_hu_integration: MockConfigEntry,
) -> None:
    """Test mode branch returning None when no preset pattern matches."""
    entity_id = _get_humidifier_entity_id(hass, init_hu_integration)
    entity = hass.data["entity_components"][HUMIDIFIER_DOMAIN].get_entity(entity_id)

    coordinator = init_hu_integration.runtime_data
    coordinator.data["D0310C"] = 255

    assert entity.mode is None


async def test_humidifier_set_humidity_regular_rounding_path(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test humidity target path when input is not +/-1 from current target."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)

    await hass.services.async_call(
        HUMIDIFIER_DOMAIN,
        "set_humidity",
        {ATTR_ENTITY_ID: entity_id, ATTR_HUMIDITY: 53},
        blocking=True,
    )

    mock_humidifier_coap_client.set_control_values.assert_called_with(data={"rhset": 50})


async def test_humidifier_set_humidity_without_existing_target_uses_input(
    hass: HomeAssistant,
    init_humidifier_integration: MockConfigEntry,
    mock_humidifier_coap_client: AsyncMock,
) -> None:
    """Test set_humidity branch when current and cached target are missing."""
    entity_id = _get_humidifier_entity_id(hass, init_humidifier_integration)
    humidifier_entity = hass.data["entity_components"][HUMIDIFIER_DOMAIN].get_entity(entity_id)

    coordinator = init_humidifier_integration.runtime_data
    coordinator.data.pop("rhset", None)
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    humidifier_entity._attr_target_humidity = None
    await humidifier_entity.async_set_humidity(46)

    mock_humidifier_coap_client.set_control_values.assert_called_with(data={"rhset": 50})
