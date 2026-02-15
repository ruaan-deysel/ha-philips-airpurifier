"""Coordinator for Philips AirPurifier integration."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Any

from philips_airctrl import CoAPClient

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import async_create_client
from .const import DOMAIN
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

    def _mark_unavailable(self, reason: str) -> None:
        """Mark the device unavailable and log transition once."""
        if self._device_available:
            _LOGGER.warning("Device at %s became unavailable: %s", self.host, reason)
            self._device_available = False

    def _mark_available(self) -> None:
        """Mark the device available and log transition once."""
        if not self._device_available:
            _LOGGER.info("Device at %s is back online", self.host)
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

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device (used for initial refresh and fallback)."""
        try:
            status, timeout = await self.client.get_status()
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

        self._observe_task = self.hass.async_create_task(
            self._async_observe_status(),
            f"philips_airpurifier_observe_{self.host}",
        )

        if self._watchdog_task is not None:
            self._watchdog_task.cancel()

        self._watchdog_task = self.hass.async_create_task(
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
            self._mark_unavailable("observation stream ended")
            _LOGGER.debug(
                "Observation stream ended for %s, triggering reconnect",
                self.host,
            )
            self.hass.async_create_task(self._async_reconnect())

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

        self._reconnect_task = self.hass.async_create_task(
            self._do_reconnect(),
            f"philips_airpurifier_reconnect_{self.host}",
        )

    async def _do_reconnect(self) -> None:
        """Perform the actual reconnect."""
        try:
            with contextlib.suppress(Exception):
                await self.client.shutdown()

            self.client = await async_create_client(self.host, create_client=CoAPClient.create)
            _LOGGER.info("Reconnected to %s", self.host)

            try:
                status, timeout = await self.client.get_status()
                self._timeout = timeout
                self._mark_available()
                self.async_set_updated_data(status)
            except Exception:
                self._mark_unavailable("reconnect status fetch failed")
                _LOGGER.debug(
                    "Failed to get status after reconnect to %s",
                    self.host,
                )

            self._start_observing()
        except asyncio.CancelledError:
            raise
        except Exception:
            _LOGGER.exception("Reconnect to %s failed", self.host)

    async def async_first_refresh_and_observe(self) -> None:
        """Perform first refresh and start observing."""
        try:
            status, timeout = await self.client.get_status()
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
        if self._observe_task is not None:
            self._observe_task.cancel()
            self._observe_task = None

        if self._watchdog_task is not None:
            self._watchdog_task.cancel()
            self._watchdog_task = None

        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            self._reconnect_task = None

        if self.client is not None:
            with contextlib.suppress(Exception):
                await self.client.shutdown()
