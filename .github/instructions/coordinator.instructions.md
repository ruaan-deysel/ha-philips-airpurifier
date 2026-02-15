---
applyTo: "custom_components/**/coordinator/**/*.py, custom_components/**/api/**/*.py"
---

# Coordinator Instructions

**Applies to:** Coordinator implementation files (always sent together with `api.instructions.md`)

## Using the Coordinator

✅ **Correct:** `self.coordinator.data.temperature` (in entity properties)

❌ **Wrong:** `await self.api_client.get_data()` (never fetch directly in entities)

## Error Handling in `_async_update_data()`

**Exception mapping:**

- `ApiAuthError` → `raise ConfigEntryAuthFailed from err` (triggers reauth)
- `ApiError` → `raise UpdateFailed("message") from err` (retry at next interval)
- `ApiRateLimited` → `raise UpdateFailed(retry_after=60) from err` (backoff)

**Automatic handling:** `TimeoutError` and `aiohttp.ClientError` handled by coordinator base class

## Pull vs. Push Architecture

**Polling (Pull) - Default for most integrations:**

- Coordinator fetches data at fixed intervals via `_async_update_data()`
- Simple, reliable, works with any API
- Set via `update_interval` parameter in coordinator constructor

**Push (Event-driven) - Preferred when available:**

- Device/service sends updates to Home Assistant
- Requires: WebSocket, Webhook, MQTT, or similar push mechanism
- Call `coordinator.async_set_updated_data(new_data)` when data arrives
- Set `update_interval=None` or use long interval as fallback for offline detection

**Prefer push over polling when:**

- Device supports push notifications (WebSocket, Webhook, etc.)
- Protocol is well-documented and implementation effort is reasonable
- Real-time updates improve user experience (faster reaction, less lag)
- Reduces system load (no periodic polling overhead, lower API/network usage)

**Use polling when:**

- Device/API doesn't support push
- Push protocol is proprietary/undocumented
- Implementation complexity outweighs benefits

**Implementation notes:**

- Pull: Coordinator handles everything automatically via `update_interval`
- Push: Set up listener in `async_setup_entry()`, call `async_set_updated_data()` on events
- Hybrid: Use push for updates + polling as fallback for connection monitoring

See [HA Data Update Patterns](https://developers.home-assistant.io/docs/integration_fetching_data)

## First Refresh

**In `async_setup_entry()` in `__init__.py`:** Call `await coordinator.async_config_entry_first_refresh()`

**Automatic handling:** If `_async_update_data()` raises `UpdateFailed`, coordinator raises `ConfigEntryNotReady` automatically

See [Integration Setup Failures](https://developers.home-assistant.io/docs/integration_setup_failures#integrations-using-async_setup_entry)

## Always Update Parameter

`always_update=True` (default) - Always notify entities of new data

`always_update=False` - Only notify if data changed (requires `__eq__` implementation in data class)

## Caching API Data

**When to cache:** API rate limits stricter than update needs (e.g., API allows 1 req/5min, entities need 30s updates)

**Pattern:** Store `_api_cache`, `_api_cache_time`, `_api_cache_ttl` as instance variables. In `_async_update_data()`: Check if cache fresh (TTL not expired), return cached data if fresh, else fetch new data and update cache.

**Use cases:** Expensive API calls, rate-limited APIs, multiple entities reading same raw data

**Result:** Entities update frequently (coordinator `update_interval`), API fetches less often (cache TTL)
