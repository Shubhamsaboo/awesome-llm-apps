# Judge Prompt

The prompts are built in code: `scripts/score_rca.py` for the RCA judges, and,
for routing, `optimizer/routing_scorer.py` in the Self-Improving Triage Agent
app (outside this skill). This file records their shape and the rules that keep
them honest.

---

## Routing judge

`team_correct` is **not** a judge call. It is a string comparison in Python
(`_score_one`). A judge adjudicating `"payments" == "payments"` adds variance
and nothing else. The judge only sees the severity cap.

```
You evaluate triage routing decisions. Return valid JSON only.

Issue: {issue_text}
Environment: {environment}
Expected severity: {expected_severity}
Agent's decision: {decision_json}
Criteria: {criteria_json}

For each criterion return passed=true only if unambiguously met.
Return JSON: {"results": [{"eval_id": 1, "passed": true, "reason": "..."}]}
```

---

## RCA check judge

All checks in one call; majority vote across `--runs` passes. Answers are
`true`, `false`, or `"na"`.

```
You audit RCA documents against binary checks. For each check answer true only
if it is unambiguously satisfied by the document as written — not by what the
author probably meant, and not by what you would have written. Answer "na" only
when the check's own precondition is absent, and only where its wording offers
na as an option. Quote the span of the RCA that decides each answer.

# Evidence bundle
{rendered_bundle}

# RCA under review
{rca}

# Checks
{checks_json}

Return JSON: {"results": [{"id": "ev_quotes_log",
                           "passed": true | false | "na",
                           "quote": "the deciding span, or empty"}]}
```

Two properties matter here:

- **"as written, not as meant."** Without it the judge credits intent and every
  RCA scores well.
- **The quote.** It makes a verdict auditable — you can see what the judge read
  as satisfying the check, which is how you find a check that is worded badly
  rather than an RCA that is written badly.

---

## Correctness gate

A separate call, because it asks a different question and must not be averaged
into quality.

```
You compare an RCA's conclusion against a documented root cause. Judge substance
over wording: an equivalent mechanism in different words is correct. Listing the
true cause as one possibility among several is partially_correct. Use
insufficient_evidence when the document declines to conclude and states what
evidence it needs — that is a valid outcome, not a failure.

# Documented root cause
{true_root_cause}

# RCA conclusion under review
{rca}

Return JSON: {"verdict": "correct|partially_correct|insufficient_evidence|wrong",
              "reason": "one sentence"}
```

The gate never sees the case's `expected_correctness`. It classifies what the
document says; the credit matrix in `rca-rubric.json` decides what that is worth.
Showing it the expectation would collapse the two steps and leak the answer.

---

## Hygiene

- **Never** show the judge the mutation diagnosis, the expected verdict, or the
  human label. Each leaks the answer and inflates the score.
- The RCA's `**Session:**` line is stripped before judging. The judge cannot
  open a replay link, and evidence that lives only in the replay must not pass
  an evidence check.
- `temperature=0.0` everywhere. The judge is a measuring instrument; drift in
  the instrument is indistinguishable from drift in the skill.
- **Re-baseline after any edit here.** Scores from before and after a judge
  change are not comparable, and the optimizer will read the discontinuity as a
  win or a regression that did not happen.
- Watch `unstable_checks`. A check that keeps splitting its vote is ambiguous —
  reword the check before raising `--runs` to paper over it.
- Calibrate against human labels (`score_rca.py --calibrate`) before trusting
  absolute values. Relative comparisons survive a biased judge; absolute ones do
  not.
