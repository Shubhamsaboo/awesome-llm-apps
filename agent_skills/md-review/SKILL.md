---
name: md-review
description: 'Review Markdown documents with scenario-aware weighted scoring, prioritizing bug and logic-error detection over style. Use this skill whenever the user asks to review, audit, check, or grade any Markdown document — review this doc, check the markdown for bugs, find logic errors, verify references, detect redundancy, check formatting, score or grade a document, review a PRD/ADR/API spec/GDD/FSD/MRD/BRD/task list/test case/level design/technical design/concept document, audit documentation, or run a document quality gate before release.'
argument-hint: '[path] [scenario: prd|adr|add|api|brd|mrd|fsd|gdd|gdo|tdd|ldd|concept|tld|tcd] [--dimensions 1-6] [--format full|summary|fix] [--solo] [--pass-threshold N] [--output file] [json]'
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, Bash, SearchExtraTools
model: sonnet
license: MIT
compatibility: Requires python3 (scripts/ for structural analysis, probing, and scoring)
metadata:
  hermes:
    tags: [Markdown, Documentation, Review, Quality]
    category: productivity
    related_skills: [skill-creator]
---

# MD Review — Scenario-Aware Markdown Review

Reviews ONE Markdown document per invocation with scenario-aware weighted scoring. **Core positioning: find bugs and logic errors that would break downstream implementation first, then check whether the document's scenario-specific required content is complete.**

## Scenarios

The scenario is optional. Without one, the review runs in generic mode (the scenario-completeness dimension is skipped).

| Scenario | Document | Required-content focus |
|---|---|---|
| `prd` | Product Requirements Document | requirement list, user stories, acceptance criteria, 5W1H |
| `adr` | Architecture Decision Record | context / decision / rationale / alternatives / consequences |
| `add` | Architecture Design Description | architecture views, quality attributes, interfaces, data flow |
| `api` | API Document | endpoint contracts, error codes, auth, runnable examples |
| `brd` | Business Requirements Document | business goals, ROI, cost/revenue model, 5W1H |
| `mrd` | Market Requirements Document | market analysis, user personas, value proposition, 5W1H |
| `fsd` | Functional Specification Document | functional behavior, use cases, test cases, acceptance criteria |
| `gdd` | Game Design Document | core loop, numbers, test cases, task lists |
| `gdo` | Game Overview Document | executive summary, core concept, design pillars, USP |
| `tdd` | Technical Design Document | system architecture, tech stack, coding standards, performance goals |
| `ldd` | Level Design Document | level layout, player path, challenge configuration, pacing |
| `concept` | Concept Design Document | game concept, market analysis, core selling points |
| `tld` | Task List Document | task decomposition, dependencies, effort estimates, owners |
| `tcd` | Test Case Document | case IDs, test steps, inputs/outputs, requirement traceability |

## Review Dimensions & Weights

