---
agent: "agent"
tools: ["search/codebase", "edit"]
description: "Create Architectural Decision Record for important design choices"
---

# Create Architectural Decision Record (ADR)

Your goal is to document an important architectural or design decision for this Home Assistant integration.

If not provided, ask for:

- What decision needs to be documented
- Context: Why is this decision being made
- Options considered
- Chosen approach and rationale

## ADR Structure

Create a new ADR in `docs/development/adr/NNNN-title-of-decision.md`:

````markdown
# ADR-NNNN: [Title of Decision]

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXXX

**Date:** YYYY-MM-DD

**Decision Makers:** [Who made or approved this decision]

## Context and Problem Statement

[Describe the context and background. What is the issue we're trying to address?]

**Key considerations:**

- [Consideration 1]
- [Consideration 2]
- [Consideration 3]

## Decision Drivers

- [Driver 1: e.g., "Must support HA Core 2024.1+"]
- [Driver 2: e.g., "Minimize API calls"]
- [Driver 3: e.g., "Maintain backward compatibility"]

## Considered Options

### Option 1: [Title]

**Description:** [What is this approach]

**Pros:**

- [Advantage 1]
- [Advantage 2]

**Cons:**

- [Disadvantage 1]
- [Disadvantage 2]

**Implementation impact:** [Low/Medium/High - what needs to change]

### Option 2: [Title]

[Same structure as Option 1]

### Option 3: [Title]

[Same structure as Option 1]

## Decision Outcome

**Chosen option:** Option X - [Title]

**Rationale:**
[Explain why this option was selected over the others]

**Consequences:**

- **Positive:**
  - [Positive outcome 1]
  - [Positive outcome 2]

- **Negative:**
  - [Negative outcome 1 and how we'll mitigate]
  - [Negative outcome 2 and how we'll mitigate]

- **Neutral:**
  - [Things that change but aren't clearly positive or negative]

## Implementation Notes

**Files affected:**

- `custom_components/ha_integration_domain/[file1.py]`
- `custom_components/ha_integration_domain/[file2.py]`

**Code pattern to follow:**

```python
# Example of key implementation detail
```
````

**Testing approach:**

- [How to verify this decision works]

## Validation

**Success criteria:**

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Performance impact:** [None/Minimal/Moderate/Significant - with explanation]

**Breaking changes:** [Yes/No - if yes, explain migration path]

## Links and References

- [Home Assistant Documentation: Relevant Topic](https://developers.home-assistant.io/...)
- [Related GitHub Issue: #XXX](link)
- [Related ADR: ADR-YYYY](./YYYY-related-decision.md)
- [External Reference](link)

## Revision History

- YYYY-MM-DD: Initial decision (Status: Accepted)
- [Future updates go here]

````

## Common ADR Topics for HA Integrations

### Data Management
- Coordinator vs direct API calls
- Caching strategy
- State update frequency
- Data structure in `hass.data`

### Entity Design
- Entity platform choices (sensor vs binary_sensor)
- Device vs device-less entities
- Attribute structure
- Unique ID generation

### Config Flow
- Multi-step vs single-step setup
- Subentry pattern usage
- Options flow organization
- Migration strategy

### API Integration
- Authentication approach
- Error handling strategy
- Rate limiting approach
- Polling vs push updates

### Architecture
- Single device vs multi-device support
- Service implementation location
- Diagnostic data structure
- Extension points for future features

## Process

1. **Number the ADR:**
   - Check existing ADRs in `docs/development/adr/`
   - Use next sequential number (0001, 0002, etc.)
   - Create directory if it doesn't exist

2. **Write the ADR:**
   - Focus on the "why" not just the "what"
   - Include enough technical detail for future maintainers
   - Link to relevant documentation
   - Be honest about trade-offs

3. **Review with developer:**
   - Present the ADR for feedback
   - Adjust based on discussion
   - Update status to "Accepted" when approved

4. **Reference in code:**
   - Add comment references in relevant files:
     ```python
     # Implementation follows ADR-0004: Coordinator Pattern
     ```

## Guidelines

**Be specific:**
- Use concrete examples from this integration
- Reference actual file paths and class names
- Include code snippets when helpful

**Be honest:**
- Document downsides of chosen approach
- Explain what we're giving up
- Note future reconsideration triggers

**Be concise:**
- Focus on the decision, not implementation details
- Link to code rather than duplicating it
- Keep it readable in 5-10 minutes

**Make it actionable:**
- Clear next steps
- Testable success criteria
- Migration path if breaking change

## Integration Context

- **Domain:** `ha_integration_domain`
- **Class prefix:** `IntegrationBlueprint`
- **Architecture docs:** `docs/development/ARCHITECTURE.md`
- **Decisions log:** `docs/development/DECISIONS.md`

Reference existing architecture documentation and ensure the ADR complements it without duplicating content.

## Output

After creating the ADR:
1. Ask if content needs adjustment
2. Suggest adding reference to `docs/development/DECISIONS.md` if it exists
3. Suggest relevant code locations for implementation
4. Ask: "Should I proceed with implementing this decision?"
````
