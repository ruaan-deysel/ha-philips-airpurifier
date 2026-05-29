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

MISSED_PACKAGE_COUNT = 3
DEFAULT_TIMEOUT = 60


class PhilipsAirPurifierCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data from Philips AirPurifier via CoAP push."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: CoAPClient,
        host: str,
        device_info: DeviceInformation,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
        )
        self.client = client
        self.host = host
        self.device_info = device_info

        self._observe_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._timeout: int = DEFAULT_TIMEOUT
        self._watchdog_task: asyncio.Task[None] | None = None
        self._last_update: float = 0.0
        self._device_available = True
        self._shutting_down: bool = False

    def _debug_event(self, event: str, **fields: Any) -> None:
        """Write a structured debug event for this coordinator."""
        async_debug_event(
            self.hass,
            event,
            host=self.host,
            model=self.model,
            device_id=self.device_id,
            available=self._device_available,
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
            self.last_update_success = True
            self.async_update_listeners()
            self._debug_event("availability_changed", state="available")
        self._device_available = True

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
        try:
            await self.client.set_control_values(data=values)
        except Exception as err:
            self._debug_event("control_failed", values=values, **exception_data(err))
            raise
        self._debug_event("control_success", values=values)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device (used for initial refresh and fallback)."""
        self._debug_event("fallback_status_start")
        start = perf_counter()
        try:
            # One-shot read: ongoing updates come from the observe stream, so
            # avoid registering a redundant observation (philips-airctrl >= 1.1.0).
            status, timeout = await self.client.get_status(observe=False)
            self._timeout = timeout
            self._mark_available()
            self._debug_event(
                "fallback_status_success",
                elapsed_seconds=round(perf_counter() - start, 3),
                max_age=timeout,
                **status_data(status),
            )
            return status
        except Exception as err:
            self._mark_unavailable("status update failed")
            self._debug_event(
                "fallback_status_failed",
                elapsed_seconds=round(perf_counter() - start, 3),
                **exception_data(err),
            )
            msg = f"Error communicating with device at {self.host}"
            raise UpdateFailed(msg) from err

    def _start_observing(self) -> None:
        """Start observing device status via CoAP push."""
        self._debug_event("observe_start_requested")
        if self._observe_task is not None:
            self._observe_task.cancel()

        self._observe_task = self.hass.async_create_background_task(
            self._async_observe_status(),
            f"philips_airpurifier_observe_{self.host}",
        )

        if self._watchdog_task is not None:
            self._watchdog_task.cancel()

        self._watchdog_task = self.hass.async_create_background_task(
            self._async_watchdog(),
            f"philips_airpurifier_watchdog_{self.host}",
        )

    async def _async_observe_status(self) -> None:
        """Observe device status via CoAP push updates."""
        self._debug_event("observe_loop_start")
        try:
            async for status in self.client.observe_status():
                self._last_update = asyncio.get_event_loop().time()
                self._mark_available()
                self.async_set_updated_data(status)
                self._debug_event("observe_update", max_age=self._timeout, **status_data(status))
        except asyncio.CancelledError:
            self._debug_event("observe_cancelled")
            raise
        except Exception as err:
            _LOGGER.debug(
                "Observation stream ended for %s, triggering reconnect",
                self.host,
            )
            self._debug_event("observe_failed", **exception_data(err))
        finally:
            if not self._shutting_down:
                self._mark_unavailable("observation stream ended")
                self._debug_event("observe_loop_ended", reconnect=True)
                self.hass.async_create_background_task(
                    self._async_reconnect(),
                    f"philips_airpurifier_reconnect_{self.host}",
                )
            else:
                self._debug_event("observe_loop_ended", reconnect=False)

    async def _async_watchdog(self) -> None:
        """Watch for missed updates and trigger reconnect if needed."""
        while True:
            await asyncio.sleep(self._timeout * MISSED_PACKAGE_COUNT)
            if self._last_update > 0:
                elapsed = asyncio.get_event_loop().time() - self._last_update
                if elapsed > self._timeout * MISSED_PACKAGE_COUNT:
                    self._mark_unavailable("watchdog timeout")
                    self._debug_event(
                        "watchdog_timeout",
                        elapsed_seconds=round(elapsed, 3),
                        timeout_seconds=self._timeout,
                        missed_package_count=MISSED_PACKAGE_COUNT,
                    )
                    _LOGGER.warning(
                        "No updates from %s for %d seconds, reconnecting",
                        self.host,
                        int(elapsed),
                    )
                    await self._async_reconnect()

    async def _async_reconnect(self) -> None:
        """Reconnect to the device."""
        if self._reconnect_task is not None and not self._reconnect_task.done():
            self._debug_event("reconnect_skipped", reason="already_running")
            return

        self._debug_event("reconnect_scheduled")
        self._reconnect_task = self.hass.async_create_background_task(
            self._do_reconnect(),
            f"philips_airpurifier_reconnect_{self.host}",
        )

    async def _do_reconnect(self) -> None:
        """Perform the actual reconnect."""
        self._debug_event("reconnect_start")
        try:
            with contextlib.suppress(Exception):
                await self.client.shutdown()

            start = perf_counter()
            self.client = await async_create_client(self.host, create_client=CoAPClient.create)
            self._debug_event(
                "reconnect_client_created",
                elapsed_seconds=round(perf_counter() - start, 3),
            )
            _LOGGER.info("Reconnected to %s", self.host)

            try:
                # One-shot read before re-establishing the observe stream.
                status_start = perf_counter()
                status, timeout = await self.client.get_status(observe=False)
                self._timeout = timeout
                self._mark_available()
                self.async_set_updated_data(status)
                self._debug_event(
                    "reconnect_status_success",
                    elapsed_seconds=round(perf_counter() - status_start, 3),
                    max_age=timeout,
                    **status_data(status),
                )
            except Exception as err:
                self._mark_unavailable("reconnect status fetch failed")
                self._debug_event("reconnect_status_failed", **exception_data(err))
                _LOGGER.debug(
                    "Failed to get status after reconnect to %s",
                    self.host,
                )

            self._start_observing()
        except asyncio.CancelledError:
            self._debug_event("reconnect_cancelled")
            raise
        except Exception as err:
            self._debug_event("reconnect_failed", **exception_data(err))
            _LOGGER.exception("Reconnect to %s failed", self.host)

    async def async_first_refresh_and_observe(self) -> None:
        """Perform first refresh and start observing."""
        self._debug_event("first_refresh_start")
        start = perf_counter()
        try:
            # One-shot initial read; continuous updates come from the observe
            # stream started below, so don't register a second observation here.
            status, timeout = await self.client.get_status(observe=False)
            self._timeout = timeout
            self._mark_available()
            self.async_set_updated_data(status)
            self._debug_event(
                "first_refresh_success",
                elapsed_seconds=round(perf_counter() - start, 3),
                max_age=timeout,
                **status_data(status),
            )
            _LOGGER.debug("First refresh completed for %s", self.host)
        except Exception as err:
            self._mark_unavailable("initial refresh failed")
            self._debug_event(
                "first_refresh_failed",
                elapsed_seconds=round(perf_counter() - start, 3),
                **exception_data(err),
            )
            msg = f"Failed to connect to device at {self.host}"
            raise ConfigEntryNotReady(msg) from err

        self._last_update = asyncio.get_event_loop().time()
        self._start_observing()

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        self._debug_event("shutdown_start")
        self._shutting_down = True

        tasks_to_cancel: list[asyncio.Task[None]] = []
        for task in (self._observe_task, self._watchdog_task, self._reconnect_task):
            if task is not None and not task.done():
                task.cancel()
                tasks_to_cancel.append(task)

        self._observe_task = None
        self._watchdog_task = None
        self._reconnect_task = None

        for task in tasks_to_cancel:
            with contextlib.suppress(asyncio.CancelledError):
                await task

        if self.client is not None:
            with contextlib.suppress(Exception):
                await self.client.shutdown()
        self._debug_event("shutdown_done")
