# FSD Scenario Checklist — Functional Specification Document

Enabled when the scenario parameter is `fsd`. Checks whether the functional specification document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Does it cover boundary conditions such as null values, over-length input, and concurrency?
2. Is the business logic unambiguous (engineers no longer need to guess)?
3. Is a state diagram provided when state transitions are involved?

## Key Focus
Input/output definitions + business rules + exception handling (a direct blueprint for writing test cases)
- Includes: **Detailed Functional List** (atomic-level functional decomposition)

## Required Content (deduct if missing)

### Functional Definition
- [ ] **Feature Overview**: Is the overall responsibility of the feature module explained?
- [ ] **Functional List**: Are features numbered (F-1, F-2...), each with a description?
- [ ] **Feature Behavior**: Is each feature's specific behavior/rules defined (trigger condition → action → result)?
- [ ] **Inter-feature Relationships**: Are dependencies/relationships between features explained?

### Functional Details
- [ ] **Input Definition**: Are the feature's inputs (parameters/data/operations) clear?
- [ ] **Output Definition**: Are the feature's outputs (results/responses/side effects) clear?
- [ ] **Processing Logic**: Is the core processing logic/algorithm/rules described?
- [ ] **Exception Handling**: Are failure/exception paths defined?
- [ ] **Boundary Conditions**: Is the behavior for null values/extreme values/invalid input explained?

### Scenarios and Use Cases
- [ ] **Usage Scenarios**: Are typical usage scenarios described?
- [ ] **Use Cases**: Are key use cases complete (main flow/extension flow/exception flow)?
- [ ] **Test Cases**: Does each feature have executable test cases (input → expected output)?
- [ ] **Acceptance Criteria**: Are testable criteria for feature completion defined?

### Priority and Planning
- [ ] **Priority**: Are features tiered (P0/P1/P2 or Must/Should/Could)?
- [ ] **Release Planning**: Are the version/milestone each feature belongs to explained?
- [ ] **Dependencies**: Are dependencies on other modules/systems/data declared?
- [ ] **Effort Estimation**: Is the implementation effort/complexity estimated (if applicable)?

### 5W1H Check (functional context)
- [ ] **What**: What does the feature do?
- [ ] **Who**: Who uses this feature (roles)?
- [ ] **When**: When is the feature triggered/available?
- [ ] **Where**: In which module/page/entry point is the feature located?
- [ ] **Why**: Why is this feature needed (what problem does it solve)?
- [ ] **How**: How is it operated / how is it implemented?

## Completeness Issue Markers
- Vague feature descriptions ("the system should support export" without specific behavior)
- Features without numbers (cannot be traced to implementation)
- Exception paths not described (only the normal flow written)
- Features without test cases

## Scoring Guide
| Finding | Deduction |
|---|---|
| Functional list missing/un-numbered | -15 |
| Incomplete feature behavior definitions | -5 per feature |
| Missing input/output definitions | -5 per occurrence |
| Missing exception handling | -8 |
| Missing boundary conditions | -3 per occurrence |
| Missing use cases | -10 |
| Missing test cases | -10 |
| Missing acceptance criteria | -10 |
| Features without priority | -5 |
| Feature dependencies not declared | -5 |
