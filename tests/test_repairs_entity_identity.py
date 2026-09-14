"""Regression tests for entity registry identity handling in repairs."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from custom_components.philips_airpurifier.const import DOMAIN
from custom_components.philips_airpurifier.repairs import (
    DuplicateEntitiesFlow,
    EntityRegistryCleanupFlow,
    async_check_integration_health,
    async_create_issue,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir


def _entity(
    entity_id: str,
    *,
    domain: str,
    platform: str = DOMAIN,
    unique_id: str = "shared-unique-id",
) -> SimpleNamespace:
    """Create a lightweight entity-registry entry for repair tests."""
    return SimpleNamespace(
        entity_id=entity_id,
        domain=domain,
        platform=platform,
        unique_id=unique_id,
        device_id=None,
    )


async def test_health_check_allows_same_unique_id_across_domains(
    hass: HomeAssistant,
) -> None:
    """Do not flag valid cross-domain entities as duplicates."""
    coordinator = MagicMock()
    coordinator.client = MagicMock()
    coordinator.data = {}
    coordinator.host = "192.0.2.1"

    entry = SimpleNamespace(entry_id="entry-1", data={}, options={})
    light = _entity("light.display_backlight", domain="light")
    switch = _entity("switch.beep", domain="switch")

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[entry]),
        patch("custom_components.philips_airpurifier.repairs.er.async_get", return_value=MagicMock()),
        patch("custom_components.philips_airpurifier.repairs.dr.async_get", return_value=MagicMock()),
        patch(
            "custom_components.philips_airpurifier.repairs.er.async_entries_for_config_entry",
            return_value=[light, switch],
        ),
    ):
        await async_check_integration_health(hass, coordinator)

    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, "entity_registry_cleanup") is None


async def test_duplicate_flow_keeps_same_unique_id_across_domains(
    hass: HomeAssistant,
) -> None:
    """Duplicate repair must not remove valid cross-domain entities."""
    flow = DuplicateEntitiesFlow()
    flow.hass = hass

    entry = SimpleNamespace(entry_id="entry-1")
    light = _entity("light.display_backlight", domain="light")
    switch = _entity("switch.beep", domain="switch")
    entity_registry = MagicMock()

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[entry]),
        patch("custom_components.philips_airpurifier.repairs.er.async_get", return_value=entity_registry),
        patch(
            "custom_components.philips_airpurifier.repairs.er.async_entries_for_config_entry",
            return_value=[light, switch],
        ),
    ):
        result = await flow.async_step_init(user_input={})

    assert result["data"]["removed_entities"] == []
    entity_registry.async_remove.assert_not_called()


async def test_cleanup_flow_keeps_same_unique_id_across_domains(
    hass: HomeAssistant,
) -> None:
    """Cleanup repair must not remove valid cross-domain entities."""
    flow = EntityRegistryCleanupFlow()
    flow.hass = hass

    entry = SimpleNamespace(entry_id="entry-1")
    light = _entity("light.display_backlight", domain="light")
    switch = _entity("switch.beep", domain="switch")
    entity_registry = MagicMock()

    async_create_issue(hass, "entity_registry_cleanup", "entity_registry_cleanup")

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[entry]),
        patch("custom_components.philips_airpurifier.repairs.er.async_get", return_value=entity_registry),
        patch("custom_components.philips_airpurifier.repairs.dr.async_get", return_value=MagicMock()),
        patch(
            "custom_components.philips_airpurifier.repairs.er.async_entries_for_config_entry",
            return_value=[light, switch],
        ),
    ):
        result = await flow.async_step_init(user_input={})

    assert result["data"]["cleaned_entities"] == []
    entity_registry.async_remove.assert_not_called()
    registry = ir.async_get(hass)
    assert registry.async_get_issue(DOMAIN, "entity_registry_cleanup") is None


async def test_duplicate_flow_still_removes_same_registry_identity(
    hass: HomeAssistant,
) -> None:
    """Entities with identical domain, platform and unique ID remain duplicates."""
    flow = DuplicateEntitiesFlow()
    flow.hass = hass

    entry = SimpleNamespace(entry_id="entry-1")
    first = _entity("sensor.first", domain="sensor")
    second = _entity("sensor.second", domain="sensor")
    entity_registry = MagicMock()

    with (
        patch.object(hass.config_entries, "async_entries", return_value=[entry]),
        patch("custom_components.philips_airpurifier.repairs.er.async_get", return_value=entity_registry),
        patch(
            "custom_components.philips_airpurifier.repairs.er.async_entries_for_config_entry",
            return_value=[first, second],
        ),
    ):
        result = await flow.async_step_init(user_input={})

    assert result["data"]["removed_entities"] == ["sensor.second"]
    entity_registry.async_remove.assert_called_once_with("sensor.second")
