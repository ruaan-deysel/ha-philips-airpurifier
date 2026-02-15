"""Philips Air Purifier select platform."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.const import ATTR_DEVICE_CLASS, CONF_ENTITY_CATEGORY, EntityCategory
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from .const import OPTIONS, SELECT_TYPES, FanAttributes, PhilipsApi
from .entity import PhilipsAirPurifierEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .__init__ import PhilipsAirPurifierConfigEntry
    from .coordinator import PhilipsAirPurifierCoordinator

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0
FAN_MODE_KIND = "fan_mode"


async def _remove_duplicate_preferred_index_entity(
    hass: HomeAssistant,
    coordinator: PhilipsAirPurifierCoordinator,
) -> None:
    """Remove duplicate preferred index entity if it exists."""
    try:
        entity_registry = async_get_entity_registry(hass)
        device_id = coordinator.device_id
        model = coordinator.model

        device_name = coordinator.device_name.lower().replace(" ", "_")
        duplicate_entity_id = f"select.{device_name}_preferred_index"

        entity_entry = entity_registry.async_get(duplicate_entity_id)
        if entity_entry and entity_entry.unique_id and "#1" in entity_entry.unique_id:
            _LOGGER.info(
                "Removing duplicate preferred index entity: %s (keeping gas-enabled version)",
                duplicate_entity_id,
            )
            entity_registry.async_remove(duplicate_entity_id)
            return

        for entity_id, entry in entity_registry.entities.items():
            if (
                entry.platform == "philips_airpurifier_coap"
                and entry.unique_id
                and f"{model}-{device_id}-d0312a#1".lower() in entry.unique_id.lower()
            ):
                _LOGGER.info(
                    "Removing duplicate preferred index entity by unique_id: %s",
                    entity_id,
                )
                entity_registry.async_remove(entity_id)
                break

    except Exception:
        _LOGGER.warning("Could not remove duplicate entity", exc_info=True)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PhilipsAirPurifierConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    coordinator = entry.runtime_data
    model_config = coordinator.model_config

    # Remove duplicate preferred index entity for AC4220 models
    if coordinator.model == "AC4220/12":
        await _remove_duplicate_preferred_index_entity(hass, coordinator)

    # Filter out the basic preferred_index for AC4220 to prevent duplicates
    filtered_selects: list[str] = []
    for kind in SELECT_TYPES:
        if kind in model_config.selects:
            if (
                coordinator.model == "AC4220/12"
                and kind == PhilipsApi.NEW2_PREFERRED_INDEX
                and PhilipsApi.NEW2_GAS_PREFERRED_INDEX in model_config.selects
            ):
                continue
            filtered_selects.append(kind)

    entities: list[SelectEntity] = [PhilipsSelect(coordinator, kind) for kind in filtered_selects]

    if model_config.create_fan and model_config.preset_modes:
        entities.append(PhilipsFanModeSelect(coordinator))

    async_add_entities(entities)


class PhilipsSelect(PhilipsAirPurifierEntity, SelectEntity):
    """Philips AirPurifier select."""

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
        kind: str,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)

        self._description = SELECT_TYPES[kind]
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_translation_key = self._description.get(FanAttributes.LABEL)
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)

        self._options = self._description.get(OPTIONS)
        self._attr_options = list(self._options.values())

        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{kind.lower()}"
        self.kind = kind.partition("#")[0]

    @property
    def current_option(self) -> str:
        """Return the currently selected option."""
        option = self._device_status.get(self.kind)
        current_option = str(self._options.get(option))
        _LOGGER.debug("option: %s, returning as current_option: %s", option, current_option)
        return current_option

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        if option is None or len(option) == 0:
            _LOGGER.error("Cannot set empty option '%s'", option)
            return
        try:
            option_key = next(key for key, value in self._options.items() if value == option)
            _LOGGER.debug(
                "async_selection_option, kind: %s - option: %s - value: %s",
                self.kind,
                option,
                option_key,
            )
            await self.coordinator.async_set_control_value(self.kind, option_key)
            self._device_status[self.kind] = option_key
            self._handle_coordinator_update()

        except KeyError:
            _LOGGER.exception("Invalid option key: '%s'", option)
        except ValueError:
            _LOGGER.exception("Invalid value for option: '%s'", option)


class PhilipsFanModeSelect(PhilipsAirPurifierEntity, SelectEntity):
    """Philips AirPurifier fan mode select for automations."""

    def __init__(self, coordinator: PhilipsAirPurifierCoordinator) -> None:
        """Initialize the fan mode select."""
        super().__init__(coordinator)
        self._attr_translation_key = FAN_MODE_KIND
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_options = list(coordinator.model_config.preset_modes.keys())
        self._preset_modes_map = coordinator.model_config.preset_modes
        self._attr_unique_id = f"{coordinator.model}-{coordinator.device_id}-{FAN_MODE_KIND}"

    @property
    def current_option(self) -> str:
        """Return the currently selected fan mode."""
        for option, status_pattern in self._preset_modes_map.items():
            for key, expected_value in status_pattern.items():
                if self._device_status.get(key) != expected_value:
                    break
            else:
                return option
        return self._attr_options[0]

    async def async_select_option(self, option: str) -> None:
        """Select a fan mode."""
        if not option:
            _LOGGER.error("Cannot set empty fan mode option")
            return

        status_pattern = self._preset_modes_map.get(option)
        if status_pattern is None:
            _LOGGER.error("Invalid fan mode option: %s", option)
            return

        await self.coordinator.async_set_control_values(status_pattern)
        self._device_status.update(status_pattern)
        self._handle_coordinator_update()
