"""Tests for Philips AirPurifier coordinator."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.coordinator import (
    DEFAULT_POLL_INTERVAL,
    MAX_POLL_INTERVAL,
    MIN_POLL_INTERVAL,
    PhilipsAirPurifierCoordinator,
    _poll_interval_from_timeout,
)
from custom_components.philips_airpurifier.model import DeviceInformation
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import MOCK_STATUS_GEN1, TEST_DEVICE_ID, TEST_HOST, TEST_MODEL, TEST_NAME


async def test_coordinator_data_available(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test coordinator has data after initialization."""
    coordinator = init_integration.runtime_data

    assert coordinator.data is not None
    assert coordinator.data["pwr"] == "1"
    assert coordinator.data["mode"] == "AG"
    assert coordinator.data["DeviceId"] == TEST_DEVICE_ID


async def test_coordinator_properties(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test coordinator properties return correct values."""
    coordinator = init_integration.runtime_data

    assert coordinator.device_id == TEST_DEVICE_ID
    assert coordinator.device_name == TEST_NAME
    assert coordinator.model == TEST_MODEL
    assert coordinator.host == TEST_HOST
    assert coordinator.update_interval == timedelta(seconds=60)


async def test_coordinator_device_info(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test coordinator stores correct device info."""
    coordinator = init_integration.runtime_data

    device_info = coordinator.device_info

    assert isinstance(device_info, DeviceInformation)
    assert device_info.model == TEST_MODEL
    assert device_info.name == TEST_NAME
    assert device_info.device_id == TEST_DEVICE_ID
    assert device_info.host == TEST_HOST


async def test_coordinator_set_control_value(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting a single control value uses a bounded temporary client."""
    coordinator = init_integration.runtime_data
    mock_coap_client.set_control_values.reset_mock()

    await coordinator.async_set_control_value("pwr", "0")

    mock_coap_client.set_control_values.assert_called_with(data={"pwr": "0"})
    mock_coap_client.shutdown.assert_called()
    assert coordinator.data["pwr"] == "0"


async def test_coordinator_set_control_values(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting multiple control values."""
    coordinator = init_integration.runtime_data
    mock_coap_client.set_control_values.reset_mock()

    values = {"pwr": "1", "mode": "M", "om": "s"}
    await coordinator.async_set_control_values(values)

    mock_coap_client.set_control_values.assert_called_with(data=values)
    assert coordinator.data["mode"] == "M"


async def test_coordinator_set_control_values_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting control values propagates errors and marks unavailable."""
    coordinator = init_integration.runtime_data

    mock_coap_client.set_control_values.side_effect = RuntimeError("connection lost")

    with pytest.raises(RuntimeError, match="connection lost"):
        await coordinator.async_set_control_values({"pwr": "1"})

    assert coordinator.last_update_success is False


async def test_coordinator_async_update_data(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test coordinator polling calls get_status and updates interval."""
    coordinator = init_integration.runtime_data

    mock_coap_client.get_status.reset_mock()
    updated_status = MOCK_STATUS_GEN1.copy()
    updated_status["pm25"] = 25
    mock_coap_client.get_status.return_value = (updated_status, 45)

    result = await coordinator._async_update_data()

    assert result == updated_status
    assert result["pm25"] == 25
    assert coordinator.update_interval == timedelta(seconds=45)
    mock_coap_client.get_status.assert_called_once()
    mock_coap_client.shutdown.assert_called()


async def test_coordinator_async_update_data_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test coordinator update data raises UpdateFailed on error."""
    coordinator = init_integration.runtime_data

    mock_coap_client.get_status.side_effect = RuntimeError("connection error")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    assert coordinator.last_update_success is False


async def test_coordinator_shutdown(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test coordinator shutdown marks the coordinator as shutting down."""
    coordinator = init_integration.runtime_data

    await coordinator.async_shutdown()

    assert coordinator._shutting_down is True


async def test_coordinator_model_config(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test coordinator provides model config."""
    coordinator = init_integration.runtime_data

    model_config = coordinator.model_config

    assert model_config is not None
    assert model_config.api_generation == "gen1"


async def test_coordinator_legacy_client_property(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test coordinator keeps the legacy client attribute for diagnostics compatibility."""
    coordinator = init_integration.runtime_data

    assert coordinator.client is None or coordinator.client == mock_coap_client


async def test_coordinator_mark_available_logs_back_online_once(hass: HomeAssistant) -> None:
    """Test back-online transition logging path."""
    coordinator = _make_coordinator(hass)
    coordinator._device_available = False

    with patch("custom_components.philips_airpurifier.coordinator._LOGGER.info") as info_log:
        coordinator._mark_available()

    assert coordinator._device_available is True
    info_log.assert_called_once()


def _make_coordinator(
    hass: HomeAssistant,
    *,
    model: str = TEST_MODEL,
    client: AsyncMock | None = None,
) -> PhilipsAirPurifierCoordinator:
    """Create a coordinator instance for unit-path testing."""
    device_info = DeviceInformation(
        model=model,
        name=TEST_NAME,
        device_id=TEST_DEVICE_ID,
        host=TEST_HOST,
    )
    if client is not None:
        return PhilipsAirPurifierCoordinator(hass, client, TEST_HOST, device_info)
    return PhilipsAirPurifierCoordinator(hass, TEST_HOST, device_info, create_client=AsyncMock())


async def test_coordinator_model_config_family_fallback(hass: HomeAssistant) -> None:
    """Test model family fallback for known model prefixes."""
    coordinator = _make_coordinator(hass, model="AMF765-variant")

    assert coordinator.model_config.api_generation == "gen3"


async def test_coordinator_model_config_default_fallback(hass: HomeAssistant) -> None:
    """Test unknown model falls back to default gen1 config."""
    coordinator = _make_coordinator(hass, model="UNKNOWN_MODEL")

    assert coordinator.model_config.api_generation == "gen1"


async def test_start_observing_is_noop_in_polling_mode(hass: HomeAssistant) -> None:
    """Test the legacy observe hook remains a no-op."""
    coordinator = _make_coordinator(hass)

    coordinator._start_observing()

    assert coordinator.update_interval == timedelta(seconds=DEFAULT_POLL_INTERVAL)


async def test_first_refresh_and_observe_raises_not_ready(hass: HomeAssistant) -> None:
    """Test initial refresh failure raises ConfigEntryNotReady."""
    create_client = AsyncMock(side_effect=RuntimeError("offline"))
    coordinator = _make_coordinator(hass)
    coordinator._create_client = create_client

    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_first_refresh_and_observe()


async def test_first_refresh_uses_cached_status_when_device_offline(hass: HomeAssistant) -> None:
    """Test setup can continue from cached status while polling recovers."""
    device_info = DeviceInformation(
        model=TEST_MODEL,
        name=TEST_NAME,
        device_id=TEST_DEVICE_ID,
        host=TEST_HOST,
    )
    coordinator = PhilipsAirPurifierCoordinator(
        hass,
        TEST_HOST,
        device_info,
        initial_status=MOCK_STATUS_GEN1.copy(),
        create_client=AsyncMock(side_effect=RuntimeError("offline")),
    )

    with patch.object(hass, "async_create_background_task", return_value=MagicMock()) as create_task:
        await coordinator.async_first_refresh_and_observe()

    assert coordinator.data == MOCK_STATUS_GEN1
    assert coordinator.last_update_success is False
    create_task.assert_called_once()


async def test_first_refresh_and_observe_success(hass: HomeAssistant) -> None:
    """Test initial refresh stores data in polling mode."""
    client = AsyncMock()
    client.get_status = AsyncMock(return_value=({"pwr": "1"}, 30))
    client.shutdown = AsyncMock()
    coordinator = _make_coordinator(hass, client=client)

    await coordinator.async_first_refresh_and_observe()

    assert coordinator.data == {"pwr": "1"}
    assert coordinator.update_interval == timedelta(seconds=30)


def test_poll_interval_from_timeout_bounds_values() -> None:
    """Test CoAP max-age values are clamped to safe polling bounds."""
    assert _poll_interval_from_timeout(1) == timedelta(seconds=MIN_POLL_INTERVAL)
    assert _poll_interval_from_timeout(45) == timedelta(seconds=45)
    assert _poll_interval_from_timeout(999) == timedelta(seconds=MAX_POLL_INTERVAL)
    assert _poll_interval_from_timeout("bad") == timedelta(seconds=DEFAULT_POLL_INTERVAL)


async def test_control_false_result_raises(hass: HomeAssistant) -> None:
    """Test a rejected control update is treated as a failure."""
    client = AsyncMock()
    client.set_control_values = AsyncMock(return_value=False)
    client.shutdown = AsyncMock()
    coordinator = _make_coordinator(hass, client=client)

    with pytest.raises(RuntimeError, match="rejected"):
        await coordinator.async_set_control_values({"pwr": "1"})


async def test_control_refresh_is_scheduled(hass: HomeAssistant) -> None:
    """Test successful controls request a follow-up status refresh."""
    client = AsyncMock()
    client.set_control_values = AsyncMock(return_value=True)
    client.shutdown = AsyncMock()
    coordinator = _make_coordinator(hass, client=client)
    coordinator.async_set_updated_data({"pwr": "0"})

    with patch.object(hass, "async_create_background_task", return_value=MagicMock()) as create_task:
        await coordinator.async_set_control_values({"pwr": "1"})

    create_task.assert_called_once()
