"""Tests for Philips AirPurifier coordinator."""

from __future__ import annotations

import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.philips_airpurifier.coordinator import (
    MAX_RECONNECT_BACKOFF_SECONDS,
    SNAPSHOT_FAILURES_BEFORE_RECONNECT,
    PhilipsAirPurifierCoordinator,
)
from custom_components.philips_airpurifier.model import DeviceInformation
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import MOCK_STATUS_GEN1, TEST_DEVICE_ID, TEST_HOST, TEST_MODEL, TEST_NAME

pytestmark = pytest.mark.unit


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


async def test_coordinator_set_control_values_updates_data(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting multiple control values updates local coordinator data."""
    coordinator = init_integration.runtime_data

    values = {"pwr": "1", "mode": "M", "om": "s"}
    await coordinator.async_set_control_values(values)

    mock_coap_client.set_control_values.assert_called_once_with(data=values)
    assert coordinator.data["mode"] == "M"
    assert coordinator.data["om"] == "s"


async def test_coordinator_set_control_values_error_schedules_reconnect(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test setting control values propagates errors and schedules reconnect."""
    coordinator = init_integration.runtime_data
    mock_coap_client.set_control_values.side_effect = RuntimeError("connection lost")

    with patch.object(coordinator, "_schedule_reconnect") as schedule_reconnect:
        with pytest.raises(RuntimeError, match="connection lost"):
            await coordinator.async_set_control_values({"pwr": "1"})

    schedule_reconnect.assert_called_once_with("control_failed")
    assert coordinator.last_update_success is False


async def test_coordinator_async_update_data_returns_observed_data(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_coap_client: AsyncMock,
) -> None:
    """Test coordinator refresh does not create a second status observation."""
    coordinator = init_integration.runtime_data
    mock_coap_client.get_status.reset_mock()

    result = await coordinator._async_update_data()

    assert result == coordinator.data
    mock_coap_client.get_status.assert_not_called()


async def test_coordinator_async_update_data_without_observed_data_raises(
    hass: HomeAssistant,
) -> None:
    """Test coordinator update raises when no observation has arrived."""
    coordinator = _make_coordinator(hass)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_first_refresh_and_observe_uses_one_public_observe_stream(hass: HomeAssistant) -> None:
    """Test first refresh fetches a snapshot and starts observation."""
    client = AsyncMock()
    client.get_status = AsyncMock(return_value=(MOCK_STATUS_GEN1.copy(), 60))
    client.observe_status = MagicMock(return_value=_status_stream(MOCK_STATUS_GEN1.copy(), block=True))
    coordinator = _make_coordinator(hass, client=client)

    await coordinator.async_first_refresh_and_observe()

    client.get_status.assert_awaited_once_with(observe=False)
    client.observe_status.assert_called_once_with()
    assert coordinator.data["pwr"] == "1"
    assert coordinator._observe_task is not None
    assert coordinator._snapshot_task is not None

    await coordinator.async_shutdown()


async def test_first_refresh_and_observe_raises_not_ready(hass: HomeAssistant) -> None:
    """Test initial snapshot failure raises ConfigEntryNotReady."""
    client = AsyncMock()
    client.get_status = AsyncMock(side_effect=RuntimeError("offline"))
    client.observe_status = MagicMock(return_value=_failing_stream(RuntimeError("offline")))
    coordinator = _make_coordinator(hass, client=client)

    with pytest.raises(ConfigEntryNotReady):
        await coordinator.async_first_refresh_and_observe()

    assert coordinator.last_update_success is False


async def test_observe_status_success_updates_data(hass: HomeAssistant) -> None:
    """Test observe stream updates coordinator data and timestamp."""
    client = AsyncMock()
    client.observe_status = MagicMock(return_value=_status_stream({"pwr": "1"}, block=True))
    coordinator = _make_coordinator(hass, client=client)

    task = hass.async_create_task(coordinator._async_observe_status())
    while coordinator.data is None:
        await asyncio.sleep(0)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert coordinator.data == {"pwr": "1"}
    assert coordinator._last_update > 0


async def test_observe_status_error_schedules_reconnect(hass: HomeAssistant) -> None:
    """Test observe stream errors schedule a bounded reconnect."""
    client = AsyncMock()
    client.observe_status = MagicMock(return_value=_failing_stream(RuntimeError("stream failed")))
    coordinator = _make_coordinator(hass, client=client)

    with patch.object(coordinator, "_schedule_reconnect") as schedule_reconnect:
        await coordinator._async_observe_status()

    schedule_reconnect.assert_called_once()
    assert coordinator.last_update_success is False


async def test_observe_status_quiet_stream_stays_open(hass: HomeAssistant) -> None:
    """Test a quiet observe stream is not reconnected solely because it is quiet."""
    client = AsyncMock()
    client.observe_status = MagicMock(return_value=_status_stream({"pwr": "1"}, block=True))
    coordinator = _make_coordinator(hass, client=client)

    with patch.object(coordinator, "_schedule_reconnect") as schedule_reconnect:
        task = hass.async_create_task(coordinator._async_observe_status())
        while coordinator.data is None:
            await asyncio.sleep(0)
        await asyncio.sleep(0.02)

    assert not task.done()
    schedule_reconnect.assert_not_called()

    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def test_first_refresh_with_cached_status_does_not_watchdog_quiet_stream(hass: HomeAssistant) -> None:
    """Test cached setup uses one snapshot and keeps a quiet observe stream open."""
    client = AsyncMock()
    client.get_status = AsyncMock(return_value=({**MOCK_STATUS_GEN1, "pm25": 7}, 60))
    client.observe_status = MagicMock(return_value=_blocking_stream_without_payload())
    coordinator = _make_coordinator(hass, client=client)

    with patch.object(coordinator, "_schedule_reconnect") as schedule_reconnect:
        await coordinator.async_first_refresh_and_observe(MOCK_STATUS_GEN1.copy())
        await asyncio.sleep(0.02)

    assert coordinator.data["pwr"] == "1"
    assert coordinator.data["pm25"] == 7
    assert coordinator.last_update_success is True
    assert coordinator._observe_task is not None
    assert not coordinator._observe_task.done()
    assert coordinator._snapshot_task is not None
    schedule_reconnect.assert_not_called()

    await coordinator.async_shutdown()


async def test_do_reconnect_success_starts_new_observe_stream(hass: HomeAssistant) -> None:
    """Test reconnect refreshes a snapshot and keeps a quiet observe stream open."""
    old_client = AsyncMock()
    old_client.shutdown = AsyncMock()
    new_client = AsyncMock()
    new_client.get_status = AsyncMock(return_value=({**MOCK_STATUS_GEN1, "pm25": 7}, 60))
    new_client.observe_status = MagicMock(return_value=_blocking_stream_without_payload())
    coordinator = _make_coordinator(hass, client=old_client)
    coordinator.async_set_updated_data(MOCK_STATUS_GEN1.copy())
    coordinator._mark_unavailable("test")

    with patch(
        "custom_components.philips_airpurifier.coordinator.async_create_client",
        new=AsyncMock(return_value=new_client),
    ):
        await asyncio.wait_for(coordinator._do_reconnect("test", 0), timeout=1)

    old_client.shutdown.assert_awaited_once()
    new_client.get_status.assert_awaited_once_with(observe=False)
    assert coordinator.client == new_client
    assert coordinator.last_update_success is True
    assert coordinator.data["pwr"] == "1"
    assert coordinator.data["pm25"] == 7
    assert coordinator._observe_task is not None
    assert not coordinator._observe_task.done()
    assert coordinator._snapshot_task is not None

    await coordinator.async_shutdown()


async def test_reconnect_guard_skips_when_existing_task_running(hass: HomeAssistant) -> None:
    """Test reconnect is not scheduled twice."""
    coordinator = _make_coordinator(hass)
    existing_task = MagicMock()
    existing_task.done.return_value = False
    coordinator._reconnect_task = existing_task

    with patch.object(hass, "async_create_background_task") as create_task:
        coordinator._schedule_reconnect("test")

    create_task.assert_not_called()


async def test_reconnect_backoff_is_bounded(hass: HomeAssistant) -> None:
    """Test reconnect backoff has an upper bound."""
    coordinator = _make_coordinator(hass)
    coordinator._consecutive_failures = 100

    assert coordinator._next_reconnect_delay() == MAX_RECONNECT_BACKOFF_SECONDS


async def test_snapshot_failure_tolerates_first_missed_refresh(hass: HomeAssistant) -> None:
    """Test one missed periodic snapshot does not flap entity availability."""
    coordinator = _make_coordinator(hass)
    coordinator.async_set_updated_data(MOCK_STATUS_GEN1.copy())
    coordinator._mark_available()

    with patch.object(coordinator, "_schedule_reconnect") as schedule_reconnect:
        needs_reconnect = coordinator._handle_snapshot_failure("periodic_snapshot", TimeoutError())

    assert needs_reconnect is False
    assert coordinator._device_available is True
    assert coordinator.last_update_success is True
    assert coordinator._consecutive_failures == 1
    schedule_reconnect.assert_not_called()


async def test_repeated_snapshot_failures_mark_unavailable(hass: HomeAssistant) -> None:
    """Test repeated missed snapshots still protect HA from stale live state."""
    coordinator = _make_coordinator(hass)
    coordinator.async_set_updated_data(MOCK_STATUS_GEN1.copy())
    coordinator._mark_available()
    coordinator._consecutive_failures = SNAPSHOT_FAILURES_BEFORE_RECONNECT - 1

    with patch.object(coordinator, "_schedule_reconnect") as schedule_reconnect:
        needs_reconnect = coordinator._handle_snapshot_failure("periodic_snapshot", TimeoutError())

    assert needs_reconnect is True
    assert coordinator._device_available is False
    assert coordinator.last_update_success is False
    assert coordinator._consecutive_failures == SNAPSHOT_FAILURES_BEFORE_RECONNECT
    schedule_reconnect.assert_called_once()


async def test_coordinator_shutdown_cancels_tasks(hass: HomeAssistant) -> None:
    """Test coordinator shutdown cancels background tasks and closes the client."""
    client = AsyncMock()
    coordinator = _make_coordinator(hass, client=client)

    async def _block_forever() -> None:
        await asyncio.Event().wait()

    observe_task = hass.async_create_task(_block_forever())
    snapshot_task = hass.async_create_task(_block_forever())
    reconnect_task = hass.async_create_task(_block_forever())
    coordinator._observe_task = observe_task
    coordinator._snapshot_task = snapshot_task
    coordinator._reconnect_task = reconnect_task

    await coordinator.async_shutdown()

    assert observe_task.cancelled()
    assert snapshot_task.cancelled()
    assert reconnect_task.cancelled()
    client.shutdown.assert_awaited_once()
    assert coordinator._observe_task is None
    assert coordinator._snapshot_task is None
    assert coordinator._reconnect_task is None


async def test_coordinator_mark_available_logs_back_online_once(hass: HomeAssistant) -> None:
    """Test back-online transition logging path."""
    coordinator = _make_coordinator(hass)
    coordinator._device_available = False

    with patch("custom_components.philips_airpurifier.coordinator._LOGGER.info") as info_log:
        coordinator._mark_available()

    assert coordinator._device_available is True
    assert coordinator.last_update_success is True
    info_log.assert_called_once()


async def test_coordinator_model_config_family_fallback(hass: HomeAssistant) -> None:
    """Test model family fallback for known model prefixes."""
    coordinator = _make_coordinator(hass, model="AMF765-variant")

    assert coordinator.model_config.api_generation == "gen3"


async def test_coordinator_model_config_default_fallback(hass: HomeAssistant) -> None:
    """Test unknown model falls back to default gen1 config."""
    coordinator = _make_coordinator(hass, model="UNKNOWN_MODEL")

    assert coordinator.model_config.api_generation == "gen1"


async def _status_stream(status: dict[str, object], *, block: bool = False):
    """Yield one status payload, optionally staying open until cancelled."""
    yield status
    if block:
        await asyncio.Event().wait()


async def _failing_stream(err: Exception):
    """Raise an exception from an async generator."""
    raise err
    yield {}


async def _blocking_stream_without_payload():
    """Keep an async generator open without yielding a status payload."""
    await asyncio.Event().wait()
    yield {}


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
