# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Home Assistant custom integration for Philips Air Purifiers using CoAP protocol. Domain: `philips_airpurifier_coap`. Uses the `philips-airctrl` library for device communication. Supports 62+ device models across 3 API generations (Gen1, Gen2, Gen3).

## Commands

```bash
scripts/setup          # Install deps with uv, set up pre-commit hooks
scripts/lint           # Format and lint with ruff (auto-fix)
scripts/test           # Run pytest test suite: uv run pytest tests/
scripts/develop        # Run Home Assistant with integration loaded (debug mode)

# Individual commands
uv run ruff format .                          # Format only
uv run ruff check . --fix                     # Lint only
uv run pytest tests/ -k "test_name"           # Single test
uv run pytest tests/ --cov --cov-report=term  # With coverage
uv run mypy custom_components/                # Type checking (strict mode)
```

## Architecture

### Communication Pattern
- **Local push** via CoAP protocol (no cloud, no polling)
- `CoAPClient` from `philips-airctrl` handles encryption, sync, and observe
- Coordinator uses `observe_status()` async iterator for real-time updates
- Watchdog monitors connection health with automatic reconnection

### Key Files
- `__init__.py` — Integration setup, icon system, platform forwarding
- `coordinator.py` — `PhilipsAirPurifierCoordinator` (DataUpdateCoordinator) with CoAP push observation
- `config_flow.py` — DHCP auto-discovery + manual IP config, model detection
- `philips.py` — 62+ device model classes with per-model capabilities (presets, speeds, available entities)
- `const.py` — API field mappings for 3 generations, entity descriptions (sensor/switch/light/select/number types)
- `model.py` — Type definitions, `DeviceInformation`, `ApiGeneration` enum, `DeviceModelConfig`
- `entity.py` — Base entity class (WIP)

### Device Model System
Models in `philips.py` use class hierarchy: `PhilipsEntity` → `PhilipsGenericControlBase` → `PhilipsGenericFanBase` → API generation base → model-specific class. Each model class declares its available entities via class attributes (`AVAILABLE_SWITCHES`, `AVAILABLE_LIGHTS`, etc.).

Three API generations with different key formats:
- Gen1: simple keys (`pwr`, `mode`, `om`)
- Gen2: `D01-XX`, `D03-XX` format
- Gen3: `D01SXX`, `D03XXX` format

### Config Entry Pattern
Uses `entry.runtime_data` typed as `PhilipsAirPurifierConfigEntry` to store the coordinator. Entity platforms access coordinator directly from the config entry.

## Quality Scale Target

Targeting **platinum** quality scale per Home Assistant integration standards. Key requirements:
- 100% test coverage (configured in pyproject.toml)
- Strict mypy typing
- Full compliance with HA integration quality scale rules

## Conventions

- Python 3.12+, line length 100, ruff for formatting/linting
- Uses `uv` for dependency management
- Async throughout — all device communication is async
- Entity platforms follow HA patterns: `async_setup_entry()` → create entities → `async_add_entities()`
- Translations in `translations/` directory (en, de, bg, etc.)
