"""Tests for Philips AirPurifier repairs."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.const import CONF_STATUS, DOMAIN
from custom_components.philips_airpurifier.repairs import (
    ConfigurationMigrationFlow,
    ConnectivityRepairFlow,
    DuplicateEntitiesFlow,
    EntityRegistryCleanupFlow,
    FilterReplacementWarningFlow,
    async_check_integration_health,
    async_create_fix_flow,
    async_create_issue,
    async_delete_issue,
)
from homeassistant.components.repairs import ConfirmRepairFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir


async def test_create_fix_flow_connectivity(hass: HomeAssistant) -> None:
    """Test creating a connectivity fix flow."""
    flow = await async_create_fix_flow(hass, "connectivity_issue", None)
    assert isinstance(flow, ConnectivityRepairFlow)


async def test_create_fix_flow_filter_warning(hass: HomeAssistant) -> None:
    """Test creating a filter warning fix flow."""
    flow = await async_create_fix_flow(hass, "filter_replacement_warning", None)
    assert isinstance(flow, FilterReplacementWarningFlow)


async def test_create_fix_flow_migration(hass: HomeAssistant) -> None:
    """Test creating a configuration migration fix flow."""
    flow = await async_create_fix_flow(hass, "configuration_migration", None)
    assert isinstance(flow, ConfigurationMigrationFlow)


async def test_create_fix_flow_unknown(hass: HomeAssistant) -> None:
    """Test creating a fix flow for an unknown issue returns ConfirmRepairFlow."""
    flow = await async_create_fix_flow(hass, "unknown_issue_id", None)
    assert isinstance(flow, ConfirmRepairFlow)


async def test_create_fix_flow_entity_cleanup(hass: HomeAssistant) -> None:
    """Test creating an entity cleanup fix flow."""
    flow = await async_create_fix_flow(hass, "entity_registry_cleanup", None)
    assert isinstance(flow, EntityRegistryCleanupFlow)


async def test_create_fix_flow_duplicate_entities(hass: HomeAssistant) -> None:
    """Test creating a duplicate entities fix flow."""
    flow = await async_create_fix_flow(hass, "duplicate_entities", None)
    assert isinstance(flow, DuplicateEntitiesFlow)


async def test_connectivity_flow_init_step(hass: HomeAssistant) -> None:
    """Test the init step of the connectivity repair flow."""
    flow = ConnectivityRepairFlow()
    flow.hass = hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert "issue_description" in result["description_placeholders"]


async def test_connectivity_flow_fix_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test connectivity flow when device is reachable."""
    mock_config_entry.add_to_hass(hass)

    flow = ConnectivityRepairFlow()
    flow.hass = hass

    with patch(
        "custom_components.philips_airpurifier.repairs.CoAPClient",
    ) as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(return_value=({"pwr": "1"}, 60))
        mock_client.shutdown = AsyncMock()
        mock_client_cls.create = AsyncMock(return_value=mock_client)

        result = await flow.async_step_init(user_input={})

        assert result["type"] == "create_entry"
        assert result["title"] == "Connectivity Restored"
        assert result["data"]["result"] == "connectivity_restored"
        assert result["data"]["host"] == mock_config_entry.data["host"]


