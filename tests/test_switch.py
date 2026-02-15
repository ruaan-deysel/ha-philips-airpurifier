"""Tests for Philips AirPurifier switch platform."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.components.switch.const import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import TEST_DEVICE_ID, TEST_MODEL

if TYPE_CHECKING:
    from unittest.mock import AsyncMock


async def test_switch_setup(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test switch entity is created correctly."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    switch_entries = [e for e in entries if e.domain == SWITCH_DOMAIN]

    # AC3858/51 (Gen1) has one switch: child_lock
    assert len(switch_entries) == 1

    # Verify child lock switch
    child_lock = next(e for e in switch_entries if "child_lock" in e.entity_id)
    assert child_lock.unique_id == f"{TEST_MODEL}-{TEST_DEVICE_ID}-cl"
    assert child_lock.translation_key == "child_lock"


async def test_switch_is_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test switch state is off when device reports off value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    switch_entries = [e for e in entries if e.domain == SWITCH_DOMAIN]

    child_lock_entry = next(e for e in switch_entries if "child_lock" in e.entity_id)
    entity_id = child_lock_entry.entity_id

    # MOCK_STATUS_GEN1 has "cl": False (child lock off)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_OFF


async def test_switch_is_on(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test switch state is on when device reports on value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    switch_entries = [e for e in entries if e.domain == SWITCH_DOMAIN]

    child_lock_entry = next(e for e in switch_entries if "child_lock" in e.entity_id)
    entity_id = child_lock_entry.entity_id

    # Update coordinator data to simulate device reporting child lock as on
    coordinator = init_integration.runtime_data
    coordinator.data["cl"] = True
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == STATE_ON


async def test_switch_turn_on(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning on the switch."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    switch_entries = [e for e in entries if e.domain == SWITCH_DOMAIN]

    child_lock_entry = next(e for e in switch_entries if "child_lock" in e.entity_id)
    entity_id = child_lock_entry.entity_id

    # Ensure switch starts in off state
    coordinator = init_integration.runtime_data
    coordinator.data["cl"] = False
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    # Verify initial state is off
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF

    # Call turn_on service
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_on",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify set_control_values was called with correct data
    # For child_lock (cl), on_value is True
    mock_coap_client.set_control_values.assert_called_with(data={"cl": True})

    # Verify state is updated to on
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON


async def test_switch_turn_off(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test turning off the switch."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    switch_entries = [e for e in entries if e.domain == SWITCH_DOMAIN]

    child_lock_entry = next(e for e in switch_entries if "child_lock" in e.entity_id)
    entity_id = child_lock_entry.entity_id

    # First, turn on the switch
    coordinator = init_integration.runtime_data
    coordinator.data["cl"] = True
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    # Verify state is on
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    # Call turn_off service
    await hass.services.async_call(
        SWITCH_DOMAIN,
        "turn_off",
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify set_control_values was called with correct data
    # For child_lock (cl), off_value is False
    mock_coap_client.set_control_values.assert_called_with(data={"cl": False})

    # Verify state is updated to off
    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF


async def test_switch_unique_id_format(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test switch unique_id follows the correct format."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    switch_entries = [e for e in entries if e.domain == SWITCH_DOMAIN]

    child_lock_entry = next(e for e in switch_entries if "child_lock" in e.entity_id)

    # Verify unique_id follows the pattern model-device_id-kind
    expected_unique_id = f"{TEST_MODEL}-{TEST_DEVICE_ID}-cl"
    assert child_lock_entry.unique_id == expected_unique_id


async def test_switch_entity_id_format(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test switch entity_id follows Home Assistant naming conventions."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    switch_entries = [e for e in entries if e.domain == SWITCH_DOMAIN]

    child_lock_entry = next(e for e in switch_entries if "child_lock" in e.entity_id)

    # Entity ID should be like: switch.living_room_child_lock
    # (test name is "Living Room" which becomes "living_room")
    assert child_lock_entry.entity_id.startswith("switch.")
    assert "child_lock" in child_lock_entry.entity_id


async def test_switch_entity_category(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test switch has correct entity category."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    switch_entries = [e for e in entries if e.domain == SWITCH_DOMAIN]

    child_lock_entry = next(e for e in switch_entries if "child_lock" in e.entity_id)

    # child_lock should have entity_category CONFIG
    assert child_lock_entry.entity_category == "config"
