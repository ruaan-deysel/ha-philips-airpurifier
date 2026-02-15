---
applyTo: "**/services.yaml"
---

# Service Actions Definition Instructions

**Applies to:** `services.yaml` files (legacy filename)

**Note:** This file defines service action schemas. The filename `services.yaml` is legacy from when these were called "services". Use "service actions" in code/documentation and "actions" for users.

## Schema Validation

**Schema:** `/schemas/yaml/services_schema.yaml`

This schema defines the complete structure for Home Assistant service definitions. Consult it when unsure about available fields or structure.

## Structure

```yaml
action_name:
  name: Human-Readable Name
  description: Clear description of what the action does.
  fields:
    parameter_name:
      name: Parameter Name
      description: What this parameter does.
      required: true
      example: "example_value"
      selector:
        text:
  target:
    entity:
      - domain: light
```

## Key Requirements

**Service action definition:**

- `name` - User-visible name (required)
- `description` - Clear explanation with Markdown support (required)
- `fields` - Parameter definitions (optional)
- `target` - Entity/device/area selector (optional)

**Field definition:**

- `name` - Field display name (required)
- `description` - Field explanation (required)
- `required` - Boolean, default false
- `example` - Example value (recommended)
- `default` - Default value (optional)
- `selector` - UI selector type (recommended)

## Selector Types

Common selectors for service action parameters:

- `text:` - String input
- `number:` - Numeric input with optional min/max/step
- `boolean:` - Toggle switch
- `select:` - Dropdown with options
- `entity:` - Entity picker with optional domain filter
- `device:` - Device picker with optional integration filter
- `time:` - Time picker
- `date:` - Date picker
- `duration:` - Duration input
- `color_rgb:` - RGB color picker
- `template:` - Template input

**Example with selector:**

```yaml
brightness:
  name: Brightness
  description: Brightness level (0-255)
  required: false
  example: 128
  selector:
    number:
      min: 0
      max: 255
      step: 1
      mode: slider
```

## Target Selector

Use `target:` to allow users to select entities, devices, or areas:

```yaml
turn_on:
  name: Turn On
  description: Turns on the device.
  target:
    entity:
      - domain: light
      - domain: switch
```

**Important:** If `target:` is defined, do NOT define `entity_id` as a field.

## Best Practices

- Always provide meaningful descriptions
- Include realistic examples for complex fields
- Use appropriate selectors for better UI
- Mark fields as required only when necessary
- Keep action names verb-based (e.g., `set_mode`, `reset_filter`)
- Validate against schema before committing

## Related Files

Service action implementations are in `custom_components/ha_integration_domain/service_actions/`.

## Validation

Service actions are validated by Home Assistant on integration load. Check logs for schema errors.

Reference: https://developers.home-assistant.io/docs/dev_101_services/