async def test_connectivity_flow_fix_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test connectivity flow when device is not reachable."""
    mock_config_entry.add_to_hass(hass)

    flow = ConnectivityRepairFlow()
    flow.hass = hass

    with patch(
        "custom_components.philips_airpurifier.repairs.CoAPClient",
    ) as mock_client_cls:
        mock_client_cls.create = AsyncMock(side_effect=TimeoutError)

        result = await flow.async_step_init(user_input={})

        assert result["type"] == "create_entry"
        assert result["title"] == "Connectivity Issue Persists"
        assert result["data"]["result"] == "connectivity_failed"


async def test_connectivity_flow_no_config_entries(hass: HomeAssistant) -> None:
    """Test connectivity flow when no entries exist."""
    flow = ConnectivityRepairFlow()
    flow.hass = hass

    result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"
    assert result["data"]["result"] == "no_config_entries_found"


async def test_connectivity_flow_outer_exception(hass: HomeAssistant) -> None:
    """Test connectivity flow handles outer exceptions."""
    flow = ConnectivityRepairFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_entries", side_effect=RuntimeError("broken")):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"
    assert result["data"]["result"] == "repair_error"


async def test_filter_replacement_flow_init_step(hass: HomeAssistant) -> None:
    """Test the init step of the filter replacement flow."""
    flow = FilterReplacementWarningFlow()
    flow.hass = hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert "issue_description" in result["description_placeholders"]


async def test_filter_replacement_flow_acknowledge(hass: HomeAssistant) -> None:
    """Test acknowledging the filter replacement warning."""
    flow = FilterReplacementWarningFlow()
    flow.hass = hass

    # First call shows the form
    result = await flow.async_step_init(user_input=None)
    assert result["type"] == "form"

    # Second call with user input acknowledges the warning
    result = await flow.async_step_init(user_input={})
    assert result["type"] == "create_entry"
    assert result["title"] == "Filter Warning Acknowledged"
    assert result["data"]["result"] == "warning_acknowledged"


async def test_configuration_migration_flow_init_step(hass: HomeAssistant) -> None:
    """Test the init step of the configuration migration flow."""
    flow = ConfigurationMigrationFlow()
    flow.hass = hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"
    assert "issue_description" in result["description_placeholders"]


async def test_configuration_migration_flow_migrate(
    hass: HomeAssistant,
) -> None:
    """Test configuration migration flow."""
    # Create an old-style config entry without CONF_STATUS
    old_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Old Entry",
        data={
            "host": "192.168.1.100",
            "model": "AC3858/51",
            "name": "Old Device",
        },
        unique_id="old_device_id",
    )
    old_entry.add_to_hass(hass)

    flow = ConfigurationMigrationFlow()
    flow.hass = hass

    mock_status = {"pwr": "1", "mode": "AG"}

    with patch(
        "custom_components.philips_airpurifier.repairs.CoAPClient",
    ) as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get_status = AsyncMock(return_value=(mock_status, 60))
        mock_client.shutdown = AsyncMock()
        mock_client_cls.create = AsyncMock(return_value=mock_client)

        result = await flow.async_step_init(user_input={})

        assert result["type"] == "create_entry"
        assert result["title"] == "Configuration Migration Complete"
        assert result["data"]["result"] == "migration_complete"
        assert old_entry.entry_id in result["data"]["migrated_entries"]

        # Verify the entry was updated
        updated_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
        assert updated_entry is not None
        assert CONF_STATUS in updated_entry.data
        assert updated_entry.data[CONF_STATUS] == mock_status


async def test_configuration_migration_flow_failure(
    hass: HomeAssistant,
) -> None:
    """Test configuration migration flow when migration fails."""
    # Create an old-style config entry without CONF_STATUS
    old_entry = MockConfigEntry(
        domain=DOMAIN,
        title="Old Entry",
        data={
            "host": "192.168.1.100",
            "model": "AC3858/51",
            "name": "Old Device",
        },
        unique_id="old_device_id",
    )
    old_entry.add_to_hass(hass)

    flow = ConfigurationMigrationFlow()
    flow.hass = hass

    with patch(
        "custom_components.philips_airpurifier.repairs.CoAPClient",
    ) as mock_client_cls:
        mock_client_cls.create = AsyncMock(side_effect=TimeoutError)

        result = await flow.async_step_init(user_input={})

        assert result["type"] == "create_entry"
        assert result["title"] == "Configuration Migration Complete"
        assert result["data"]["result"] == "migration_complete"
        assert len(result["data"]["migrated_entries"]) == 0


async def test_configuration_migration_flow_outer_exception(hass: HomeAssistant) -> None:
    """Test migration flow handles outer exceptions."""
    flow = ConfigurationMigrationFlow()
    flow.hass = hass

    with patch.object(hass.config_entries, "async_entries", side_effect=RuntimeError("broken")):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"
    assert result["data"]["result"] == "migration_error"


async def test_entity_registry_cleanup_flow_success(hass: HomeAssistant) -> None:
    """Test entity registry cleanup removes orphaned/duplicate entities."""
    flow = EntityRegistryCleanupFlow()
    flow.hass = hass

    entry = SimpleNamespace(entry_id="entry-1")
    orphan = SimpleNamespace(entity_id="sensor.orphan", device_id="missing", unique_id="uid-1")
    dup1 = SimpleNamespace(entity_id="sensor.dup_1", device_id=None, unique_id="dup")
    dup2 = SimpleNamespace(entity_id="sensor.dup_2", device_id=None, unique_id="dup")

    entity_registry = MagicMock()
    device_registry = MagicMock()
    device_registry.async_get.return_value = None

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[entry]),
        patch("custom_components.philips_airpurifier.repairs.er.async_get", return_value=entity_registry),
        patch("custom_components.philips_airpurifier.repairs.dr.async_get", return_value=device_registry),
        patch(
            "custom_components.philips_airpurifier.repairs.er.async_entries_for_config_entry",
            return_value=[orphan, dup1, dup2],
        ),
    ):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"
    assert result["data"]["result"] == "cleanup_complete"
    assert entity_registry.async_remove.called


async def test_entity_registry_cleanup_flow_exception(hass: HomeAssistant) -> None:
    """Test entity cleanup flow handles exceptions."""
    flow = EntityRegistryCleanupFlow()
    flow.hass = hass

    with patch(
        "custom_components.philips_airpurifier.repairs.er.async_get",
        side_effect=RuntimeError("boom"),
    ):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"
    assert result["data"]["result"] == "cleanup_error"


async def test_duplicate_entities_flow_success(hass: HomeAssistant) -> None:
    """Test duplicate entities flow removes duplicates."""
    flow = DuplicateEntitiesFlow()
    flow.hass = hass

    entry = SimpleNamespace(entry_id="entry-1")
    ent1 = SimpleNamespace(entity_id="sensor.a", unique_id="dup")
    ent2 = SimpleNamespace(entity_id="sensor.b", unique_id="dup")
    ent3 = SimpleNamespace(entity_id="sensor.c", unique_id="unique")
    entity_registry = MagicMock()

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[entry]),
        patch("custom_components.philips_airpurifier.repairs.er.async_get", return_value=entity_registry),
        patch(
            "custom_components.philips_airpurifier.repairs.er.async_entries_for_config_entry",
            return_value=[ent1, ent2, ent3],
        ),
    ):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"
    assert result["data"]["result"] == "duplicates_removed"
    entity_registry.async_remove.assert_called_once_with("sensor.b")


async def test_duplicate_entities_flow_exception(hass: HomeAssistant) -> None:
    """Test duplicate entities flow handles exceptions."""
    flow = DuplicateEntitiesFlow()
    flow.hass = hass

    with patch(
        "custom_components.philips_airpurifier.repairs.er.async_get",
        side_effect=RuntimeError("boom"),
    ):
        result = await flow.async_step_init(user_input={})

    assert result["type"] == "create_entry"
    assert result["data"]["result"] == "removal_error"


async def test_entity_registry_cleanup_flow_init_form(hass: HomeAssistant) -> None:
    """Test entity cleanup flow initial form branch."""
    flow = EntityRegistryCleanupFlow()
    flow.hass = hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_duplicate_entities_flow_init_form(hass: HomeAssistant) -> None:
    """Test duplicate entities flow initial form branch."""
    flow = DuplicateEntitiesFlow()
    flow.hass = hass

    result = await flow.async_step_init(user_input=None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"


async def test_create_issue(hass: HomeAssistant) -> None:
    """Test creating a repair issue."""
    issue_id = "test_issue"
    translation_key = "test_translation"

    async_create_issue(
        hass,
        issue_id,
        translation_key,
        severity=ir.IssueSeverity.ERROR,
    )

    registry = ir.async_get(hass)
    issue = registry.async_get_issue(DOMAIN, issue_id)

    assert issue is not None
    assert issue.issue_id == issue_id
    assert issue.translation_key == translation_key
    assert issue.severity == ir.IssueSeverity.ERROR
    assert issue.is_fixable is True


async def test_delete_issue(hass: HomeAssistant) -> None:
    """Test deleting a repair issue."""
    issue_id = "test_issue"

    # Create an issue first
    async_create_issue(hass, issue_id, "test_translation")

    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, issue_id) is not None

    # Delete the issue
    async_delete_issue(hass, issue_id)

    assert registry.async_get_issue(DOMAIN, issue_id) is None


async def test_check_health_no_client(hass: HomeAssistant) -> None:
    """Test health check when coordinator has no client."""
    coordinator = MagicMock()
    coordinator.client = None
    coordinator.data = {}

    await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    issue = registry.async_get_issue(DOMAIN, "connectivity_issue")

    assert issue is not None
    assert issue.translation_key == "connectivity_issue"
    assert issue.severity == ir.IssueSeverity.ERROR


async def test_check_health_filter_warning_gen1(hass: HomeAssistant) -> None:
    """Test health check when filter needs replacement (Gen1 keys)."""
    coordinator = MagicMock()
    mock_client = MagicMock()
    coordinator.client = mock_client
    coordinator.data = {
        "fltsts0": 150,  # 15 hours remaining
        "flttotal0": 2400,  # 2400 hours total = 6.25% remaining
        "fltsts1": 1000,
        "flttotal1": 4800,
        "fltsts2": 500,
        "flttotal2": 2400,
    }

    await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)

    # Should not have connectivity issue
    connectivity_issue = registry.async_get_issue(DOMAIN, "connectivity_issue")
    assert connectivity_issue is None

    # Should have filter warning
    filter_issue = registry.async_get_issue(DOMAIN, "filter_replacement_warning")
    assert filter_issue is not None
    assert filter_issue.translation_key == "filter_replacement_warning"


async def test_check_health_filter_warning_gen2(hass: HomeAssistant) -> None:
    """Test health check when filter needs replacement (Gen2 keys)."""
    coordinator = MagicMock()
    mock_client = MagicMock()
    coordinator.client = mock_client
    coordinator.data = {
        "D05-14": 100,  # Remaining
        "D05-08": 2000,  # Total = 5% remaining
    }

    await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    filter_issue = registry.async_get_issue(DOMAIN, "filter_replacement_warning")

    assert filter_issue is not None
    assert filter_issue.translation_key == "filter_replacement_warning"


async def test_check_health_filter_warning_at_threshold(hass: HomeAssistant) -> None:
    """Test health check when filter is exactly at 15% threshold."""
    coordinator = MagicMock()
    mock_client = MagicMock()
    coordinator.client = mock_client
    coordinator.data = {
        "fltsts0": 360,  # Exactly 15% of 2400
        "flttotal0": 2400,
    }

    await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    filter_issue = registry.async_get_issue(DOMAIN, "filter_replacement_warning")

    assert filter_issue is not None


async def test_check_health_ok(hass: HomeAssistant) -> None:
    """Test health check when everything is ok."""
    coordinator = MagicMock()
    mock_client = MagicMock()
    coordinator.client = mock_client
    coordinator.data = {
        "fltsts0": 2000,  # 83% remaining
        "flttotal0": 2400,
        "fltsts1": 4000,
        "flttotal1": 4800,
        "fltsts2": 2000,
        "flttotal2": 2400,
    }

    # Create some issues first to test deletion
    async_create_issue(hass, "connectivity_issue", "connectivity_issue")
    async_create_issue(hass, "filter_replacement_warning", "filter_replacement_warning")

    await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)

    # Both issues should be deleted
    connectivity_issue = registry.async_get_issue(DOMAIN, "connectivity_issue")
    assert connectivity_issue is None

    filter_issue = registry.async_get_issue(DOMAIN, "filter_replacement_warning")
    assert filter_issue is None


async def test_check_health_multiple_filters(hass: HomeAssistant) -> None:
    """Test health check with multiple filters, one needing replacement."""
    coordinator = MagicMock()
    mock_client = MagicMock()
    coordinator.client = mock_client
    coordinator.data = {
        "fltsts0": 2000,  # 83% - OK
        "flttotal0": 2400,
        "fltsts1": 500,  # 10% - Warning
        "flttotal1": 4800,
        "fltsts2": 2000,  # 83% - OK
        "flttotal2": 2400,
    }

    await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    filter_issue = registry.async_get_issue(DOMAIN, "filter_replacement_warning")

    assert filter_issue is not None


async def test_check_health_no_filter_data(hass: HomeAssistant) -> None:
    """Test health check when no filter data is available."""
    coordinator = MagicMock()
    mock_client = MagicMock()
    coordinator.client = mock_client
    coordinator.data = {"pwr": "1", "mode": "AG"}  # No filter data

    await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    filter_issue = registry.async_get_issue(DOMAIN, "filter_replacement_warning")

    # Should not create a filter warning without data
    assert filter_issue is None


async def test_check_health_zero_total(hass: HomeAssistant) -> None:
    """Test health check when filter total is zero (edge case)."""
    coordinator = MagicMock()
    mock_client = MagicMock()
    coordinator.client = mock_client
    coordinator.data = {
        "fltsts0": 100,
        "flttotal0": 0,  # Zero total - should not trigger warning
    }

    await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    filter_issue = registry.async_get_issue(DOMAIN, "filter_replacement_warning")

    # Should not create warning when total is 0
    assert filter_issue is None


async def test_check_health_creates_entity_registry_cleanup_issue(hass: HomeAssistant) -> None:
    """Test health check creates cleanup issue for orphaned/duplicate entities."""
    coordinator = MagicMock()
    coordinator.client = MagicMock()
    coordinator.data = {}

    entry = SimpleNamespace(entry_id="entry-1")
    orphan = SimpleNamespace(entity_id="sensor.orphan", device_id="missing", unique_id="u1")
    dup1 = SimpleNamespace(entity_id="sensor.dup_1", device_id=None, unique_id="dup")
    dup2 = SimpleNamespace(entity_id="sensor.dup_2", device_id=None, unique_id="dup")
    entity_registry = MagicMock()
    device_registry = MagicMock()
    device_registry.async_get.return_value = None

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[entry]),
        patch("custom_components.philips_airpurifier.repairs.er.async_get", return_value=entity_registry),
        patch("custom_components.philips_airpurifier.repairs.dr.async_get", return_value=device_registry),
        patch(
            "custom_components.philips_airpurifier.repairs.er.async_entries_for_config_entry",
            return_value=[orphan, dup1, dup2],
        ),
    ):
        await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    issue = registry.async_get_issue(DOMAIN, "entity_registry_cleanup")
    assert issue is not None


async def test_check_health_deletes_entity_registry_cleanup_issue_when_clean(
    hass: HomeAssistant,
) -> None:
    """Test health check deletes cleanup issue when no entity problems exist."""
    coordinator = MagicMock()
    coordinator.client = MagicMock()
    coordinator.data = {}

    async_create_issue(hass, "entity_registry_cleanup", "entity_registry_cleanup")

    entry = SimpleNamespace(entry_id="entry-1")
    clean_entity = SimpleNamespace(entity_id="sensor.clean", device_id=None, unique_id="u1")

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[entry]),
        patch("custom_components.philips_airpurifier.repairs.er.async_get", return_value=MagicMock()),
        patch("custom_components.philips_airpurifier.repairs.dr.async_get", return_value=MagicMock()),
        patch(
            "custom_components.philips_airpurifier.repairs.er.async_entries_for_config_entry",
            return_value=[clean_entity],
        ),
    ):
        await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    issue = registry.async_get_issue(DOMAIN, "entity_registry_cleanup")
    assert issue is None
