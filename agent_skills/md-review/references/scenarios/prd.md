# PRD Scenario Checklist — Product Requirements Document

Enabled when the scenario parameter is `prd`. Checks whether the product requirements document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Is the requirement source traceable to the MRD or user research?
2. Are acceptance criteria quantified (e.g., response time, success rate)?
3. Is priority (P0/P1/P2) explicitly assigned?

## Key Focus
User stories + feature flows + business rules
- Includes: **Requirements List** (a uniquely numbered list of all functional points)

## Required Content (deduct if missing)

### Requirements Definition
- [ ] **Background**: Is the reason for building this product/feature stated (problem/opportunity/market driver)?
- [ ] **Target Users**: Is the target user group clear (persona/scenarios)?
- [ ] **User Stories**: Are the key user stories complete (As X, I want Y, so that Z)?
- [ ] **Requirements List**: Are functional requirements numbered (FR-1, FR-2...), each with a description and priority?

### Functional and Non-Functional Requirements
- [ ] **Feature List**: Does each feature have a clear behavior description?
- [ ] **Non-Functional Requirements**: Are performance/security/usability/compatibility metrics defined?
- [ ] **Priority**: Are requirements tiered (P0/P1/P2 or MoSCoW: Must/Should/Could/Won't)?
- [ ] **Dependencies**: Are dependencies between requirements declared (FR-3 depends on FR-1)?

### Scope and Acceptance
- [ ] **Scope Definition**: Is In-Scope / Out-of-Scope clearly defined?
- [ ] **Acceptance Criteria**: Does each requirement have testable acceptance criteria?
- [ ] **Edge Cases**: Are abnormal inputs/boundary conditions/failure scenarios described?
- [ ] **Test Cases**: Are there test cases for key flows (input → expected output)?

### 5W1H Check (product context)
- [ ] **Who**: Who are the target users?
- [ ] **What**: What features/value does the product provide?
- [ ] **When**: When do users use it?
- [ ] **Where**: In what scenarios/channels do users use it?
- [ ] **Why**: Why do users need it (pain points/motivations)?
- [ ] **How**: How does the product meet the need (flows/interactions)?

### Supporting Documents
- [ ] **Flow/Sequence Diagrams**: Are there diagrams for key flows?
- [ ] **Data Requirements**: Are the involved data fields/storage described?
- [ ] **Release Plan**: Is version planning/milestones described?
- [ ] **Tracking/Metrics**: Are success metrics (KPI/conversion rate) defined?

## Completeness Issue Markers
- Vague requirement descriptions ("better experience" without concrete standards)
- Requirements without numbers (untraceable)
- Untestable acceptance criteria ("the system should work well")

## Scoring Guide
| Finding | Deduction |
|---|---|
| Missing requirements background | -10 |
| Missing target users | -8 |
| Requirements list missing/un-numbered | -15 |
| Missing user stories | -8 |
| Missing non-functional requirements | -8 |
| Missing acceptance criteria | -10 |
| Missing test cases | -10 |
| Scope not defined | -8 |
| Requirements without priority | -5 |
| Edge cases not handled | -3 per occurrence |
| 5W1H missing 2 or more items | -10 |
