# GitHub Copilot Instructions

> **Comprehensive docs:** See [`AGENTS.md`](../AGENTS.md) at the repository root for full AI agent documentation.
>
> **Why two files?** This file is loaded automatically by GitHub Copilot. `AGENTS.md` serves non-Copilot agents (Claude Code, Cursor, etc.) who don't read this file. Some overlap is intentional. Path-specific `*.instructions.md` files provide detailed patterns per file type — avoid duplicating their content here.

## Project Identity

- **Domain:** `philips_airpurifier_coap` (use this in all user-facing text)
- **Title:** Philips Air Purifier Integration
- **Class prefix:** `PhilipsAirPurifier`
- **Main code:** `custom_components/philips_airpurifier/`
- **Validate:** `script/check` (type-check + lint-check + spell-check)
- **Start HA:** `./script/develop` (kills existing, starts on port 8123)
- **Force restart:** `pkill -f "hass --config" || true && pkill -f "debugpy.*5678" || true && ./script/develop`

Use these exact identifiers throughout the codebase. Never hardcode different values.

## Code Quality Baseline

- **Python:** 4 spaces, 120 char lines, double quotes, full type hints, async for all I/O
- **YAML:** 2 spaces, modern Home Assistant syntax (no legacy `platform:` style)
- **JSON:** 2 spaces, no trailing commas, no comments

Before considering any coding task complete, the following **must** pass:

```bash
script/check      # Runs type-check + lint-check + spell-check
```

Generate code that passes these checks on first run. As an AI agent, you should produce higher quality code than manual development. Aim for zero validation errors.

## Architecture (Quick Reference)

**Data Flow:** Entities → Coordinator → API Client (never skip layers)

**Package Structure (DO NOT create other packages):**

- `coordinator/` — DataUpdateCoordinator (base + data_processing + error_handling + listeners)
- `api/` — External API client (async aiohttp)
- `entity/` — Base entity class (`IntegrationBlueprintEntity`)
- `entity_utils/` — Entity-specific helpers (device_info, state formatting)
- `config_flow_handler/` — Config flow with `schemas/` and `validators/` subdirs
- `[platform]/` — One directory per platform (sensor, switch, etc.), one class per file
- `service_actions/` — Service action implementations
- `utils/` — Integration-wide utilities

**Forbidden packages:** `helpers/`, `ha_helpers/`, `common/`, `shared/`, `lib/` — use `utils/` or `entity_utils/` instead. Do NOT create new top-level packages without explicit approval.

**Key patterns** (details in path-specific `*.instructions.md`):

- Entity MRO: `(PlatformEntity, IntegrationBlueprintEntity)` — order matters
- Unique ID: `{entry_id}_{description.key}` (set in base entity)
- Services: register in `async_setup()`, NOT `async_setup_entry()` (Quality Scale requirement)
- Config entry data: `entry.runtime_data.client` / `entry.runtime_data.coordinator`

## Workflow Rules

1. **Small, focused changes** — avoid large refactorings unless explicitly requested
2. **Implement features completely** — even if spanning 5-8 files
   - Example: New sensor needs entity class + platform init + descriptions → implement all together
   - Example: Bug fix touching coordinator + entity + error handling → do all at once
3. **Multiple independent features:** implement one at a time, suggest commit between each
4. **Large refactoring (>10 files or architectural changes):** propose plan first, get explicit confirmation
5. **Validation:** run `script/check` before considering task complete
6. **File size:** keep files at ~200-400 lines. Split large modules into smaller ones when needed.

**Important: Do NOT write tests unless explicitly requested.** Focus on implementing functionality. The developer decides when and if tests are needed.

**Translation strategy:**

- Business logic first, translations later
- Update `en.json` only when asked or at major feature completion
- NEVER update other language files automatically — extremely time-consuming
- Ask before updating multiple translation files
- Use placeholders in code (e.g., `"config.step.user.title"`) — functionality works without translations

## Research First

**Don't guess — look it up:**

1. Search [Home Assistant Developer Docs](https://developers.home-assistant.io/) for current patterns
2. Check the [developer blog](https://developers.home-assistant.io/blog/) for recent changes
3. Look at existing patterns in similar files in the integration (e.g., existing sensor implementations)
4. Search: `site:developers.home-assistant.io [your question]` for official guidance
5. Run `script/check` early and often — catch issues before they compound
6. Consult [Ruff rules](https://docs.astral.sh/ruff/rules/) or [Pyright docs](https://microsoft.github.io/pyright/) when validation fails
7. Ask for clarification rather than implementing based on assumptions

**Home Assistant evolves rapidly** — verify current best practices rather than relying on outdated knowledge.

## Local Development

**Always use the project's scripts** — do NOT craft your own `hass`, `pip`, `pytest`, or similar commands. The scripts handle environment setup, virtual environments, port management, and cleanup that raw commands miss. Agents that bypass scripts frequently break.

**Start Home Assistant:**

```bash
./script/develop
```

**Force restart (when HA is unresponsive or port conflicts):**

```bash
pkill -f "hass --config" || true && pkill -f "debugpy.*5678" || true && ./script/develop
```

**When to restart HA:** After modifying Python files, `manifest.json`, `services.yaml`, translations, or config flow changes

**Validate changes:**

```bash
script/check      # Always run before considering task complete
```

**Logs:**

- Live: terminal where `./script/develop` runs
- File: `config/home-assistant.log` (most recent), `config/home-assistant.log.1` (previous)
- Debug level: `custom_components.philips_airpurifier: debug` in `config/configuration.yaml`

## Working With the Developer

**When requests conflict with these instructions:**

1. Clarify if deviation is intentional
2. Confirm you understood correctly
3. Suggest updating instructions if this is a permanent change
4. Proceed after confirmation

**Maintaining instructions:**

- This project is evolving — instructions should too
- Suggest updates when patterns change
- Remove outdated rules, don't just add new ones

**Documentation rules:**

- ❌ **NEVER** create markdown files without explicit permission
- ❌ **NEVER** create "helpful" READMEs, GUIDE.md, NOTES.md, etc.
- ❌ **NEVER** create documentation in `.github/` unless it's a GitHub-specified file
- ✅ **ALWAYS ask first** before creating permanent documentation
- ✅ **Prefer module/class/function docstrings** over separate markdown files
- ✅ **Prefer extending** existing docs over creating new files
- ✅ **Use `.ai-scratch/`** for temporary planning and notes (never committed)
- Developer docs → `docs/development/` (ASK FIRST)
- User docs → `docs/user/` (ASK FIRST)

**Session management:**

- When task completes and developer moves on: suggest commit with message
- Monitor context size — warn if getting large and a new topic starts
- Offer to create summary for fresh session if context is strained
- Suggest once, don't nag if declined

**Commit format:** [Conventional Commits](https://www.conventionalcommits.org/)

```text
type(scope): short summary (max 72 chars)

- Optional detailed points
- Reference issues if applicable
```

**Always check `git diff` first** — don't rely on session memory. Include all changes in your message.

**Common types:**

- `feat:` — User-facing functionality (new sensor, service, config option)
- `fix:` — Bug fixes (user-facing issues)
- `chore:` — Dev tools, dependencies, devcontainer (NOT user-facing)
- `refactor:` — Code restructuring (no functional change)
- `docs:` — Documentation changes
