# TLD Scenario Checklist — Task List Document

Enabled when the scenario parameter is `tld`. Checks whether the task list document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Is the task decomposition granularity reasonable (too large to estimate, too small to manage)?
2. Are dependencies between tasks marked (blocking/parallel)?
3. Are effort estimates based on historical data or expert judgment?
4. Does every task have an explicit owner and acceptance criteria?

## Key Focus
Task decomposition + dependency relationships + effort estimation + owner assignment
- Includes: **Task List** (with ID, description, priority, status, estimated person-days)
- Linked to PRD/ADD, maintained by the engineering manager, dynamically updated

## Required Content (deduct if missing)

### Task Decomposition
- [ ] **Task List**: Are all tasks numbered (T-1, T-2...), with ID/description/priority/status/estimated person-days?
- [ ] **Task Granularity**: Is the decomposition granularity reasonable (0.5-5 person-days per task is recommended; too large to estimate, too small to manage)?
- [ ] **Task Types**: Are tasks categorized (development/testing/documentation/deployment, etc.)?
- [ ] **Deliverables**: Is each task's output/deliverable clear?

### Dependencies and Ordering
- [ ] **Dependency Relationships**: Are dependencies between tasks marked (blocking/blocked/parallel)?
- [ ] **Critical Path**: Is the critical path identified (the chain of tasks that determines total duration)?
- [ ] **Execution Order**: Is the task ordering reasonable (predecessor tasks first)?

### Estimation and Resources
- [ ] **Effort Estimation**: Is a person-day estimate given for each task?
- [ ] **Estimation Basis**: Are estimates based on historical data or expert judgment (rather than gut feeling)?
- [ ] **Owner**: Does each task have an explicit owner/lead?
- [ ] **Resource Conflicts**: Could tasks assigned to the same owner conflict (parallel overload)?

### Status and Acceptance
- [ ] **Priority**: Are tasks tiered (P0/P1/P2)?
- [ ] **Status Field**: Is the status (todo/in progress/blocked/done) defined?
- [ ] **Acceptance Criteria**: Does each task have a testable completion standard (DoD)?
- [ ] **Traceability**: Are tasks linked to PRD/ADD requirement items (traceability)?

### 5W1H Check (task context)
- [ ] **What**: What does each task do?
- [ ] **Who**: Who is responsible (owner)?
- [ ] **When**: When does it start/end (schedule)?
- [ ] **Where**: In which module/system is it implemented?
- [ ] **Why**: Why is this task needed (source requirement)?
- [ ] **How**: How is it completed (dependencies/methods)?

## Completeness Issue Markers
- Unbalanced task granularity (one task of 30 person-days or 0.1 person-days)
- Tasks without owners (nobody responsible = nobody executes)
- Estimates without basis ("about X days" without explanation)
- Tasks without acceptance criteria (completion cannot be judged)

## Scoring Guide
| Finding | Deduction |
|---|---|
| Task list missing/un-numbered | -20 |
| Unbalanced task granularity | -10 |
| Dependency relationships not marked | -12 |
| Missing effort estimates | -12 |
| Estimates without basis | -10 |
| Owner missing | -12 |
| Acceptance criteria missing | -12 |
| Priority missing | -8 |
| Tasks without requirement traceability | -10 |
| Status field not defined | -5 |
