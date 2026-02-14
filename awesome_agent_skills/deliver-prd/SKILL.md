---
name: deliver-prd
description: |
  Creates a comprehensive Product Requirements Document that aligns stakeholders on what to build, why, and how success will be measured.
  Use when: specifying features, creating PRDs, defining requirements for engineering handoff, scoping product initiatives,
  or when user mentions PRD, product requirements, feature spec, or engineering handoff.
license: Apache-2.0
metadata:
  author: product-on-purpose
  version: "2.0.0"
---

# Product Requirements Document

You are an expert product manager who creates clear, comprehensive PRDs that bridge the gap between problem understanding and engineering implementation.

## When to Apply

Use this skill when:
- Specifying features, epics, or product initiatives for engineering handoff
- Aligning stakeholders on scope before development investment
- Coordinating multiple teams on a shared deliverable
- Creating reference documentation for development and QA
- After problem and solution alignment, before engineering work begins

## PRD Creation Process

### 1. **Summarize the Problem**
- Start with a brief recap of the problem being solved
- Link to the problem statement if available
- Ensure readers understand *why* this work matters before diving into *what* to build

### 2. **Define Goals and Success Metrics**
- Articulate what success looks like
- Include specific, measurable metrics with baselines and targets
- Connect metrics directly to the problem being solved

### 3. **Outline the Solution**
- Describe the proposed solution at a high level
- Focus on user-facing functionality and key capabilities
- Include enough detail for stakeholders to evaluate the approach without over-specifying implementation

### 4. **Detail Functional Requirements**
- Break down what the system must do
- Use user stories or requirement statements
- Each requirement should be testable — someone should be able to verify if it's met

### 5. **Define Scope Boundaries**
- Explicitly state what's in scope, out of scope, and deferred to future iterations
- Clear scope prevents scope creep and sets realistic expectations

### 6. **Address Technical Considerations**
- Note technical constraints, architectural decisions, or integration requirements
- Surface considerations engineering needs to know without designing the system

### 7. **Identify Dependencies and Risks**
- List external dependencies, assumptions, and risks that could impact delivery
- Include mitigation strategies where applicable

### 8. **Propose Timeline and Milestones**
- Outline key phases and checkpoints
- Help stakeholders understand the delivery plan without committing to specific dates prematurely

## Output Format

```markdown
## PRD: [Feature/Initiative Name]

**Problem**: [Brief recap of the problem being solved]
**Solution**: [High-level description of what we're building]
**Target Users**: [Who will use this feature]

---

## Goals & Success Metrics

| Metric | Current Baseline | Target | Timeline |
|--------|-----------------|--------|----------|
| [Primary metric] | [Value] | [Value] | [Date] |
| [Secondary metric] | [Value] | [Value] | [Date] |

**Non-Goals**:
- [What we're explicitly NOT trying to achieve]

---

## User Stories

| ID | User Story | Priority |
|----|-----------|----------|
| US-1 | As a [user], I want [action] so that [benefit] | P0 |
| US-2 | As a [user], I want [action] so that [benefit] | P1 |

---

## Scope

**In Scope**:
- [Feature/capability 1]
- [Feature/capability 2]

**Out of Scope**:
- [Excluded item 1]

**Future Considerations**:
- [Deferred item] — [Rationale]

---

## Functional Requirements

### [Requirement Area 1]
- FR-1: [Requirement statement]
- FR-2: [Requirement statement]

### [Requirement Area 2]
- FR-3: [Requirement statement]

---

## Technical Considerations

- **Constraints**: [Technical limitations]
- **Integration Points**: [Systems/APIs involved]
- **Data Requirements**: [Storage, migration, privacy notes]

---

## Dependencies & Risks

| Dependency/Risk | Type | Owner | Impact | Mitigation |
|----------------|------|-------|--------|------------|
| [Item] | Dependency/Risk | [Team] | High/Med/Low | [Strategy] |

---

## Timeline & Milestones

| Milestone | Description | Target Date |
|-----------|-------------|-------------|
| [Milestone 1] | [Description] | [Date] |
| [Launch] | [Description] | [Date] |

---

## Open Questions

- [ ] [Question 1] — Owner: [Name]
- [ ] [Question 2] — Owner: [Name]
```

## Quality Guidelines

- Problem and "why now" are clearly articulated
- Success metrics are specific and measurable
- Scope boundaries are explicit (in/out/future)
- Requirements are testable and unambiguous
- Technical considerations are surfaced without over-specifying
- Dependencies and risks are documented with owners
- Document is readable in under 15 minutes

---

*Created for product specification and engineering handoff — from [pm-skills](https://github.com/product-on-purpose/pm-skills), a library of 24 product management agent skills*
