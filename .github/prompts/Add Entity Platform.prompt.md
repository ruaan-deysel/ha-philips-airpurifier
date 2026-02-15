---
agent: "agent"
tools: ["search/codebase", "edit", "search", "runCommands"]
description: "Add a new entity platform (sensor, switch, binary_sensor, etc.) to the integration"
---

# Add Entity Platform

Your goal is to add a new entity platform to this Home Assistant integration.

If not provided, ask for:

- Platform type (sensor, binary_sensor, switch, button, number, select, fan, etc.)
- Initial entity or entities to create
- Data source (from coordinator, API, config)
- Purpose and user benefit

## Implementation Steps

### 1. Create Platform Directory Structure

**Directory:** `custom_components/ha_integration_domain/[platform]/`

**Files to create:**

- `__init__.py` - Platform setup and entity list
- `[entity_name].py` - Individual entity implementation(s)

### 2. Platform `__init__.py` Template

```python
"""[Platform] platform for Integration Blueprint."""

from __future__ import annotations

from homeassistant.components.[platform] import [PlatformEntityClass]
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import IntegrationBlueprintEntity
from .[entity_file] import IntegrationBlueprint[EntityName]
from .const import DOMAIN
from .coordinator import IntegrationBlueprintDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up [platform] platform."""
    coordinator: IntegrationBlueprintDataUpdateCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]

    async_add_entities(
        [
            IntegrationBlueprint[EntityName](coordinator, entry),
            # Add more entities here
        ]
    )
```

### 3. Entity Implementation Template

```python
"""[Entity description] for Integration Blueprint."""

from __future__ import annotations

from typing import Any

from homeassistant.components.[platform] import (
    [PlatformEntityClass],
    [EntityDescription if applicable],
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback

from .coordinator import IntegrationBlueprintDataUpdateCoordinator
from .entity import IntegrationBlueprintEntity


class IntegrationBlueprint[EntityName](
    IntegrationBlueprintEntity,
    [PlatformEntityClass],
):
    """Representation of [entity description]."""

    # MANDATORY for new integrations (2025)
    _attr_has_entity_name = True

    # Use EntityDescription for sensors, binary_sensors, etc.
    entity_description: [EntityDescription] = [EntityDescription](
        key="[entity_key]",
        translation_key="[entity_key]",  # Use translation_key instead of name
        # Add platform-specific attributes (device_class, state_class, unit, etc.)
    )

    def __init__(
        self,
        coordinator: IntegrationBlueprintDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the [entity]."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_[entity_key]"
        # With has_entity_name=True, entity_id becomes: {device_name}_{translation_key}
        # Initialize any additional attributes

    @property
    def [platform_property](self) -> [ReturnType]:
        """Return the [property description]."""
        # Access coordinator data: self.coordinator.data["key"]
        return self.coordinator.data.get("[data_key]")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Optional: Add custom update logic
        # Check coordinator.context for selective updates:
        # if self.coordinator.context and self.coordinator.context != self.entity_id:
        #     return  # Skip update if context doesn't match this entity
        super()._handle_coordinator_update()

    # Add platform-specific methods (async_turn_on, async_press, etc.)
```

### 4. Update Manifest

Add platform to `custom_components/ha_integration_domain/manifest.json`:

```json
{
  "platforms": ["[existing_platforms]", "[new_platform]"]
}
```

### 5. Add Translations

**`translations/en.json`:**

```json
{
  "entity": {
    "[platform]": {
      "[entity_key]": {
        "name": "[Entity Name]"
      }
    }
  }
}
```

**`translations/de.json`:**

```json
{
  "entity": {
    "[platform]": {
      "[entity_key]": {
        "name": "[German Entity Name]"
      }
    }
  }
}
```

**Note:** With `has_entity_name=True` and `translation_key`, the entity name comes from translations, not hardcoded in code. Icons should also be defined in `icons.json` when possible instead of in EntityDescription.

### 6. Verify Integration

Run validation and test:

```bash
script/check           # Type checking and linting
script/develop         # Start Home Assistant for testing
```

