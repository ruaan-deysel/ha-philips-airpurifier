---
applyTo: "**/translations/*.json"
---

# Translation Files Instructions

**Applies to:** `custom_components/ha_integration_domain/translations/*.json`

## Schema Validation

**Schema:** `/schemas/json/translation_schema.json` - Defines complete structure

Translation files define user-facing text for config flows, options, entities, and errors.

## File Location

**Custom integrations** use the `translations/` folder with language-specific files:

- `en.json` - English (required base language)
- `de.json`, `fr.json`, etc. - Additional languages

**Language codes:** BCP47 format (e.g., `en`, `de`, `fr-CA`)

## Critical Instructions

### Translation Placeholders

**Runtime values:** Use `{variable}` syntax - replaced with actual values at runtime

- Never translate placeholder names (e.g., `{host}` stays `{host}`, not `{hôte}`)
- Placeholder names must match code exactly

**CRITICAL: Quotes inside string values** - Do not use single quotes (`'`) within string content around placeholders:

- ✅ `"message": "Service {service} is unavailable"` (no quotes around placeholder)
- ✅ `"message": "Service \"{service}\" is unavailable"` (escaped double quotes)
- ❌ `"message": "Service '{service}' is unavailable"` (single quotes cause hassfest errors)

**Why:** Single quotes within strings around placeholders are not translatable across languages (e.g., German uses „…", French uses «…») and cause validation failures.

**Note:** This is about quotes _inside the string value_, not the JSON delimiter quotes (which must always be double quotes per JSON spec).

**Key references:** Use `[%key:...]` syntax to reuse translations

```json
{
  "config": {
    "error": {
      "invalid_auth": "Invalid credentials",
      "stale_auth": "[%key:component::ha_integration_domain::config::error::invalid_auth%]"
    }
  }
}
```

**Reference Home Assistant common strings:**

```json
"state": {
  "off": "[%key:common::state::off%]",
  "on": "[%key:common::state::on%]"
}
```

### Entity Translations

**Requirements in code:**

- Set `has_entity_name=True` on entity
- Set `translation_key` property to match JSON key
- For placeholders: Set `translation_placeholders` dict

**Example:**

```json
"entity": {
  "sensor": {
    "air_quality": {
      "name": "Air Quality Index",
      "state": {
        "good": "Good",
        "poor": "Poor"
      }
    }
  }
}
```

### Markdown Support

These fields support Markdown formatting:

- Config/Options: `description`, `abort`, `progress`, `create_entry`
- Issues: `title`, `description`

### Proper Nouns

**Never translate:**

- Home Assistant
- Supervisor
- Brand names (product names)
- Technical identifiers

### Formality Level

**Use informal language** in languages that distinguish between formal and informal address:

- **German:** Use "du" (informal), not "Sie" (formal). Use correct imperative forms (e.g., "Gib", not "Gebe").
- **French:** Use "tu" (informal), not "vous" (formal)
- **Spanish:** Use "tú" (informal), not "usted" (formal)
- Apply to all variations (we/you plural: wir/ihr, nous/vous, etc.)

**Example (German):**

- ✅ "Gib deine Anmeldedaten ein" (informal, correct imperative)
- ❌ "Geben Sie Ihre Anmeldedaten ein" (formal)
- ❌ "Gebe deine Anmeldedaten ein" (wrong imperative form)

**German-specific rule:** Pay attention to correct imperative forms (Befehlsform). See [Duden: Bildung des Imperativs](https://www.duden.de/sprachwissen/sprachratgeber/Bildung-des-Imperativs).

### Multi-Language Files

All language files must have identical structure - only values differ:

**en.json:**

```json
{ "config": { "step": { "user": { "title": "Configure Device" } } } }
```

**de.json:**

```json
{ "config": { "step": { "user": { "title": "Gerät konfigurieren" } } } }
```

## Common Mistakes

- ❌ Translating placeholder names (e.g., `{host}` → `{hôte}`)
- ❌ Translating proper nouns (Home Assistant, brand names)
- ❌ Using formal language (Sie/vous) instead of informal (du/tu)
- ❌ Missing `translation_key` in entity code
- ❌ Using entity translations without `has_entity_name=True`
- ❌ Inconsistent key structure across language files
- ❌ Invalid JSON syntax (trailing commas, comments)
- ❌ Wrong key reference syntax (must be exact: `[%key:...]`)

## Best Practices

**Translation Quality Guidelines:**

1. **Only native speakers** should provide translations
2. **Stick to [Material Design guidelines](https://material.io/design/communication/writing.html)** for writing
3. **Don't translate proper nouns** (Home Assistant, Supervisor, brand names)
4. **Keep badge labels short** - Test `state_badge` translations fit in UI without overflowing
5. **Use key references** `[%key:...]` to avoid duplicate translations
6. **Keep consistent terminology** within and across languages
7. **Provide helpful descriptions** for non-obvious fields in `data_description`

**For region-specific translations** (e.g., `en-US`, `fr-CA`): Only include if translations differ from base language. Clone unchanged keys from source (helps track review status).

## References

- [Custom Integration Localization](https://developers.home-assistant.io/docs/internationalization/custom_integration) - **Primary reference**
- [Backend Localization](https://developers.home-assistant.io/docs/internationalization/core) - Complete structure documentation
- [ICU Message Format](https://formatjs.github.io/docs/core-concepts/icu-syntax/) - Placeholder syntax for plurals
