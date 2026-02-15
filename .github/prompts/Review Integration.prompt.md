---
agent: "agent"
tools: ["search/codebase", "search", "runCommands"]
description: "Comprehensive quality review of integration code and configuration"
---

# Review Integration

Your goal is to perform a comprehensive quality review of this Home Assistant integration, identifying issues and suggesting improvements.

If not provided, ask for:

- Review scope (full integration, specific component, recent changes)
- Focus areas (code quality, architecture, security, performance, user experience)
- Known issues or concerns to investigate

## Review Process

### 1. Automated Validation

Run all validation tools first:

```bash
script/check           # Type checking + linting + spell check
script/lint-check      # Read-only lint check
script/type-check      # Pyright only
```

Report any errors found. Fix critical issues before proceeding.

### 2. Architecture Review

**Coordinator Pattern:**

- [ ] All API calls go through coordinator
- [ ] Coordinator has proper error handling
- [ ] Update interval is reasonable (not too frequent)
- [ ] Data structure is efficient and typed
- [ ] Coordinator refresh is async

**Entity Organization:**

- [ ] Entities inherit from both platform base and `IntegrationBlueprintEntity`
- [ ] `_attr_has_entity_name = True` for all new entities (MANDATORY 2025)
- [ ] Entity names use `translation_key` instead of hardcoded `name`
- [ ] Entity IDs are stable (won't change on restart)
- [ ] Unique IDs are properly set
- [ ] Device info is consistent across entities for same device
- [ ] Entities use coordinator data (not direct API calls)

**Config Flow:**

- [ ] User input validation is comprehensive
- [ ] Error messages are clear and actionable
- [ ] Reauthentication flow exists if needed
- [ ] Options flow for configuration changes
- [ ] No blocking I/O in flow steps

**API Client:**

- [ ] Uses aiohttp for HTTP requests
- [ ] Proper timeout handling
- [ ] Custom exceptions for different error types
- [ ] Session management (connection pooling)
- [ ] Rate limiting if needed

### 3. Code Quality Review

**Type Hints:**

```python
# ✅ Good - Full type hints
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up integration."""

# ❌ Bad - Missing types
async def async_setup_entry(hass, entry):
    """Set up integration."""
```

**Error Handling:**

```python
# ✅ Good - Specific exceptions
try:
    data = await client.fetch_data()
except ClientConnectionError as err:
    raise ConfigEntryNotReady(f"Connection failed: {err}") from err

# ❌ Bad - Bare except
try:
    data = await client.fetch_data()
except:
    pass
```

**Async Patterns:**

```python
# ✅ Good - Proper async timeout
async with asyncio.timeout(30):
    data = await client.fetch_data()

async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        return await response.json()

# ❌ Bad - Blocking I/O or deprecated timeout
import async_timeout  # DEPRECATED - use asyncio.timeout()
time.sleep(5)
requests.get(url)
```

**Import Organization:**

- [ ] Future annotations imported
- [ ] Proper import order (stdlib, third-party, HA, local)
- [ ] No unused imports
- [ ] Standard HA aliases used (`cv`, `vol`, `dr`, `er`)

**Naming Conventions:**

- [ ] Classes use `PascalCase` with `IntegrationBlueprint` prefix
- [ ] Functions and variables use `snake_case`
- [ ] Constants use `UPPER_SNAKE_CASE`
- [ ] Private members have `_leading_underscore`

### 4. Home Assistant Best Practices

**Anti-Patterns to Check:**

- [ ] ❌ No `time.sleep()` (use `await asyncio.sleep()`)
- [ ] ❌ No blocking I/O in async functions
- [ ] ❌ No direct `hass.states` access in entities
- [ ] ❌ No imports from other integrations
- [ ] ❌ No hardcoded secrets or URLs
- [ ] ❌ No direct `hass.data` modification outside setup
- [ ] ❌ No I/O in `@property` methods
- [ ] ❌ No broad exception catching without re-raising

**Required Patterns:**

- [ ] ✅ Entities become unavailable when device unreachable
- [ ] ✅ Config entry data properly stored and accessed
- [ ] ✅ Proper cleanup in `async_unload_entry`
- [ ] ✅ Integration service actions registered in `async_setup`, NOT `async_setup_entry`
- [ ] ✅ Entity service actions registered in platform `async_setup_entry`
- [ ] ✅ Entity unique IDs never change
- [ ] ✅ Coordinator handles `UpdateFailed` gracefully

### 5. Documentation Review

**Docstrings:**

- [ ] All public classes have Google-style docstrings
- [ ] All public functions have docstrings
- [ ] Complex algorithms explained
- [ ] Parameters documented where not obvious

**Code Comments:**

- [ ] Why, not what (code shows what)
- [ ] References to ADRs or documentation
- [ ] Warnings about non-obvious behavior
- [ ] TODOs have context and issue numbers

**External Documentation:**

- [ ] `docs/user/GETTING_STARTED.md` exists and is clear
- [ ] `docs/user/CONFIGURATION.md` covers all options
- [ ] `docs/development/ARCHITECTURE.md` reflects current design
- [ ] `AGENTS.md` is up to date with project patterns
- [ ] `icons.json` used for entity and action icons (not hardcoded)

### 6. Translation Review

**English (`translations/en.json`):**

- [ ] All config flow steps translated
- [ ] All entity names translated
- [ ] All service actions translated (under `services` key)
- [ ] Error messages are clear
- [ ] Help text is helpful

**German (`translations/de.json`):**

- [ ] Matches English structure
- [ ] All keys present
- [ ] Translation quality (not just literal)

### 7. Security Review

**Sensitive Data:**

- [ ] API keys stored in config entry data (encrypted)
- [ ] Passwords never logged
- [ ] Sensitive data excluded from diagnostics
- [ ] User input sanitized before API calls

**API Security:**

- [ ] HTTPS used for API calls
- [ ] Certificate verification enabled
- [ ] Tokens refreshed properly
- [ ] No credentials in URLs

### 8. Performance Review

**API Efficiency:**

- [ ] Batch requests where possible
- [ ] Reasonable update intervals
- [ ] Caching used appropriately
- [ ] Debouncing for user inputs

**Memory Usage:**

- [ ] No memory leaks (proper cleanup)
- [ ] Data structures are appropriate size
- [ ] Old data is cleared
- [ ] Large responses handled efficiently

### 9. User Experience Review

**Setup Experience:**

- [ ] Setup flow is clear and simple
- [ ] Validation provides helpful feedback
- [ ] Discovery works if applicable
- [ ] Reauthentication is straightforward

**Entity Naming:**

- [ ] Entity names are clear and consistent
- [ ] No confusing abbreviations
- [ ] Proper capitalization
- [ ] Follows HA naming conventions

**Attributes:**

- [ ] Useful diagnostic info in attributes
- [ ] Not too many attributes (cluttered)
- [ ] Attribute names are clear
- [ ] Units are specified

### 10. Maintenance Review

**Code Maintainability:**

- [ ] Files are reasonably sized (<500 lines)
- [ ] Functions are focused and single-purpose
- [ ] No code duplication
- [ ] Clear separation of concerns

**Testing Readiness:**

- [ ] Code is testable (dependency injection)
- [ ] Mock points are clear
- [ ] Test directory structure exists

**Future-Proofing:**

- [ ] Breaking changes avoided
- [ ] Migration paths considered
- [ ] Extensibility points clear
- [ ] HA version requirements documented

## Review Report Structure

Create report in `.ai-scratch/review-report.md`:

```markdown
# Integration Review Report

**Date:** YYYY-MM-DD
**Scope:** [Full integration / Specific component]
**Reviewer:** GitHub Copilot

## Executive Summary

[Brief overview of findings: critical issues, minor issues, recommendations]

## Critical Issues

### 1. [Issue Title]

**Severity:** Critical
**Location:** `file.py:123`
**Issue:** [Description]
**Impact:** [User impact or technical debt]
**Recommendation:** [How to fix]

## Warnings

### 1. [Issue Title]

**Severity:** Warning
**Location:** `file.py:456`
**Issue:** [Description]
**Recommendation:** [How to fix]

## Improvement Opportunities

### 1. [Opportunity Title]

**Area:** [Code Quality / Performance / UX]
**Description:** [What could be better]
**Benefit:** [Why this matters]
**Effort:** [Low / Medium / High]

## Positive Findings

- [Good pattern found]
- [Well-implemented feature]
- [Strong code quality area]

## Metrics

- **Total files reviewed:** X
- **Lines of code:** X
- **Type coverage:** X%
- **Validation status:** ✅ Pass / ❌ Fail
- **Critical issues:** X
- **Warnings:** X
- **Recommendations:** X

## Next Steps

1. [Immediate action needed]
2. [Short-term improvement]
3. [Long-term enhancement]
```

## Output Formats

### Quick Review (for small changes)

- Run validation tools
- List issues found
- Suggest immediate fixes

### Full Review (for complete integration)

- Generate comprehensive report
- Categorize issues by severity
- Provide code examples
- Suggest refactoring opportunities

### Focused Review (specific area)

- Deep dive into requested area
- Compare against best practices
- Provide specific recommendations
- Include code examples

## Integration Context

- **Domain:** `ha_integration_domain`
- **Class prefix:** `IntegrationBlueprint`
- **Instructions:** `.github/instructions/*.instructions.md`
- **Guidelines:** `AGENTS.md`, `CONTRIBUTING.md`

Reference project-specific patterns and standards.

## After Review

1. Present findings with priorities
2. Ask: "Which issues should I address first?"
3. Offer to create implementation plan for fixes
4. Suggest creating ADRs for architectural improvements
