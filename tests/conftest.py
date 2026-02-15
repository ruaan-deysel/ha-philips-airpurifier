"""Shared fixtures for Philips AirPurifier tests."""

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
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant

from .const import MOCK_STATUS_GEN1, TEST_DEVICE_ID, TEST_HOST, TEST_MODEL, TEST_NAME

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"{TEST_MODEL} {TEST_NAME}",
        data={
            CONF_HOST: TEST_HOST,
            CONF_MODEL: TEST_MODEL,
            CONF_NAME: TEST_NAME,
            CONF_DEVICE_ID: TEST_DEVICE_ID,
            CONF_STATUS: MOCK_STATUS_GEN1,
        },
        unique_id=TEST_DEVICE_ID,
    )


@pytest.fixture
def mock_coap_client() -> Generator[AsyncMock]:
    """Return a mocked CoAP client."""
    with (
        patch(
            "custom_components.philips_airpurifier.CoAPClient",
        ) as mock_client_cls,
        patch(
            "custom_components.philips_airpurifier.coordinator.PhilipsAirPurifierCoordinator._start_observing",
        ),
    ):
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(MOCK_STATUS_GEN1.copy(), 60))
        client.set_control_values = AsyncMock()
        client.set_control_value = AsyncMock()
        client.shutdown = AsyncMock()

        mock_client_cls.create = AsyncMock(return_value=client)
        mock_client_cls.return_value = client

        yield client


@pytest.fixture
def mock_coap_client_config_flow() -> Generator[AsyncMock]:
    """Return a mocked CoAP client for config flow tests."""
    with patch(
        "custom_components.philips_airpurifier.config_flow.CoAPClient",
    ) as mock_client_cls:
        client = AsyncMock()
        client.get_status = AsyncMock(return_value=(MOCK_STATUS_GEN1.copy(), 60))
        client.shutdown = AsyncMock()

        mock_client_cls.create = AsyncMock(return_value=client)

        yield client


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable custom integrations for all tests."""


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> MockConfigEntry:
    """Set up the integration for testing."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    return mock_config_entry
