"""Coordinator for Philips AirPurifier integration."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import timedelta
import logging
from typing import TYPE_CHECKING, Any, cast

from philips_airctrl import CoAPClient

from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import async_get_status, async_set_control_values
from .const import DOMAIN
from .device_models import DEVICE_MODELS
from .model import ApiGeneration, DeviceInformation, DeviceModelConfig

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

DEFAULT_POLL_INTERVAL = 60
MIN_POLL_INTERVAL = 30
MAX_POLL_INTERVAL = 300
STATUS_RETRY_COUNT = 3
STATUS_RETRY_DELAY = 2


class PhilipsAirPurifierCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data from Philips AirPurifier via bounded CoAP polling."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str | CoAPClient,
        device_info: DeviceInformation | str,
        legacy_device_info: DeviceInformation | None = None,
        initial_status: dict[str, Any] | None = None,
        create_client: Any | None = None,
    ) -> None:
        """Initialize the coordinator."""
        legacy_client: CoAPClient | None = None
        if not isinstance(host, str):
            legacy_client = host
            host = cast("str", device_info)
            device_info = cast("DeviceInformation", legacy_device_info)
        else:
            device_info = cast("DeviceInformation", device_info)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )
        self.client = legacy_client
        self._create_client = create_client or _client_factory_from_legacy_client(legacy_client) or CoAPClient.create
        self.host = host
        self.device_info = device_info

        self._timeout: int = DEFAULT_POLL_INTERVAL
        self._last_update: float = 0.0
        self._device_available = True
        self._shutting_down: bool = False
        self._initial_status = initial_status
        self._control_lock = asyncio.Lock()

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
        async with self._control_lock:
            try:
                await async_set_control_values(
                    self.host,
                    data=values,
                    create_client=self._create_client,
                )
            except Exception:
                self._mark_unavailable("control update failed")
                raise

            if self.data is not None:
                self.async_set_updated_data({**self.data, **values})

            self.hass.async_create_background_task(
                self.async_request_refresh(),
                f"philips_airpurifier_refresh_after_control_{self.host}",
            )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the device."""
        last_error: Exception | None = None
        for attempt in range(1, STATUS_RETRY_COUNT + 1):
            try:
                status, timeout = await async_get_status(
                    self.host,
                    create_client=self._create_client,
                )
                self._timeout = timeout
                self.update_interval = _poll_interval_from_timeout(timeout)
                self._last_update = asyncio.get_running_loop().time()
                self._mark_available()
                return status
            except Exception as err:
                last_error = err
                if attempt < STATUS_RETRY_COUNT:
                    _LOGGER.debug(
                        "Status poll %d/%d failed for %s; retrying",
                        attempt,
                        STATUS_RETRY_COUNT,
                        self.host,
                        exc_info=True,
                    )
                    await asyncio.sleep(STATUS_RETRY_DELAY * attempt)

        self._mark_unavailable("status update failed")
        msg = f"Error communicating with device at {self.host}"
        raise UpdateFailed(msg) from last_error

    def _start_observing(self) -> None:
        """Compatibility shim for older tests; status is now refreshed by polling."""
        _LOGGER.debug("CoAP observe mode is disabled for %s; using bounded polling", self.host)

    async def async_first_refresh_and_observe(self) -> None:
        """Perform first refresh and schedule periodic polling."""
        if self._initial_status:
            self.async_set_updated_data(self._initial_status)
            self._mark_unavailable("awaiting live status")
            self.hass.async_create_background_task(
                self.async_request_refresh(),
                f"philips_airpurifier_initial_refresh_{self.host}",
            )
            return

        try:
            await self.async_config_entry_first_refresh()
            _LOGGER.debug("First refresh completed for %s", self.host)
        except Exception as err:
            msg = f"Failed to connect to device at {self.host}"
            raise ConfigEntryNotReady(msg) from err

    async def async_shutdown(self) -> None:
        """Shut down the coordinator."""
        self._shutting_down = True


def _poll_interval_from_timeout(timeout: int) -> timedelta:
    """Return a bounded polling interval from the device CoAP max-age value."""
    try:
        seconds = int(timeout)
    except (TypeError, ValueError):
        seconds = DEFAULT_POLL_INTERVAL

    seconds = min(max(seconds, MIN_POLL_INTERVAL), MAX_POLL_INTERVAL)
    return timedelta(seconds=seconds)


def _client_factory_from_legacy_client(
    client: CoAPClient | None,
) -> Callable[[str], Awaitable[CoAPClient]] | None:
    """Return a create_client callback for older tests that pass a client."""
    if client is None:
        return None

    async def _create_client(_host: str) -> CoAPClient:
        return client

    return _create_client
