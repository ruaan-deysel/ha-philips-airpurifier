"""Coordinator for Philips AirPurifier integration."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from time import perf_counter
from typing import TYPE_CHECKING, Any

from philips_airctrl import CoAPClient

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import async_create_client
from .const import DOMAIN
from .debug_log import async_debug_event, exception_data, status_data
from .device_models import DEVICE_MODELS
from .model import ApiGeneration, DeviceInformation, DeviceModelConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DEFAULT_OBSERVE_MAX_AGE = 60
CONNECT_TIMEOUT = 25
STATUS_SNAPSHOT_TIMEOUT = 25
SNAPSHOT_FAILURES_BEFORE_RECONNECT = 2
CONTROL_TIMEOUT = 25
SHUTDOWN_TIMEOUT = 5
RECONNECT_BACKOFF_SECONDS = 60
MAX_RECONNECT_BACKOFF_SECONDS = 900


class PhilipsAirPurifierCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data from Philips AirPurifier via snapshots and one observe stream."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CoAPClient | None,
        host: str,
        device_info: DeviceInformation,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.client = client
        self.host = host
        self.device_info = device_info

        self._observe_task: asyncio.Task[None] | None = None
        self._snapshot_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._timeout: int = DEFAULT_OBSERVE_MAX_AGE
        self._last_update: float = 0.0
        self._device_available = True
        self._shutting_down = False
        self._control_lock = asyncio.Lock()
        self._consecutive_failures = 0

    def _debug_event(self, event: str, **fields: Any) -> None:
        """Write a structured debug event for this coordinator."""
        async_debug_event(
            self.hass,
            event,
            host=self.host,
            model=self.model,
            device_id=self.device_id,
            available=self._device_available,
            observe_max_age_seconds=self._timeout,
            consecutive_failures=self._consecutive_failures,
            **fields,
        )

    def _mark_unavailable(self, reason: str) -> None:
        """Mark the device unavailable and log transition once."""
        if self._device_available:
            _LOGGER.warning("Device at %s became unavailable: %s", self.host, reason)
            self._device_available = False
            self.last_update_success = False
            self.async_update_listeners()
            self._debug_event("availability_changed", state="unavailable", reason=reason)

    def _mark_available(self) -> None:
        """Mark the device available and log transition once."""
        if not self._device_available:
            _LOGGER.info("Device at %s is back online", self.host)
            self._device_available = True
            self.last_update_success = True
            self.async_update_listeners()
            self._debug_event("availability_changed", state="available")
            return

        self._device_available = True
        self.last_update_success = True

    @property
    def model(self) -> str:
        """Return the device model."""
        return self.device_info.model

    @property
    def device_id(self) -> str:
        """Return the device ID."""
        return self.device_info.device_id

    @property
    def device_name(self) -> str:
        """Return the device name."""
        return self.device_info.name

    @property
    def mac(self) -> str | None:
        """Return the device MAC address, if known (from DHCP discovery)."""
        return self.device_info.mac

    @property
    def model_config(self) -> DeviceModelConfig:
        """Return the device model configuration."""
        model = self.device_info.model
        model_family = model[:6]
        if model in DEVICE_MODELS:
            return DEVICE_MODELS[model]
        if model_family in DEVICE_MODELS:
            return DEVICE_MODELS[model_family]
        return DeviceModelConfig(api_generation=ApiGeneration.GEN1)

    async def async_set_control_value(self, key: str, value: Any) -> None:
        """Set a single control value on the device."""
        await self.async_set_control_values({key: value})

    async def async_set_control_values(self, values: dict[str, Any]) -> None:
        """Set multiple control values on the device."""
        self._debug_event("control_start", values=values)
        if self.client is None:
            self._mark_unavailable("control update failed")
            self._schedule_reconnect("control_failed")
            msg = f"No connected client is available for device at {self.host}"
            self._debug_event("control_failed", values=values, error=msg)
            raise UpdateFailed(msg)

        async with self._control_lock:
            try:
                await asyncio.wait_for(
                    self.client.set_control_values(data=values),
                    timeout=CONTROL_TIMEOUT,
                )
            except Exception as err:
                self._mark_unavailable("control update failed")
                self._debug_event("control_failed", values=values, **exception_data(err))
                self._schedule_reconnect("control_failed")
                raise

        if self.data is not None:
            self.async_set_updated_data({**self.data, **values})
        self._debug_event("control_success", values=values)

    async def _async_update_data(self) -> dict[str, Any]:
        """Return the latest coordinator data without creating an ad hoc CoAP read."""
        if self.data is None:
            msg = f"No observed data is available for device at {self.host}"
            raise UpdateFailed(msg)
        return self.data

    def _start_observing(self) -> None:
        """Start observing device status via one long-lived CoAP observe stream."""
        self._debug_event("observe_start_requested")
        if self.client is None:
            self._debug_event("observe_start_skipped", reason="client_unavailable")
            self._schedule_reconnect("client_unavailable", delay=self._next_reconnect_delay())
            return

        if self._observe_task is not None and not self._observe_task.done():
            self._observe_task.cancel()

        self._observe_task = self.hass.async_create_background_task(
            self._async_observe_status(),
            f"philips_airpurifier_observe_{self.host}",
        )

    def _start_snapshot_refresh(self) -> None:
        """Start bounded status snapshots to keep HA state fresh if observe is quiet."""
        if self.client is None:
            return
        if self._snapshot_task is not None and not self._snapshot_task.done():
            return

        self._snapshot_task = self.hass.async_create_background_task(
            self._async_snapshot_refresh(),
            f"philips_airpurifier_snapshot_{self.host}",
        )

    async def _async_snapshot_refresh(self) -> None:
        """Refresh status using cancelled public snapshots at the device max-age."""
        self._debug_event("snapshot_loop_start")
        try:
            while not self._shutting_down:
                await asyncio.sleep(max(self._timeout, DEFAULT_OBSERVE_MAX_AGE))
                if self._shutting_down:
                    return
                try:
                    await self._async_fetch_status_snapshot("periodic_snapshot")
                except Exception as err:
                    if self._handle_snapshot_failure("periodic_snapshot", err):
                        return
        except asyncio.CancelledError:
            self._debug_event("snapshot_cancelled")
            raise
        finally:
            self._debug_event("snapshot_loop_ended", shutting_down=self._shutting_down)

    def _handle_snapshot_failure(self, reason: str, err: Exception) -> bool:
        """Record a snapshot failure and return whether reconnect is needed."""
        self._consecutive_failures += 1
        fields = {
            "reason": reason,
            "failure_threshold": SNAPSHOT_FAILURES_BEFORE_RECONNECT,
            **exception_data(err),
        }

        if self._consecutive_failures < SNAPSHOT_FAILURES_BEFORE_RECONNECT:
            self._debug_event("snapshot_missed", **fields)
            return False

        self._mark_unavailable("status snapshot failed")
        self._debug_event("snapshot_failed", **fields)
        self._schedule_reconnect("snapshot_failed", delay=self._next_reconnect_delay())
        return True

    async def _async_fetch_status_snapshot(self, reason: str) -> dict[str, Any]:
        """Fetch one current status snapshot and cancel the temporary observation."""
        if self.client is None:
            msg = f"No connected client is available for device at {self.host}"
            raise UpdateFailed(msg)

        self._debug_event("snapshot_start", reason=reason)
        status, max_age = await asyncio.wait_for(
            self.client.get_status(observe=False),
            timeout=STATUS_SNAPSHOT_TIMEOUT,
        )
        self._timeout = max_age or DEFAULT_OBSERVE_MAX_AGE
        self._handle_status_success(status, source="snapshot", reason=reason)
        return status

    async def _async_observe_status(self) -> None:
        """Observe device status via public CoAP push updates."""
        self._debug_event("observe_loop_start")
        try:
            async for status in self.client.observe_status():
                self._handle_status_success(status, source="observe")
            if not self._shutting_down:
                msg = "observation stream ended"
                raise RuntimeError(msg)
        except asyncio.CancelledError:
            self._debug_event("observe_cancelled")
            raise
        except Exception as err:
            self._consecutive_failures += 1
            self._mark_unavailable("observation stream ended")
            self._debug_event("observe_failed", **exception_data(err))
            if not self._shutting_down:
                self._schedule_reconnect("observe_failed", delay=self._next_reconnect_delay())
        finally:
            self._debug_event("observe_loop_ended", shutting_down=self._shutting_down)

    def _handle_status_success(self, status: dict[str, Any], *, source: str, reason: str | None = None) -> None:
        """Update coordinator state after an observed status payload."""
        self._last_update = asyncio.get_running_loop().time()
        self._consecutive_failures = 0
        self._mark_available()
        self.async_set_updated_data(status)
        fields: dict[str, Any] = status_data(status)
        if reason is not None:
            fields["reason"] = reason
        self._debug_event(f"{source}_update", **fields)

    def _schedule_reconnect(self, reason: str, *, delay: int = 0) -> None:
        """Schedule a bounded reconnect attempt if one is not already running."""
        if self._shutting_down:
            return
        if self._reconnect_task is not None and not self._reconnect_task.done():
            self._debug_event("reconnect_skipped", reason=reason, skip_reason="already_running")
            return

        self._debug_event("reconnect_scheduled", reason=reason, delay_seconds=delay)
        self._reconnect_task = self.hass.async_create_background_task(
            self._do_reconnect(reason, delay),
            f"philips_airpurifier_reconnect_{self.host}",
        )

    def _next_reconnect_delay(self) -> int:
        """Return a bounded reconnect backoff based on consecutive failures."""
        multiplier = max(self._consecutive_failures, 1)
        return min(RECONNECT_BACKOFF_SECONDS * multiplier, MAX_RECONNECT_BACKOFF_SECONDS)

    async def _do_reconnect(self, reason: str, delay: int) -> None:
        """Reconnect and restart the long-lived observe stream."""
        try:
            if delay > 0:
                await asyncio.sleep(delay)
            if self._shutting_down:
                return

            self._debug_event("reconnect_start", reason=reason)
            if self._observe_task is not None and not self._observe_task.done():
                self._observe_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._observe_task
            self._observe_task = None

            if self.client is not None:
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(self.client.shutdown(), timeout=SHUTDOWN_TIMEOUT)

            start = perf_counter()
            self.client = await async_create_client(
                self.host,
                timeout=CONNECT_TIMEOUT,
                create_client=CoAPClient.create,
            )
            self._debug_event(
                "reconnect_client_created",
                reason=reason,
                elapsed_seconds=round(perf_counter() - start, 3),
            )

            await self._async_fetch_status_snapshot("reconnect")
            self._start_observing()
            self._start_snapshot_refresh()
            self._debug_event("reconnect_success", reason=reason)
        except asyncio.CancelledError:
            self._debug_event("reconnect_cancelled", reason=reason)
            raise
        except Exception as err:
            self._consecutive_failures += 1
            self._mark_unavailable("reconnect failed")
            self._debug_event("reconnect_failed", reason=reason, **exception_data(err))
            if self._observe_task is not None and not self._observe_task.done():
                self._observe_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._observe_task
            if not self._shutting_down:
                self._reconnect_task = None
                self._schedule_reconnect("reconnect_failed", delay=self._next_reconnect_delay())
        finally:
            if self._reconnect_task is asyncio.current_task():
                self._reconnect_task = None

    async def async_first_refresh_and_observe(self, cached_status: dict[str, Any] | None = None) -> None:
        """Fetch a fresh snapshot and start the observe and snapshot refresh loops."""
        self._debug_event("first_refresh_start")
        has_cached_status = bool(cached_status)
        if cached_status:
            self.async_set_updated_data(cached_status)
            self._debug_event("cached_status_loaded", **status_data(cached_status))

        if has_cached_status:
            if self.client is None:
                self._mark_unavailable("initial client unavailable")
                self._start_observing()
            else:
                try:
                    await self._async_fetch_status_snapshot("cached_setup")
                except Exception as err:
                    self._mark_unavailable("cached status awaiting fresh snapshot")
                    self._debug_event("snapshot_failed", reason="cached_setup", **exception_data(err))
                self._start_observing()
                self._start_snapshot_refresh()
            self._debug_event("first_refresh_using_cached_status")
            return

        if self.client is None:
            self._mark_unavailable("initial connection failed")
            msg = f"Failed to connect to device at {self.host}"
            raise ConfigEntryNotReady(msg)

        try:
            await self._async_fetch_status_snapshot("initial_setup")
        except Exception as err:
            self._mark_unavailable("initial status snapshot failed")
            self._debug_event("first_refresh_failed", **exception_data(err))
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self.client.shutdown(), timeout=SHUTDOWN_TIMEOUT)
            msg = f"Failed to fetch status from device at {self.host}"
            raise ConfigEntryNotReady(msg) from err

        self._start_observing()
        self._start_snapshot_refresh()

        self._debug_event("first_refresh_success")

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        self._debug_event("shutdown_start")
        self._shutting_down = True

        tasks_to_cancel: list[asyncio.Task[None]] = []
        for task in (self._observe_task, self._snapshot_task, self._reconnect_task):
            if task is not None and not task.done():
                task.cancel()
                tasks_to_cancel.append(task)

        self._observe_task = None
        self._snapshot_task = None
        self._reconnect_task = None

        for task in tasks_to_cancel:
            with contextlib.suppress(asyncio.CancelledError):
                await task

        if self.client is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self.client.shutdown(), timeout=SHUTDOWN_TIMEOUT)
        self._debug_event("shutdown_done")
