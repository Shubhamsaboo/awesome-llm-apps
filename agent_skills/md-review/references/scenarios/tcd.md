# TCD Scenario Checklist — Test Case Document

Enabled when the scenario parameter is `tcd`. Checks whether the test case document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Do the cases cover all happy-path flows, boundary values, and exception scenarios?
2. Are the prerequisites clear (e.g., user state, data preparation)?
3. Are expected results verifiable (not vague descriptions)?
4. Is a traceability relationship established with requirement items in the PRD/FSD?

## Key Focus
Case numbering + test steps + input data + expected output + prerequisites
- Includes: **Test Case Set** (with linked requirement IDs, priority, execution result)
- Written by the QA team; the basis for automation scripts and manual testing

## Required Content (deduct if missing)

### Case Structure
- [ ] **Case Numbering**: Does each case have a unique number (TC-1, TC-2...)?
- [ ] **Case Title**: Is the title descriptive ("verify successful login" rather than "case 1")?
- [ ] **Test Steps**: Are test steps numbered and executable (1. 2. 3.)?
- [ ] **Input Data**: Is the input data explicit (including boundary values/special characters)?
- [ ] **Expected Output**: Are expected results verifiable (specific values/status codes/behavior, not "normal")?

### Scenario Coverage
- [ ] **Happy-Path Flows**: Are the normal paths of the main features covered?
- [ ] **Boundary Values**: Are boundary/extreme value tests covered (minimum/maximum/critical values)?
- [ ] **Exception Scenarios**: Are abnormal/failure paths covered (invalid input/timeout/insufficient permission/network failure)?
- [ ] **Null/Over-length/Concurrency**: Are null values, over-length inputs, and concurrency scenarios covered?

### Prerequisites and Traceability
- [ ] **Prerequisites**: Are each case's prerequisites clear (user state/data preparation/environment)?
- [ ] **Requirement Traceability**: Are cases linked to requirement IDs in the PRD/FSD (traceability)?
- [ ] **Priority**: Are cases tiered (P0 critical path/P1 important/P2 general)?

### Execution and Management
- [ ] **Execution Result**: Is there a field to record execution results (pass/fail/blocked)?
- [ ] **Automation Flag**: Is it marked whether the case can be automated (as the basis for automation scripts)?
- [ ] **Linked Defects**: Is there a defect-link field (corresponding bug ID on failure)?

### 5W1H Check (testing context)
- [ ] **What**: What feature/scenario is tested?
- [ ] **Who**: Who executes it (QA/automation)?
- [ ] **When**: When is it executed (smoke/regression/pre-release)?
- [ ] **Where**: In what environment is it executed (test/staging)?
- [ ] **Why**: Why test it (which requirement does it verify)?
- [ ] **How**: How is it tested (steps/data/tools)?

## Completeness Issue Markers
- Vague expected results ("the system runs normally", "no exceptions")
- No prerequisites (executors don't know how to prepare)
- Cases without requirement traceability (coverage cannot be proven)
- Only happy-path flows covered (no boundary/exception)

## Scoring Guide
| Finding | Deduction |
|---|---|
| Case numbering missing | -15 |
| Test steps not executable | -12 |
| Expected results not verifiable | -15 |
| Boundary values not covered | -10 |
| Exception scenarios not covered | -12 |
| Prerequisites missing | -10 |
| No requirement traceability | -12 |
| Cases without priority | -5 |
| No execution result field | -5 |
| Incomplete coverage (happy path only) | -10 |
