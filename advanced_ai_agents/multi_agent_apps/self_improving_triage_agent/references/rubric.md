# Rubric

Why the rubric is shaped the way it is. The machine-readable definition lives in
`rca-rubric.json`; this file explains the four decisions behind it.

---

## Part A — Routing

Binary per issue. An issue passes only if **both** checks pass.

| Check | Passes when |
|---|---|
| `team_correct` | predicted team == expected team, exactly |
| `severity_capped` | non-prod issue is P2 or lower |

Routing accuracy = passing issues / total issues.

A near-miss route costs the same as a wrong one: the ticket lands in the wrong
queue and waits for a human. Partial credit would let the optimizer plateau on
"plausible but wrong".

---

## Part B — RCA

### 1. Binary checks, not 0–4 scores

The original rubric scored seven dimensions 0–4. That reads well and measures
badly: an LLM asked to "rate evidence quality 0–4" returns a number that moves
±1 between identical runs on identical text. A composite built from seven such
numbers drifts ±8 points, which is larger than most real improvements — so you
cannot tell a better skill from a restless judge.

Each dimension is now a handful of questions with one defensible answer:

> Does the RCA reference a trace, span, or correlation ID that appears in the
> evidence bundle?

That is stable across runs because it is checkable, not aesthetic. Composite =
weighted pass rate. The dimensions and weights are unchanged from the original
rubric; only the instrument changed.

Residual variance is handled by **majority vote per check** across N judge
passes, not by taking a median of composites — variance enters at the individual
judgment, so that is where it is suppressed. Checks that split their vote are
reported as `unstable_checks`; a check that keeps splitting is ambiguous and
should be reworded.

### 2. Correctness and quality are never averaged

Two numbers come back:

| | Asks | Needs |
|---|---|---|
| **Correctness** | Did it reach the documented root cause? | ground truth |
| **Quality** | How well is the reasoning evidenced and presented? | always available |

A polished RCA with the wrong conclusion scores high on quality and fails
correctness — `aws-wrong-conclusion` in the golden set scores 89 quality
and `wrong`. One blended number would report ~70 and hide the only fact that
matters. Any `wrong` verdict blocks handoff regardless of quality.

The optimizer hill-climbs `0.6 × correctness + 0.4 × quality`, so a perfectly
formatted wrong RCA caps at 40 and the loop chases conclusions over formatting.

### 3. Correctness is scored against what the case *should* produce

Credit comes from a matrix keyed `[expected][actual]`, not from a fixed target
of "correct":

| Expected | Actual | Credit | Why |
|---|---|---|---|
| correct | correct | 1.00 | found it |
| correct | partially_correct | 0.50 | hedged among options |
| correct | insufficient_evidence | 0.25 | over-cautious; the evidence was there |
| correct | wrong | 0.00 | committed to the wrong cause |
| insufficient_evidence | insufficient_evidence | 1.00 | correctly declined |
| insufficient_evidence | correct | 0.30 | right answer, no evidence — a guess that landed |
| insufficient_evidence | wrong | 0.00 | confident, unevidenced, wrong |

For a ticket with no telemetry, **declining is the pass and concluding is the
failure**. Scoring against a fixed "correct" target would have rewarded guessing
on exactly the cases where guessing is most dangerous.

`insufficient_evidence → correct` earns only partial credit on purpose. An
unevidenced right answer teaches the reader to trust the next unevidenced
answer, and that one will be wrong.

### 4. Checks can be n/a, and weight redistributes

`user_input_handling` asks whether the RCA tested the user's hypothesis. When
the user offered none, those checks answer `na` — they leave both numerator and
denominator. If every check in a dimension is `na`, the dimension is dropped and
its weight is rescaled proportionally across the rest.

Without this, an RCA for a case where the user volunteered nothing would cap at
88 for a gap that was never its fault. With it, the GCP reference RCA scores
85.2 against a human label of 85.

---

## Profiles

Same checks, different weights, chosen by who is reading.

| Profile | For | Weights up | Weights down |
|---|---|---|---|
| `balanced` | handoff gating (default) | the original rubric | — |
| `returning-owner` | you built it, moved on, got tagged a year later | context, timeline, user input | falsifiability |
| `curious` | you want the mechanism | causal chain, context | reproducibility, actionability |

`returning-owner` weights `user_input_handling` highest (0.15): that person
arrives holding a year-old theory, and the most valuable thing the RCA can do is
test it rather than agree with it.

## Bands

Quality: **<60** send back · **60–80** conditional, flag gaps · **>80** hand off.
Correctness `wrong` blocks handoff at any quality.

## Judge hygiene

- Never let the judge see the mutation diagnosis or the expected verdict — both
  leak the answer.
- `temperature=0.0`. The judge is a measuring instrument; drift in the
  instrument is indistinguishable from drift in the skill.
- Re-baseline after any judge-prompt or rubric edit. Scores from before and
  after are not comparable.
- Run `score_rca.py --calibrate` against the human labels before trusting
  absolute values. A mean bias over 10 points means reword the checks the judge
  keeps misreading.
