# TDD Scenario Checklist — Technical Design Document

Enabled when the scenario parameter is `tdd`. Checks whether the technical design document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Are design concepts translated into clear technical specifications?
2. Are system architecture, coding standards, and performance goals defined?
3. Is the technology selection aligned with the design goals?

## Key Focus
System architecture + technology stack + coding standards + performance requirements

## Required Content (deduct if missing)

### Technical Specification Translation
- [ ] **Requirements Mapping**: Are the design document's functional requirements mapped to concrete technical implementations?
- [ ] **Technical Specifications**: Are the implementation specifications of key modules (interfaces, data structures, algorithms) clear?
- [ ] **Traceability**: Can each technical module be traced back to its corresponding design requirement?

### System Architecture
- [ ] **Overall Architecture**: Are the system layering/component division/interaction relationships described?
- [ ] **Module Design**: Are module responsibilities, inputs/outputs, and dependency relationships clear?
- [ ] **Interface Definitions**: Are inter-module interface/API contracts complete (parameters/returns/error codes)?
- [ ] **Data Design**: Are the data model/storage scheme/data flows defined?

### Technology Stack
- [ ] **Technology Selection**: Are the language/framework/middleware choices clear?
- [ ] **Selection Rationale**: Is the technology selection aligned with design goals (with comparison/trade-off explanation)?
- [ ] **Compatibility**: Is the chosen technology stack compatible with existing systems?
- [ ] **Version Locking**: Are dependency versions locked?

### Coding Standards
- [ ] **Coding Conventions**: Are naming/format/code style defined (or referenced from existing conventions)?
- [ ] **Project Structure**: Are the module organization and project structure explained?
- [ ] **Error Handling**: Are unified error handling/logging conventions defined?

### Performance Requirements
- [ ] **Performance Goals**: Are key performance indicators (latency/throughput/resource usage) quantified?
- [ ] **Bottleneck Identification**: Are potential performance bottlenecks and optimization plans explained?
- [ ] **Testing Strategy**: Is the plan for unit/integration/performance testing described?

### 5W1H Check (technical context)
- [ ] **What**: What technical solution is implemented?
- [ ] **Why**: Why is it implemented this way (design intent)?
- [ ] **How**: How is it implemented (architecture/flow)?
- [ ] **Where**: In which modules/systems is it implemented?
- [ ] **When**: What is the implementation sequence/dependencies?
- [ ] **Who**: Who maintains / who depends on this technology?

## Completeness Issue Markers
- Only high-level descriptions without technical specifications (cannot be developed directly)
- Technology selection without rationale ("use X" without comparison)
- Performance goals not quantified

## Scoring Guide
| Finding | Deduction |
|---|---|
| Requirements not mapped to technical implementation | -15 |
| Missing overall architecture | -15 |
| Missing interface definitions | -12 |
| Technology selection without rationale | -12 |
| Missing coding conventions | -8 |
| Performance goals not quantified | -12 |
| Missing testing strategy | -10 |
| Technology stack compatibility not assessed | -8 |
| Module dependencies unclear | -8 |
