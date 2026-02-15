---
agent: "agent"
tools: ["edit", "search", "runCommands"]
description: "Update or add translation strings for entities, config flow, actions, and error messages"
---

# Update Translations

Your goal is to update translation strings for this Home Assistant integration.

If not provided, ask for:

- Which language to update (English is required, German optional)
- What to translate (entities, config flow, actions, errors)
- New or changed strings

## Requirements

**Translation Structure:**

- English: `translations/en.json` (always required)
- German: `translations/de.json` (optional, maintain if exists)
- Follow Home Assistant translation schema
- Keep structure identical across language files

**Common Translation Sections:**

1. **Config Flow:**

   ```json
   "config": {
     "step": {
       "user": {
         "data": {
           "host": "Host",
           "password": "Password"
         },
         "data_description": {
           "host": "Hostname or IP address"
         }
       }
     },
     "error": {
       "cannot_connect": "Failed to connect"
     },
     "abort": {
       "already_configured": "Device already configured"
     }
   }
   ```

2. **Entity Translations:**

   ```json
   "entity": {
     "sensor": {
       "air_quality": {
         "name": "Air Quality",
         "state": {
           "good": "Good",
           "moderate": "Moderate"
         }
       }
     }
   }
   ```

3. **Service Actions:**

   ```json
   "services": {
     "reset_filter": {
       "name": "Reset Filter",
       "description": "Reset the filter counter",
       "fields": {
         "entity_id": {
           "name": "Entity",
           "description": "Entity to reset"
         }
       }
     }
   }
   ```

4. **Options Flow:**
   ```json
   "options": {
     "step": {
       "init": {
         "data": {
           "update_interval": "Update interval (seconds)"
         }
       }
     }
   }
   ```

**Translation Guidelines:**

- Use clear, concise language
- Be consistent with Home Assistant terminology
- Provide helpful descriptions for config options
- Keep error messages user-friendly
- Use sentence case for names, not title case
- Don't include entity_id suffixes in translations

**Validation:**

- JSON must be valid (no trailing commas, proper quotes)
- All keys in English file should exist in other language files
- Maintain identical structure across language files
- Run `script/check` to validate JSON syntax

**German Translation Tips:**

- Use formal "Sie" for consistency with Home Assistant
- Translate technical terms appropriately (not literal)
- Keep button/action text concise
- Follow German grammar and capitalization rules

**Related Files:**

- English: [#file:custom_components/ha_integration_domain/translations/en.json]
- German: [#file:custom_components/ha_integration_domain/translations/de.json]
- Schema: [#file:schemas/json/translation_schema.json]
- Documentation: Reference [#file:.github/instructions/translations.instructions.md]

## Before Finishing

- Validate JSON syntax with `script/check`
- Restart Home Assistant to load new translations
- Verify translations appear correctly in UI
- Check all affected screens (config, options, entities, actions)

**DO NOT create tests unless explicitly requested.**
