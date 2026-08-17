# Full Review Report Template

Fill in this template during Phase 4. Generic mode (no scenario): omit the "Missing Scenario Content" section and the "2. Scenario completeness" row (that dimension is skipped and scored 100) — the in-template notes mark these.

# MD Review Report

## Basic Info

- **Document**: <path> | **Scenario**: [PRD/.../Generic] | **Size**: X lines / X words / ~Y tokens
- **Overall**: X/100 | **Risk**: [Low/Medium/High/Critical]

## Executive Summary

3-5 sentences on document quality: main strengths, key defects (bug-level issues and scenario gaps first), publish recommendation.

## Bug-Level Issues (P0, may break downstream implementation)

| # | Type | Location | Description | Fix | Impact |
|---|---|---|---|---|---|
| 1 | 🔴 Formula error | line 45 | Division by zero unhandled | Add a zero-value branch | Runtime crash |

## Missing Scenario Content ({scenario} required items)

| # | Missing item | Note | Suggestion |
|---|---|---|---|
| 1 | Test cases | Core mechanic has no executable tests | Add input → expected-output cases |

> Generic mode (no scenario): omit this section entirely.

## Issue Summary

| # | Level | Dimension | Location | Description | Suggestion | Impact |
|---|---|---|---|---|---|---|
| 1 | 🔴 Error | Logic | line 45 | Contradictory parameters | Unify defaults | May cause... |

Levels: 🔴 Error (must fix) / 🟡 Warning (should fix) / 🟢 Suggestion (optional)

## Dimension Scores

| Dimension | Weight | Score | Weighted | Issues | Severe |
|---|---|---|---|---|---|
| 1. Logic | 30% | 60 | 18.0 | 5 | 2 (bug-level) |
| 2. Scenario completeness | 25% | 70 | 17.5 | 3 | 1 |
| 3. Sections | 15% | 80 | 12.0 | 2 | 0 |
| 4. References | 10% | 50 | 5.0 | 4 | 1 |
| 5. Redundancy | 10% | 70 | 7.0 | 3 | 0 |
| 6. Format | 10% | 90 | 9.0 | 1 | 0 |
| **Overall** | 100% | - | **68.5** | **18** | **4** |

> Generic mode (no scenario): omit the "2. Scenario completeness" row (the dimension is skipped and scored 100).

## Top 5 Issues

1. [most severe issue, one sentence] ...

## Detailed Issue List

Each issue must include: location (line or section), original text (evidence), level, dimension, description, fix suggestion, impact.

## Fix Priority

**P0 (bug-level / scenario gaps, must fix)**: ... | **P1 (strongly recommended)**: ... | **P2 (optional)**: ...

## Highlights (optional)

[Notable strengths; stay constructive]

## Auto-Fix Summary (--format fix)

- Fixed: X | Could not auto-fix: Y (needs judgment)

---

MD-REVIEW-SUMMARY
File: <doc> | P0 bugs: N | Scenario gaps: N | Fixable: N | Generated: {timestamp}
