---
applyTo: "**/configuration.yaml"
---

# Home Assistant Configuration Instructions

**Applies to:** `configuration.yaml` files

## Schema

**Schema:** `/schemas/yaml/configuration_schema.yaml`

Consult this schema for available configuration options and structure.

## Minimal Structure

For development and testing, keep configuration minimal:

```yaml
# Load default configuration
default_config:

# Enable your integration
ha_integration_domain:

# Logging for development
logger:
  default: info
  logs:
    custom_components.ha_integration_domain: debug
```

## Modern Syntax Only

**Always use modern automation/script syntax:**

```yaml
# ✅ Correct (modern)
automation:
  - alias: "Motion detected"
    trigger:
      - trigger: state
        entity_id: binary_sensor.motion
        to: "on"
    action:
      - action: light.turn_on
        target:
          entity_id: light.hallway
```

**Never use legacy platform-based syntax:**

```yaml
# ❌ Wrong (legacy)
automation:
  - alias: "Motion detected"
    trigger:
      platform: state # Don't use this!
      entity_id: binary_sensor.motion
      to: "on"
```

## Service Calls

**Use `action:` key (not deprecated `service:`):**

```yaml
action:
  - action: light.turn_on # Modern syntax
    target:
      entity_id: light.living_room
    data:
      brightness: 255
```

## Logger Configuration

**Adjust log levels for debugging:**

```yaml
logger:
  default: warning
  logs:
    # Your integration - verbose
    custom_components.ha_integration_domain: debug

    # Reduce noise from other components
    homeassistant.components.http: warning
    homeassistant.components.websocket_api: error

    # Keep important helpers visible
    homeassistant.helpers.entity_registry: info
    homeassistant.helpers.device_registry: info
    homeassistant.config_entries: info
```

## Common Patterns

**Conditions:**

```yaml
condition:
  - condition: state
    entity_id: input_boolean.enable_automation
    state: "on"
  - condition: time
    after: "07:00:00"
    before: "23:00:00"
```

**Templates:**

```yaml
action:
  - action: notify.notify
    data:
      message: >
        Temperature is {{ states('sensor.temperature') }}°C
```

**Delays:**

```yaml
action:
  - action: light.turn_on
    target:
      entity_id: light.hallway
  - delay:
      seconds: 30
  - action: light.turn_off
    target:
      entity_id: light.hallway
```

## Validation

Configuration is validated on Home Assistant startup:

```bash
script/develop  # Start HA and check logs for validation errors
```

Check terminal output and `config/home-assistant.log` for schema errors.

## Staying Current

**Home Assistant configuration syntax evolves:**

- Check [automation documentation](https://www.home-assistant.io/docs/automation/)
- Review [condition documentation](https://www.home-assistant.io/docs/scripts/conditions/)
- Search for examples: `site:www.home-assistant.io automation [trigger type]`
- Don't use deprecated syntax even if it still works
