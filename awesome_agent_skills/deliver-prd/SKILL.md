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

## Worked Example

```markdown
## PRD: One-Click Reorder

**Problem**: Returning customers who purchase the same items regularly must re-navigate the catalog, re-add items, and re-enter preferences each time — adding 3-5 minutes of friction to repeat purchases.
**Solution**: A "Reorder" button on past orders that pre-fills the cart with previous items, quantities, and saved preferences.
**Target Users**: Returning customers with 2+ past orders (38% of active customer base)

---

## Goals & Success Metrics

| Metric | Current Baseline | Target | Timeline |
|--------|-----------------|--------|----------|
| Repeat purchase conversion rate | 22% | 35% | 60 days post-launch |
| Time-to-checkout for repeat orders | 4.2 min | <1 min | 60 days post-launch |
| Customer satisfaction (repeat buyers) | 3.8/5 | 4.2/5 | 90 days post-launch |

**Non-Goals**:
- Subscription/auto-reorder functionality (future consideration)
- Reorder across different delivery addresses in a single flow

---

## User Stories

| ID | User Story | Priority |
|----|-----------|----------|
| US-1 | As a returning customer, I want to reorder my last purchase with one click so I don't have to rebuild my cart manually | P0 |
| US-2 | As a returning customer, I want to edit quantities before confirming a reorder so I can adjust for this week's needs | P0 |
| US-3 | As a returning customer, I want to see my 5 most recent orders so I can pick which one to reorder | P1 |
| US-4 | As a returning customer, I want to be notified if a previously ordered item is unavailable so I can substitute before checkout | P1 |

---

## Scope

**In Scope**:
- "Reorder" button on order history and order confirmation pages
- Pre-filled cart with item availability checking
- Quantity editing before checkout
- Handling of unavailable items (notify + suggest removal)

**Out of Scope**:
- Subscription or scheduled reorders
- Reorder from multiple past orders combined into one cart
- Personalized reorder suggestions based on purchase patterns

**Future Considerations**:
- Scheduled reorders — dependent on subscription infrastructure (Q3 roadmap)
- Smart substitutions for out-of-stock items — requires ML recommendation engine

---

## Functional Requirements

### Cart Pre-fill
- FR-1: System shall populate cart with all items from the selected past order at their original quantities
- FR-2: System shall check real-time inventory for each item and flag unavailable products before checkout
- FR-3: User shall be able to modify quantities or remove items from the pre-filled cart before confirming

### Order History Integration
- FR-4: "Reorder" button shall appear on the 5 most recent completed orders
- FR-5: Reorder shall preserve item-level preferences (size, color, customizations) from the original order

---

## Technical Considerations

- **Constraints**: Must work within existing cart API — no new microservice for v1
- **Integration Points**: Inventory service (real-time stock check), Order History API, Cart API
- **Data Requirements**: No new data storage; reads from existing order history records

---

## Dependencies & Risks

| Dependency/Risk | Type | Owner | Impact | Mitigation |
|----------------|------|-------|--------|------------|
| Inventory API latency under load | Risk | Platform team | Med | Cache stock status with 5-min TTL |
| Discontinued SKUs in old orders | Risk | Catalog team | Low | Show "unavailable" badge, allow partial reorder |

---

## Timeline & Milestones

| Milestone | Description | Target Date |
|-----------|-------------|-------------|
| Design review | UX mocks approved | Week 2 |
| API contract | Cart pre-fill endpoint finalized | Week 3 |
| Beta launch | Internal dogfood with employees | Week 5 |
| GA launch | Full rollout to returning customers | Week 7 |

---

## Open Questions

- [ ] Should reorder preserve the original delivery address or default to the current saved address? — Owner: Product
- [ ] How do we handle price changes between original order and reorder? — Owner: Product + Legal
```

## Quality Guidelines

- Problem and "why now" are clearly articulated
- Success metrics are specific and measurable
- Scope boundaries are explicit (in/out/future)
- Requirements are testable and unambiguous
- Technical considerations are surfaced without over-specifying
- Dependencies and risks are documented with owners
- Document is readable in under 15 minutes