## Platform-Specific Guidance

### Sensor

- Use `SensorEntity` and `SensorEntityDescription`
- Set `native_value` property (returns value in native unit)
- Add `device_class`, `state_class`, `native_unit_of_measurement` if applicable
- Use `state_class=SensorStateClass.MEASUREMENT` for values that can go up/down
- Use `state_class=SensorStateClass.TOTAL_INCREASING` for cumulative counters
- Common device classes: temperature, humidity, power, energy, timestamp
- Sensors with device_class often get automatic naming/units

### Binary Sensor

- Use `BinarySensorEntity` and `BinarySensorEntityDescription`
- Set `is_on` property (returns bool)
- Add `device_class` (motion, door, window, connectivity, etc.)

### Switch

- Use `SwitchEntity`
- Implement `async_turn_on()` and `async_turn_off()`
- Set `is_on` property
- Add `async_toggle()` if custom logic needed

### Button

- Use `ButtonEntity` and `ButtonEntityDescription`
- Implement `async_press()` method
- Set `device_class` if applicable (restart, update, identify)

### Number

- Use `NumberEntity` and `NumberEntityDescription`
- Set `native_value`, `native_min_value`, `native_max_value`, `native_step`
- Implement `async_set_native_value(value: float)`
- Add `native_unit_of_measurement` and `mode` (auto, box, slider)

### Select

- Use `SelectEntity` and `SelectEntityDescription`
- Set `current_option` and `options` properties
- Implement `async_select_option(option: str)`

### Fan

- Use `FanEntity`
- Set `is_on`, `percentage`, `speed_count` properties
- Implement `async_turn_on()`, `async_turn_off()`, `async_set_percentage()`
- Add preset modes if applicable

## Common Patterns

### Device Grouping with device_info

```python
from homeassistant.helpers.device_registry import DeviceInfo

class IntegrationBlueprint[EntityName](
    IntegrationBlueprintEntity,
    [PlatformEntityClass],
):
    """Entity with device grouping."""

    def __init__(
        self,
        coordinator: IntegrationBlueprintDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_[entity_key]"

        # Group entities by device (RECOMMENDED for multi-device integrations)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="[Manufacturer]",
            model="[Model]",
            sw_version="[Version]",
        )
```

### Using Coordinator Data

```python
@property
def native_value(self) -> str | None:
    """Return sensor value from coordinator."""
    return self.coordinator.data.get("sensor_key")
```

### Availability Based on Coordinator

```python
@property
def available(self) -> bool:
    """Return if entity is available."""
    return super().available and self.coordinator.data.get("device_online", False)
```

### Entity with Action

```python
async def async_press(self) -> None:
    """Handle button press."""
    await self.coordinator.api_client.trigger_action()
    await self.coordinator.async_request_refresh()
```

## Validation Checklist

- [ ] Platform directory created with `__init__.py`
- [ ] Entity class inherits from both `IntegrationBlueprintEntity` and platform class
- [ ] `_attr_has_entity_name = True` set (MANDATORY for new integrations)
- [ ] Entity uses `translation_key` instead of hardcoded `name`
- [ ] Unique ID set correctly
- [ ] Platform added to `manifest.json`
- [ ] Translations added (en, de) matching translation_key
- [ ] Device info consistent if multiple entities per device
- [ ] Type hints complete
- [ ] Docstrings added
- [ ] `script/check` passes
- [ ] Entity appears in HA UI with correct name
- [ ] State updates correctly
- [ ] No errors in logs

## Integration Context

- **Domain:** `ha_integration_domain`
- **Class prefix:** `IntegrationBlueprint`
- **Base entity:** `IntegrationBlueprintEntity` in `entity/base.py`
- **Coordinator:** `IntegrationBlueprintDataUpdateCoordinator`

Follow patterns from existing platforms in the integration for consistency.

## Output

After implementation:

1. Run `script/check` to validate
2. Start Home Assistant with `script/develop`
3. Verify entity appears and functions correctly
4. Report results and any issues found