| # | Dimension | Weight | Scope |
|---|---|---|---|
| 1. | **Logic (bug detection)** | **30%** | formula/number contradictions, missing edge cases, broken flows (generic, all scenarios) |
| 2. | **Scenario completeness** | **25%** | required content for the scenario (test cases / checklists / 5W1H, etc.) |
| 3. | Sections | 15% | missing required sections, undefined terms, incomplete markers (generic) |
| 4. | References | 10% | broken links, wrong references, version inconsistency (generic) |
| 5. | Redundancy | 10% | duplicated content, low-value information (generic) |
| 6. | Format | 10% | rendering-critical formatting (detailed linting is the editor's job) |

**Overall score = Σ(dimension score × weight)**. Dimensions that don't apply to the document are scored 100.

## Usage

```
/md-review <path> <scenario: prd|adr|add|api|brd|mrd|fsd|gdd|gdo|tdd|ldd|concept|tld|tcd (optional)> [--dimensions 1,2,3,4,5,6] [--format full|summary|fix] [--solo] [--pass-threshold N] [--output file] [json]
```

- **path** — the Markdown file to review
- **Scenario (optional arg 1)** — document scenario; omit to review as generic (skips the scenario-completeness dimension)
- `--dimensions` — restrict to specific dimensions (default: all), e.g. `--dimensions 1,2` (logic + scenario completeness only); when focusing on specific dimensions, Error-level issues must still be flagged. **P0 (blocking) determination is independent of `--dimensions`**: a P0 found in any dimension — including non-focused ones — still sets the solo exit code to `1` and is listed in the report
- `--format` — `full` (default) complete report / `summary` score table only / `fix` report + auto-fix
- `--solo` — non-interactive mode, see Modes below
- `--pass-threshold` — solo-mode exit-code gate on the overall score (default 75)
- `--output` — write the report to a file (useful in solo mode / CI)
- `json` — append to also emit machine-readable JSON output

## Examples

**Example 1: Full review of a single document (interactive)**
Input: `/md-review docs/requirements.md prd`
Output: a review plan first (approval gate), then a full report with weighted scores, bug-level issues, and missing scenario content.

**Example 2: Solo-mode CI gate**
Input: `/md-review docs/requirements.md prd --solo --pass-threshold 75`
Output: report to stdout ending with the `MD-REVIEW-SUMMARY` block; exit code 0 (no P0, score ≥ 75) / 1 (P0 issues or below threshold) / 2 (error).

**Example 3: Score table only**
Input: `/md-review docs/api-spec.md api --format summary`
Output: weighted score table only, no issue details.

## Modes

### Interactive Mode (default)

The full workflow below with approval gates at Phase 0 (review plan) and before any fix. Use `AskUserQuestion` (load it via SearchExtraTools first) when a decision is needed; report obvious findings (broken links, formula errors) directly.

### Solo Mode (`--solo`)

Non-interactive, for CI pipelines and headless invocation. Skips all approval gates, never prompts, and never calls AskUserQuestion:

- Phase 0 runs metadata probing only — no plan is printed and no approval is requested
- `--format fix` applies only safe mechanical fixes automatically (link-text repairs, filler-word replacements, echo-title removals, trailing newlines); anything requiring judgment is reported as unfixed
- Writes the full report to stdout; `--output <file>` also saves it
- Always ends with the machine-readable `MD-REVIEW-SUMMARY` block so CI can parse the result
- Exit codes: `0` = review completed with no P0 (blocking) issues and overall score ≥ `--pass-threshold`; `1` = review completed but P0 issues exist or the score is below the threshold; `2` = error (missing file, invalid arguments)

## Workflow

Core principle: **review phases are read-only**. Files change only after user approval in interactive mode, or in solo mode with `--format fix` — and always after a fix plan is presented (the fix-plan approval is skipped only in solo mode).

### Phase 0: Path Gate & Review Plan (all modes)

1. **Path-argument gate FIRST (all modes)** — run `python3 <skill-dir>/scripts/validate_path.py <path>`; it is the single entry gate and rejects directories, missing files, non-`*.md` files, and binary/undecodable content with a clear stderr message and exit `2`. Proceed only if it exits `0`. Do not run any probe or script before this gate.
2. **Metadata probing** (without a full read): run `python3 <skill-dir>/scripts/probe.py <file>`
3. Print the review plan and wait for approval (interactive only): load example/review-plan.md, fill it in with the probe results, and present it

**In solo mode, the gate and probing still run, but no plan is printed and no approval is requested — go straight to Phase 1.**

After approval, continue to Phase 1. If the user asks for adjustments (e.g. "logic only"), update the plan and continue.

### Phase 1: Initial Understanding

1. **Resolve the scenario and remaining flags**
2. **Classify the document** — read the first 10 lines / frontmatter to guess the type (by content, not by file path); if no scenario was given, try to infer it (SCQA, user stories, interface definitions, architecture diagrams, ...)
3. **Structural analysis** — run `python3 <skill-dir>/scripts/analyze_structure.py <file>` for lines/words/tokens, heading-level distribution, code-block languages, tables/links/images counts, TODO/FIXME markers, and heading skips (H1→H3); then read the document and check for orphan headings

### Phase 2: Single-Document Scope

Review the single document directly across all 6 dimensions in Phase 3. Do **not** recursively follow links out of the reviewed document to review other files — reference links are verified for correctness only (target existence, anchors), never followed as review subjects.

### Phase 3: Dimension-by-Dimension Review

Run the 6 dimensions on the single document. **Load each dimension rule file when running its dimension (the `Rules:` line below); the scenario checklists are read only when that scenario is reviewed.**

#### 1. Logic — bug detection (30%, generic)

The core dimension. Focus on bugs that would make implementation wrong:

- **Formula errors**: undefined variables, inconsistent units, ambiguous evaluation order, division by zero
- **Number contradictions**: same parameter with different values, unit conversion errors, percent vs. multiplier confusion
- **Missing edge cases**: null/zero/negative/extreme values, timeout/retry, concurrency conflicts, data-volume limits
- **Broken flows**: data flow without source or sink, unreasonable operation order, circular dependencies, dead branches
- **Interface inconsistencies**: the same interface with conflicting parameters/returns/error codes across sections
- **Logical fallacies**: causal jumps, overgeneralization, false dichotomy, circular reasoning

Rules: @./references/logic-rules.md

#### 2. Scenario completeness (25%, scenario-specific)

Load the checklist for the scenario and verify every required item, both presence and quality. Each checklist contains "Core Questions" (what editors must address) and "Key Focus". Required content per scenario:

**Report every checklist item individually.** An item that is absent or under-specified must appear as its own entry in the Missing Scenario Content section — do not merge several thin items into one row (e.g. folding an incomplete Physical View into "scalability content") just because the document also has larger P0 defects. Placeholder markers in the source ("no further details", "TBD", "to be defined", "lorem ipsum") count as under-specified.

- **PRD**: requirement list (unique IDs) / user stories / business rules / quantifiable acceptance criteria / 5W1H
- **ADR**: context / decision / rationale / at least 2 rejected alternatives / consequences / impact scope
- **ADD**: module list / system layers / data flow / deployment topology / non-functional requirements / tech-stack compatibility
- **API**: endpoint contracts / error-code list / auth method / runnable examples
- **BRD**: business value / ROI data / cost estimates / external risks / success metrics
- **MRD**: market analysis / real research-backed personas / competitor differentiation / timing window
- **FSD**: atomic function list / inputs-outputs / business rules / state diagrams / edge cases
- **GDD**: core experience / core-loop visualization / system rule interactions / core mechanics list
- **GDO**: executive summary / core concept (1-2 pages) / design pillars / USP / target audience & platform
- **TDD**: technical spec translation / system architecture / tech-stack alignment / coding standards / performance goals
- **LDD**: level list / layout / player path / challenge pacing / metrics / interactive element list
- **Concept**: concept appeal / market potential / competitor analysis / go-no-go rationale / core selling points
- **TLD**: task decomposition granularity / dependencies / effort estimates / owners & acceptance criteria / task list
- **TCD**: positive / boundary / exception coverage / preconditions / verifiable expected results / requirement traceability / test case set

Checklists: load the matching file under references/scenarios/ (prd.md / adr.md / add.md / api.md / brd.md / mrd.md / fsd.md / gdd.md / gdo.md / tdd.md / ldd.md / concept.md / tld.md / tcd.md)

#### 3. Sections (15%, generic)

Context first ("why" before "what"), basic structure (title / overview / progression / conclusion), doc-type required sections, SCQA (for technical proposals), incomplete markers (TODO / TBD / empty sections — **undefined terms and missing edge-case explanations are bug sources**).

Rules: @./references/completeness-rules.md

#### 4. References (10%, generic)

Run `python3 <skill-dir>/scripts/extract_refs.py <file>` first; then check internal links (do the target files/anchors/images exist), external links (URL format / placeholders / text match), link quality (descriptive text, links inside headings, duplicates), version consistency. Reference targets are verified for existence/anchors only — never reviewed as review subjects.

Rules: @./references/reference-rules.md

#### 5. Redundancy (10%, generic)

Word-level redundancy (filler words / hedges / overuse), structural redundancy (echo headings / repeated intros / repeated examples / mergable sections), semantic duplication (>80% similar paragraphs), over-detail (copied install instructions, explained common sense, irrelevant content), decorative elements (excess emoji / dividers), token optimization, reader-focused writing (preamble/closers, tangents, over-long lists, vague estimates, buried actions).

Rules: @./references/redundancy-rules.md

#### 6. Format (10%, generic)

Only rendering-critical and structural issues; detailed linting is the editor's job: unclosed fenced code blocks, unclosed inline code, heading-level skips, multiple H1s, step-numbering breaks in ordered lists (1,2,4 gaps / duplicates), incomplete link syntax.

Rules: @./references/format-rules.md

### Phase 4: Report Generation

#### Weighted scoring (100-point scale)

**Overall = Logic×0.30 + Scenario completeness×0.25 + Sections×0.15 + References×0.10 + Redundancy×0.10 + Format×0.10** — compute it with `python3 <skill-dir>/scripts/score.py <d1> <d2> <d3> <d4> <d5> <d6> [--p0 N]` (validates 0-100 and outputs grade + risk; `--p0` is the P0 issue count)

| Overall | Grade | Action |
|---|---|---|
| 90-100 | Excellent | Ready to publish; minor polish only |
| 75-89 | Good | Fix P0/P1, then publish |
| 60-74 | Passing | Must fix P0 (bug-level) before re-review |
| < 60 | Failing | Rewrite or restructure recommended |

**Risk level**: Low (≥80 and no P0) / Medium (60-79 or few P0) / High (40-59 or multiple P0) / Critical (<40 or a blocking bug)

#### Report template

Load example/report-full.md and fill it in (its in-template notes mark what to omit in generic mode).

### Phase 5: Output & Handoff

1. **Review summary table**: load example/summary-table.md and fill it in

2. **Handoff block** (for downstream tools):

```
MD-REVIEW-SUMMARY
File: <doc> | P0 bugs: N | Scenario gaps: N | Fixable: N | Generated: {timestamp}
```

   Field semantics (CI contract): `P0 bugs` = blocking/bug-level issue count; `Scenario gaps` = missing/under-specified scenario-checklist items; `Fixable` = issues that carry a concrete fix suggestion in the report (mechanical or judgmental). The `--format fix` Auto-Fix Summary separately reports `Fixed: X | Could not auto-fix: Y` (mechanical fixes applied vs. left for judgment) — `Fixable` counts suggestions, not applied fixes.

   The `MD-REVIEW-SUMMARY` block must be the **last line of the output**: when `--output` is used, append it as the final line of the written file too (the report template ends with it), and repeat it in the stdout handoff.

3. **JSON output** (when the user appends `json`): emit machine-readable `{doc, scenario, scores, weights, overall, risk, issues[]}` during the initial run (parameter-driven). If the user later asks for the review in another format in-session, re-emit from the already-computed scores without re-running — see Phase 6 "Regenerate output".

4. **Output self-check** (mandatory): after writing the report with `--output`, verify the written file is the complete report — it contains the sections filled from example/report-full.md (omitting only what generic mode marks to omit) and its last non-empty line is the `MD-REVIEW-SUMMARY` block. If the write failed (permission/disk error) or the file is incomplete, retry the write once; if it still fails, print the full report to stdout and state explicitly that `report.md` was not written. Never leave a partial or placeholder file as the artifact.

### Phase 6: Follow-Up & Re-review

The report is a starting point, not an endpoint. Handle these follow-ups:

1. **Explain findings** — the user asks "why is this a bug?" or "why did dimension Y score low?": answer with the original text as evidence and the concrete impact; no re-run needed.
2. **Focused re-review** — the user fixed specific issues and asks to re-check: re-review only the changed sections or dimensions; list resolved issues and any new ones introduced by the fix.
3. **Full re-review** — after significant edits, re-run the complete review and produce a **delta report**: before/after scores per dimension, and resolved / remaining / new issues.
4. **Delta table** (for 2 & 3): load example/delta-table.md and fill it in

5. **Regenerate output** — the user wants the same review in another format (summary / JSON / markdown table) after the initial run: re-emit from the already-computed scores/issues without re-running (distinct from the parameter-driven `json` flag in Phase 5, which emits during the initial run).

Next steps after a review: fix P0 issues (see Fix Plan below), ask for a focused re-review of a dimension, or re-run `/md-review <path> <scenario>` after edits to track the score.

## Fix Plan

**Never modify the original without first presenting a fix plan and getting approval** — even in `--format fix` mode (solo mode is the exception: mechanical fixes only, applied directly and reported).

Load example/fix-plan.md, fill it in, and present it.

Only after approval, edit with Edit/Write. Mechanical fixes safe to auto-apply without per-item confirmation: link-text repairs, filler-word replacements, echo-title removals, trailing newlines. Mark auto-fixes with ✅ and show diffs; mark un-fixable items with ⚠️.

## Error Handling

- **Path validation (run `scripts/validate_path.py <path>` first)**: rejects directories, a missing file, a non-`*.md` extension, and binary/undecodable content — all with a clear stderr message and exit `2`
- Missing file / binary file / non-UTF-8 encoding: the helper scripts (`probe.py` / `analyze_structure.py` / `extract_refs.py`) also handle these themselves: missing or binary (NUL-containing) input → clear stderr message and exit `2`; non-UTF-8 text that decodes as latin-1 is processed normally
- `extract_refs.py` failure: fall back to manual link checking
- Invalid scenario value (not in the 14 scenarios): list the valid values and review as generic

Solo-mode exit codes (CI gate): `0` = no P0 and score ≥ `--pass-threshold`; `1` = P0 issues exist or score below threshold; `2` = error (missing file, invalid arguments, undecodable input).

## Reference Files

- `references/logic-rules.md` — logic consistency (bug detection) rules — load when running dimension 1 (Logic)
- `references/completeness-rules.md` — section completeness rules — load when running dimension 3 (Sections)
- `references/reference-rules.md` — reference correctness rules — load when running dimension 4 (References)
- `references/redundancy-rules.md` — redundancy detection rules — load when running dimension 5 (Redundancy)
- `references/format-rules.md` — format rules (rendering-critical only) — load when running dimension 6 (Format)

## Scenario Checklists

- `references/scenarios/prd.md` — Product Requirements Document
- `references/scenarios/adr.md` — Architecture Decision Record
- `references/scenarios/add.md` — Architecture Design Description
- `references/scenarios/api.md` — API Document
- `references/scenarios/brd.md` — Business Requirements Document
- `references/scenarios/mrd.md` — Market Requirements Document
- `references/scenarios/fsd.md` — Functional Specification Document
- `references/scenarios/gdd.md` — Game Design Document
- `references/scenarios/gdo.md` — Game Overview Document
- `references/scenarios/tdd.md` — Technical Design Document
- `references/scenarios/ldd.md` — Level Design Document
- `references/scenarios/concept.md` — Concept Design Document
- `references/scenarios/tld.md` — Task List Document
- `references/scenarios/tcd.md` — Test Case Document

## Helper Scripts

- `scripts/validate_path.py` — path-argument gate: validates the target is a single `*.md` file (rejects missing/non-md/binary; exit 2) — run FIRST in Phase 0 (all modes)
- `scripts/probe.py` — metadata probe: lines / words / est. tokens / heading outline / preview (Phase 0)
- `scripts/analyze_structure.py` — structural analysis: heading levels, code-block languages, tables/links/images, TODO/FIXME, heading skips (Phase 1)
- `scripts/extract_refs.py` — extract and classify reference links (target existence is verified manually, used in dimension 4)
- `scripts/score.py` — weighted scoring: overall score, grade, risk, 0-100 validation (Phase 4)

## Templates

- example/review-plan.md — Phase 0 review plan
- example/report-full.md — Phase 4 full report
- example/summary-table.md — Phase 5 summary table
- example/delta-table.md — Phase 6 delta table
- example/fix-plan.md — Fix Plan
