"""Diagnostics support for Philips Air Purifier integration."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_NAME, __version__ as HA_VERSION
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.util import dt as dt_util

from .const import CONF_DEVICE_ID, CONF_MODEL, CONF_STATUS, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .__init__ import PhilipsAirPurifierConfigEntry

TO_REDACT = {
    "device_id",
    "DeviceId",
    "device_serial",
    "serial_number",
    "mac",
    "ip_address",
    "host",
    "ssid",
    "wifi_ssid",
    "network_name",
    "bssid",
    "wifi_password",
    "password",
    "token",
    "api_key",
    "unique_id",
    "id",
    "entry_id",
    "config_entry_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PhilipsAirPurifierConfigEntry
) -> dict[str, Any]:  # pragma: no cover
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    device_entry = None
    for device in device_registry.devices.values():  # pragma: no branch
        if entry.entry_id in device.config_entries:
            device_entry = device
            break

    entities = er.async_entries_for_config_entry(entity_registry, entry.entry_id)

    status = coordinator.data or {}

    diagnostics_data: dict[str, Any] = {
        "system_info": {
            "home_assistant_version": HA_VERSION,
            "python_version": sys.version,
            "domain": DOMAIN,
            "entry_id": entry.entry_id,
            "entry_title": entry.title,
            "entry_version": entry.version,
            "timestamp": dt_util.utcnow().isoformat(),
        },
        "device_info": {
            "model": coordinator.device_info.model,
            "name": coordinator.device_info.name,
            "host": coordinator.host,
            "device_id": coordinator.device_info.device_id,
        },
        "configuration": {
            "host": entry.data.get(CONF_HOST),
            "model": entry.data.get(CONF_MODEL),
            "name": entry.data.get(CONF_NAME),
            "has_device_id": CONF_DEVICE_ID in entry.data,
            "has_status": CONF_STATUS in entry.data,
            "source": entry.source,
            "state": entry.state.value,
        },
        "coordinator": {
            "client_available": coordinator.client is not None,
            "has_data": status is not None and len(status) > 0,
            "status_keys": list(status.keys()) if status else [],
        },
        "entities": {
            "total": len(entities),
            "details": [
                {
                    "entity_id": e.entity_id,
                    "platform": e.platform,
                    "device_class": e.device_class,
                    "entity_category": str(e.entity_category) if e.entity_category else None,  # pragma: no branch
                    "disabled": e.disabled_by is not None,
                    "translation_key": e.translation_key,
                }
                for e in entities
            ],
        },
        "device_registry": {},
        "device_status": status,
    }

    if device_entry:
        diagnostics_data["device_registry"] = {
            "manufacturer": device_entry.manufacturer,
            "model": device_entry.model,
            "name": device_entry.name,
            "sw_version": device_entry.sw_version,
        }

    return async_redact_data(diagnostics_data, TO_REDACT)
