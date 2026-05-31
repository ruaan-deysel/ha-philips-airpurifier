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
FIRST_STATUS_TIMEOUT = 90
CONTROL_TIMEOUT = 25
SHUTDOWN_TIMEOUT = 5
RECONNECT_BACKOFF_SECONDS = 60
MAX_RECONNECT_BACKOFF_SECONDS = 900
OBSERVE_IDLE_TIMEOUT_SECONDS = 1800


class ObserveIdleTimeout(TimeoutError):
    """Raised when the public observe stream stops delivering updates."""


class PhilipsAirPurifierCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data from Philips AirPurifier via one CoAP observe stream."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CoAPClient,
        host: str,
        device_info: DeviceInformation,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.client = client
        self.host = host
        self.device_info = device_info

        self._observe_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._initial_observe_timeout_task: asyncio.Task[None] | None = None
        self._first_status_future: asyncio.Future[dict[str, Any]] | None = None
        self._timeout: int = DEFAULT_OBSERVE_MAX_AGE
        self._observe_idle_timeout: float = OBSERVE_IDLE_TIMEOUT_SECONDS
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
        """Return the latest observed data without creating a second observation."""
        if self.data is None:
            msg = f"No observed data is available for device at {self.host}"
            raise UpdateFailed(msg)
        return self.data

    def _start_observing(self) -> None:
        """Start observing device status via one long-lived CoAP observe stream."""
        self._debug_event("observe_start_requested")
        if self._observe_task is not None and not self._observe_task.done():
            self._observe_task.cancel()

        self._observe_task = self.hass.async_create_background_task(
            self._async_observe_status(),
            f"philips_airpurifier_observe_{self.host}",
        )

    async def _async_observe_status(self) -> None:
        """Observe device status via public CoAP push updates."""
        self._debug_event("observe_loop_start", idle_timeout_seconds=self._observe_idle_timeout)
        try:
            stream = self.client.observe_status()
            async with contextlib.aclosing(stream):
                while not self._shutting_down:
                    try:
                        status = await asyncio.wait_for(anext(stream), timeout=self._observe_idle_timeout)
                    except StopAsyncIteration:
                        if self._shutting_down:
                            break
                        msg = "observation stream ended"
                        raise RuntimeError(msg) from None
                    except TimeoutError as err:
                        seconds_since_last_update = self._seconds_since_last_update()
                        self._debug_event(
                            "observe_idle_timeout",
                            idle_timeout_seconds=self._observe_idle_timeout,
                            seconds_since_last_update=seconds_since_last_update,
                        )
                        msg = f"observation stream idle for {self._observe_idle_timeout} seconds"
                        raise ObserveIdleTimeout(msg) from err

                    self._handle_status_success(status)
        except asyncio.CancelledError:
            self._debug_event("observe_cancelled")
            self._reject_first_status(asyncio.CancelledError())
            raise
        except ObserveIdleTimeout as err:
            self._reject_first_status(err)
            self._consecutive_failures += 1
            self._mark_unavailable("observation stream idle")
            self._debug_event("observe_failed", reason="idle_timeout", **exception_data(err))
            if not self._shutting_down:
                self._schedule_reconnect("observe_idle_timeout", delay=self._next_reconnect_delay())
        except Exception as err:
            self._reject_first_status(err)
            self._consecutive_failures += 1
            self._mark_unavailable("observation stream ended")
            self._debug_event("observe_failed", **exception_data(err))
            if not self._shutting_down:
                self._schedule_reconnect("observe_failed", delay=self._next_reconnect_delay())
        finally:
            self._debug_event("observe_loop_ended", shutting_down=self._shutting_down)

    def _handle_status_success(self, status: dict[str, Any]) -> None:
        """Update coordinator state after an observed status payload."""
        self._last_update = asyncio.get_running_loop().time()
        self._consecutive_failures = 0
        self._mark_available()
        self.async_set_updated_data(status)
        self._resolve_first_status(status)
        self._debug_event("observe_update", **status_data(status))

    def _seconds_since_last_update(self) -> float | None:
        """Return monotonic age of the last observed payload."""
        if self._last_update <= 0:
            return None
        return round(asyncio.get_running_loop().time() - self._last_update, 3)

    def _resolve_first_status(self, status: dict[str, Any]) -> None:
        """Resolve the setup/reconnect waiter when the first observation arrives."""
        if self._first_status_future is not None and not self._first_status_future.done():
            self._first_status_future.set_result(status)

    def _reject_first_status(self, err: BaseException) -> None:
        """Reject the setup/reconnect waiter if the observe stream fails early."""
        if self._first_status_future is not None and not self._first_status_future.done():
            self._first_status_future.set_exception(err)

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

    async def _async_initial_observe_timeout(self, future: asyncio.Future[dict[str, Any]]) -> None:
        """Mark cached setup unavailable if no fresh observation arrives."""
        try:
            await asyncio.wait_for(asyncio.shield(future), timeout=FIRST_STATUS_TIMEOUT)
        except TimeoutError as err:
            self._consecutive_failures += 1
            self._first_status_future = None
            self._mark_unavailable("initial observation timed out")
            self._debug_event("first_refresh_timeout_using_cached_status", **exception_data(err))
            self._schedule_reconnect("initial_observe_timeout", delay=self._next_reconnect_delay())
        except asyncio.CancelledError:
            raise
        except Exception as err:
            self._consecutive_failures += 1
            self._first_status_future = None
            self._mark_unavailable("initial observation failed")
            self._debug_event("first_refresh_failed_using_cached_status", **exception_data(err))
            self._schedule_reconnect("initial_observe_failed", delay=self._next_reconnect_delay())

    async def _do_reconnect(self, reason: str, delay: int) -> None:
        """Reconnect and wait for the first observed status payload."""
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

            self._first_status_future = asyncio.get_running_loop().create_future()
            self._start_observing()
            await asyncio.wait_for(self._first_status_future, timeout=FIRST_STATUS_TIMEOUT)
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
        """Start observing and wait for the first status payload."""
        self._debug_event("first_refresh_start")
        has_cached_status = bool(cached_status)
        if cached_status:
            self.async_set_updated_data(cached_status)
            self._debug_event("cached_status_loaded", **status_data(cached_status))

        self._first_status_future = asyncio.get_running_loop().create_future()
        self._start_observing()
        if has_cached_status:
            self._initial_observe_timeout_task = self.hass.async_create_background_task(
                self._async_initial_observe_timeout(self._first_status_future),
                f"philips_airpurifier_initial_observe_timeout_{self.host}",
            )
            self._debug_event("first_refresh_using_cached_status")
            return

        try:
            await asyncio.wait_for(self._first_status_future, timeout=FIRST_STATUS_TIMEOUT)
        except TimeoutError as err:
            self._mark_unavailable("initial observation failed")
            self._debug_event("first_refresh_failed", **exception_data(err))
            if self._observe_task is not None and not self._observe_task.done():
                self._observe_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._observe_task
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self.client.shutdown(), timeout=SHUTDOWN_TIMEOUT)
            msg = f"Failed to observe device at {self.host}"
            raise ConfigEntryNotReady(msg) from err
        except Exception as err:
            if has_cached_status:
                self._first_status_future = None
                self._mark_unavailable("initial observation failed")
                self._debug_event("first_refresh_failed_using_cached_status", **exception_data(err))
                return

            self._mark_unavailable("initial observation failed")
            self._debug_event("first_refresh_failed", **exception_data(err))
            if self._observe_task is not None and not self._observe_task.done():
                self._observe_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._observe_task
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self.client.shutdown(), timeout=SHUTDOWN_TIMEOUT)
            msg = f"Failed to observe device at {self.host}"
            raise ConfigEntryNotReady(msg) from err

        self._debug_event("first_refresh_success")

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        self._debug_event("shutdown_start")
        self._shutting_down = True

        tasks_to_cancel: list[asyncio.Task[None]] = []
        for task in (self._observe_task, self._reconnect_task):
            if task is not None and not task.done():
                task.cancel()
                tasks_to_cancel.append(task)
        if self._initial_observe_timeout_task is not None and not self._initial_observe_timeout_task.done():
            self._initial_observe_timeout_task.cancel()
            tasks_to_cancel.append(self._initial_observe_timeout_task)

        self._observe_task = None
        self._reconnect_task = None
        self._initial_observe_timeout_task = None

        for task in tasks_to_cancel:
            with contextlib.suppress(asyncio.CancelledError):
                await task

        if self.client is not None:
            with contextlib.suppress(Exception):
                await asyncio.wait_for(self.client.shutdown(), timeout=SHUTDOWN_TIMEOUT)
        self._debug_event("shutdown_done")
