---
name: triage-issue
description: Triage a non-prod incident or bug report by investigating
  logs/traces/tickets, forming an RCA hypothesis, routing to the owning team,
  and scoring the RCA against a rubric before handoff. Use when the user asks
  to triage, investigate, root-cause, route, or RCA an issue — especially
  cross-team issues where the fix is out of scope and evidence quality matters
  for the handoff. Also use for "score this RCA", "review this incident
  writeup", or "who owns this bug."
---

# Triage Issue

Read this file, then load **only** the reference the chosen path names. Do not
read every reference up front.

## 1. Intake — ask before investigating

Ask once, as a single grouped question. Accept "I don't know" for any item.

1. **Trace / correlation IDs** — these scope everything, so ask first.
2. **Their own analysis** — "What do you already think is happening?" Capture it
   verbatim, hedges included.
3. **Symptom window** — when it started; when it was last known good.
4. **Where the signals live** — GCP Logs Explorer, AWS CloudWatch, a
   Jira/GitHub ticket, or nothing yet.
5. **What they already ruled out**, and how.

A user hypothesis is a **candidate to falsify, not a conclusion to confirm**.
Test it, then say plainly whether the evidence confirmed or refuted it — never
hedge to be agreeable, and never promote it on the user's confidence alone. If
none was offered, omit the section rather than inventing one to knock down.

## 2. Pick the path

| What intake produced | Load only | Outcome |
|---|---|---|
| Logs / traces / metrics | `references/evidence-schema.md` | full RCA |
| A Jira or GitHub ticket, no telemetry | `references/intake-ticket.md` | **evidence request**, not an RCA |
| Both | both of the above | full RCA; the ticket seeds intake |
| Neither | `references/intake-ticket.md` | evidence request |

Normalize any vendor export with `scripts/normalize_evidence.py` first, so the
evidence shape is identical across GCP and AWS.

**The no-evidence path is a real outcome, not a failure.** With no telemetry,
state `insufficient_evidence`, list what is needed, and give the exact query to
fetch it. A confident RCA built only on a ticket narrative is the worst possible
output — it reads as authoritative and rests on nothing.

## 3. Investigate (evidence path)

1. **Gather** — start from the intake trace IDs, then widen to the symptom window.
2. **Form the hypothesis** as: observation → hypothesis → predicted if true →
   predicted if false.
3. **Validate without fixing.** Load `references/validation-methods.md` for the
   eight techniques and which one settles a given dispute.

## 4. Route to the owning team

Pick exactly one team from `references/team-roster.md` (load it now). Route on
the **failing component**, not the surface symptom: when two teams plausibly own
it, the first non-retryable error in the trace decides.

## 5. Write and score

- Write using `references/rca-template.md`. For its **Session** line, run
  `scripts/session_link.py`; omit the line if it exits non-zero.
- Score with `scripts/score_rca.py --rca <doc> --evidence <bundle>`. The rubric
  lives in `references/rca-rubric.json`; `references/rubric.md` explains it.
- Two numbers come back and are never averaged: **correctness** (did it reach the
  documented cause?) and **quality** (weighted pass rate over the checks).
- If Logs Explorer links or code were attached, a third comes back: **grounding**.
  Load `references/grounding.md` before writing: it sets how to cite them.

**Handoff gate** on quality: <60 send back · 60–80 conditional, flag gaps ·
\>80 hand off with reproduction. Any `wrong` correctness verdict blocks handoff
regardless of quality, and so does citing a link or code line that was never
attached.

### Profiles

Pass `--profile` to match the reader:

- `balanced` — handoff gating (default)
- `returning-owner` — you built it, moved on, and got tagged a year later;
  weights context and timeline over falsification paperwork
- `curious` — you want to understand the mechanism; weights causal chain and
  readability

## Severity for non-prod issues

Non-prod (dev/staging/CI) caps at **P2**. Reserve P0/P1 for production customer
impact.

- **P2** — blocks a team or a release candidate
- **P3** — degraded, workaround exists
- **P4** — cosmetic

## When to skip scoring

- Sev-1 in flight: triage first, score in the retro
- Trivial bug with an obvious cause: overkill
- No evidence yet: take the `insufficient_evidence` path instead

## Reference map

Load on demand, not up front.

| File | Load when |
|---|---|
| `references/evidence-schema.md` | normalizing or reading telemetry |
| `references/grounding.md` | the case has Logs Explorer links or code attached |
| `references/intake-ticket.md` | the input is a Jira/GitHub ticket |
| `references/team-roster.md` | routing |
| `references/validation-methods.md` | choosing how to confirm a hypothesis |
| `references/rca-template.md` | writing the document |
| `references/rca-rubric.json` | scoring |
| `references/rubric.md` | why the rubric is shaped this way |
| `references/rca-golden-set.json` | calibrating the judge, or wanting a worked example |
| `references/examples.md` | routing exemplars and the symptom-collision pairs |
