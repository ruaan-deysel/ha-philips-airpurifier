---
applyTo: "**/*.yaml, **/*.yml"
---

# YAML Instructions

**Applies to:** All YAML files

## Formatting Standards

- **2 spaces** for indentation (never tabs)
- No trailing whitespace
- End files with a single newline
- Use lowercase for keys (except where case matters)
- Prefer `>` for multi-line strings (folded) over inline strings
- Use `|` when preserving newlines is important

## Project-Specific Rules

- Keep files focused and readable
- Use comments to separate logical sections
- Group related configuration together

## Schema Validation

YAML schema files are available in `/schemas/yaml/`:

- `configuration_schema.yaml` — Validates Home Assistant `configuration.yaml`
- `services_schema.yaml` — Validates `services.yaml` (service action definitions)

Consult the relevant schema when editing YAML files to ensure correct structure.

## Home Assistant YAML Conventions

- Use modern HA configuration syntax (no legacy `platform:` style)
- Prefer `!include` for splitting large configurations
- Use `!secret` for sensitive values (passwords, API keys, tokens)
- Boolean values: `true`/`false` (lowercase)
