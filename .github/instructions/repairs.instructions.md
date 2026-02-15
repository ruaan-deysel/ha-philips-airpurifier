---
applyTo: "custom_components/**/repairs.py"
---

# Repairs Instructions

**Official Documentation:**

- [Repairs Framework](https://developers.home-assistant.io/docs/core/platform/repairs)
- [Issue Registry](https://developers.home-assistant.io/docs/core/platform/repairs#issue-registry)

## Overview

Repair Flows guide users through fixing issues (expired credentials, deprecated settings, missing configuration, etc.).

**Key differences from Config Flow:**

- **Location**: `repairs.py` in integration root (NOT in `config_flow_handler/`)
- **Base class**: `homeassistant.components.repairs.RepairsFlow` (NOT `ConfigFlow`)
- **Trigger**: System creates issue → user clicks "Fix" → Repair Flow runs
- **Purpose**: Fix existing problems, not create new config entries

## Architecture

**Lifecycle:**

1. Integration detects issue → `async_create_issue()`
2. User clicks "Fix" → `async_create_fix_flow()` called with issue_id
3. Repair flow guides user through steps
4. Fix applied → `async_delete_issue()`

## Creating Issues

```python
from homeassistant.helpers import issue_registry as ir

ir.async_create_issue(
    hass,
    DOMAIN,
    "issue_id",
    is_fixable=True,  # Shows "Fix" button
    severity=ir.IssueSeverity.WARNING,  # WARNING, ERROR, CRITICAL
    translation_key="issue_id",
    translation_placeholders={"key": "value"},  # Optional
)
```

**When to create:**

- During `async_setup_entry()` - Config validity, API compatibility
- In coordinator updates - Deprecated endpoints, expired features
- On API responses - Device warnings, missing capabilities

## Repair Flow Implementation

**Required function in repairs.py:**

```python
async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create flow for issue_id."""
    return MyRepairFlow()
```

**Flow class structure:**

```python
from homeassistant.components.repairs import RepairsFlow

class MyRepairFlow(RepairsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Apply fix
            entry = self.hass.config_entries.async_get_entry(self.handler)
            # Update entry, reload if needed
            ir.async_delete_issue(self.hass, entry.domain, "issue_id")
            return self.async_create_entry(data={})

        return self.async_show_form(step_id="init")
```

## Data Entry Flow Patterns

**Show form:**

```python
return self.async_show_form(
    step_id="init",
    data_schema=vol.Schema({...}),
    errors={"base": "error_key"},
)
```

**Complete repair:**

```python
return self.async_create_entry(data={})  # Always empty dict
```

**Multi-step flow:**

```python
async def async_step_init(self, user_input=None):
    if user_input:
        self._data = user_input
        return await self.async_step_confirm()
    return self.async_show_form(step_id="init", data_schema=SCHEMA)
```

## Common Patterns

**Redirect to reauth:**

```python
async def async_step_init(self, user_input=None):
    if user_input:
        entry = self.hass.config_entries.async_get_entry(self.handler)
        ir.async_delete_issue(self.hass, entry.domain, "issue_id")
        entry.async_start_reauth(self.hass)
        return self.async_create_entry(data={})
    return self.async_show_form(step_id="init")
```

**With validation:**

```python
async def async_step_init(self, user_input=None):
    errors = {}
    if user_input:
        try:
            await validate(user_input)
            # Apply fix
            ir.async_delete_issue(self.hass, entry.domain, "issue_id")
            return self.async_create_entry(data={})
        except ValueError:
            errors["base"] = "invalid_input"
    return self.async_show_form(step_id="init", data_schema=SCHEMA, errors=errors)
```

## Translations

**Required keys:**

```json
{
  "issues": {
    "issue_id": {
      "title": "Issue title",
      "description": "Description with {placeholder}",
      "fix_flow": {
        "step": {
          "init": {
            "title": "Repair step title",
            "description": "Instructions"
          }
        }
      }
    }
  }
}
```

## Rules

**MUST:**

- Place `repairs.py` in integration root (NOT in `config_flow_handler/`)
- Implement `async_create_fix_flow()` function returning `RepairsFlow` subclass
- Delete issue after successful repair: `ir.async_delete_issue()`
- Set `is_fixable=True` only if repair flow exists
- Provide translations for all text (title, description, fix_flow steps)
- Validate user input before applying fixes
- Use appropriate severity: WARNING (non-critical) / ERROR (important) / CRITICAL (urgent)

**SHOULD:**

- Keep repair steps simple (1-2 steps maximum)
- Use existing patterns (reauth, reconfigure) when applicable
- Reload entry after config changes: `await hass.config_entries.async_reload(entry.entry_id)`

**NEVER:**

- Put repair flows in `config_flow_handler/` (separate system)
- Leave issues after repair completes (always delete)
- Use repair flows for normal config changes (use reconfigure instead)
- Create issues without translations
- Skip validation of user input
