"""Base entity for Philips AirPurifier integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PhilipsAirPurifierCoordinator


class PhilipsAirPurifierEntity(CoordinatorEntity[PhilipsAirPurifierCoordinator]):
    """Base class for Philips AirPurifier entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PhilipsAirPurifierCoordinator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.device_id)},
            name=coordinator.device_name,
            manufacturer="Philips",
            model=coordinator.model,
        )

    @property
    def available(self) -> bool:
        """Return if the device is available."""
        return super().available and self.coordinator.data is not None

    @property
    def _device_status(self) -> dict[str, Any]:
        """Return the current device status data."""
        return self.coordinator.data
