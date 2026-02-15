"""Tests for Philips AirPurifier coordinator."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.coordinator import (
    PhilipsAirPurifierCoordinator,
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


async def test_coordinator_device_info(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test coordinator stores correct device info."""
    coordinator = init_integration.runtime_data

    device_info = coordinator.device_info

    # device_info is a DeviceInformation dataclass, not a HA DeviceInfo dict
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
    """Test setting a single control value."""
    coordinator = init_integration.runtime_data

    await coordinator.async_set_control_value("pwr", "0")

    mock_coap_client.set_control_values.assert_called_once_with(data={"pwr": "0"})


async def test_coordinator_set_control_values(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting multiple control values."""
    coordinator = init_integration.runtime_data

    values = {"pwr": "1", "mode": "M", "om": "s"}
    await coordinator.async_set_control_values(values)

    mock_coap_client.set_control_values.assert_called_once_with(data=values)


async def test_coordinator_set_control_values_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting control values propagates errors."""
    coordinator = init_integration.runtime_data

    mock_coap_client.set_control_values.side_effect = Exception("connection lost")

    # The method doesn't wrap errors in UpdateFailed, it just propagates the exception
    with pytest.raises(Exception, match="connection lost"):
        await coordinator.async_set_control_values({"pwr": "1"})


async def test_coordinator_async_update_data(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test coordinator update data calls get_status."""
    coordinator = init_integration.runtime_data

    # Reset the mock to clear initialization calls
    mock_coap_client.get_status.reset_mock()

    # Mock updated status
    updated_status = MOCK_STATUS_GEN1.copy()
    updated_status["pm25"] = 25
    mock_coap_client.get_status.return_value = (updated_status, 60)

    # Call internal update method
    result = await coordinator._async_update_data()

    assert result == updated_status
    assert result["pm25"] == 25
    mock_coap_client.get_status.assert_called_once()


async def test_coordinator_async_update_data_error(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test coordinator update data raises UpdateFailed on error."""
    coordinator = init_integration.runtime_data

    mock_coap_client.get_status.side_effect = Exception("connection error")

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_shutdown(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test coordinator shutdown cancels tasks and shuts down client."""
    coordinator = init_integration.runtime_data

    await coordinator.async_shutdown()

    # Verify client shutdown was called
    mock_coap_client.shutdown.assert_called()

    # Verify tasks are None after shutdown
    assert coordinator._observe_task is None
    assert coordinator._watchdog_task is None
    assert coordinator._reconnect_task is None


async def test_coordinator_model_config(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
) -> None:
    """Test coordinator provides model config."""
    coordinator = init_integration.runtime_data

    model_config = coordinator.model_config

    assert model_config is not None
    # DeviceModelConfig has api_generation, not model
    assert model_config.api_generation == "gen1"


async def test_coordinator_client_property(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test coordinator client property returns the CoAP client."""
    coordinator = init_integration.runtime_data

    assert coordinator.client == mock_coap_client


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
    return PhilipsAirPurifierCoordinator(hass, client or AsyncMock(), TEST_HOST, device_info)


async def test_coordinator_model_config_family_fallback(hass: HomeAssistant) -> None:
    """Test model family fallback for known model prefixes."""
    coordinator = _make_coordinator(hass, model="AMF765-variant")

    assert coordinator.model_config.api_generation == "gen3"


async def test_coordinator_model_config_default_fallback(hass: HomeAssistant) -> None:
    """Test unknown model falls back to default gen1 config."""
    coordinator = _make_coordinator(hass, model="UNKNOWN_MODEL")

    assert coordinator.model_config.api_generation == "gen1"


async def test_start_observing_cancels_existing_tasks(hass: HomeAssistant) -> None:
    """Test _start_observing cancels old tasks before creating new ones."""
    coordinator = _make_coordinator(hass)
    old_observe = MagicMock()
    old_watchdog = MagicMock()
    coordinator._observe_task = old_observe
    coordinator._watchdog_task = old_watchdog

    def _fake_create_task(coro, *_args, **_kwargs):
        coro.close()
        return MagicMock()

    with patch.object(hass, "async_create_task", side_effect=_fake_create_task) as create_task:
        coordinator._start_observing()

    old_observe.cancel.assert_called_once()
    old_watchdog.cancel.assert_called_once()
    assert create_task.call_count == 2


async def test_start_observing_without_existing_tasks(hass: HomeAssistant) -> None:
    """Test _start_observing path when no previous tasks exist."""
    coordinator = _make_coordinator(hass)

    def _fake_create_task(coro, *_args, **_kwargs):
        coro.close()
        return MagicMock()

    with patch.object(hass, "async_create_task", side_effect=_fake_create_task) as create_task:
        coordinator._start_observing()

    assert create_task.call_count == 2


async def test_async_observe_status_cancelled_raises(hass: HomeAssistant) -> None:
    """Test observe loop propagates cancellation."""
    client = MagicMock()

    async def cancelled_stream():
        raise asyncio.CancelledError
        yield {}

    client.observe_status = MagicMock(return_value=cancelled_stream())
    coordinator = _make_coordinator(hass, client=client)

    with pytest.raises(asyncio.CancelledError):
        await coordinator._async_observe_status()


async def test_async_observe_status_error_triggers_reconnect(hass: HomeAssistant) -> None:
    """Test observe loop errors schedule reconnect task."""
    client = MagicMock()

    async def failing_stream():
        msg = "stream failed"
        raise RuntimeError(msg)
        yield {}

    client.observe_status = MagicMock(return_value=failing_stream())
    coordinator = _make_coordinator(hass, client=client)

    def _fake_create_task(coro, *_args, **_kwargs):
        coro.close()
        return MagicMock()

    with (
        patch.object(coordinator, "_async_reconnect", new=AsyncMock()) as reconnect_mock,
        patch.object(hass, "async_create_task", side_effect=_fake_create_task) as create_task,
    ):
        await coordinator._async_observe_status()

    reconnect_mock.assert_called_once()
    create_task.assert_called_once()


async def test_async_watchdog_triggers_reconnect_when_elapsed(hass: HomeAssistant) -> None:
    """Test watchdog reconnects when updates are overdue."""
    coordinator = _make_coordinator(hass)
    coordinator._timeout = 1
    coordinator._last_update = 1

    fake_loop = MagicMock()
    fake_loop.time.return_value = 10

    with (
        patch(
            "custom_components.philips_airpurifier.coordinator.asyncio.sleep",
            side_effect=[None, asyncio.CancelledError],
        ),
        patch("custom_components.philips_airpurifier.coordinator.asyncio.get_event_loop", return_value=fake_loop),
        patch.object(coordinator, "_async_reconnect", new=AsyncMock()) as reconnect_mock,
    ):
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_watchdog()

    reconnect_mock.assert_awaited_once()


async def test_async_watchdog_no_reconnect_when_recent(hass: HomeAssistant) -> None:
    """Test watchdog does not reconnect when updates are recent."""
    coordinator = _make_coordinator(hass)
    coordinator._timeout = 10
    coordinator._last_update = 100

    fake_loop = MagicMock()
    fake_loop.time.return_value = 101

    with (
        patch(
            "custom_components.philips_airpurifier.coordinator.asyncio.sleep",
            side_effect=[None, asyncio.CancelledError],
        ),
        patch("custom_components.philips_airpurifier.coordinator.asyncio.get_event_loop", return_value=fake_loop),
        patch.object(coordinator, "_async_reconnect", new=AsyncMock()) as reconnect_mock,
    ):
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_watchdog()

    reconnect_mock.assert_not_awaited()


async def test_async_reconnect_inflight_guard(hass: HomeAssistant) -> None:
    """Test _async_reconnect returns when reconnect task already running."""
    coordinator = _make_coordinator(hass)
    in_flight = MagicMock()
    in_flight.done.return_value = False
    coordinator._reconnect_task = in_flight

    with patch.object(hass, "async_create_task", return_value=MagicMock()) as create_task:
        await coordinator._async_reconnect()

    create_task.assert_not_called()


async def test_do_reconnect_handles_status_fetch_failure(hass: HomeAssistant) -> None:
    """Test reconnect continues even when status fetch after reconnect fails."""
    old_client = AsyncMock()
    old_client.shutdown = AsyncMock()
    coordinator = _make_coordinator(hass, client=old_client)

    new_client = AsyncMock()
    new_client.get_status.side_effect = RuntimeError("status failed")

    with (
        patch(
            "custom_components.philips_airpurifier.coordinator.CoAPClient.create",
            new=AsyncMock(return_value=new_client),
        ),
        patch.object(coordinator, "_start_observing") as start_observing,
    ):
        await coordinator._do_reconnect()

    start_observing.assert_called_once()


async def test_do_reconnect_generic_failure_suppressed(hass: HomeAssistant) -> None:
    """Test reconnect logs and suppresses non-cancelled failures."""
    coordinator = _make_coordinator(hass, client=AsyncMock())

    with patch(
        "custom_components.philips_airpurifier.coordinator.CoAPClient.create",
        new=AsyncMock(side_effect=RuntimeError("connect failed")),
    ):
        await coordinator._do_reconnect()


async def test_do_reconnect_cancelled_propagates(hass: HomeAssistant) -> None:
    """Test reconnect cancellation is propagated."""
    coordinator = _make_coordinator(hass, client=AsyncMock())

    with (
        patch(
            "custom_components.philips_airpurifier.coordinator.CoAPClient.create",
            new=AsyncMock(side_effect=asyncio.CancelledError),
        ),
        pytest.raises(asyncio.CancelledError),
    ):
        await coordinator._do_reconnect()


async def test_first_refresh_and_observe_raises_not_ready(hass: HomeAssistant) -> None:
    """Test initial refresh failure raises ConfigEntryNotReady."""
    client = AsyncMock()
    client.get_status.side_effect = RuntimeError("offline")
    coordinator = _make_coordinator(hass, client=client)

    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_first_refresh_and_observe()


async def test_shutdown_suppresses_client_shutdown_exception(hass: HomeAssistant) -> None:
    """Test async_shutdown suppresses client shutdown exceptions."""
    client = AsyncMock()
    client.shutdown.side_effect = RuntimeError("ignore")
    coordinator = _make_coordinator(hass, client=client)

    await coordinator.async_shutdown()


async def test_async_observe_status_success_updates_data(hass: HomeAssistant) -> None:
    """Test observe stream updates coordinator data and timestamp."""

    async def stream():
        yield {"pwr": "1"}

    client = MagicMock()
    client.observe_status = MagicMock(return_value=stream())
    coordinator = _make_coordinator(hass, client=client)

    fake_loop = MagicMock()
    fake_loop.time.return_value = 123.0

    with patch("custom_components.philips_airpurifier.coordinator.asyncio.get_event_loop", return_value=fake_loop):
        await coordinator._async_observe_status()

    assert coordinator._last_update == 123.0
    assert coordinator.data == {"pwr": "1"}


async def test_async_reconnect_creates_task_when_idle(hass: HomeAssistant) -> None:
    """Test reconnect schedules reconnect task when none is running."""
    coordinator = _make_coordinator(hass)

    def _fake_create_task(coro, *_args, **_kwargs):
        coro.close()
        return MagicMock()

    with patch.object(hass, "async_create_task", side_effect=_fake_create_task) as create_task:
        await coordinator._async_reconnect()

    create_task.assert_called_once()


async def test_async_shutdown_with_none_client(hass: HomeAssistant) -> None:
    """Test shutdown handles missing client gracefully."""
    coordinator = _make_coordinator(hass)
    coordinator.client = None
    coordinator._observe_task = None
    coordinator._watchdog_task = None
    coordinator._reconnect_task = None

    await coordinator.async_shutdown()


async def test_async_watchdog_skips_elapsed_check_when_no_last_update(hass: HomeAssistant) -> None:
    """Test watchdog branch where _last_update is zero."""
    coordinator = _make_coordinator(hass)
    coordinator._timeout = 1
    coordinator._last_update = 0

    with (
        patch(
            "custom_components.philips_airpurifier.coordinator.asyncio.sleep",
            side_effect=[None, asyncio.CancelledError],
        ),
        patch.object(coordinator, "_async_reconnect", new=AsyncMock()) as reconnect_mock,
    ):
        with pytest.raises(asyncio.CancelledError):
            await coordinator._async_watchdog()

    reconnect_mock.assert_not_awaited()


async def test_async_reconnect_done_task_creates_new_task(hass: HomeAssistant) -> None:
    """Test reconnect schedules when previous reconnect task is done."""
    coordinator = _make_coordinator(hass)
    done_task = MagicMock()
    done_task.done.return_value = True
    coordinator._reconnect_task = done_task

    def _fake_create_task(coro, *_args, **_kwargs):
        coro.close()
        return MagicMock()

    with patch.object(hass, "async_create_task", side_effect=_fake_create_task) as create_task:
        await coordinator._async_reconnect()

    create_task.assert_called_once()


async def test_do_reconnect_success_updates_data_and_timeout(hass: HomeAssistant) -> None:
    """Test reconnect success path updates coordinator state and restarts observe."""
    old_client = AsyncMock()
    old_client.shutdown = AsyncMock()
    coordinator = _make_coordinator(hass, client=old_client)

    new_status = {"pwr": "1", "pm25": 5}
    new_client = AsyncMock()
    new_client.get_status = AsyncMock(return_value=(new_status, 45))

    with (
        patch(
            "custom_components.philips_airpurifier.coordinator.CoAPClient.create",
            new=AsyncMock(return_value=new_client),
        ),
        patch.object(coordinator, "_start_observing") as start_observing,
    ):
        await coordinator._do_reconnect()

    assert coordinator.data == new_status
    assert coordinator._timeout == 45
    start_observing.assert_called_once()


async def test_async_shutdown_cancels_all_existing_tasks(hass: HomeAssistant) -> None:
    """Test shutdown cancels observe/watchdog/reconnect tasks when present."""
    coordinator = _make_coordinator(hass)
    observe_task = MagicMock()
    watchdog_task = MagicMock()
    reconnect_task = MagicMock()
    coordinator._observe_task = observe_task
    coordinator._watchdog_task = watchdog_task
    coordinator._reconnect_task = reconnect_task
    coordinator.client = AsyncMock()

    await coordinator.async_shutdown()

    observe_task.cancel.assert_called_once()
    watchdog_task.cancel.assert_called_once()
    reconnect_task.cancel.assert_called_once()
