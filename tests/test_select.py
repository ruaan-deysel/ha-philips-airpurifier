"""Tests for Philips AirPurifier select platform."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.const import DOMAIN, PhilipsApi
from custom_components.philips_airpurifier.select import (
    _remove_duplicate_preferred_index_entity,
    async_setup_entry as select_async_setup_entry,
)
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, ATTR_OPTION
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import TEST_DEVICE_ID, TEST_MODEL


async def test_select_setup(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test select entity is created correctly."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    # AC3858/51 (Gen1) has two selects: preferred_index and fan_mode
    assert len(select_entries) == 2

    # Verify preferred_index select
    preferred_index = next(e for e in select_entries if "preferred_index" in e.entity_id)
    assert preferred_index.unique_id == f"{TEST_MODEL}-{TEST_DEVICE_ID}-ddp#2"
    assert preferred_index.translation_key == "preferred_index"

    fan_mode = next(e for e in select_entries if e.translation_key == "fan_mode")
    assert fan_mode.unique_id == f"{TEST_MODEL}-{TEST_DEVICE_ID}-fan_mode"


async def test_select_current_option(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test select current_option returns correct value based on device status."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)
    entity_id = preferred_index_entry.entity_id

    # MOCK_STATUS_GEN1 has "ddp": "1" which maps to "pm25"
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "pm25"


async def test_select_options(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test select has correct options available."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)
    entity_id = preferred_index_entry.entity_id

    state = hass.states.get(entity_id)
    assert state is not None

    # GAS_PREFERRED_INDEX_MAP has 3 options: "0": indoor_allergen_index, "1": pm25, "2": gas_level
    options = state.attributes.get("options")
    assert options is not None
    assert len(options) == 3
    assert "indoor_allergen_index" in options
    assert "pm25" in options
    assert "gas_level" in options


async def test_select_option_indoor_allergen_index(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test selecting indoor_allergen_index option."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)
    entity_id = preferred_index_entry.entity_id

    # Verify initial state is pm25 (ddp="1")
    state = hass.states.get(entity_id)
    assert state.state == "pm25"

    # Call select_option service with indoor_allergen_index
    await hass.services.async_call(
        SELECT_DOMAIN,
        "select_option",
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "indoor_allergen_index"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify set_control_values was called with correct data
    # indoor_allergen_index maps to "0" in GAS_PREFERRED_INDEX_MAP
    mock_coap_client.set_control_values.assert_called_with(data={"ddp": "0"})

    # Verify state is updated to indoor_allergen_index
    state = hass.states.get(entity_id)
    assert state.state == "indoor_allergen_index"


async def test_select_option_pm25(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test selecting pm25 option."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)
    entity_id = preferred_index_entry.entity_id

    # Call select_option service with pm25
    await hass.services.async_call(
        SELECT_DOMAIN,
        "select_option",
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "pm25"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify set_control_values was called with correct data
    # pm25 maps to "1" in GAS_PREFERRED_INDEX_MAP
    mock_coap_client.set_control_values.assert_called_with(data={"ddp": "1"})

    # Verify state is updated to pm25
    state = hass.states.get(entity_id)
    assert state.state == "pm25"


async def test_select_option_gas_level(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test selecting gas_level option."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)
    entity_id = preferred_index_entry.entity_id

    # Call select_option service with gas_level
    await hass.services.async_call(
        SELECT_DOMAIN,
        "select_option",
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "gas_level"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Verify set_control_values was called with correct data
    # gas_level maps to "2" in GAS_PREFERRED_INDEX_MAP
    mock_coap_client.set_control_values.assert_called_with(data={"ddp": "2"})

    # Verify state is updated to gas_level
    state = hass.states.get(entity_id)
    assert state.state == "gas_level"


async def test_select_unique_id_format(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test select unique_id follows the correct format."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)

    # Format: {model}-{device_id}-{kind.lower()}
    # Note: kind is "ddp#2" (GAS_PREFERRED_INDEX) lowercased
    expected_unique_id = f"{TEST_MODEL}-{TEST_DEVICE_ID}-ddp#2"
    assert preferred_index_entry.unique_id == expected_unique_id


async def test_select_entity_id_format(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test select entity_id follows Home Assistant naming conventions."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)

    # Entity ID should be like: select.living_room_preferred_index
    # (test name is "Living Room" which becomes "living_room")
    assert preferred_index_entry.entity_id.startswith("select.")
    assert "preferred_index" in preferred_index_entry.entity_id


async def test_select_entity_category(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test select has correct entity category."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)

    # preferred_index should have entity_category CONFIG
    assert preferred_index_entry.entity_category == "config"


async def test_select_updates_on_coordinator_change(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test select state updates when coordinator data changes."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entries = [e for e in entries if e.domain == SELECT_DOMAIN]

    preferred_index_entry = next(e for e in select_entries if "preferred_index" in e.entity_id)
    entity_id = preferred_index_entry.entity_id

    # Reset coordinator data to known state (ddp="1" = pm25)
    coordinator = init_integration.runtime_data
    coordinator.data["ddp"] = "1"
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    # Initial state should be pm25 (ddp="1")
    state = hass.states.get(entity_id)
    assert state.state == "pm25"

    # Update coordinator data to simulate device reporting gas_level
    coordinator = init_integration.runtime_data
    coordinator.data["ddp"] = "2"
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    # Verify state is updated to gas_level
    state = hass.states.get(entity_id)
    assert state.state == "gas_level"

    # Update coordinator data again to indoor_allergen_index
    coordinator.data["ddp"] = "0"
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    # Verify state is updated to indoor_allergen_index
    state = hass.states.get(entity_id)
    assert state.state == "indoor_allergen_index"


async def test_select_async_select_option_empty_noop(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test empty option is ignored."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entry = next(e for e in entries if e.domain == SELECT_DOMAIN and "preferred_index" in e.entity_id)
    entity = hass.data["entity_components"][SELECT_DOMAIN].get_entity(select_entry.entity_id)

    mock_coap_client.set_control_values.reset_mock()
    await entity.async_select_option("")

    mock_coap_client.set_control_values.assert_not_called()


async def test_select_async_select_option_invalid_value_noop(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test invalid option value is ignored."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entry = next(e for e in entries if e.domain == SELECT_DOMAIN and "preferred_index" in e.entity_id)
    entity = hass.data["entity_components"][SELECT_DOMAIN].get_entity(select_entry.entity_id)

    mock_coap_client.set_control_values.reset_mock()
    with pytest.raises(RuntimeError):
        await entity.async_select_option("not_a_valid_option")

    mock_coap_client.set_control_values.assert_not_called()


async def test_remove_duplicate_preferred_index_entity_by_entity_id(
    hass: HomeAssistant,
) -> None:
    """Test duplicate preferred-index entity gets removed by direct entity id."""
    entry = MockConfigEntry(domain=DOMAIN, title="Test", data={}, unique_id="u1")
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)
    entity_registry.async_get_or_create(
        "select",
        "philips_airpurifier_coap",
        "AC4220/12-device-01-d0312a#1",
        suggested_object_id="living_room_preferred_index",
        config_entry=entry,
    )

    coordinator = SimpleNamespace(device_id="device-01", model="AC4220/12", device_name="Living Room")

    await _remove_duplicate_preferred_index_entity(hass, coordinator)

    assert entity_registry.async_get("select.living_room_preferred_index") is None


async def test_remove_duplicate_preferred_index_entity_by_unique_id_scan(
    hass: HomeAssistant,
) -> None:
    """Test duplicate preferred-index entity gets removed by unique-id scan."""
    entry = MockConfigEntry(domain=DOMAIN, title="Test", data={}, unique_id="u2")
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)
    entity_registry.async_get_or_create(
        "select",
        "philips_airpurifier_coap",
        "AC4220/12-device-02-d0312a#1",
        suggested_object_id="some_other_entity",
        config_entry=entry,
    )

    coordinator = SimpleNamespace(device_id="device-02", model="AC4220/12", device_name="Different Name")

    await _remove_duplicate_preferred_index_entity(hass, coordinator)

    assert entity_registry.async_get("select.some_other_entity") is None


async def test_remove_duplicate_preferred_index_entity_exception_safe(
    hass: HomeAssistant,
) -> None:
    """Test duplicate cleanup helper handles internal exceptions safely."""
    coordinator = SimpleNamespace(device_id="device-03", model="AC4220/12", device_name="X")

    with patch(
        "custom_components.philips_airpurifier.select.async_get_entity_registry",
        side_effect=RuntimeError("registry unavailable"),
    ):
        await _remove_duplicate_preferred_index_entity(hass, coordinator)


async def test_remove_duplicate_preferred_index_entity_non_matching_unique_id_kept(
    hass: HomeAssistant,
) -> None:
    """Test direct duplicate lookup branch does not remove non-matching unique IDs."""
    entry = MockConfigEntry(domain=DOMAIN, title="Test", data={}, unique_id="u3")
    entry.add_to_hass(hass)

    entity_registry = er.async_get(hass)
    kept = entity_registry.async_get_or_create(
        "select",
        "philips_airpurifier_coap",
        "AC4220/12-device-03-d0312a#2",
        suggested_object_id="living_room_preferred_index",
        config_entry=entry,
    )

    coordinator = SimpleNamespace(device_id="device-03", model="AC4220/12", device_name="Living Room")
    await _remove_duplicate_preferred_index_entity(hass, coordinator)

    assert entity_registry.async_get(kept.entity_id) is not None


async def test_select_async_select_option_keyerror_branch(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test select option handler catches KeyError from options mapping."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entry = next(e for e in entries if e.domain == SELECT_DOMAIN and "preferred_index" in e.entity_id)
    entity = hass.data["entity_components"][SELECT_DOMAIN].get_entity(select_entry.entity_id)

    class BrokenOptionsKeyError:
        def items(self):
            msg = "broken"
            raise KeyError(msg)

    entity._options = BrokenOptionsKeyError()
    await entity.async_select_option("pm25")


async def test_select_async_select_option_valueerror_branch(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test select option handler catches ValueError from options mapping."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entry = next(e for e in entries if e.domain == SELECT_DOMAIN and "preferred_index" in e.entity_id)
    entity = hass.data["entity_components"][SELECT_DOMAIN].get_entity(select_entry.entity_id)

    class BrokenOptionsValueError:
        def items(self):
            msg = "broken"
            raise ValueError(msg)

    entity._options = BrokenOptionsValueError()
    await entity.async_select_option("pm25")


async def test_select_current_option_unknown_value_returns_string_none(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test current_option returns stringified None for unknown raw option value."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    select_entry = next(e for e in entries if e.domain == SELECT_DOMAIN and "preferred_index" in e.entity_id)
    entity = hass.data["entity_components"][SELECT_DOMAIN].get_entity(select_entry.entity_id)

    coordinator = init_integration.runtime_data
    coordinator.data["ddp"] = "unexpected"
    coordinator.async_set_updated_data(coordinator.data)
    await hass.async_block_till_done()

    assert entity.current_option == "None"


async def test_select_setup_entry_ac4220_invokes_duplicate_cleanup(hass: HomeAssistant) -> None:
    """Test AC4220 setup path triggers duplicate preferred-index cleanup helper."""
    coordinator = SimpleNamespace(
        model="AC4220/12",
        model_config=SimpleNamespace(
            selects=[PhilipsApi.NEW2_PREFERRED_INDEX, PhilipsApi.NEW2_GAS_PREFERRED_INDEX],
            create_fan=False,
            preset_modes={},
        ),
    )
    entry = SimpleNamespace(runtime_data=coordinator)
    added_entities = []

    def _add_entities(entities):
        added_entities.extend(list(entities))

    with (
        patch(
            "custom_components.philips_airpurifier.select._remove_duplicate_preferred_index_entity",
            new=AsyncMock(),
        ) as cleanup_mock,
        patch(
            "custom_components.philips_airpurifier.select.PhilipsSelect",
            side_effect=lambda _coordinator, kind: SimpleNamespace(kind=kind),
        ) as select_cls,
    ):
        await select_async_setup_entry(hass, entry, _add_entities)

    cleanup_mock.assert_awaited_once()
    assert select_cls.call_count == 1
    kinds = {entity.kind for entity in added_entities}
    assert PhilipsApi.NEW2_PREFERRED_INDEX not in kinds
    assert PhilipsApi.NEW2_GAS_PREFERRED_INDEX in kinds


async def test_fan_mode_select_option_updates_preset(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test fan_mode select calls set_control_values with preset status pattern."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    fan_mode_entry = next(e for e in entries if e.domain == SELECT_DOMAIN and e.translation_key == "fan_mode")
    entity_id = fan_mode_entry.entity_id

    await hass.services.async_call(
        SELECT_DOMAIN,
        "select_option",
        {ATTR_ENTITY_ID: entity_id, ATTR_OPTION: "sleep"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "1", "mode": "S", "om": "s"})

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "sleep"


async def test_fan_mode_select_empty_option_noop(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test fan_mode select ignores empty options."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    fan_mode_entry = next(e for e in entries if e.domain == SELECT_DOMAIN and e.translation_key == "fan_mode")
    entity = hass.data["entity_components"][SELECT_DOMAIN].get_entity(fan_mode_entry.entity_id)

    mock_coap_client.set_control_values.reset_mock()
    await entity.async_select_option("")
    mock_coap_client.set_control_values.assert_not_called()


async def test_fan_mode_select_invalid_option_noop(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test fan_mode select ignores invalid options."""
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, init_integration.entry_id)
    fan_mode_entry = next(e for e in entries if e.domain == SELECT_DOMAIN and e.translation_key == "fan_mode")
    entity = hass.data["entity_components"][SELECT_DOMAIN].get_entity(fan_mode_entry.entity_id)

    mock_coap_client.set_control_values.reset_mock()
    await entity.async_select_option("invalid_mode")
    mock_coap_client.set_control_values.assert_not_called()
