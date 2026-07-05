"""Coordinator for Philips AirPurifier integration."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Any

from philips_airctrl import CoAPClient

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import async_create_client, async_fetch_status_with_nudge
from .const import DOMAIN
from .device_models import DEVICE_MODELS
from .model import ApiGeneration, DeviceInformation, DeviceModelConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

MISSED_PACKAGE_COUNT = 3
DEFAULT_TIMEOUT = 60
RECONNECT_INITIAL_DELAY = 5
RECONNECT_MAX_DELAY = 60


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
        self._reconnect_retry_task: asyncio.Task[None] | None = None
        self._timeout: int = DEFAULT_TIMEOUT
        self._watchdog_task: asyncio.Task[None] | None = None
        self._last_update: float = 0.0
        self._reconnect_delay: int = RECONNECT_INITIAL_DELAY
        self._device_available = True
        self._shutting_down: bool = False

    def _mark_unavailable(self, reason: str) -> None:
        """Mark the device unavailable and log transition once."""
        if self._device_available:
            _LOGGER.warning("Device at %s became unavailable: %s", self.host, reason)
            self._device_available = False
            self.last_update_success = False
            self.async_update_listeners()

    def _mark_available(self) -> None:
        """Mark the device available and log transition once."""
        if not self._device_available:
            _LOGGER.info("Device at %s is back online", self.host)
            self.last_update_success = True
            self.async_update_listeners()
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
        await self.client.set_control_values(data=values)

    def _build_status_nudge(self) -> list[tuple[str, Any]]:
        """Build the nudge write sequence for a push-on-change device.

        The model declares a default sequence: a transient value followed by a
        resting value the device is left on. Writing a fixed resting value
        clobbers a user setting on every nudge -- e.g. forcing the display
        backlight back on after each reconnect, so the display can never be
        turned off. Instead, end the sequence on the value we last observed for
        that key (the user's choice), while still passing through a different
        transient value first so the device sees a genuine change and pushes.
        """
        base = self.model_config.status_nudge or []
        if not base:
            return []

        key = base[0][0]
        transient = base[0][1]
        resting = base[-1][1]

        # Restore the user's last-known value for the nudged key when we have it.
        if self.data is not None and self.data.get(key) is not None:
            resting = self.data[key]

        # The transient write must differ from the resting value, otherwise the
        # device sees no change and never pushes. The model's two values differ,
        # so fall back to the other one when the resting value collides.
        if transient == resting:
            transient = base[-1][1]

        return [(key, transient), (key, resting)]

    async def _async_nudge_fetch(self) -> dict[str, Any]:
        """Fetch a status snapshot from a device that only pushes on change."""
        nudge = self._build_status_nudge()
        return await async_fetch_status_with_nudge(self.host, nudge, create_client=CoAPClient.create)

    async def _async_refresh_via_nudge(self) -> None:
        """Fetch via nudge and publish the resulting status to listeners."""
        # The nudge helper opens its own short-lived client. Single-client
        # firmware evicts any other connection, so close the coordinator client
        # first and recreate it afterwards — otherwise the observe stream started
        # after this would attach to the connection the nudge just evicted.
        with contextlib.suppress(Exception):
            await self.client.shutdown()
        status = await self._async_nudge_fetch()
        self.client = await async_create_client(self.host, create_client=CoAPClient.create)
        self._timeout = DEFAULT_TIMEOUT
        self._last_update = asyncio.get_event_loop().time()
        self._mark_available()
        self.async_set_updated_data(status)

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device (used for initial refresh and fallback)."""
        if self.model_config.status_nudge:
            # This firmware never answers a status read; ongoing state comes
            # from the observe stream. Return the last pushed status if we have
            # it, otherwise force one push via a nudge.
            if self.data is not None:
                self._mark_available()
                return self.data
            try:
                return await self._async_nudge_fetch()
            except Exception as err:
                self._mark_unavailable("status update failed")
                msg = f"Error communicating with device at {self.host}"
                raise UpdateFailed(msg) from err
        try:
            # One-shot read: ongoing updates come from the observe stream, so
            # avoid registering a redundant observation (philips-airctrl >= 1.1.0).
            status, timeout = await self.client.get_status(observe=False)
            self._timeout = timeout
            self._mark_available()
            return status
        except Exception as err:
            self._mark_unavailable("status update failed")
            msg = f"Error communicating with device at {self.host}"
            raise UpdateFailed(msg) from err

    def _start_observing(self) -> None:
        """Start observing device status via CoAP push."""
        if self._observe_task is not None:
            self._observe_task.cancel()

        self._observe_task = self.hass.async_create_background_task(
            self._async_observe_status(),
            f"philips_airpurifier_observe_{self.host}",
        )

        if self.model_config.status_nudge:
            # Nudge-only devices push status only on a real state change, so an
            # idle device legitimately sends nothing. A periodic watchdog would
            # force needless reconnects (each re-toggling the nudge value) while
            # the device is simply idle. Rely on observe-stream errors to detect
            # real disconnects instead of a missed-update timer.
            return

        if self._watchdog_task is not None:
            self._watchdog_task.cancel()

        self._watchdog_task = self.hass.async_create_background_task(
            self._async_watchdog(),
            f"philips_airpurifier_watchdog_{self.host}",
        )

    async def _async_observe_status(self) -> None:
        """Observe device status via CoAP push updates."""
        try:
            async for status in self.client.observe_status():
                self._last_update = asyncio.get_event_loop().time()
                self._mark_available()
                self.async_set_updated_data(status)
        except asyncio.CancelledError:
            raise
        except Exception:
            _LOGGER.debug(
                "Observation stream ended for %s, triggering reconnect",
                self.host,
            )
        finally:
            if not self._shutting_down:
                self.hass.async_create_background_task(
                    self._async_reconnect(),
                    f"philips_airpurifier_reconnect_{self.host}",
                )

    async def _async_watchdog(self) -> None:
        """Watch for missed updates and trigger reconnect if needed."""
        while True:
            await asyncio.sleep(self._timeout * MISSED_PACKAGE_COUNT)
            if self._last_update > 0:
                elapsed = asyncio.get_event_loop().time() - self._last_update
                if elapsed > self._timeout * MISSED_PACKAGE_COUNT:
                    self._mark_unavailable("watchdog timeout")
                    _LOGGER.warning(
                        "No updates from %s for %d seconds, reconnecting",
                        self.host,
                        int(elapsed),
                    )
                    await self._async_reconnect()

    async def _async_reconnect(self) -> None:
        """Reconnect to the device."""
        if self._reconnect_task is not None and not self._reconnect_task.done():
            return

        current_task = asyncio.current_task()
        if (
            self._reconnect_retry_task is not None
            and not self._reconnect_retry_task.done()
            and current_task is not self._reconnect_retry_task
        ):
            self._reconnect_retry_task.cancel()
            self._reconnect_retry_task = None

        self._reconnect_task = self.hass.async_create_background_task(
            self._do_reconnect(),
            f"philips_airpurifier_reconnect_{self.host}",
        )

    def _schedule_reconnect_retry(self, delay: int) -> None:
        """Schedule a reconnect retry after a delay."""
        if self._shutting_down:
            return

        if self._reconnect_retry_task is not None and not self._reconnect_retry_task.done():
            self._reconnect_retry_task.cancel()

        self._reconnect_retry_task = self.hass.async_create_background_task(
            self._async_retry_reconnect(delay),
            f"philips_airpurifier_retry_{self.host}",
        )

    async def _async_retry_reconnect(self, delay: int) -> None:
        """Wait before attempting reconnect again."""
        await asyncio.sleep(delay)
        await self._async_reconnect()

    async def _do_reconnect(self) -> None:
        """Perform the actual reconnect."""
        try:
            with contextlib.suppress(Exception):
                await self.client.shutdown()

            if self.model_config.status_nudge:
                # Re-fetch via nudge before re-establishing the observe stream.
                # _async_refresh_via_nudge owns the coordinator client here: a
                # client created now would be evicted by the nudge helper's
                # temporary connection, so it (re)creates one after the nudge.
                await self._async_refresh_via_nudge()
            else:
                self.client = await async_create_client(self.host, create_client=CoAPClient.create)
                # One-shot read before re-establishing the observe stream.
                status, timeout = await self.client.get_status(observe=False)
                self._timeout = timeout
                self._last_update = asyncio.get_event_loop().time()
                self._mark_available()
                self.async_set_updated_data(status)
            self._reconnect_delay = RECONNECT_INITIAL_DELAY
            _LOGGER.info("Reconnected to %s", self.host)
            self._start_observing()
        except asyncio.CancelledError:
            raise
        except Exception:
            retry_delay = self._reconnect_delay
            self._reconnect_delay = min(self._reconnect_delay * 2, RECONNECT_MAX_DELAY)
            self._mark_unavailable("reconnect failed")
            _LOGGER.warning(
                "Reconnect to %s failed, retrying in %s seconds",
                self.host,
                retry_delay,
            )
            self._schedule_reconnect_retry(retry_delay)

    async def async_first_refresh_and_observe(self) -> None:
        """Perform first refresh and start observing."""
        if self.model_config.status_nudge:
            try:
                # This firmware never answers a status read; force the first
                # push with a nudge, then observe for subsequent changes.
                await self._async_refresh_via_nudge()
                _LOGGER.debug("First refresh (via nudge) completed for %s", self.host)
            except Exception as err:
                self._mark_unavailable("initial nudge refresh failed")
                msg = f"Failed to connect to device at {self.host}"
                raise ConfigEntryNotReady(msg) from err
            self._start_observing()
            return

        try:
            # One-shot initial read; continuous updates come from the observe
            # stream started below, so don't register a second observation here.
            status, timeout = await self.client.get_status(observe=False)
            self._timeout = timeout
            self._mark_available()
            self.async_set_updated_data(status)
            _LOGGER.debug("First refresh completed for %s", self.host)
        except Exception as err:
            self._mark_unavailable("initial refresh failed")
            msg = f"Failed to connect to device at {self.host}"
            raise ConfigEntryNotReady(msg) from err

        self._last_update = asyncio.get_event_loop().time()
        self._start_observing()

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        self._shutting_down = True

        tasks_to_cancel: list[asyncio.Task[None]] = []
        for task in (
            self._observe_task,
            self._watchdog_task,
            self._reconnect_task,
            self._reconnect_retry_task,
        ):
            if task is not None and not task.done():
                task.cancel()
                tasks_to_cancel.append(task)

        self._observe_task = None
        self._watchdog_task = None
        self._reconnect_task = None
        self._reconnect_retry_task = None

        for task in tasks_to_cancel:
            with contextlib.suppress(asyncio.CancelledError):
                await task

        with contextlib.suppress(Exception):
            await self.client.shutdown()
