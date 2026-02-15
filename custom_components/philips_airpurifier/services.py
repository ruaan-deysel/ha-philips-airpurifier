"""Service implementations for Philips Air Purifier integration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.service import async_extract_entity_ids

from .const import DOMAIN, PhilipsApi

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from .coordinator import PhilipsAirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_FILTER_RESET = "filter_reset"
SERVICE_SET_CHILD_LOCK = "set_child_lock"

FILTER_RESET_SCHEMA = vol.Schema(
    {
        vol.Optional("filter_type", default="all"): vol.In(
            [
                "all",
                "pre_filter",
                "hepa_filter",
                "active_carbon_filter",
                "nanoprotect_filter",
            ]
        ),
        vol.Optional("reset_maintenance_schedule", default=True): cv.boolean,
    }
)

SET_CHILD_LOCK_SCHEMA = vol.Schema(
    {
        vol.Required("enabled"): cv.boolean,
    }
)


def _get_coordinator_from_entity_id(hass: HomeAssistant, entity_id: str) -> PhilipsAirPurifierCoordinator | None:
    """Get coordinator from entity ID."""
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get(entity_id)

    if not entity_entry or not entity_entry.config_entry_id:
        return None

    config_entry = hass.config_entries.async_get_entry(entity_entry.config_entry_id)
    if (
        not config_entry
        or config_entry.domain != DOMAIN
        or config_entry.runtime_data is None
        or config_entry.state is not ConfigEntryState.LOADED
    ):
        return None

    return config_entry.runtime_data


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Philips Air Purifier integration."""

    async def async_filter_reset(call: ServiceCall) -> None:
        """Handle filter reset service call."""
        entity_ids = await async_extract_entity_ids(call)
        if not entity_ids:
            raise ServiceValidationError(
                "No target entities provided",
                translation_domain=DOMAIN,
                translation_key="no_target_entities",
            )
        filter_type = call.data.get("filter_type", "all")

        for entity_id in entity_ids:
            coordinator = _get_coordinator_from_entity_id(hass, entity_id)
            if not coordinator:
                raise ServiceValidationError(
                    f"Invalid target entity: {entity_id}",
                    translation_domain=DOMAIN,
                    translation_key="invalid_target_entity",
                    translation_placeholders={"entity_id": entity_id},
                )

            try:
                await _reset_filter_counters(coordinator, filter_type)
            except Exception as ex:
                raise HomeAssistantError(
                    f"Filter reset failed for {entity_id}: {ex}",
                    translation_domain=DOMAIN,
                    translation_key="filter_reset_failed",
                    translation_placeholders={"entity_id": entity_id},
                ) from ex

    async def async_set_child_lock(call: ServiceCall) -> None:
        """Handle set child lock service call."""
        entity_ids = await async_extract_entity_ids(call)
        if not entity_ids:
            raise ServiceValidationError(
                "No target entities provided",
                translation_domain=DOMAIN,
                translation_key="no_target_entities",
            )
        enabled = call.data["enabled"]

        for entity_id in entity_ids:
            coordinator = _get_coordinator_from_entity_id(hass, entity_id)
            if not coordinator:
                raise ServiceValidationError(
                    f"Invalid target entity: {entity_id}",
                    translation_domain=DOMAIN,
                    translation_key="invalid_target_entity",
                    translation_placeholders={"entity_id": entity_id},
                )

            try:
                await coordinator.async_set_control_value(PhilipsApi.CHILD_LOCK, enabled)
            except Exception as ex:
                raise HomeAssistantError(
                    f"Set child lock failed for {entity_id}: {ex}",
                    translation_domain=DOMAIN,
                    translation_key="set_child_lock_failed",
                    translation_placeholders={"entity_id": entity_id},
                ) from ex

    services = {
        SERVICE_FILTER_RESET: (async_filter_reset, FILTER_RESET_SCHEMA),
        SERVICE_SET_CHILD_LOCK: (async_set_child_lock, SET_CHILD_LOCK_SCHEMA),
    }

    for service_name, (handler, schema) in services.items():
        if not hass.services.has_service(DOMAIN, service_name):
            hass.services.async_register(DOMAIN, service_name, handler, schema=schema)


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services for Philips Air Purifier integration."""
    for service_name in (SERVICE_FILTER_RESET, SERVICE_SET_CHILD_LOCK):
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)


async def _reset_filter_counters(
    coordinator: PhilipsAirPurifierCoordinator,
    filter_type: str,
) -> None:
    """Reset filter life counters."""
    filter_mappings = {
        "pre_filter": ("fltsts0", "flttotal0"),
        "hepa_filter": ("fltsts1", "flttotal1"),
        "active_carbon_filter": ("fltsts2", "flttotal2"),
        "nanoprotect_filter": ("D05-14", "D05-08"),
    }

    if filter_type == "all":
        filters_to_reset = list(filter_mappings.values())
    else:
        if filter_type not in filter_mappings:
            msg = f"Unknown filter type: {filter_type}"
            raise ServiceValidationError(msg)
        filters_to_reset = [filter_mappings[filter_type]]

    status = coordinator.data or {}

    for status_key, total_key in filters_to_reset:
        total_capacity = status.get(total_key, 0)
        if total_capacity > 0:
            await coordinator.async_set_control_value(status_key, total_capacity)
            _LOGGER.info("Reset filter %s to full capacity (%s)", status_key, total_capacity)
        else:
            _LOGGER.warning("Could not reset filter %s: total capacity unknown", status_key)
