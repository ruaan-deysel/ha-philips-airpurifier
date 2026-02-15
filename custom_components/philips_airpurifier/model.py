"""Type definitions for Philips AirPurifier integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

DeviceStatus = dict[str, Any]

# Type aliases for entity description dicts used in const.py.
# These replace the old TypedDict definitions and will be migrated to
# proper EntityDescription subclasses as each platform is refactored.
SensorDescription = dict[str, Any]
FilterDescription = dict[str, Any]
SwitchDescription = dict[str, Any]
LightDescription = dict[str, Any]
SelectDescription = dict[str, Any]
NumberDescription = dict[str, Any]
HumidifierDescription = dict[str, Any]
HeaterDescription = dict[str, Any]


@dataclass
class DeviceInformation:
    """Device information class."""

    model: str
    name: str
    device_id: str
    host: str
    mac: str | None = None


class ApiGeneration(StrEnum):
    """API generation of the device."""

    GEN1 = "gen1"
    GEN2 = "gen2"
    GEN3 = "gen3"


@dataclass
class DeviceModelConfig:
    """
    Configuration for a specific device model.

    This is the data-driven replacement for the per-model class hierarchy.
    Each model's capabilities, preset modes, speeds, and available entities
    are defined as data rather than through class inheritance.
    """

    api_generation: ApiGeneration
    preset_modes: dict[str, dict[str, Any]] = field(default_factory=dict)
    speeds: dict[str, dict[str, Any]] = field(default_factory=dict)
    switches: list[str] = field(default_factory=list)
    lights: list[str] = field(default_factory=list)
    selects: list[str] = field(default_factory=list)
    numbers: list[str] = field(default_factory=list)
    humidifiers: list[str] = field(default_factory=list)
    heaters: list[str] = field(default_factory=list)
    binary_sensors: list[str] = field(default_factory=list)
    unavailable_filters: list[str] = field(default_factory=list)
    unavailable_sensors: list[str] = field(default_factory=list)
    oscillation: dict[str, dict[str, Any]] | None = None
    create_fan: bool = True
    # Special behavior flags
    requires_mode_cycling: bool = False  # AC1214 needs mode cycling

    @property
    def power_key(self) -> str:
        """Return the power key for this API generation."""
        if self.api_generation == ApiGeneration.GEN2:
            return "D03-02"
        if self.api_generation == ApiGeneration.GEN3:
            return "D03102"
        return "pwr"

    @property
    def power_on(self) -> str | int:
        """Return the power-on value for this API generation."""
        if self.api_generation == ApiGeneration.GEN2:
            return "ON"
        if self.api_generation == ApiGeneration.GEN3:
            return 1
        return "1"

    @property
    def power_off(self) -> str | int:
        """Return the power-off value for this API generation."""
        if self.api_generation == ApiGeneration.GEN2:
            return "OFF"
        if self.api_generation == ApiGeneration.GEN3:
            return 0
        return "0"
