---
applyTo: "**/*.py"
---

# Python Code Instructions

**Applies to:** All Python files in the integration

## File Structure

### Module Organization

**Integration modules:**

- `__init__.py` - Platform setup with `async_setup_entry()`
- Individual files - One class per file when practical
- `const.py` - Module constants only (no logic)

**File size guidelines:**

- **Target:** 200-400 lines per file
- **Maximum:** ~500 lines before refactoring
- **Reason:** AI models have context limits - keep files manageable

**When a file grows too large:**

1. Extract helper functions to separate files
2. Move entity classes to individual files
3. Create subpackages for related functionality
4. Split constants into logical groups

**Example structure:**

```
sensor/
  __init__.py          # Setup and entity list (50 lines)
  air_quality.py       # Air quality sensor class (200 lines)
  temperature.py       # Temperature sensor class (150 lines)
  diagnostic.py        # Diagnostic sensors (180 lines)
  const.py             # Sensor-specific constants (30 lines)
```

**Naming:**

- Files: `snake_case.py`
- Classes: `PascalCase` prefixed with `IntegrationBlueprint`
- Functions/methods: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Type Annotations

**Required for:**

- All function parameters and return values
- Class attributes (when not obvious)

**Import rules:**

- `from __future__ import annotations` (always first import)
- `collections.abc` for abstract base classes (prefer over `typing`)
- `typing` for complex types (Any, TYPE_CHECKING, etc.)

**Avoiding circular imports:**

Use `if TYPE_CHECKING:` block for type-only imports that would cause circular dependencies.

## Async Patterns

**All I/O operations must be async** - Network, file, database, blocking operations

**Core patterns:**

- `async def` for coroutines, `await` for async calls
- `asyncio.gather()` for concurrent operations
- `asyncio.timeout()` for timeouts (not `async_timeout`)
- Never: `time.sleep()`, synchronous HTTP libraries, blocking operations

**Running blocking code:**

- `await hass.async_add_executor_job(sync_function, arg1, arg2)` - Run blocking I/O in executor thread
- Avoid if sync function also uses executor internally (deadlock risk)

**Background tasks:**

- `hass.async_create_task(coroutine)` - Fire-and-forget parallel execution
- `asyncio.run_coroutine_threadsafe(coro, hass.loop).result()` - From sync thread (rare)

**Callback decorator:**

- `@callback` from `homeassistant.core` - For event loop functions without blocking
- Required for event listeners, state change callbacks
- Cannot do I/O, cannot call coroutines (only schedule them)
- Missing decorator causes execution in executor thread (wrong context)

**Blocking operations (NEVER in event loop):**

- File: `open()`, `pathlib.Path.read_text()`, `pathlib.Path.write_bytes()`
- Directory: `os.listdir()`, `os.walk()`, `glob.glob()`
- Network: `urllib` (use `aiohttp`)
- Other: `time.sleep()`, `SSLContext.load_default_certs()`
- **All must run in executor:** `await hass.async_add_executor_job(blocking_func)`

**Late imports:**

- Module-level imports are safe
- Late async imports: `await async_import_module(hass, "module.path")`
- `if TYPE_CHECKING:` for type-only imports

## Code Style

**Conventions not enforced by Ruff:**

- Comments as complete sentences with capitalization and ending period
- Alphabetical sorting of constants/lists when order doesn't matter

**Note:** Ruff enforces `__all__`/`__slots__` sorting, import ordering, f-string usage in logs.

## Home Assistant Requirements

**Setup Failure Handling:**

