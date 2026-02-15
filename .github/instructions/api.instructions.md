---
applyTo: "custom_components/**/api/**/*.py, custom_components/**/coordinator/**/*.py"
---

# API and Coordinator Instructions

**Applies to:** API client and coordinator implementation files

## Three-Layer Architecture (CRITICAL)

**Entities → Coordinator → API Client** - Never skip layers

- **Entities:** Read `coordinator.data` only, never call API
- **Coordinator:** Calls API, transforms data, handles errors/timing
- **API Client:** HTTP communication, auth, exception translation

## API Client vs PyPI Library Decision

**Build custom API client when:**

- Device/service uses simple REST API or GraphQL (HTTP, JSON)
- Available PyPI libraries are unmaintained, bloated, or poorly designed
- Using `aiohttp` + `json` is more maintainable than framework dependency

**Use existing PyPI library when:**

- Library is actively maintained, async-compatible, well-documented
- Protocol is complex (OAuth2 flows, WebSocket reconnection, binary protocols)
- Industry-standard protocols (MQTT, XMPP) have established libraries

**PyPI library requirements (if publishing):**

- Source distributions available (not binary-only)
- Tagged releases correspond to PyPI versions
- Automated PyPI publishing (CI/CD)
- Issue tracker enabled for external libraries
- OSI-approved license required

## API Client Rules

**Session management:**

- MUST accept `aiohttp.ClientSession` parameter in `__init__`
- NEVER create session (`aiohttp.ClientSession()`) in client
- Session comes from `async_get_clientsession(hass)` in `__init__.py`

**Timeout handling:**

- Use `asyncio.timeout()` not `async_timeout`
- Set reasonable timeout per request (10-30s typical)

**Return values:**

- Return raw API response data
- Let coordinator transform data for entities
- Don't process/restructure in API client

## Exception Hierarchy (REQUIRED)

Define in `api/__init__.py`:

- `IntegrationBlueprintApiClientError` (Base)
- `IntegrationBlueprintApiClientCommunicationError` (Network, timeout, HTTP errors)
- `IntegrationBlueprintApiClientAuthenticationError` (401, 403, invalid credentials)
- Optional: `ApiClientRateLimitError(retry_after)` for rate limiting

**Mapping:** HTTP 401/403 → Auth, HTTP 429 → RateLimit, Timeout/ClientError → Communication

## Coordinator Exception Mapping

Map API exceptions to Home Assistant exceptions in `_async_update_data()`:

| API Exception         | Coordinator Exception          | Home Assistant Behavior |
| --------------------- | ------------------------------ | ----------------------- |
| `AuthenticationError` | `ConfigEntryAuthFailed`        | Triggers reauth flow    |
| `CommunicationError`  | `UpdateFailed("message")`      | Retry with backoff      |
| `RateLimitError`      | `UpdateFailed(retry_after=60)` | Wait before retry       |

**Import from:** `homeassistant.exceptions.ConfigEntryAuthFailed`, `homeassistant.helpers.update_coordinator.UpdateFailed`

**Logging:** Pass error message to exception constructor. **Do NOT log** setup/update failures manually - HA handles it automatically. Normal operation logging (debug/info) is still appropriate.

See [Integration Setup Failures](https://developers.home-assistant.io/docs/integration_setup_failures).

## Data Transformation (Coordinator Responsibility)

**Pattern:** `_async_update_data()` fetches raw API data, transforms to simple dict for entities

**Goal:** Entities read `coordinator.data["temperature"]`, not nested API structure like `coordinator.data["sensors"]["temp"]["value"]`

## Rate Limiting Pattern

**If API has rate limits:**

1. **API Client:** Detect HTTP 429, parse `Retry-After` header, raise `RateLimitError(retry_after=seconds)`
2. **Coordinator:** Catch exception, raise `UpdateFailed(retry_after=seconds)`
3. **Home Assistant:** Automatically backs off

**Common headers:** `Retry-After`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

## Pagination

**When API returns paginated results:**

- Implement in API client (fetch all pages)
- Return complete dataset to coordinator
- Set reasonable page size (50-100 items)
- Add timeout per page, not total operation
- Consider memory for large datasets

**Common patterns:** Offset/limit, cursor-based, link headers, `has_more` flag

## Update Interval

**Set in coordinator:** `super().__init__(hass, LOGGER, name="...", update_interval=timedelta(seconds=30))`

**Guidelines:** Environmental sensors (30-60s), Energy (10-30s), Status (60-300s), Slow data (5-15min)

## Context-Based Fetching (Optional)

**Only when:** API has separate endpoints and fetching all is expensive

**Pattern:** `self.async_contexts()` returns active entities, conditionally fetch based on entity types

**Default:** Simpler to fetch all data unless performance issue

## Package Organization

**Split large modules (~200-400 lines per file):**

- `coordinator/base.py` - Core coordinator
- `coordinator/data_processing.py` - Transform helpers
- `coordinator/error_handling.py` - Recovery logic
- `api/client.py` - Main client
- `api/auth.py` - Auth helpers (OAuth, token refresh)
- `api/endpoints/` - Grouped endpoints (if many)

## Common Mistakes

**❌ Don't:**

- Create `aiohttp.ClientSession()` in API client
- Call API directly from entities
- Catch `TimeoutError`/`ClientError` in coordinator (base class handles)
- Return transformed data from API client
- Implement retry logic in API client (coordinator does this)

**✅ Do:**

- Accept session parameter
- Translate all exceptions to integration-specific types
- Transform data in coordinator
- Use specific exception types for different failures
- Let coordinator handle retries and timing

## Reference

[Home Assistant: Fetching Data](https://developers.home-assistant.io/docs/integration_fetching_data)
