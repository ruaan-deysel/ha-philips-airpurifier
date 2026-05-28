"""Shared fixtures for Philips AirPurifier tests."""

from __future__ import annotations

import json
from types import SimpleNamespace
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
    from typing import Any

    from collections.abc import Generator


class _MockStatusRequester:
    """Small aiocoap requester stand-in with an awaitable response."""

    def __init__(self, client: AsyncMock) -> None:
        async def _response() -> SimpleNamespace:
            if client.status_error is not None:
                raise client.status_error
            payload = json.dumps({"state": {"reported": client.status_data}}).encode()
            return SimpleNamespace(
                payload=payload,
                opt=SimpleNamespace(max_age=client.status_max_age),
            )

        self.response = _response()


class _MockClientContext:
    """Record CoAP requests issued by the integration."""

    def __init__(self, client: AsyncMock) -> None:
        self._client = client

    def request(self, request: Any) -> _MockStatusRequester:
        """Return a mocked requester for a status poll."""
        self._client.status_requests.append(request)
        return _MockStatusRequester(self._client)


class _MockEncryptionContext:
    """Return plaintext test payloads unchanged."""

    def decrypt(self, payload: str) -> str:
        """Decrypt a payload."""
        return payload


def _configure_status_poll_client(client: AsyncMock, status: dict[str, Any]) -> None:
    """Configure a mock CoAP client for non-observe status polling."""
    client.host = TEST_HOST
    client.port = 5683
    client.STATUS_PATH = "/sys/dev/status"
    client.status_data = status.copy()
    client.status_max_age = 60
    client.status_error = None
    client.status_requests = []
    client._client_context = _MockClientContext(client)
    client._encryption_context = _MockEncryptionContext()


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
        _configure_status_poll_client(client, MOCK_STATUS_GEN1)

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
