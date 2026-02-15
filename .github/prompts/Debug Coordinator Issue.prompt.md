---
agent: "agent"
tools: ["search/codebase", "search", "problems", "runCommands", "runCommands/terminalLastCommand"]
description: "Diagnose and fix data update coordinator problems like stale data or unavailable entities"
---

# Debug Coordinator Issue

Your goal is to diagnose and fix issues with the data update coordinator.

## Common Issues to Check

**Data Not Updating:**

- Check coordinator update interval in `coordinator/base.py`
- Verify `async_update_data()` is actually fetching new data
- Look for exceptions in Home Assistant logs
- Check if API client is returning stale data
- Verify coordinator is properly registered with entities

**Entities Unavailable:**

- Check if coordinator is raising `UpdateFailed` exception
- Verify entity's `available` property logic
- Look for missing keys in coordinator data
- Check API authentication/connection
- Verify error handling in `async_update_data()`

**Performance Issues:**

- Check update interval (too frequent updates?)
- Look for blocking I/O in coordinator (should be async)
- Verify API client uses `aiohttp`, not `requests`
- Check if data processing is efficient
- Consider debouncing rapid updates

**Data Structure Issues:**

- Verify coordinator data type matches entity expectations
- Check for missing or renamed data keys
- Verify data transformation in `async_update_data()`
- Look for type mismatches in entity properties

## Debugging Steps

1. **Enable Debug Logging:**
   - Add/verify in `config/configuration.yaml`:
     ```yaml
     logger:
       logs:
         custom_components.ha_integration_domain: debug
     ```
   - Restart Home Assistant: `./script/develop`

2. **Check Logs:**
   - Look at terminal output where `./script/develop` is running
   - Or check `config/home-assistant.log`
   - Search for error traces and `UpdateFailed` exceptions

3. **Verify Coordinator State:**
   - Check `coordinator.last_update_success`
   - Inspect `coordinator.data` in debugger or logs
   - Verify `coordinator.update_interval` is set correctly

4. **Test API Client Separately:**
   - Use `mcp_pylance_mcp_s_pylanceRunCodeSnippet` to test API calls
   - Verify data format matches expectations
   - Check for network issues or authentication failures

5. **Review Entity Implementation:**
   - Ensure entities inherit from `CoordinatorEntity`
   - Verify `coordinator_context` is set if using context-specific updates
   - Check entity's `available` property logic

## Common Fixes

**Add Error Handling:**

```python
async def async_update_data(self) -> dict[str, Any]:
    """Fetch data from API."""
    try:
        data = await self.api_client.fetch_data()
        _LOGGER.debug("Coordinator updated: %s", data)
        return data
    except AuthenticationError as err:
        # Trigger reauth flow
        raise ConfigEntryAuthFailed from err
    except ConnectionError as err:
        raise UpdateFailed(f"Connection error: {err}") from err
```

**Handle Missing Data:**

```python
@property
def native_value(self) -> float | None:
    """Return sensor value."""
    if not self.coordinator.last_update_success:
        return None
    return self.coordinator.data.get("key_name")
```

**Adjust Update Interval:**

```python
# In coordinator/base.py
super().__init__(
    hass,
    _LOGGER,
    name=DOMAIN,
    update_interval=timedelta(seconds=30),  # Adjust as needed
)
```

## Related Files to Review

- [#file:custom_components/ha_integration_domain/coordinator/base.py]
- [#file:custom_components/ha_integration_domain/api/client.py]
- [#file:custom_components/ha_integration_domain/entity/base.py]
- [#file:config/configuration.yaml] - for log levels
- [#file:config/home-assistant.log] - for error traces

## Before Finishing

- Run `script/check` to validate code quality
- Restart Home Assistant to test fixes
- Monitor logs for any remaining errors
- Verify entities update correctly and stay available
