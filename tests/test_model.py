"""Tests for Philips AirPurifier model module."""

from __future__ import annotations

from custom_components.philips_airpurifier.model import (
    ApiGeneration,
    DeviceModelConfig,
)


def test_gen1_power_key() -> None:
    """Test Gen1 power key."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN1)
    assert config.power_key == "pwr"


def test_gen1_power_on() -> None:
    """Test Gen1 power-on value."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN1)
    assert config.power_on == "1"


def test_gen1_power_off() -> None:
    """Test Gen1 power-off value."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN1)
    assert config.power_off == "0"


def test_gen2_power_key() -> None:
    """Test Gen2 power key."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN2)
    assert config.power_key == "D03-02"


def test_gen2_power_on() -> None:
    """Test Gen2 power-on value."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN2)
    assert config.power_on == "ON"


def test_gen2_power_off() -> None:
    """Test Gen2 power-off value."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN2)
    assert config.power_off == "OFF"


def test_gen3_power_key() -> None:
    """Test Gen3 power key."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN3)
    assert config.power_key == "D03102"


def test_gen3_power_on() -> None:
    """Test Gen3 power-on value."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN3)
    assert config.power_on == 1


def test_gen3_power_off() -> None:
    """Test Gen3 power-off value."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN3)
    assert config.power_off == 0


def test_default_fields() -> None:
    """Test default field values for DeviceModelConfig."""
    config = DeviceModelConfig(api_generation=ApiGeneration.GEN1)
    assert config.preset_modes == {}
    assert config.speeds == {}
    assert config.switches == []
    assert config.lights == []
    assert config.selects == []
    assert config.numbers == []
    assert config.humidifiers == []
    assert config.heaters == []
    assert config.binary_sensors == []
    assert config.unavailable_filters == []
    assert config.unavailable_sensors == []
    assert config.oscillation is None
    assert config.create_fan is True
    assert config.requires_mode_cycling is False