See [Integration Setup Failures](https://developers.home-assistant.io/docs/integration_setup_failures) for details.

- `ConfigEntryNotReady` - Device offline/unavailable (raises in `async_setup_entry()`)
- `ConfigEntryAuthFailed` - Expired credentials (triggers reauth flow)
- Pass error message to exception (HA logs at debug level automatically)
- **Do NOT log setup failures manually** - Avoid log spam

**Constants:**

- Prefer `homeassistant.const` over defining new ones (e.g., `CONF_USERNAME`, `CONF_PASSWORD`)
- Only add to integration's `const.py` if widely used internally

**Units of Measurement:**

- Always use constants from `homeassistant.const` - Never hardcode strings
- Examples: `CONCENTRATION_MICROGRAMS_PER_CUBIC_METER`, `PERCENTAGE`, `UnitOfTime.HOURS`
- Construct compound units if no combined constant exists: `f"{UnitOfLength.METERS}/{UnitOfTime.SECONDS}"`

**Time and Timestamps:**

- Always use UTC timestamps (ISO 8601 or Unix)
- Use `dt_util.utcnow().isoformat()` from `homeassistant.util`
- Never use relative time ("2 hours ago") in state/attributes

**Service Actions:**

- Format: `<integration_domain>.<action_name>`
- Register under integration domain (not platform domain)
- Example: `hass.services.async_register(DOMAIN, "reset_filter", handler)`

**Event Names:**

- Prefix with integration domain: `<domain>_<event_name>`
- Example: `hass.bus.async_fire(f"{DOMAIN}_device_paired", data)`

**PARALLEL_UPDATES:**

- Define in platform `__init__.py` if needed
- Controls concurrent entity updates (default: 0 for async, 1 for sync)
- Import from `const.py` if shared across platforms

## Imports

**Order (separated by blank lines):**

1. `from __future__ import annotations`
2. Standard library
3. Third-party packages
4. Home Assistant core
5. Local integration imports

**Standard HA aliases:** `vol`, `cv`, `dr`, `er`, `dt_util`

## Entity Classes

**Structure requirements:**

- Inherit from both platform entity and `IntegrationBlueprintEntity` (order matters)
- Set `_attr_unique_id` in `__init__` (format: `{entry_id}_{key}`)
- Use coordinator data only - Never call API directly
- Handle unavailability via `_attr_available`

## Error Handling

**Use specific exceptions from integration's exception module**

**Logging levels:**

- `_LOGGER.critical()` - System-critical failures
- `_LOGGER.exception()` - Errors with full traceback (in exception handlers)
- `_LOGGER.error()` - Errors affecting functionality
- `_LOGGER.warning()` - Recoverable issues
- `_LOGGER.info()` - Sparingly, user-facing only
- `_LOGGER.debug()` - Detailed troubleshooting

**Log message style:**

- No periods at end (syslog style)
- Never log credentials/tokens/API keys
- Use `%` formatting (enforced by Ruff G004)

## Testing Considerations

**Note: Only write tests when explicitly requested by the developer.**

If you are asked to write tests for entities:

**Example test structure:**

```python
"""Test sensor platform."""

import pytest

from custom_components.ha_integration_domain.sensor import async_setup_entry

@pytest.mark.unit
async def test_sensor_setup(hass, config_entry, coordinator):
    """Test sensor platform setup."""
    # Test implementation
```

## Common Patterns

**Config entry data:** `entry_data: IntegrationBlueprintData = hass.data[DOMAIN][entry.entry_id]`

**Device info:** Provided via base entity class (manufacturer, model, serial, config URL, firmware)

## Validation

Run before submitting: `script/type-check`, `script/lint`, `script/test`

**When validation fails:**

- Look up error codes: [Ruff rules](https://docs.astral.sh/ruff/rules/), [Pyright docs](https://microsoft.github.io/pyright/)
- Search [HA docs](https://developers.home-assistant.io/) for patterns
- Fix root cause - Don't bypass checks

**Suppressing checks (use sparingly for false positives/library issues):**

- Specific suppression: `# noqa: F401 - Reason` or `# type: ignore[attr-defined] - Reason`
- **Never use blanket:** `# noqa`, `# type: ignore`, `# ruff: noqa`
- Always include error codes and explanatory comments

## Verify Current Patterns

Home Assistant APIs evolve - Always verify current patterns:

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Developer Blog](https://developers.home-assistant.io/blog/) for deprecations/changes
- Search: `site:developers.home-assistant.io [feature type]`
