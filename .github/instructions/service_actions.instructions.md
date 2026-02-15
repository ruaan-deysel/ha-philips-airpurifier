---
applyTo: "custom_components/**/service_actions/**/*.py"
---

# Service Actions Instructions

**Applies to:** Service action implementation files

**Reference:** [Home Assistant Service Actions Documentation](https://developers.home-assistant.io/docs/dev_101_services/)

## Critical Rules

**Registration location (Silver Quality Scale requirement):**

- ✅ Register service actions in `async_setup()` (component level)
- ❌ Never register in `async_setup_entry()` (per config entry)
- Check `hass.services.has_service(DOMAIN, "action_name")` before registering
  **Service naming:**

- Format: `<integration_domain>.<action_name>`
- Always use integration DOMAIN, never platform domain (e.g., `sensor`, `switch`)

**Implementation structure:**

- Call `await async_setup_services(hass)` from `async_setup()` in `__init__.py`
- Implement handlers in `service_actions/__init__.py`
- Handlers iterate over `hass.data[DOMAIN]` to access config entries

## Service Schema

Use voluptuous with `homeassistant.helpers.config_validation` for parameter validation:

```python
import voluptuous as vol
from homeassistant.helpers import config_validation as cv

SERVICE_SCHEMA = vol.Schema({
    vol.Required("device_id"): cv.string,
    vol.Optional("force", default=False): cv.boolean,
})
```

## Exception Handling

**Use appropriate exceptions:**

- `ServiceValidationError` - User provided invalid data (no stack trace in logs except at debug level)
- `HomeAssistantError` - Device/communication errors (full stack trace in logs)

Both exceptions support translation keys for localization.

## Target Field

Use modern `target` field in `services.yaml` instead of deprecated `entity_id`:

```yaml
reset_filter:
  target:
    entity:
      domain: sensor
```

## Response Data

Services can return JSON-serializable data (`homeassistant.util.json.JsonObjectType`) for use in automations:

**Critical requirements:**

- Response MUST be a `dict`
- **datetime objects MUST use `.isoformat()`** - Template engine cannot handle raw datetime
- Raise exceptions for errors, never return error codes in response data

**SupportsResponse modes:**

- `SupportsResponse.OPTIONAL` - Returns data only if `call.return_response` is True
- `SupportsResponse.ONLY` - Always returns data, performs no action

Example with datetime conversion:

```python
from homeassistant.core import SupportsResponse

async def search_items(call: ServiceCall) -> ServiceResponse:
    items = await client.search(call.data["start"], call.data["end"])
    return {
        "items": [
            {
                "summary": item["summary"],
                "timestamp": item["timestamp"].isoformat(),  # ✅ Convert datetime!
            }
            for item in items
        ],
    }

hass.services.async_register(
    DOMAIN, "search", search_items,
    supports_response=SupportsResponse.ONLY,
)
```

## Entity Service Actions

For services targeting entities, use `async_register_platform_entity_service`:

```python
from homeassistant.helpers import service

service.async_register_platform_entity_service(
    hass,
    DOMAIN,  # Integration domain, NOT platform domain!
    "set_timer",
    entity_domain="media_player",
    schema={vol.Required("sleep_time"): cv.time_period},
    func="set_sleep_timer",  # Method name on entity class
)
```

Alternative with custom handler function:

```python
async def custom_handler(entity, service_call):
    """Custom handler logic."""
    await entity.set_sleep_timer(service_call.data['sleep_time'])

service.async_register_platform_entity_service(
    hass, DOMAIN, "set_timer",
    entity_domain="media_player",
    schema={vol.Required("sleep_time"): cv.time_period},
    func=custom_handler,  # Function instead of method name
)
```

## Service Icons

Define in `icons.json`:

```json
{
  "services": {
    "turn_on": { "service": "mdi:lightbulb-on" },
    "start_brewing": {
      "service": "mdi:flask",
      "sections": { "advanced_options": "mdi:test-tube" }
    }
  }
}
```

## Permissions

Verify authentication when required:

```python
async def handle_service(call: ServiceCall) -> None:
    if not call.context.user_id:
        raise Unauthorized("Service requires authentication")
```
