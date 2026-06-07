# CODEX.md

This repository uses a shared AI agent instruction system. **All instructions are in [`AGENTS.md`](AGENTS.md).**

Read `AGENTS.md` completely before starting any work. It contains:

- **CRITICAL: Upstream Library Rules** — Never bypass `philips-airctrl` library
- Project overview and integration identifiers
- Package structure and architectural rules
- Code style, validation commands, and quality expectations
- Home Assistant patterns (config flow, coordinator, entities, services)
- Workflow rules and breaking change policy

## Quick Reference

- **Domain:** `philips_airpurifier_coap`
- **Title:** Philips Air Purifier Integration
- **Class prefix:** `PhilipsAirPurifier`
- **Main code:** `custom_components/philips_airpurifier/`
- **Upstream library:** `philips-airctrl==1.1.0` — Never bypass it
- **Validate:** `script/check` (type-check + lint + spell)
- **Test:** `script/test`
- **Run HA:** `./script/develop`

## 🚫 CRITICAL: Upstream Library Rule

**Device communication MUST ONLY go through `philips-airctrl` library. Never bypass it.**

- ✅ Use: `await self.client.get_status()`, `await self.client.observe_status()`, `await self.client.set_control_values()`
- ❌ Never: Direct socket calls, alternative CoAP libraries, manual encryption, HTTP workarounds

**If feature is missing:** Open upstream issue at [philips-airctrl/issues](https://github.com/ruaan-deysel/philips-airctrl/issues) — do not work around it.

See `AGENTS.md` section "CRITICAL: Upstream Library Rules" for full details and examples.

## Path-Specific Instructions

Additional domain-specific guidance is available in `.github/instructions/*.instructions.md`.

These files use `applyTo` globs to indicate which file types they cover:

- `python.instructions.md` — Python style, async patterns, HA imports
- `coordinator.instructions.md` — Coordinator patterns
- `entities.instructions.md` — Entity implementation
- `upstream_library.instructions.md` — Upstream library rules (CRITICAL)
- And others for specific file types

## Commands

```bash
scripts/setup          # Install deps with uv, set up pre-commit hooks
scripts/lint           # Format and lint with ruff (auto-fix)
scripts/test           # Run pytest test suite
scripts/develop        # Run Home Assistant with integration loaded
scripts/check          # Full validation (type + lint + spell)
```

Start with `AGENTS.md` for comprehensive guidance on all project conventions.
