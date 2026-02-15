"""Tests for Philips AirPurifier diagnostics."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.diagnostics import (
    async_get_config_entry_diagnostics,
)
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant

from .const import TEST_DEVICE_ID, TEST_HOST, TEST_MODEL, TEST_NAME


async def test_diagnostics_data_structure(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that diagnostics output has expected top-level keys."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    # Verify all expected top-level keys are present
    assert "system_info" in result
    assert "device_info" in result
    assert "configuration" in result
    assert "coordinator" in result
    assert "entities" in result
    assert "device_registry" in result
    assert "device_status" in result

    # Verify system_info structure
    assert "home_assistant_version" in result["system_info"]
    assert "python_version" in result["system_info"]
    assert "domain" in result["system_info"]
    assert "entry_id" in result["system_info"]
    assert "entry_title" in result["system_info"]
    assert "entry_version" in result["system_info"]
    assert "timestamp" in result["system_info"]

    # Verify device_info structure
    assert "model" in result["device_info"]
    assert "name" in result["device_info"]
    assert "host" in result["device_info"]
    assert "device_id" in result["device_info"]

    # Verify configuration structure
    assert "host" in result["configuration"]
    assert "model" in result["configuration"]
    assert "name" in result["configuration"]
    assert "has_device_id" in result["configuration"]
    assert "has_status" in result["configuration"]
    assert "source" in result["configuration"]
    assert "state" in result["configuration"]

    # Verify coordinator structure
    assert "client_available" in result["coordinator"]
    assert "has_data" in result["coordinator"]
    assert "status_keys" in result["coordinator"]

    # Verify entities structure
    assert "total" in result["entities"]
    assert "details" in result["entities"]


async def test_diagnostics_redaction(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that sensitive fields are properly redacted."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    # Verify host is redacted
    assert result["device_info"]["host"] == REDACTED
    assert result["configuration"]["host"] == REDACTED

    # Verify device_id is redacted
    assert result["device_info"]["device_id"] == REDACTED

    # Verify entry_id is redacted
    assert result["system_info"]["entry_id"] == REDACTED

    # Verify device_id in status is redacted (if present)
    if "DeviceId" in result["device_status"]:
        assert result["device_status"]["DeviceId"] == REDACTED

    # Verify entity unique_ids and IDs are redacted (if present)
    for entity in result["entities"]["details"]:
        # entity_id contains the unique_id or entry_id, so should not contain actual values
        assert TEST_DEVICE_ID not in entity.get("entity_id", "")
        assert TEST_HOST not in entity.get("entity_id", "")


async def test_diagnostics_device_info(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that model and name are present and not redacted."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    # Model and name should be present and not redacted
    assert result["device_info"]["model"] == TEST_MODEL
    assert result["device_info"]["name"] == TEST_NAME
    assert result["configuration"]["model"] == TEST_MODEL
    assert result["configuration"]["name"] == TEST_NAME


async def test_diagnostics_coordinator_info(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that coordinator information is correctly populated."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    # Client should be available after init
    assert result["coordinator"]["client_available"] is True

    # Should have data after successful setup
    assert result["coordinator"]["has_data"] is True

    # Should have status keys
    assert isinstance(result["coordinator"]["status_keys"], list)
    assert len(result["coordinator"]["status_keys"]) > 0

    # Common status keys for Gen1 devices
    expected_keys = ["pwr", "mode", "om", "pm25", "iaql"]
    for key in expected_keys:
        assert key in result["coordinator"]["status_keys"]


async def test_diagnostics_entities_listed(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that entities are listed in diagnostics."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    # Should have entities registered
    assert result["entities"]["total"] >= 0
    assert isinstance(result["entities"]["details"], list)
    assert len(result["entities"]["details"]) == result["entities"]["total"]

    # Verify entity structure if any entities exist
    if result["entities"]["total"] > 0:
        entity = result["entities"]["details"][0]
        assert "entity_id" in entity
        assert "platform" in entity
        assert "device_class" in entity
        assert "entity_category" in entity
        assert "disabled" in entity
        assert "translation_key" in entity


async def test_diagnostics_device_registry_populated(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that device registry information is populated."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    # Device registry should have data
    device_registry = result["device_registry"]
    assert isinstance(device_registry, dict)

    # If device is registered, check fields
    if device_registry:
        assert "manufacturer" in device_registry
        assert "model" in device_registry
        assert "name" in device_registry
        # sw_version might be None, but key should exist
        assert "sw_version" in device_registry


async def test_diagnostics_status_data(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that device status data is included."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    # Should have status data
    assert isinstance(result["device_status"], dict)
    assert len(result["device_status"]) > 0

    # Should have some expected fields (with sensitive ones redacted)
    assert "pwr" in result["device_status"]
    assert "mode" in result["device_status"]

    # Verify name in status is NOT redacted (name is not in TO_REDACT)
    if "name" in result["device_status"]:
        assert result["device_status"]["name"] == TEST_NAME


async def test_diagnostics_configuration_flags(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test that configuration boolean flags are correct."""
    result = await async_get_config_entry_diagnostics(hass, init_integration)

    # Should have device_id and status in config entry data
    assert result["configuration"]["has_device_id"] is True
    assert result["configuration"]["has_status"] is True

    # Should have source and state
    assert result["configuration"]["source"] is not None
    assert result["configuration"]["state"] is not None


async def test_diagnostics_empty_status_and_no_device_entry_branch(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test diagnostics branch paths when device lookup fails and status is empty."""
    coordinator = init_integration.runtime_data
    coordinator.data = {}

    with patch(
        "custom_components.philips_airpurifier.diagnostics.dr.async_get",
        return_value=SimpleNamespace(devices={}),
    ):
        result = await async_get_config_entry_diagnostics(hass, init_integration)

    assert result["coordinator"]["has_data"] is False
    assert result["coordinator"]["status_keys"] == []
    assert result["device_registry"] == {}
