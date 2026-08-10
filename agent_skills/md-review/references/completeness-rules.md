# Completeness Rules — Detailed Rules for Content Completeness

## Document Type Classification

First determine the document type; different types have different completeness standards:

| Document type | Typical characteristics | Applicable standard |
|---|---|---|
| **Requirements doc** | Describes what to build, user flows, acceptance conditions | Requirements standard |
| **Technical proposal / RFC** | Describes technical decisions, architecture options, trade-off analysis | Proposal standard |
| **Design doc** | Describes system design, interface definitions, data flow | Design standard |
| **Tutorial / Guide** | Guides the user through operational steps | Tutorial standard |
| **Reference doc** | API reference, configuration instructions, spec definitions | Reference standard |
| **General description** | Doesn't fit the above | General standard |

## General Completeness Standard (applies to all types)

### Basic Structure

- [ ] **Title**: a clear and unique H1 title (MD025)
- [ ] **Overview**: the first 1-3 paragraphs state the document's purpose and scope
- [ ] **Logical progression**: sections ordered by the reader's comprehension sequence
- [ ] **Conclusion/Summary**: the document has a clear ending (not required but recommended)

### Content Depth

- [ ] Every point fully elaborated (no fewer than 2 sentences)
- [ ] Key concepts and terms defined at first occurrence
- [ ] Every section has a clear reason to exist
- [ ] No "orphan paragraphs" (paragraphs unrelated to the rest)

### Completion Markers

Scan for these markers:

- [ ] Incomplete markers: "TODO", "FIXME", "HACK", "TBD", "WIP"
- [ ] Empty section headings (heading with no content after it)
- [ ] Placeholder text (e.g., "lorem ipsum")

## System Design Document Standard (10 required sections)

> Applies to system-level design documents (full architecture, multiple modules). For module-level or single-system designs, use the [Design Document Standard](#design-document-standard) below instead.

- [ ] **Background and Goals**: why? what problem does it solve?
- [ ] **Scope Definition**: In-Scope / Out-of-Scope
- [ ] **Overall Architecture**: system topology diagram, core components, interaction relationships
- [ ] **Module Design**: each module's responsibility, input, output, dependencies
- [ ] **Interface Design**: API definitions, parameters, return values, error codes
- [ ] **Data Model**: ER diagram, key table structures, data flow
- [ ] **Deployment Architecture**: environment division, service topology, resource configuration
- [ ] **Non-Functional Requirements**: performance, security, availability, scalability metrics
- [ ] **Risk Assessment**: technical risks, business risks, mitigation plans
- [ ] **Milestones**: implementation plan, acceptance criteria

## PRD Standard

The authoritative PRD required-content checklist lives in `references/scenarios/prd.md` — load it when reviewing with scenario `prd` and use its deduction scale. Do not apply a different scale here. For quick reference, the required sections are: Requirements Background, User Stories / Use Cases, Feature List, Flow / Sequence Diagrams, Data Requirements, Acceptance Criteria, Release Plan.

## API Document Standard

The authoritative API required-content checklist lives in `references/scenarios/api.md` — load it when reviewing with scenario `api` and use its deduction scale. Do not apply a different scale here. For quick reference, the required sections are: Interface Overview, Authentication, Request/Response Format, Error Code Definitions, Examples, Change Log.

## Requirements Document Standard

Applies to generic requirements documents that do not match the PRD scenario (e.g., plain requirement specs without product framing). For product requirements, use the PRD Standard above / `references/scenarios/prd.md`.

### Required Sections

- [ ] **Background and Goals**: why this requirement is needed
- [ ] **Users/Roles**: which roles are involved
- [ ] **Key Flows**: core user flows or feature flows
- [ ] **Acceptance Examples**: concrete acceptance conditions and examples
- [ ] **Open Questions**: record unresolved issues

### Content Completeness Checks

- [ ] Each requirement has a unique number (R1, R2...)
- [ ] Each flow has a happy path and an exception path
- [ ] Acceptance conditions testable (QA can clearly determine pass/fail)
- [ ] Priority marked (P0/P1/P2 or must-have/should-have)
- [ ] Edge cases considered

## Technical Proposal / RFC Document Standard

Uses the SCQA framework:

### SCQA Structure

- [ ] **Situation**: the current technical background and context clearly described
- [ ] **Complication**: the problem or deficiency of the current solution clearly stated
- [ ] **Question**: the core question to be resolved posed
- [ ] **Answer**: a clear solution or recommendation given

### Additional Requirements

- [ ] Multiple options compared (at least the rejected ones mentioned)
- [ ] Implementation plan present
- [ ] Migration/rollback plan present (if applicable)
- [ ] Impact on other systems considered
- [ ] Performance/security/compliance considerations

## Design Document Standard

> Applies to module-level or single-system design documents. For full system architecture designs, use the [System Design Document Standard](#system-design-document-standard-10-required-sections) above.

### Required Sections

- [ ] **Overview**: one-sentence description of the module's responsibility
- [ ] **Interface Definition**: type signatures / function signatures / API definitions
- [ ] **Data Flow**: complete chain of input → processing → output
- [ ] **Edge Cases**: strategies for null values, errors, concurrency conflicts
- [ ] **Tuning Knobs**: configurable parameter names, defaults, impact scope

### Content Depth

- [ ] Interface definitions include input/output types
- [ ] Data flow diagram or sequence diagram (if necessary)
- [ ] Bidirectional dependency declaration (A depends on B, B's doc mentions A)
- [ ] Verification/testing strategy

## Tutorial / Guide Standard

- [ ] **Prerequisites**: what the reader needs to prepare
- [ ] **Steps**: numbered and executable operation steps
- [ ] **Examples**: key steps have copyable commands or code
- [ ] **Expected Output**: lets the reader confirm success
- [ ] **Troubleshooting**: solutions for common problems

## Reference Document Standard

- [ ] **Completeness**: covers all relevant configuration/API/parameters
- [ ] **Examples**: every configuration item or API has a usage example
- [ ] **Defaults**: all defaults marked
- [ ] **Value Ranges**: valid ranges for parameters

## Scoring Guide

| Finding | Deduction |
|---|---|
| Missing overview | -2 |
| Missing required sections (per document type) | -1 each |
| Incomplete markers (TODO/TBD) | -1 each |
| Key terms undefined | -1 each |
| Single-sentence paragraphs (need expansion) | -0.5 each |
| No conclusion/summary | -1 |
