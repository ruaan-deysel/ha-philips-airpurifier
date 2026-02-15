---
agent: "agent"
tools: ["search/codebase", "edit", "search", "runCommands"]
description: "Add a new sensor entity with proper structure, coordinator integration, and translations"
---

# Add New Sensor

Your goal is to add a new sensor entity to this Home Assistant integration.

If not provided, ask for:

- Sensor name and purpose
- Data type (temperature, humidity, battery, etc.)
- Unit of measurement (if applicable)
- Device class (if applicable)
- State class (measurement, total, total_increasing)

## Requirements

**Entity Implementation:**

- Create new sensor file in `custom_components/ha_integration_domain/sensor/`
- Inherit from `IntegrationBlueprintEntity` and `SensorEntity`
- Use `SensorEntityDescription` for static metadata
- Implement `native_value` property to return sensor value from coordinator data
- Add proper type hints for all methods and properties

**Platform Registration:**

- Use tuple of `SensorEntityDescription` in `SENSORS` constant (see template above)
- Entity class should accept `description` parameter in `__init__`
- Alternatively, add sensor instance to list in `async_setup_entry`

**Translations:**

- Add sensor name to `translations/en.json` under `entity.sensor.[sensor_key].name`
- Update `translations/de.json` with German translation
- Translation key must match `translation_key` in EntityDescription
- With `has_entity_name=True`, entity name comes from translations (not hardcoded)

**Data Flow:**

- Sensor must read data from `self.coordinator.data`
- Never fetch data directly in entity - use coordinator pattern
- Set `_attr_available = False` if data is missing

**Entity Template:**

```python
"""[Sensor description] for Integration Blueprint."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import [UNIT_CONSTANT]  # e.g., PERCENTAGE, UnitOfTemperature
from homeassistant.core import callback

from ..coordinator import IntegrationBlueprintDataUpdateCoordinator
from ..entity import IntegrationBlueprintEntity


class IntegrationBlueprint[SensorName]Sensor(
    IntegrationBlueprintEntity,
    SensorEntity,
):
    """Sensor for [description]."""

    # MANDATORY for new integrations (2025)
    _attr_has_entity_name = True

    entity_description = SensorEntityDescription(
        key="[sensor_key]",
        translation_key="[sensor_key]",  # Use translation_key instead of name
        device_class=SensorDeviceClass.[DEVICE_CLASS],  # Optional: TEMPERATURE, HUMIDITY, BATTERY, etc.
        state_class=SensorStateClass.[STATE_CLASS],  # MEASUREMENT or TOTAL_INCREASING
        native_unit_of_measurement=[UNIT],  # Optional: PERCENTAGE, UnitOfTemperature.CELSIUS, etc.
    )

    def __init__(
        self,
        coordinator: IntegrationBlueprintDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_{self.entity_description.key}"

    @property
    def native_value(self) -> [ValueType] | None:
        """Return the sensor value from coordinator data."""
        return self.coordinator.data.get("[data_key]")
```

**State Class Guidance:**

- `MEASUREMENT`: Value can increase or decrease (temperature, humidity, pressure)
- `TOTAL_INCREASING`: Monotonically increasing counter (energy consumed, data uploaded)
- `TOTAL`: Like TOTAL_INCREASING but resets are allowed (daily counter)

**Platform Registration (Modern Pattern):**

In `sensor/__init__.py`, use tuple of EntityDescription:

```python
from homeassistant.components.sensor import SensorEntityDescription

SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    SensorEntityDescription(
        key="[your_new_sensor_key]",
        translation_key="[your_new_sensor_key]",
        device_class=SensorDeviceClass.[CLASS],
        state_class=SensorStateClass.[STATE],
        native_unit_of_measurement=[UNIT],
    ),
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        YourSensorClass(coordinator, entry, description)
        for description in SENSORS
    )
```

**Code Quality:**

- Follow existing sensor patterns (see `sensor/*.py` for examples)
- Use constants from `const.py` for keys
- Add proper docstrings (Google-style)
- Run `script/check` to validate before completion

**Related Files:**

- Entity: `custom_components/ha_integration_domain/sensor/[sensor_name].py`
- Platform: `custom_components/ha_integration_domain/sensor/__init__.py`
- Translations: `custom_components/ha_integration_domain/translations/*.json`
- Documentation: Reference [#file:docs/development/ARCHITECTURE.md]

**DO NOT create tests unless explicitly requested.**
