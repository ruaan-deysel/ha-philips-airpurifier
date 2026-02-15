---
agent: "agent"
tools: ["search/codebase", "edit", "search", "runCommands"]
description: "Add a new configuration option to initial setup or options flow with validation"
---

# Add Config Option

Your goal is to add a new configuration option to the config flow (setup or options flow).

If not provided, ask for:

- Option name and purpose
- Data type (string, int, float, bool, selector)
- Where to add (initial setup or options flow)
- Default value (if applicable)
- Validation requirements

## Requirements

**Schema Definition:**

- Add to appropriate schema in `config_flow_handler/schemas/`
- Use voluptuous validators from `homeassistant.helpers.config_validation as cv`
- Use selectors for better UI (BooleanSelector, NumberSelector, etc.)
- Set appropriate default values with `vol.Optional()`

**Config Flow Logic:**

- Update flow step in `config_flow_handler/config_flow.py` or `options_flow.py`
- Handle new field in `async_step_[step_name]()` method
- Validate input if needed (add validator to `validators/` if complex)
- Store value in `config_entry.data` or `config_entry.options`

**Using the Option:**

- Access via `entry.data[CONF_OPTION_KEY]` or `entry.options.get(CONF_OPTION_KEY)`
- Pass to coordinator if needed for data fetching
- Update entity behavior based on option value
- Handle option changes via `async_update_entry()` listener

**Translations:**

- Add label and description to `translations/en.json` under `config.step.[step_name].data`
- Add helper text if needed under `data_description`
- Add error messages if validation fails under `error.[error_key]`
- Update `translations/de.json` with German translations

**Constants:**

- Add constant to `const.py` if reused across files
- Use descriptive names: `CONF_[OPTION_NAME]`
- Document purpose with inline comment

**Migration (if changing existing config):**

- Increment `VERSION` in config flow handler
- Implement `async_migrate_entry()` if needed
- Handle both old and new format for backwards compatibility

**Code Quality:**

- Follow existing config flow patterns
- Use proper selector types for best UX
- Add proper type hints
- Run `script/check` to validate before completion

**Related Files:**

- Schemas: `config_flow_handler/schemas/`
- Flow Handler: `config_flow_handler/config_flow.py` or `options_flow.py`
- Validators: `config_flow_handler/validators/`
- Constants: `const.py`
- Translations: `translations/*.json`

**DO NOT create tests unless explicitly requested.**
