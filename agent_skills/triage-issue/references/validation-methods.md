# Validation Methods

Techniques for confirming a hypothesis **without** shipping a fix. The point is
a handoff the owning team trusts, not a patch.

## 1. Deterministic reproduction in a lower env

Pin exact inputs, env vars, feature-flag state, and data fixtures. "Happens
sometimes" is not a repro. If it is timing-dependent, say so and give the
window.

## 2. Falsification test

State a prediction that must be **false** if the hypothesis is wrong, then test
it. A test that passes under both the hypothesis and its negation proves
nothing.

## 3. Boundary pinning with a contract test

Assert the interface between two services. A failing contract test names the
owner: the side that broke the contract owns the bug. This is what converts a
routing guess into a routing fact.

## 4. Change-timeline correlation

Line up deploys, config pushes, flag flips, and migrations against the symptom
window with timestamps. Correlation names a trigger, not a cause — see the
anti-pattern in `team-roster.md`.

## 5. Bisection

Over commits, over config, or over traffic slices. Halves the search space per
step and produces the exact delta.

## 6. Differential comparison

Same request against a healthy env and a broken one. Diff the traces. The first
divergence is where to look.

## 7. Load / concurrency isolation

Confirms whether the defect is contention (pool, lock, race) or logic. Run
single-threaded: if it survives, it is contention.

## 8. Dependency pinning

Roll one dependency at a time to the previously known-good version. Confirms
whether the defect came in from outside your code.

---

## Which method resolves a routing dispute

| Dispute | Use |
|---|---|
| "Is it us or upstream?" | contract test (3), differential comparison (6) |
| "Did the deploy cause it?" | bisection (5), timeline (4) |
| "Is it a real bug or flaky infra?" | concurrency isolation (7) |
| "Is it our code or the library?" | dependency pinning (8) |
