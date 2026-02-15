---
applyTo: "custom_components/**/alarm_control_panel/**/*.py, custom_components/**/binary_sensor/**/*.py, custom_components/**/button/**/*.py, custom_components/**/camera/**/*.py, custom_components/**/climate/**/*.py, custom_components/**/cover/**/*.py, custom_components/**/fan/**/*.py, custom_components/**/humidifier/**/*.py, custom_components/**/light/**/*.py, custom_components/**/lock/**/*.py, custom_components/**/number/**/*.py, custom_components/**/select/**/*.py, custom_components/**/sensor/**/*.py, custom_components/**/siren/**/*.py, custom_components/**/switch/**/*.py, custom_components/**/vacuum/**/*.py, custom_components/**/water_heater/**/*.py, custom_components/**/entity/**/*.py, custom_components/**/entity_utils/**/*.py"
---

# Entity Platform Instructions

**Applies to:** All entity platform implementations (sensor, binary_sensor, switch, etc.), entity base classes, and entity utilities

## Shared Infrastructure

- **`entity/`** - Base entity classes (inherit `IntegrationBlueprintEntity` from `entity/base.py`)
- **`entity_utils/`** - Shared utilities (device info, state helpers) used by 3+ entity classes
- **`coordinator/`** - Data fetching (entities never call API directly)

## Base Entity Inheritance

**MUST inherit from:** `(PlatformEntity, IntegrationBlueprintEntity)` - order matters for MRO

**Base class provides:** Coordinator integration, device info, unique ID (`{entry_id}_{description.key}`), attribution, entity naming

**You implement:** Platform-specific properties/methods (`native_value`, `is_on`, `async_press`, etc.)

**Imports pattern:** `from homeassistant.components.PLATFORM import PlatformEntity, PlatformEntityDescription` + `from ..entity import IntegrationBlueprintEntity`

**Constructor:** Call `super().__init__(coordinator, entity_description)` - base handles setup

## Entity Descriptions

**Define at module level:** `ENTITY_DESCRIPTIONS: tuple[PlatformEntityDescription, ...]`

**Required fields:**

- `key` - Used in unique_id, must match coordinator data key
- `name` - Display name
- Platform-specific: `device_class`, `state_class`, `unit_of_measurement`, `options`, etc.

**Entity Categories:**

- `None` - Primary functionality (prominent display)
- `EntityCategory.DIAGNOSTIC` - Diagnostic info (uptime, signal, errors)
- `EntityCategory.CONFIG` - Configuration settings

## Platform Setup

**Pattern:** `async_setup_entry()` creates entities from descriptions

- Import entity classes + DESCRIPTIONS from submodules
- Generator: `async_add_entities(EntityClass(entry.runtime_data.coordinator, desc) for desc in DESCRIPTIONS)`
- Combine multiple entity types in one platform
- Access coordinator: `entry.runtime_data.coordinator`

## Coordinator Data Access

**MUST use coordinator only:** `self.coordinator.data.get(self.entity_description.key)`

**NEVER call API directly:** No `self.coordinator.client` or `await api_call()` in entities

**Handle missing data:** Override `available` property to check `self.entity_description.key in self.coordinator.data`

## File Organization

**Group related entities:** `primary_entities.py`, `diagnostic.py`, `configuration.py`

**Split when:** Complex entity >100 lines → one file per entity class

## Custom State Attributes

**Use `extra_state_attributes` property** returning dict for supplemental data

**NEVER override `state_attributes`** - reserved for base platform components (brightness, color, etc.)

## Disabled By Default

**Set property:** `entity_registry_enabled_default = False` for advanced/diagnostic entities

**Config-controlled visibility:** Conditionally add/remove entities in setup, NOT via `disabled_by`

## Platform-Required Methods

**Must implement per platform:**

- Sensors: `native_value`, `native_unit_of_measurement`
- Binary Sensors: `is_on`
- Switches: `is_on`, `turn_on()`, `turn_off()`
- Buttons: `async_press()`
- Numbers: `native_value`, `async_set_native_value()`
- Selects: `current_option`, `async_select_option()`

**Reference:** [Entity Developer Docs](https://developers.home-assistant.io/docs/core/entity)

## Entity Utilities

**Add to `entity_utils/` when:**

- Used by 3+ entity classes
- Complex logic benefiting from testing
- Device info customization, state formatting

**Import pattern:** `from ..entity_utils.module import function`

## Type Hints

**Avoid circular imports:** Use `TYPE_CHECKING` block for coordinator imports

```python
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..coordinator import IntegrationBlueprintDataUpdateCoordinator
```

## PARALLEL_UPDATES

**Import from integration:** `from ..const import PARALLEL_UPDATES` in platform `__init__.py`

**Override to 1** only if platform requires sequential updates

## Dynamic Entity Creation

**Filter by available data:** Check `desc.key in coordinator.data` before creating entities

**Conditional features:** Use `self.coordinator.data.get("capability")` to determine `supported_features`

## Common Pitfalls

**❌ Don't:**

- Call API directly from entities
- Create entities without EntityDescription
- Override base class methods unnecessarily
- Hardcode unique IDs
- Log in property getters (called frequently)
- Duplicate constants (use `homeassistant.const` or integration `const.py`)

**✅ Do:**

- Use coordinator data exclusively
- Define EntityDescriptions with all metadata
- Generate unique IDs from `entry_id + description.key`
- Log only in async methods or `__init__`
- Consult HA docs for platform-specific patterns
- Use `entity_utils/` for shared logic
