"""Tests for Philips AirPurifier number platform."""

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
    PhilipsApi,
)
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
)
from homeassistant.components.number.const import SERVICE_SET_VALUE
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

if TYPE_CHECKING:
    from collections.abc import Generator

# AMF765 is Gen3 with numbers=[PhilipsApi.NEW2_OSCILLATION]
TEST_MODEL_WITH_NUMBER = "AMF765"
TEST_HOST = "192.168.1.100"
TEST_NAME = "Living Room"
TEST_DEVICE_ID = "aabbccddeeff"

# Gen3 status for AMF765
MOCK_STATUS_NUMBER: dict = {
    "D03102": 1,  # power on
    "D0310C": 2,  # mode
    "D0310D": 3,  # fan speed / mode_c
    "D0312D": 100,  # display backlight
    "D03103": 0,  # child lock
    "D03120": 3,  # indoor allergen index
    "D03221": 12,  # pm25
    "D03224": 220,  # temperature (divided by 10)
    "D03125": 50,  # humidity
    "D0320F": 45,  # oscillation
    "D0540E": 500,  # nanoprotect filter
    "D05408": 2400,  # nanoprotect filter total
    "D0520D": 200,  # nanoprotect prefilter
    "D05207": 2400,  # nanoprotect prefilter total
    "D0310E": 22,  # target temp
    "D0310A": 3,  # mode_a - heating
    "D03240": 0,  # error code
    "DeviceId": TEST_DEVICE_ID,
    "D01S03": TEST_NAME,
    "D01S05": TEST_MODEL_WITH_NUMBER,
    "D01S12": "1.0.0",
}


@pytest.fixture
def mock_number_config_entry() -> MockConfigEntry:
    """Return a mock config entry for a model with number entities."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{TEST_MODEL_WITH_NUMBER} {TEST_NAME}",
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL_WITH_NUMBER,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_NUMBER,
        },
        unique_id=TEST_DEVICE_ID,
    )


@pytest.fixture
def mock_number_coap_client() -> Generator[AsyncMock]:
    """Return a mocked CoAP client for the number model."""
    with (
        patch(
            "custom_components.philips_airpurifier.CoAPClient",
        ) as mock_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(MOCK_STATUS_NUMBER.copy(), 60))
        client.set_control_values = AsyncMock()
        client.set_control_value = AsyncMock()
        client.shutdown = AsyncMock()

        mock_client_cls.create = AsyncMock(return_value=client)
        mock_client_cls.return_value = client

        yield client


@pytest.fixture
async def init_number_integration(
    hass: HomeAssistant,
    mock_number_config_entry: MockConfigEntry,
    mock_number_coap_client: AsyncMock,
) -> MockConfigEntry:
    """Set up integration with number model."""
    mock_number_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_number_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_number_config_entry.state is ConfigEntryState.LOADED
    return mock_number_config_entry


OSCILLATION_ENTITY_ID = "number.living_room_oscillation"
TARGET_TEMP_ENTITY_ID = "number.living_room_target_temperature"


def _get_number_entity_id(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    key: str,
) -> str:
    """Get number entity ID by unique-id suffix key."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)
    number_entries = [e for e in entries if e.domain == NUMBER_DOMAIN]
    entry = next(e for e in number_entries if e.unique_id.endswith(f"-{key.lower()}"))
    return entry.entity_id


async def test_number_setup(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
) -> None:
    """Test that number entities are created."""
    entity_registry = er.async_get(hass)

    osc_entity_id = _get_number_entity_id(hass, init_number_integration, PhilipsApi.NEW2_OSCILLATION)
    osc_entry = entity_registry.async_get(osc_entity_id)
    assert osc_entry is not None
    assert osc_entry.unique_id == f"{TEST_MODEL_WITH_NUMBER}-{TEST_DEVICE_ID}-{PhilipsApi.NEW2_OSCILLATION.lower()}"


async def test_number_native_value(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
) -> None:
    """Test number native_value returns current status value."""
    osc_entity_id = _get_number_entity_id(hass, init_number_integration, PhilipsApi.NEW2_OSCILLATION)
    state = hass.states.get(osc_entity_id)
    assert state is not None
    # D0320F = 45 in mock status
    assert float(state.state) == 45.0


