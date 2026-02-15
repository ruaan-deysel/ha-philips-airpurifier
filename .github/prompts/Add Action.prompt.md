---
agent: "agent"
tools: ["search/codebase", "edit", "search"]
description: "Add a new service action to the integration with proper schema and registration"
---

# Add Service Action

Your goal is to add a new **service action** to this Home Assistant integration that users can call from automations, scripts, or the UI.

**Terminology:**

- **Developer/Code:** "service action" (e.g., function names, comments, documentation)
- **User-facing:** "action" only (e.g., in UI, translations under `actions` key)
- **Legacy:** `services.yaml`, `hass.services.async_register()`, `ServiceCall` class (internal API)

If not provided, ask for:

- Service action name and purpose
- Parameters required (with types and validation)
- What the service action does (API call, state change, etc.)
- Response data (if any)
- Target: device, entity, or integration-wide

## Implementation Steps

### 1. Define Service Action in `services.yaml`

**File:** `custom_components/ha_integration_domain/services.yaml`

**Note:** `services.yaml` is a legacy filename from when these were called "services". We now call them "service actions" in code and "actions" for users.

**CRITICAL:** Per [HA documentation](https://developers.home-assistant.io/docs/dev_101_services), action names and descriptions must be defined in translation files under the `actions` key (not `services`), NOT in `services.yaml`. The `services.yaml` file only defines the schema.

Add service action definition:

```yaml
[action_name]:
  # Use translation_key to reference translations
  translation_key: [action_name]

  # For device or entity-targeted service actions
  target:
    entity:
      domain: [platform] # sensor, switch, etc.
      # OR
      integration: ha_integration_domain

  # Service action parameters - organize with sections for better UX
  fields:
    # SECTION: Basic parameters
    [parameter_name]:
      translation_key: [parameter_name]
      required: true
      example: "[example value]"
      selector:
        text:
          # OR number:, boolean:, select:, etc.

    [another_parameter]:
      translation_key: [another_parameter]
      required: false
      default: [default value]
      selector:
        number:
          min: 0
          max: 100
          mode: slider

    # Advanced section (appears collapsed by default)
    advanced:
      collapsed: true
      fields:
        [advanced_parameter]:
          translation_key: [advanced_parameter]
          required: false
          selector:
            boolean:
```

**With sections for better organization:**

```yaml
[action_name]:
  # No name/description - translations only!

  target:
    entity:
      integration: ha_integration_domain

  fields:
    # Basic section - always visible
    basic:
      # Section names come from translations: actions.[action_name].sections.basic.name
      collapsed: false
      icon: mdi:cog-outline
      fields:
        [parameter_name]:
          # Field names come from translations: actions.[action_name].fields.[parameter_name].name
          required: true
          selector:
            text:

    # Advanced section - collapsed by default
    advanced:
      # Section names come from translations: actions.[action_name].sections.advanced.name
      collapsed: true
      icon: mdi:tune-vertical
      fields:
        [advanced_parameter]:
          # Field names come from translations: actions.[action_name].fields.[advanced_parameter].name
          required: false
          selector:
            boolean:
```

**Special case: `translation_key` in selectors**

Use `translation_key` only for `select` selectors with dynamic options:

```yaml
fields:
  preset_mode:
    selector:
      select:
        translation_key: "fan_speed" # Only needed here!
        options:
          - "off"
          - "low"
          - "medium"
          - "high"
```

This allows translating the option labels via `selector.[translation_key].options.[option_value]` in translations.

**Best Practices for Schema Definition:**

1. **Always add icons** - Provide meaningful icons for sections AND individual fields where applicable
   - Sections: `icon: mdi:cog-outline` (basic), `icon: mdi:tune-vertical` (advanced)
   - Fields: Consider field type and purpose (e.g., `mdi:timer` for duration, `mdi:thermometer` for temperature)

2. **Always add descriptions** - Provide descriptions wherever the schema allows (sections, fields)
   - Makes the UI more user-friendly
   - Helps users understand what each parameter does

3. **Markdown support** - Be aware of where markdown is supported:
   - ✅ **Service action descriptions** - Markdown is supported
   - ✅ **Section descriptions** - Markdown is supported
   - ❌ **Field names** - Plain text only (keep short, 2-4 words)
   - ✅ **Field descriptions** - Markdown is supported (can use `**bold**`, `[links](url)`, etc.)
   - Use markdown for formatting longer descriptions, links to documentation, etc.

4. **Choose text appropriately**:
   - Names: Short, concise labels (2-4 words)
   - Descriptions: Detailed explanations with examples, constraints, or links
   - Use field descriptions to explain valid ranges, formats, or special behavior

**Reference:** [Home Assistant Services Documentation](https://developers.home-assistant.io/docs/dev_101_services)

### 2. Create Service Action Handler

**Directory naming:** Use `service_actions/` for new code (preferred) or `actions/` (acceptable). Be consistent within your integration.

**Option A: Simple service action in `service_actions/` directory**

Create `custom_components/ha_integration_domain/service_actions/[action_name].py`:

```python
"""[Action name] service action for Integration Blueprint."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv

from ..const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Action parameter constants
ATTR_PARAMETER = "parameter_name"

# Action schema for validation
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PARAMETER): cv.string,
        # Add more parameters with validators
        vol.Optional("optional_param", default=100): cv.positive_int,
    }
)


async def async_setup_service_action(hass: HomeAssistant) -> None:
    """Set up the [action_name] service action."""

    async def async_handle_service_action(call: ServiceCall) -> None:
        """Handle the service action call."""
        # Extract parameters
        parameter_value = call.data[ATTR_PARAMETER]
        optional_value = call.data.get("optional_param", 100)

        _LOGGER.debug(
            "Service action [action_name] called with: %s=%s",
            ATTR_PARAMETER,
            parameter_value,
        )

        # Get coordinator or API client from hass.data
        # For each config entry that this service action applies to:
        for entry_id, entry_data in hass.data[DOMAIN].items():
            coordinator = entry_data  # Or entry_data["coordinator"]

            try:
                # Perform the action action
                await coordinator.api_client.do_something(parameter_value)

                # Optionally refresh data
                await coordinator.async_request_refresh()

            except Exception as err:
                _LOGGER.error(
                    "Error executing service action [action_name]: %s",
                    err,
                )
                # Consider raising HomeAssistantError for user visibility

    # Register the service action (legacy API uses hass.services)
    hass.services.async_register(  # Legacy API: hass.services, not hass.actions
        DOMAIN,
        "[action_name]",
        async_handle_service_action,
        schema=SERVICE_SCHEMA,
    )
```

**Option B: Entity-targeted service action**

```python
async def async_handle_entity_service_action(entity, call: ServiceCall) -> None:
    """Handle service action call for specific entity."""
    parameter_value = call.data[ATTR_PARAMETER]

    # Entity has access to coordinator
    await entity.coordinator.api_client.do_something(
        entity.device_id,
        parameter_value,
    )
    await entity.coordinator.async_request_refresh()


async def async_setup_service_action(hass: HomeAssistant) -> None:
    """Set up entity-targeted service action."""
    platform = entity_platform.async_get_current_platform()

    platform.async_register_entity_service(  # Note: uses 'service', not 'action'
        "[action_name]",
        SERVICE_SCHEMA,
        async_handle_entity_service_action,
    )
```

### 3. Register Service Action in `__init__.py`

**File:** `custom_components/ha_integration_domain/__init__.py`

**CRITICAL:** Service actions must register in `async_setup` or `setup`, NOT in `async_setup_entry`!

Service actions are integration-wide, not per config entry.

```python
from .service_actions.[action_name] import async_setup_service_action as async_setup_[action_name]_service_action

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    # Register integration-wide service actions (only once for entire integration)
    await async_setup_[action_name]_service_action(hass)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from a config entry."""
    # ... existing setup code ...
    # DO NOT register service actions here!

    return True
```

**For platform-specific service actions (entity service actions):**

Register in platform `__init__.py` during `async_setup_entry`:

```python
# In sensor/__init__.py or other platform
from homeassistant.helpers import entity_platform

async def async_setup_entry(...) -> None:
    """Set up platform."""
    # ... add entities ...

    # Register entity service actions
    platform = entity_platform.async_get_current_platform()

    from ..service_actions.[action_name] import (
        SERVICE_SCHEMA,
        async_handle_entity_service_action,
    )

    platform.async_register_entity_service(  # Uses 'service', not 'action'
        "[action_name]",
        SERVICE_SCHEMA,
        async_handle_entity_service_action,
    )
```

### 4. Add Service Action Constants

**File:** `custom_components/ha_integration_domain/const.py`

```python
# Service action names (use SERVICE_ prefix for legacy compatibility)
SERVICE_[SERVICE_NAME] = "[action_name]"

# Service action parameters
ATTR_[PARAMETER_NAME] = "[parameter_name]"
```

### 5. Add Translations

**CRITICAL:** All action names, descriptions, and field labels MUST be in translation files under the `services` key. Per [HA documentation](https://developers.home-assistant.io/docs/internationalization/core#service-actions), `services.yaml` contains only the schema, not user-facing text. Note: The key is `services` (legacy) even though they are called "service actions" in documentation and "actions" in the UI.

**`translations/en.json`:**

```json
{
  "services": {
    "[action_name]": {
      "name": "[Action Name]",
      "description": "[Detailed description with **markdown** support. Can include [links](https://example.com) and formatting.]",
      "sections": {
        "basic": {
          "name": "Basic Settings",
          "description": "Essential parameters. You can use **markdown** here to highlight important information."
        },
        "advanced": {
          "name": "Advanced Settings",
          "description": "Optional advanced configuration. See [documentation](https://example.com) for details."
        }
      },
      "fields": {
        "[parameter_name]": {
          "name": "Parameter Name",
          "description": "Detailed explanation of what this parameter does. **Supports markdown**, can include ranges like `0-100`, examples, or [links](https://example.com)."
        },
        "[another_parameter]": {
          "name": "Another Parameter",
          "description": "Another detailed description. Explain valid values, constraints, and behavior."
        },
        "[advanced_parameter]": {
          "name": "Advanced Parameter",
          "description": "Advanced parameter description with technical details."
        }
      }
    }
  }
}
```

**`translations/de.json`:**

```json
{
  "services": {
    "[action_name]": {
      "name": "[German Action Name]",
      "description": "[Detaillierte Beschreibung mit **Markdown**-Unterstützung. Kann [Links](https://example.com) und Formatierung enthalten.]",
      "sections": {
        "basic": {
          "name": "Grundeinstellungen",
          "description": "Wesentliche Parameter. Sie können hier **Markdown** verwenden, um wichtige Informationen hervorzuheben."
        },
        "advanced": {
          "name": "Erweiterte Einstellungen",
          "description": "Optionale erweiterte Konfiguration. Siehe [Dokumentation](https://example.com) für Details."
        }
      },
      "fields": {
        "[parameter_name]": {
          "name": "Parametername",
          "description": "Detaillierte Erklärung, was dieser Parameter tut. **Unterstützt Markdown**, kann Bereiche wie `0-100`, Beispiele oder [Links](https://example.com) enthalten."
        },
        "[another_parameter]": {
          "name": "Anderer Parameter",
          "description": "Eine weitere detaillierte Beschreibung. Erklären Sie gültige Werte, Einschränkungen und Verhalten."
        },
        "[advanced_parameter]": {
          "name": "Erweiterter Parameter",
          "description": "Beschreibung des erweiterten Parameters mit technischen Details."
        }
      }
    }
  }
}
```

**Translation structure:**

- `services.[action_name].name` - Action display name (required)
- `services.[action_name].description` - Action description (required)
- `services.[action_name].sections.[section_key].name` - Section heading (if using sections)
- `services.[action_name].sections.[section_key].description` - Section description (optional)
- `services.[action_name].fields.[parameter_name].name` - Field label (required)
- `services.[action_name].fields.[parameter_name].description` - Field description (required)

**When `translation_key` is needed:**

Only use `translation_key` in `services.yaml` for **select selectors** with dynamic options:

```json
{
  "selector": {
    "fan_speed": {
      "options": {
        "off": "Off",
        "low": "Low",
        "medium": "Medium",
        "high": "High"
      }
    }
  }
}
```

This maps to `selector: select: translation_key: "fan_speed"` in `services.yaml`.

### 6. Add Response Data (Optional)

If service action returns data:

```python
from homeassistant.core import SupportsResponse

# In service action handler
async def async_handle_service_action(call: ServiceCall) -> dict[str, Any]:
    """Handle service action and return data."""
    result = await do_something()

    # Return response data
    return {
        "success": True,
        "value": result,
    }

# When registering
hass.services.async_register(  # Legacy API: hass.services
    DOMAIN,
    "[action_name]",
    async_handle_service_action,
    schema=SERVICE_SCHEMA,
    supports_response=SupportsResponse.OPTIONAL,  # OPTIONAL: may return data | ONLY: always returns data
)
```

**SupportsResponse values:**

- `NONE` (default): Service action does not return data
- `OPTIONAL`: Service action may conditionally return data
- `ONLY`: Service action always returns data

### 7. Field Filtering by supported_features (Advanced)

For entity actions with dynamic fields based on capabilities:

```yaml
# In services.yaml
[action_name]:
  target:
    entity:
      domain: fan
  fields:
    preset_mode:
      # Only show if entity has PRESET_MODE feature
      filter:
        supported_features:
          - fan.FanEntityFeature.PRESET_MODE
      selector:
        select:
          options: [] # Entity provides options dynamically
```

### 8. Action Icons (2025 Best Practice)

**CRITICAL:** Define icons for actions, sections, AND fields for better UX.

**`icons.json`:**

```json
{
  "actions": {
    "[action_name]": {
      "service": "mdi:icon-name",
      "sections": {
        "basic": "mdi:cog-outline",
        "advanced": "mdi:tune-vertical"
      }
    }
  }
}
```

**Icon selection tips:**

- Choose meaningful, recognizable icons from [Material Design Icons](https://pictogrammers.com/library/mdi/)
- Actions: Use action-specific icons (e.g., `mdi:restart`, `mdi:update`, `mdi:cog-play`)
- Sections: `mdi:cog-outline` (basic/general), `mdi:tune-vertical` (advanced/fine-tuning)
- Fields: Consider in `services.yaml` if field needs visual distinction (e.g., `mdi:timer`, `mdi:thermometer`)

## Service Action Types

### Integration-Wide Service Action

- Applies to all devices/entries
- Example: Refresh all devices, reset cache

### Device-Targeted Service Action

- Uses `target.device` selector
- Applies to specific device
- Example: Reboot device, update firmware

### Entity-Targeted Service Action

- Uses `target.entity` selector
- Applies to specific entity
- Example: Set mode, calibrate sensor

## Validation Patterns

### Common Validators

```python
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

SERVICE_SCHEMA = vol.Schema({
    vol.Required("string_param"): cv.string,
    vol.Required("int_param"): cv.positive_int,
    vol.Required("float_param"): vol.Range(min=0.0, max=100.0),
    vol.Required("bool_param"): cv.boolean,
    vol.Required("time_param"): cv.time,
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("enum_param"): vol.In(["option1", "option2", "option3"]),
    vol.Optional("optional_param", default="default"): cv.string,
})
```

### Custom Validator

```python
def validate_custom(value: Any) -> Any:
    """Validate custom parameter."""
    if not meets_criteria(value):
        raise vol.Invalid("Parameter does not meet criteria")
    return value

SERVICE_SCHEMA = vol.Schema({
    vol.Required("custom"): validate_custom,
})
```

## Error Handling

```python
from homeassistant.exceptions import HomeAssistantError

async def async_handle_service_action(call: ServiceCall) -> None:
    """Handle service action with error handling."""
    try:
        result = await do_something(call.data)

    except ConnectionError as err:
        raise HomeAssistantError(
            f"Failed to connect to device: {err}"
        ) from err

    except ValueError as err:
        raise HomeAssistantError(
            f"Invalid parameter value: {err}"
        ) from err
```

## Validation Checklist

- [ ] Service action defined in `services.yaml` with proper schema (no `name`/`description` fields!)
- [ ] **CRITICAL:** NO static text in `services.yaml` - all user-facing text in translations under `services` key
- [ ] `translation_key` only used for select selectors with dynamic options
- [ ] Sections used for parameter organization (basic/advanced) if applicable
- [ ] **Icons defined** in `icons.json` under `services` key for action, sections, and fields
- [ ] **Descriptions provided** in translations under `services` key for action, sections, and fields
- [ ] **Markdown used appropriately** - formatted descriptions where supported, plain text for names
- [ ] Service action handler implemented with error handling
- [ ] Service action registered in `async_setup` (integration-wide) using `hass.services.async_register()`
- [ ] Entity service actions registered in platform using `platform.async_register_entity_service()`
- [ ] **CRITICAL:** Integration service actions NOT registered in `async_setup_entry`
- [ ] Constants added to `const.py` with `SERVICE_` prefix
- [ ] Translations added (en, de) under `services` key with all required fields
- [ ] SupportsResponse imported if service action returns data
- [ ] Type hints complete (use `ServiceCall`, not `ActionCall`)
- [ ] Docstrings added (refer to "service action" in comments)
- [ ] `script/check` passes
- [ ] Service action appears in HA Developer Tools > Actions tab
- [ ] Service action UI shows icons and descriptions correctly
- [ ] Service action executes correctly
- [ ] Error cases handled appropriately

## Testing

1. Start Home Assistant: `script/develop`
2. Go to Developer Tools > Actions tab (user-facing: "Actions", not "Services")
3. Find service action: `ha_integration_domain.[action_name]`
4. Test with valid parameters
5. Test with invalid parameters (should show validation errors)
6. Test with edge cases
7. Check logs for errors
8. Verify icons display correctly
9. Verify descriptions are helpful and formatted

## Additional Resources

- [Home Assistant Services Documentation](https://developers.home-assistant.io/docs/dev_101_services) - Official developer guide
- [Service Translations](https://developers.home-assistant.io/docs/internationalization/core/#service-actions) - Translation key patterns (use `services` key)
- [Service Sections](https://developers.home-assistant.io/docs/dev_101_services#service-sections) - Organizing parameters with sections

## Integration Context

- **Domain:** `ha_integration_domain`
- **Service actions directory:** `custom_components/ha_integration_domain/service_actions/` (preferred) or `actions/`
- **Service actions definition:** `custom_components/ha_integration_domain/services.yaml` (legacy filename)
- **Icons:** `custom_components/ha_integration_domain/icons.json` under `services` key (legacy)
- **Translations:** `custom_components/ha_integration_domain/translations/*.json` under `services` key (legacy)

Follow patterns from existing service actions in the integration.

## Output

After implementation:

1. Run `script/check` to validate
2. Start Home Assistant and test service action
3. Verify service action appears in UI Actions tab with proper description
4. Verify translations show "action" terminology for users (not "service action")
5. Test all parameters and edge cases
6. Report results
