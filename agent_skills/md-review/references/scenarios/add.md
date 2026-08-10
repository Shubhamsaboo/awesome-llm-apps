# ADD Scenario Checklist — Architecture Design Description

Enabled when the scenario parameter is `add`. Checks whether the architecture design description document contains the following content and assesses its completeness.

## Core Questions (editors must address)
1. Are module inputs/outputs and dependency relationships clear?
2. Does it cover non-functional requirements such as performance, security, and scalability?
3. Is the chosen technology stack compatible with existing systems?

## Key Focus
System layering + data flow + deployment topology
- Includes: **Module List** (a list of all subsystems/services)

## Required Content (deduct if missing)

### Architecture Views
- [ ] **Logical View**: Are the system functional decomposition, module responsibilities, and interaction relationships described?
- [ ] **Physical View**: Are the deployment topology and server/node distribution described? Report the view as INCOMPLETE when it is only a sentence or contains placeholder markers such as "no further details", "TBD", "to be defined" — do not fold a thin view into a different checklist item (e.g. scalability); list it explicitly
- [ ] **Data View**: Are the data model, storage scheme, and data flows described?
- [ ] **Interface View**: Are the internal and external interface definitions complete?

### Architecture Elements
- [ ] **Overall Architecture Diagram**: Is there an architecture diagram (ASCII/Mermaid/UML)?
- [ ] **Module Design**: Are each module's responsibilities/inputs/outputs/dependencies explained?
- [ ] **Interface Definitions**: Are API/service interface parameters, return values, and error codes complete?
- [ ] **Data Flow**: Is the core data flow (input → processing → output → storage) closed-loop?
- [ ] **Constraints and Assumptions**: Are technical constraints, business constraints, and assumptions declared?

### Quality Attributes
- [ ] **Quality Attribute Scenarios**: Are scenarios described for performance/availability/security/maintainability/scalability (stimulus → response → measure)?
- [ ] **Reliability**: Single point of failure / fault isolation / degradation strategies
- [ ] **Performance**: Bottleneck identification / caching strategy / asynchronous processing
- [ ] **Security**: Authentication / authorization / data protection / input validation
- [ ] **Scalability**: Horizontal scaling / sharding / plug-in architecture

### Decisions and Evolution
- [ ] **Key Decisions**: Are architecture decisions recorded (linkable to ADRs)?
- [ ] **Trade-off Analysis**: Are the trade-offs of key technology choices explained?
- [ ] **Evolution Path**: Is the future architecture evolution direction described?

### 5W1H Check (architecture context)
- [ ] **What**: What system/subsystem does the architecture describe?
- [ ] **Why**: Why was this architecture adopted (business drivers)?
- [ ] **Who**: Who uses this system / who maintains it?
- [ ] **Where**: Where is it deployed / in what environment does it run?
- [ ] **When**: When are key flows triggered?
- [ ] **How**: How do components collaborate / how is it deployed?

## Completeness Issue Markers
- Only a module list without interaction relationships
- Missing architecture diagram (pure text descriptions are hard to understand)
- Incomplete interface definitions (missing parameters/error codes)

## Scoring Guide
| Finding | Deduction |
|---|---|
| Missing overall architecture diagram | -15 |
| Missing any of logical/physical/data views | -10 per view |
| Missing quality attribute scenarios | -12 |
| Missing interface definitions | -12 |
| Data flow not closed-loop | -10 |
| Missing constraints and assumptions | -8 |
| Missing key decision records | -8 |
| Missing trade-off analysis | -10 |
| Missing reliability/performance/security | -8 per item |
