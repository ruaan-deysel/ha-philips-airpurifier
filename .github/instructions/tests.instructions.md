---
applyTo: "tests/**/*.py"
---

# Test Instructions

**Applies to:** `tests/` directory

**Official documentation:** [Home Assistant Testing](https://developers.home-assistant.io/docs/development_testing)

## Test Structure

**Mirror integration structure:**

```text
tests/
  conftest.py          # Shared fixtures
  test_init.py         # Integration setup
  test_config_flow.py  # Config flow
  sensor/test_air_quality.py
  binary_sensor/test_connectivity.py
```

**File organization:**

- One test file per module/feature
- Named `test_*.py`
- Use fixtures from `conftest.py`

## Pytest Markers

**Categorize tests:**

- `@pytest.mark.unit` - Fast, isolated (no external dependencies)
- `@pytest.mark.integration` - With coordinator, time service, etc.

## Fixtures

**Standard fixtures (define in `conftest.py`):**

- `hass` - Mock Home Assistant instance
- `config_entry` - `MockConfigEntry` from `pytest-homeassistant-custom-component`
- `coordinator` - IntegrationBlueprintDataUpdateCoordinator
- `mock_api_client` - Mocked API client

**Define fixtures in `conftest.py`:** Use `MockConfigEntry` from `pytest-homeassistant-custom-component`

**Use [Syrupy](https://github.com/tophat/syrupy) for large outputs:**

- Snapshots for: Entity states, registry entries, diagnostics, config flow results
- Update: `script/test --snapshot-update`, commit `.ambr` files
- Complement functional tests, don't replace them
- Pattern: `assert hass.states.get("sensor.x") == snapshot`

## Core Interface Testing

**Rule: Test through core interfaces (`hass.states`, `hass.services`), not integration internals.**

✅ **Correct:** `hass.states.get("sensor.x")`, `await hass.services.async_call(DOMAIN, "action")`

❌ **Wrong:** Direct entity instantiation, accessing entity properties directly

## Registry Testing

**Registry Testing:**

- Device: `dr.async_get(hass).async_get_device(identifiers={(DOMAIN, id)})` - Verify manufacturer, model, identifiers
- Entity: `er.async_get(hass).async_get("sensor.x")` - Verify unique_id, disabled state
- Lifecycle: Test `async_setup()` → `LOADED`, `async_unload()` → `NOT_LOADED`

## Mocking

**Mocking:**

✅ **Mock:** External APIs, network calls, time-dependent operations

- Use `patch.object()` for success cases, `side_effect` for errors
- Pattern: `with patch.object(client, "method", return_value=data):`

❌ **Don't mock:** Home Assistant internals, your own integration code

## Entity Testing

**Entity Testing:**

Pattern: Setup entry → `async_block_till_done()` → `hass.states.get("entity_id")` → assert state/attributes

## Config Flow Testing

**Config Flow Testing:**

Pattern: `hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"}, data={...})`

Verify: `result["type"]` (form/create_entry/abort), `result["step_id"]`, `result["errors"]`

## Test Commands

```bash
script/test                    # All tests
script/test -v                 # Verbose
script/test --cov-html         # Coverage report (htmlcov/index.html)
script/test tests/sensor/      # Specific directory
script/test -k test_sensor     # Pattern matching
script/test -m unit            # Marker filtering
script/test --snapshot-update  # Update snapshots
```

## Rules

**Do:**

- Test success and error cases
- Mock external dependencies (API, network, time)
- Use descriptive test names and docstrings
- Keep tests focused (one assertion concept per test)
- Use fixtures for setup
- Test through core interfaces (`hass.states`, `hass.services`)
- Use snapshots for large outputs (don't replace functional tests)
- Verify registry entries and config entry lifecycle
- Use `async_fire_time_changed` instead of `time.sleep()`

**Don't:**

- Make real network requests
- Test Home Assistant internals
- Access entity objects directly
- Create complex test scenarios
- Skip error condition testing
- Assume patterns - research when uncertain

## Research Resources

**When uncertain about testing patterns:**

- [Home Assistant Testing Docs](https://developers.home-assistant.io/docs/development_testing) - HA-specific patterns
- [pytest Documentation](https://docs.pytest.org/) - Fixtures, markers, advanced usage
- [Home Assistant Core Tests](https://github.com/home-assistant/core/tree/dev/tests/components) - Integration examples
- Google: `site:developers.home-assistant.io testing [topic]`

**Coverage targets:**

- Coordinator logic, config flow validation, error handling, entity state calculations
- Check: `script/test --cov-html`
