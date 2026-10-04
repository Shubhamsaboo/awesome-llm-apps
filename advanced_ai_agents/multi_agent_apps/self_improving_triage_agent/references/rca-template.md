# RCA Template

Fill every section. "Unknown" is a valid answer and scores better than a
confident guess — the rubric penalizes unevidenced prose.

---

```markdown
# RCA: <one-line symptom>

- **Issue:** <JIRA-key or Teams permalink>
- **Environment:** dev | staging | CI
- **Severity:** P2 | P3 | P4
- **Routed to:** <team>  ·  **Routing signal:** <first error / contract test / roster rule>
- **Symptom window:** <start> – <end> (with timezone)
- **Session:** <output of `scripts/session_link.py`; omit the line if it exits non-zero>

## Intake
What the user supplied. Omit any line they could not answer; omit the whole
section only if they supplied nothing.

- **Trace IDs supplied:** <ids>
- **Reporter's hypothesis:** <verbatim, hedges included>
- **Reporter's context:** <do they own this service? how long since they worked on it?>
- **Already ruled out by reporter:** <what, and how>

## Verdict on the reporter's hypothesis: CONFIRMED | REFUTED | UNTESTED
Include this section whenever a hypothesis was offered. Lead with the verdict,
then the single piece of evidence that decided it. If refuted, say so plainly —
do not soften it. If the hypothesis was partly right, say which part and which
part was not.

Omit this section entirely when no hypothesis was offered. Do not invent one.

## Symptom
What is observably wrong. No interpretation.

## Evidence
| Signal | Source | What it shows |
|---|---|---|
| | | |

Correlation IDs: `<ids>`

## Hypothesis
- **Observation:**
- **Hypothesis:**
- **If true, we expect:**
- **If false, we expect:**

## Validation
Methods from `validation-methods.md` that were actually run, and their results.
Include the falsification test and its outcome.

## Causal chain
symptom ← mechanism ← trigger. One arrow per hop, no gaps.

## Scope and ownership
Which component owns the defect, and the evidence that pins the boundary
(ideally a contract test). Name what is explicitly *out* of scope.

## Reproduction
Numbered, deterministic steps. Env and fixture state included.

## Timeline
| Time | Event |
|---|---|

## Recommended next step
One concrete action the owning team can start on. Not a fix — a starting point.

## Open questions
What is still unknown, and what would resolve it.
```

---

## The Session line

A link to the AgentsView replay of the session that wrote this RCA: every query
run and every hypothesis dropped. It is for the reader, not the scorer —
`score_rca.py` strips it before judging, so anything that matters must also be
cited in **Evidence**. The link is `127.0.0.1` and opens only on the author's
machine; say so if you hand the RCA to someone else.

## When there is no evidence

Do not fill this template from a ticket narrative alone. Every evidence check
fails by construction and the result is confident fiction. Take the
`insufficient_evidence` path in `intake-ticket.md` and output an evidence
request instead.

## Common score-killers

- Causal chain that jumps from symptom straight to trigger with no mechanism
- Hypothesis with no falsification prediction
- "Started after the deploy" offered as a cause
- Owner named without boundary evidence — the top cause of re-routes
- Adopting the reporter's hypothesis as the conclusion without testing it
- Quietly dropping their hypothesis instead of returning a verdict on it
