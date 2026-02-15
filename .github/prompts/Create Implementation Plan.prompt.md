---
agent: "agent"
tools: ["search/codebase", "search", "edit"]
description: "Create structured implementation plan for new features or refactoring"
---

# Create Implementation Plan

Your goal is to create a comprehensive, phased implementation plan for a new feature, major refactoring, or architectural change in this Home Assistant integration.

If not provided, ask for:

- Feature/change description and goals
- User requirements or problem being solved
- Any constraints or dependencies
- Preferred approach (if known)

## Implementation Plan Structure

Create a markdown file in `.ai-scratch/plan-[feature-name].md` (never committed) with:

### 1. Overview

- **Goal:** What we're building and why
- **User Benefit:** How this helps users
- **Scope:** What's included and excluded
- **Constraints:** Technical limitations, HA version requirements, dependencies

### 2. Architecture Analysis

- Current architecture relevant to this change
- Proposed architecture changes
- Impact on existing components (coordinator, entities, config flow, etc.)
- Breaking changes assessment

### 3. Implementation Phases

Break down into logical phases (typically 3-5):

**Phase 1: [Foundation/Setup]**

- File(s) to create/modify
- Key changes required
- Dependencies to install (if any)
- Validation: How to test this phase works

**Phase 2: [Core Implementation]**

- File(s) to create/modify
- Key changes required
- Integration points with Phase 1
- Validation: How to test this phase works

**Phase 3: [Integration/Polish]**

- File(s) to create/modify
- Translations updates
- Documentation updates
- Final validation

### 4. Quality Checklist

- [ ] Type hints complete
- [ ] Error handling implemented
- [ ] Translations added (en, de)
- [ ] Docstrings updated
- [ ] `script/check` passes
- [ ] Manual testing completed
- [ ] Breaking changes documented (if any)

### 5. Testing Strategy

- Manual testing steps
- Key scenarios to verify
- Expected behavior
- Edge cases to check

### 6. Rollout Considerations

- Configuration migration needed?
- User-facing changes
- Documentation updates required
- Potential issues and mitigations

## Process

1. **Research Phase:**
   - Analyze existing code patterns
   - Check Home Assistant documentation for best practices
   - Review similar integrations if helpful
   - Identify all files that need changes

2. **Create Plan:**
   - Write comprehensive plan in `.ai-scratch/`
   - Get developer confirmation before implementation
   - Adjust based on feedback

3. **Implementation Phase:**
   - Work through phases sequentially
   - Run `script/check` after each phase
   - Test functionality before moving to next phase
   - Mark phases complete in plan file

4. **Completion:**
   - Verify all checklist items
   - Run full validation suite
   - Suggest commit message following Conventional Commits

## Guidelines

**Keep phases small and testable:**

- Each phase should be completable in one session
- Always runnable after each phase (even if incomplete)
- Clear validation criteria for each phase

**Document decisions:**

- Why this approach over alternatives
- Trade-offs made
- Future improvements deferred

**Consider impact:**

- Existing users' configurations
- Entity ID stability
- Backward compatibility
- Migration requirements

**Integration-specific considerations:**

- Domain: `ha_integration_domain`
- Title: Integration Blueprint
- Class prefix: `IntegrationBlueprint`
- Follow patterns in `AGENTS.md` and path-specific `.instructions.md`

## Example Phase Structure

```markdown
## Phase 2: Implement New Sensor Platform

**Files to modify:**

- `custom_components/ha_integration_domain/sensor/__init__.py`
- `custom_components/ha_integration_domain/sensor/new_sensor.py` (create)

**Changes:**

1. Create `new_sensor.py` with `NewSensor` entity class
2. Add entity description with proper metadata
3. Register in `__init__.py` async_setup_entry
4. Add translation keys

**Validation:**

- Sensor appears in HA UI
- State updates correctly
- Attributes are present
- No errors in logs

**Dependencies:**

- Phase 1 (coordinator changes) must be complete
```

## Output

Present the plan and ask:

- "Does this approach make sense?"
- "Should I proceed with Phase 1?"
- "Any adjustments needed?"

Never start implementation without explicit confirmation.
