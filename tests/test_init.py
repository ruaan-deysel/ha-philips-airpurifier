"""Tests for Philips AirPurifier integration setup."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier import async_unload_entry
from custom_components.philips_airpurifier.const import (
    CONF_DEVICE_ID,
    CONF_MODEL,
    DOMAIN,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant


async def test_setup_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test successful setup of config entry."""
    assert init_integration.state is ConfigEntryState.LOADED


async def test_setup_entry_connection_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test setup fails when connection cannot be established."""
    with patch(
        "custom_components.philips_airpurifier.CoAPClient",
    ) as mock_client_cls:
        mock_client_cls.create = AsyncMock(side_effect=TimeoutError)
        mock_config_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test unloading a config entry."""
    assert init_integration.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state is ConfigEntryState.NOT_LOADED
    mock_coap_client.shutdown.assert_called()


async def test_setup_entry_without_status_updates_entry(
    hass: HomeAssistant,
) -> None:
    """Test setup stores initial status into config entry when missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="AC3858/51 Living Room",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_MODEL: "AC3858/51",
            CONF_NAME: "Living Room",
            CONF_DEVICE_ID: "aabbccddeeff",
        },
        unique_id="aabbccddeeff",
    )
    entry.add_to_hass(hass)

    with (
        patch("custom_components.philips_airpurifier.CoAPClient") as mock_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
        patch.object(hass.config_entries, "async_update_entry") as update_entry,
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=({"pwr": "1"}, 60))
        client.shutdown = AsyncMock()
        mock_client_cls.create = AsyncMock(return_value=client)

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    update_entry.assert_called_once()


async def test_async_unload_entry_false_skips_shutdown(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test async_unload_entry does not shutdown when unload_platforms fails."""
    coordinator = init_integration.runtime_data
    coordinator.async_shutdown = AsyncMock()

    with patch.object(hass.config_entries, "async_unload_platforms", new=AsyncMock(return_value=False)):
        result = await async_unload_entry(hass, init_integration)

    assert result is False
    coordinator.async_shutdown.assert_not_called()
