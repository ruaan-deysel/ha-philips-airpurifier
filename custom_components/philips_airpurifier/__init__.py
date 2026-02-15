"""Support for Philips AirPurifier with CoAP."""

from __future__ import annotations

import logging

from philips_airctrl import CoAPClient

from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .client import async_create_client
from .const import (
    CONF_DEVICE_ID,
    CONF_MODEL,
    CONF_STATUS,
    DOMAIN,
)
from .coordinator import PhilipsAirPurifierCoordinator
from .model import DeviceInformation
from .repairs import async_check_integration_health
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

type PhilipsAirPurifierConfigEntry = ConfigEntry[PhilipsAirPurifierCoordinator]

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.FAN,
    Platform.HUMIDIFIER,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
HEALTH_LISTENERS = f"{DOMAIN}_health_listeners"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Philips AirPurifier integration."""
    _ = config
    await async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsAirPurifierConfigEntry,
) -> bool:
    """Set up Philips AirPurifier from a config entry."""
    host = entry.data[CONF_HOST]
    model = entry.data[CONF_MODEL]
    name = entry.data[CONF_NAME]
    device_id = entry.data[CONF_DEVICE_ID]

    _LOGGER.debug("async_setup_entry called for host %s", host)

    try:
        client = await async_create_client(host, timeout=25, create_client=CoAPClient.create)
        _LOGGER.debug("Got a valid client for host %s", host)
    except Exception as err:
        _LOGGER.warning("Failed to connect to host %s: %s", host, err)
        msg = f"Failed to connect to device at {host}"
        raise ConfigEntryNotReady(msg) from err

    device_information = DeviceInformation(
        host=host,
        mac=None,
        model=model,
        name=name,
        device_id=device_id,
    )

    coordinator = PhilipsAirPurifierCoordinator(hass, client, host, device_information)

    # Perform initial data refresh, then start CoAP observation
    await coordinator.async_first_refresh_and_observe()

    hass.async_create_task(async_check_integration_health(hass, coordinator))

    def _schedule_health_check() -> None:
        hass.async_create_task(async_check_integration_health(hass, coordinator))

    remove_health_listener = coordinator.async_add_listener(_schedule_health_check)
    hass.data.setdefault(HEALTH_LISTENERS, {})[entry.entry_id] = remove_health_listener

    # Store initial status in config entry data if missing
    if CONF_STATUS not in entry.data:
        _LOGGER.debug("Saving initial status data for model %s", model)
        new_data = {**entry.data, CONF_STATUS: coordinator.data}
        hass.config_entries.async_update_entry(entry, data=new_data)

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: PhilipsAirPurifierConfigEntry,
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        remove_health_listener = hass.data.get(HEALTH_LISTENERS, {}).pop(entry.entry_id, None)
        if remove_health_listener is not None:
            remove_health_listener()

        await entry.runtime_data.async_shutdown()

        loaded_entries = [
            config_entry
            for config_entry in hass.config_entries.async_entries(DOMAIN)
            if config_entry.entry_id != entry.entry_id and config_entry.state is ConfigEntryState.LOADED
        ]
        if not loaded_entries:
            await async_unload_services(hass)

    return unload_ok
