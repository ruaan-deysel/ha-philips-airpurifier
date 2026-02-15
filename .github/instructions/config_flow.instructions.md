---
applyTo: "custom_components/**/config_flow_handler/**/*.py, custom_components/**/config_flow.py"
---

# Config Flow Instructions

**Official Documentation:**

- [Data Entry Flow Index](https://developers.home-assistant.io/docs/data_entry_flow_index) - Fundamental flow concepts and result types
- [Config Entries Index](https://developers.home-assistant.io/docs/config_entries_index) - Overview and lifecycle
- [Config Flow Handler](https://developers.home-assistant.io/docs/config_entries_config_flow_handler)
- [Options Flow Handler](https://developers.home-assistant.io/docs/config_entries_options_flow_handler)

## Architecture Overview

Understanding the relationship between these components is essential:

**Data Entry Flow** (Framework Layer):

- Generic **UI flow system** in Home Assistant Core for collecting user input
- Provides building blocks: `FlowHandler`, result types (`FORM`, `CREATE_ENTRY`, etc.), form schemas
- Used for multiple purposes: config flows, options flows, repairs flows, subentry flows, even user login
- Think of it as the **library/framework** that provides the UI interaction mechanics
- Has **nothing to do** with `data.py` (runtime data) - confusing naming!

**Config Flow** (Application Layer):

- **Uses Data Entry Flow framework** to implement integration setup
- Special purpose: Initial setup of integrations (create `ConfigEntry`)
- Adds integration-specific features: discovery, reauth, reconfigure, YAML import
- Inherits from `config_entries.ConfigFlow` which inherits from `data_entry_flow.FlowHandler`
- Creates **immutable data** (credentials, host) and **mutable options** (scan interval, features)

**Options Flow** (Application Layer):

- **Also uses Data Entry Flow framework** to implement settings changes
- Special purpose: Modify existing integration settings (update `ConfigEntry.options`)
- Simpler than Config Flow: no discovery, reauth, or import
- Inherits from `config_entries.OptionsFlow` which inherits from `data_entry_flow.FlowHandler`
- Only modifies **mutable options**, never immutable data (use reconfigure for that)

**Where Data Entry Flow is actually used:**

1. **Config Flow** (`config_flow_handler/config_flow.py`):
   - User adds integration → shows forms → collects input → creates `ConfigEntry`
   - Methods like `async_show_form()`, `async_create_entry()` are Data Entry Flow

2. **Options Flow** (`config_flow_handler/options_flow.py`):
   - User changes settings → shows forms → collects input → updates `ConfigEntry.options`

3. **Subentry Flow** (`config_flow_handler/subentry_flow.py`):
   - User adds sub-devices → shows forms → collects input → creates sub-entries

4. **Repair Flow** (`repairs.py` - separate from config_flow_handler):
   - User fixes issues → shows forms → collects input → resolves problem
   - See `repairs.instructions.md` for Repair Flow patterns (different architecture)

**Common confusion - Data Entry Flow vs. data.py:**

- **Data Entry Flow** = UI system for **collecting data from users** (forms, wizards)
- **`data.py`** = Type definitions for **runtime data** (`entry.runtime_data`)
- These are completely unrelated despite the similar names!

**Why this matters:**

- Both Config Flow and Options Flow use the **same result types** and patterns from Data Entry Flow
- You'll use `async_show_form()`, `async_create_entry()`, etc. in both
- The form schemas, validation patterns, and UI controls work identically
- Home Assistant's documentation separates these by abstraction level, not by usage together

**Timeline - How it all fits together:**

1. User clicks "Add Integration" → **Data Entry Flow** (via Config Flow) shows UI forms
2. User enters host/credentials → **Data Entry Flow** validates and collects input
3. `ConfigEntry` created with data/options → stored in `.storage/core.config_entries`
4. `async_setup_entry()` runs → creates runtime objects (client, coordinator)
5. `entry.runtime_data = IntegrationBlueprintData(...)` → stores runtime objects (from `data.py`)
6. Integration operates using `entry.runtime_data.coordinator`, `entry.runtime_data.client`

## Data Entry Flow Fundamentals

Every step method must return one of these result types (see [Data Entry Flow docs](https://developers.home-assistant.io/docs/data_entry_flow_index)):

**Result Types:**

- `FORM` - Show form: `async_show_form(step_id, data_schema, errors={}, description_placeholders={})`
- `CREATE_ENTRY` - Create entry: `async_create_entry(title, data={}, options={})`
- `ABORT` - Stop flow: `async_abort(reason="...")`
- `SHOW_MENU` - Navigation menu: `async_show_menu(step_id, menu_options=[...])`
- `EXTERNAL_STEP` - OAuth2 redirect: `async_external_step(step_id, url)` then `async_external_step_done(next_step_id)`
- `SHOW_PROGRESS` - Long tasks: `async_show_progress(step_id, progress_action, progress_task)` then `async_show_progress_done(next_step_id)`
- Progress decorator: `@progress_step("translation_key")` for simplified handling

### Form Schemas

**Simple fields** - Use voluptuous: `vol.Required("field"): str`, `vol.Optional("field", default=value): int`

**Rich UI** - Use selectors for better UX: `TextSelector`, `NumberSelector`, `EntitySelector`, etc. (see [Selector docs](https://developers.home-assistant.io/docs/data_entry_flow_index#show-form))

**Sections** - Group with `section()`: `vol.Required("advanced"): section(vol.Schema({...}), {"collapsed": True})`

**Pre-filling:**

- Default values: `vol.Optional("field", default="value")`
- Suggested values: `vol.Optional("field", description={"suggested_value": "value"})`
- Merge from existing: `self.add_suggested_values_to_schema(schema, entry.options)`

**Read-only fields** - Set `read_only=True` in selector config (e.g., `EntitySelectorConfig(read_only=True)`)

### Validation and Error Handling

**Return errors dict for validation failures** - Use translation keys: `errors={"base": "cannot_connect"}`

**Common error keys:** `cannot_connect`, `invalid_auth`, `already_configured`, `unknown`

**Pattern:** Try validation → catch exceptions → set errors → re-show form

**MUST log unexpected exceptions:** `_LOGGER.exception("Unexpected exception")`

### Multi-Step Flows

**Store data between steps** - Save to instance: `self.step_data = user_input`

**Forward to next step** - Return: `return await self.async_step_next_step()`

**Access previous data** - Read from instance: `self.step_data`

### Browser Autofill

**Option 1:** Use recognized field names (`username`, `password` → auto-mapped)

**Option 2:** Explicit autocomplete in selectors: `TextSelectorConfig(autocomplete="username")`

**Common values:** `username`, `current-password`, `email`, `tel`, `postal-code`

## File Organization

- Place config flow in `config_flow_handler/config_flow.py`
- Place options flow in `config_flow_handler/options_flow.py`
- Place subentry flow in `config_flow_handler/subentry_flow.py` (if needed)
- Place shared logic in `config_flow_handler/handler.py`
- Place schemas in `config_flow_handler/schemas/*.py`
- Place validators in `config_flow_handler/validators/*.py`
- **MUST** maintain `config_flow.py` at integration root (hassfest requirement) that imports from package

## Step Names

**Reserved discovery steps** (require manifest entry):

- `bluetooth`, `dhcp`, `homekit`, `mqtt`, `ssdp`, `usb`, `zeroconf`

**Reserved system steps:**

- `user` - User-initiated setup
- `reauth` - Re-authentication flow
- `reconfigure` - Configuration changes
- `import` - YAML migration
- `hassio` - Supervisor add-on discovery

**Rules:**

- If discovery step exists → called on discovery
- If discovery step omitted → `user` step called on discovery
- **NEVER** auto-create entries from discovery - always confirm with user first

## Unique IDs

**MUST:**

- Set unique ID for all discovery flows: `await self.async_set_unique_id(device_id)`
- Call `self._abort_if_unique_id_configured()` to prevent duplicates
- Use stable identifiers: serial number, MAC address, device ID, geo coordinates, account ID
- Normalize IDs: MAC via `format_mac()`, email/username to lowercase
- Use `updates` parameter to refresh config data: `self._abort_if_unique_id_configured(updates={CONF_HOST: host})`

**NEVER:**

- Use IP addresses (can change via DHCP)
- Use device names (user-changeable)
- Use hostnames (user-changeable)
- Use URLs (can change)

**Discovery without unique ID:**

- Use `await self._async_handle_discovery_without_unique_id()` if ID unavailable
- Implement `is_matching(other_flow)` if unique ID is ambiguous

## Discovery Flows

**MUST:**

- Set unique ID in discovery step
- Abort if already configured: `self._abort_if_unique_id_configured()`
- Store placeholders for title: `self.context["title_placeholders"] = {"name": device_name}`
- Forward to user step for confirmation
- Update existing entries via `updates` parameter when device details change

**NEVER:**

- Auto-create entries without user confirmation
- Skip unique ID check

## Setup Entry Error Handling

**In `async_setup_entry()` in `__init__.py`:**

**MUST:**

- Raise `ConfigEntryNotReady` for temporary failures (timeout, device offline, network issues)
- Raise `ConfigEntryAuthFailed` for authentication failures (expired credentials, invalid tokens)
- Include descriptive error message

**NEVER:**

- Log `ConfigEntryNotReady` manually (HA logs at debug automatically)
- Implement custom retry logic (HA handles exponential backoff)
- Ignore exceptions

**Alternative to `ConfigEntryAuthFailed`:**

- Call `entry.async_start_reauth()` directly in exception handler

## User Flow

**MUST:**

- Validate input before creating entry
- Set unique ID if available: `await self.async_set_unique_id(unique_id)`
- Abort if duplicate: `self._abort_if_unique_id_configured()`
- Return errors dict with translation keys: `{"base": "cannot_connect"}`
- Log unexpected exceptions: `_LOGGER.exception("Unexpected exception")`

**Common error keys:**

- `cannot_connect` - Connection failed
- `invalid_auth` - Invalid credentials
- `already_configured` - Already set up
- `unknown` - Unexpected error

## Reauth Flow

**MUST:**

- Implement `async_step_reauth()` that forwards to `async_step_reauth_confirm()`
- Use `self._get_reauth_entry()` to access current entry
- Verify unique ID unchanged: `await self.async_set_unique_id(id)` then `self._abort_if_unique_id_mismatch()`
- Check source: `if self.source == SOURCE_REAUTH`
- Update entry: `return self.async_update_reload_and_abort(self._get_reauth_entry(), data_updates=user_input)`
- Set description placeholders: `description_placeholders={"name": self._get_reauth_entry().title}`

**NEVER:**

- Create new entry (always update existing)
- Skip unique ID verification
- Skip confirmation step

**Translation keys:**

- `config.step.reauth_confirm.title` - Use `[%key:common::config_flow::title::reauth%]`
- `config.step.reauth_confirm.description` - Explain what expired
- `config.abort.reauth_successful` - Use `[%key:common::config_flow::abort::reauth_successful%]`

## Reconfigure Flow

**MUST:**

- Use `self._get_reconfigure_entry()` to access current entry
- Verify unique ID unchanged if applicable: `await self.async_set_unique_id(id)` then `self._abort_if_unique_id_mismatch()`
- Check source: `if self.source == SOURCE_RECONFIGURE`
- Update entry: `return self.async_update_reload_and_abort(entry, data_updates=user_input)`
- Pre-fill form: `self.add_suggested_values_to_schema(schema, entry.data)`

**NEVER:**

- Create new entry (always update existing)
- Use for authentication changes (use reauth)

**Optional:**

- Set `reload_even_if_entry_is_unchanged=False` to skip reload if unchanged

## Version and Migration

**Define versions in ConfigFlow:**

- `VERSION` - Major (breaking changes), `MINOR_VERSION` - Minor (compatible)

**Implement `async_migrate_entry()` in `__init__.py`:**

- Return `False` for downgrades
- Update via `hass.config_entries.async_update_entry(entry, version=X, minor_version=Y)`
- Log migration events

**Minor:** Compatible changes, loads without migration. **Major:** Breaking changes, requires migration.

## Titles and Translations

**Title priority:** `title_placeholders` + `flow_title` → `title_placeholders["name"]` → `title` → manifest `name` → domain

**Set placeholders:** `self.context["title_placeholders"] = {"name": device_name}`

**Translation keys:** `config.step.<step>.title`, `config.error.<key>`, `config.abort.<key>`

## Subentry Flows

**MUST:** Return types via `async_get_supported_subentry_types()`, implement `async_step_user()`, use `async_create_subentry()`

**NEVER:** Support discovery/reauth in subentries

## Options Flow

**MUST:** Return via `async_get_options_flow()`, implement `async_step_init()`, pre-fill with existing options

**Auto-reload:** Subclass `OptionsFlowWithReload` (no manual listener needed)

**Manual listener:** Register update listener in `async_setup_entry()` that calls `async_reload()`

## Code Organization

**MUST:**

- Place schemas in `schemas/` directory, one file per schema
- Place validators in `validators/` directory, one file per validator type
- Import in `__init__.py` for each subdirectory
- Keep flow files focused (<400 lines per file)

## Config Entry Lifecycle

**States:** `not loaded`, `setup in progress`, `loaded`, `setup error`, `setup retry`, `migration error`, `unload in progress`, `failed unload`

**Setup (in `__init__.py`):**

**`async_setup_entry(hass, entry)`** - Forward platforms, return `True`, raise `ConfigEntryNotReady`/`ConfigEntryAuthFailed`

**`async_unload_entry(hass, entry)`** - Optional (Silver+), unload platforms, close connections, return `True`/`False`

**`async_remove_entry(hass, entry)`** - Optional, cleanup cloud resources after deletion

**CRITICAL:**

- **NEVER mutate ConfigEntry directly** - Use `hass.config_entries.async_update_entry()`
- Use `entry.async_on_unload()` for cleanup callbacks
- Entity cleanup: `async_will_remove_from_hass()` in entities

## Rules Summary

**ALWAYS:**

- Set unique ID for discovery flows
- Abort if unique ID already configured
- Confirm with user before creating entry
- Update existing entries in reauth/reconfigure (never create new)
- Verify unique ID unchanged in reauth/reconfigure
- Validate input before creating/updating entries
- Use translation keys for errors
- Pre-fill forms with current values
- Log unexpected exceptions
- Use `async_forward_entry_setups()` for platform setup
- Implement `async_unload_entry()` for clean teardown (Silver+ Quality Scale)
- Use `hass.config_entries.async_update_entry()` to modify entries

**NEVER:**

- Auto-create entries from discovery
- Use changeable values as unique IDs
- Create new entries in reauth/reconfigure
- Log `ConfigEntryNotReady` manually
- Skip unique ID check in discovery flows
- Skip confirmation in discovery flows
- Mutate ConfigEntry objects directly (use `async_update_entry()` instead)
