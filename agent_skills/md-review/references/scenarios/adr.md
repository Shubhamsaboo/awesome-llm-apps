# ADR Scenario Checklist — Architecture Decision Record

Enabled when the scenario parameter is `adr`. Checks whether the architecture decision record contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Is the context sufficient (can a newcomer understand the decision background)?
2. Are at least 2 rejected alternatives listed with the reasons for rejection?
3. Is the impact scope (affected modules/services) clearly marked?

## Key Focus
Decision context + trade-off logic + consequence estimation

## Required Content (deduct if missing)

### Decision Record Structure (Nygard template)
- [ ] **Status**: Is the decision status marked (Proposed / Accepted / Superseded / Deprecated)?
- [ ] **Context**: Is the decision's context/background sufficient (problems, constraints, driving factors)?
- [ ] **Decision**: Is the decision itself clear (what was chosen, what was not)?
- [ ] **Rationale**: Why was this decision made (comparative analysis, trade-offs)?
- [ ] **Alternatives**: Are other considered options listed along with the reasons they were rejected?
- [ ] **Consequences**: Is the impact of the decision stated (positive/negative, costs, migration impact)?

### Decision Quality
- [ ] **Title**: Is the title descriptive ("Adopt PostgreSQL instead of MySQL" rather than "Database selection")?
- [ ] **Number**: Is there a unique number (ADR-001)?
- [ ] **Date**: Is the decision date marked?
- [ ] **Decision Maker**: Are the decision makers/reviewers recorded (if applicable)?
- [ ] **Supersession Record**: Are the reasons stated when a decision is superseded/deprecated?

### 5W1H Check (decision context)
- [ ] **Why**: Why is this decision needed (driving factors)?
- [ ] **What**: What was decided (solution/technology/architecture choice)?
- [ ] **When**: When was the decision made (point in time/triggering conditions)?
- [ ] **Where**: Impact scope (which modules/systems are affected)?
- [ ] **Who**: Who made the decision / who is affected?
- [ ] **How**: How is it implemented / how is the migration done?

### Relationships with Other Documents
- [ ] Are the related architecture documents/code locations referenced?
- [ ] Do affected systems have corresponding documents?
- [ ] Does it conflict with existing ADRs (should be cross-checked)?

## Completeness Issue Markers
- Only conclusions without context (the "why" cannot be understood)
- Rejected alternatives not listed
- Consequences not stated (nobody knows the impact after the decision)

## Scoring Guide
| Finding | Deduction |
|---|---|
| Missing context | -20 |
| Missing decision | -20 |
| Missing rationale | -15 |
| Missing alternatives | -15 |
| Missing consequences | -15 |
| Status not marked | -10 |
| Title not descriptive | -5 |
| No number/date | -5 |
| Conflict with existing ADRs not stated | -10 |