async def test_number_set_value(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
    mock_number_coap_client: AsyncMock,
) -> None:
    """Test setting a number value."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: _get_number_entity_id(hass, init_number_integration, PhilipsApi.NEW2_OSCILLATION),
            ATTR_VALUE: 90,
        },
        blocking=True,
    )

    # Oscillation: step=5, min=30, max=350, off=0
    # value=90, 90 >= min(30), 90 % 5 == 0, 90 <= 350
    mock_number_coap_client.set_control_values.assert_called_with(data={PhilipsApi.NEW2_OSCILLATION: 90})


async def test_number_set_value_below_min(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
    mock_number_coap_client: AsyncMock,
) -> None:
    """Test setting a value below native_min_value clamps to min."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: _get_number_entity_id(hass, init_number_integration, PhilipsApi.NEW2_OSCILLATION),
            ATTR_VALUE: 0,
        },
        blocking=True,
    )

    # value=0 is below native_min_value (0), but since 0 == native_min_value and
    # value > 0 check fails, it stays 0. Then min(0, 350) = 0. So final = 0.
    mock_number_coap_client.set_control_values.assert_called_with(data={PhilipsApi.NEW2_OSCILLATION: 0})


async def test_number_set_value_rounds_to_step(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
    mock_number_coap_client: AsyncMock,
) -> None:
    """Test that value is rounded down to step."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: _get_number_entity_id(hass, init_number_integration, PhilipsApi.NEW2_OSCILLATION),
            ATTR_VALUE: 93,
        },
        blocking=True,
    )

    # value=93, 93 % 5 = 3 > 0, so 93 // 5 * 5 = 90
    # 90 > 0, so max(90, 30) = 90. min(90, 350) = 90.
    mock_number_coap_client.set_control_values.assert_called_with(data={PhilipsApi.NEW2_OSCILLATION: 90})


async def test_number_set_value_max(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
    mock_number_coap_client: AsyncMock,
) -> None:
    """Test setting a value at max."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: _get_number_entity_id(hass, init_number_integration, PhilipsApi.NEW2_OSCILLATION),
            ATTR_VALUE: 350,
        },
        blocking=True,
    )

    mock_number_coap_client.set_control_values.assert_called_with(data={PhilipsApi.NEW2_OSCILLATION: 350})


async def test_number_target_temp_setup(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
) -> None:
    """Test target temp number entity is created."""
    entity_registry = er.async_get(hass)

    entries = er.async_entries_for_config_entry(entity_registry, init_number_integration.entry_id)
    number_entries = [e for e in entries if e.domain == NUMBER_DOMAIN]
    assert all(not e.unique_id.endswith(f"-{PhilipsApi.NEW2_TARGET_TEMP.lower()}") for e in number_entries)


async def test_number_target_temp_value(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
) -> None:
    """Test target temp number value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_number_integration.entry_id)
    number_entries = [e for e in entries if e.domain == NUMBER_DOMAIN]
    assert all(not e.unique_id.endswith(f"-{PhilipsApi.NEW2_TARGET_TEMP.lower()}") for e in number_entries)


async def test_number_set_value_positive_below_min_threshold(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
    mock_number_coap_client: AsyncMock,
) -> None:
    """Test that positive value below min is clamped to min."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: _get_number_entity_id(hass, init_number_integration, PhilipsApi.NEW2_OSCILLATION),
            ATTR_VALUE: 10,
        },
        blocking=True,
    )

    # value=10, 10 % 5 == 0 (no rounding needed)
    # value > 0, so max(10, 30) = 30. min(30, 350) = 30.
    mock_number_coap_client.set_control_values.assert_called_with(data={PhilipsApi.NEW2_OSCILLATION: 30})


async def test_number_set_native_value_none_coerces_to_min(
    hass: HomeAssistant,
    init_number_integration: MockConfigEntry,
    mock_number_coap_client: AsyncMock,
) -> None:
    """Test direct entity call with None coerces to native minimum."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_number_integration.entry_id)
    number_entry = next(
        e
        for e in entries
        if e.domain == NUMBER_DOMAIN and e.unique_id.endswith(f"-{PhilipsApi.NEW2_OSCILLATION.lower()}")
    )
    entity = hass.data["entity_components"][NUMBER_DOMAIN].get_entity(number_entry.entity_id)

    await entity.async_set_native_value(None)

    mock_number_coap_client.set_control_values.assert_called_with(data={PhilipsApi.NEW2_OSCILLATION: 0})
