# Grounding: citing log links and code

Load this when the case has **Logs Explorer links or code attached**. Without
them, skip it: grounding is `n/a` and nothing here is scored.

Grounding is the third score, beside correctness and quality, and never averaged
into either. It asks one thing: is the RCA tied to the links and code it was given?

## How to cite

**A log link.** Paste the attached URL itself, unchanged, next to the claim it
supports. A Markdown link is fine: `[trace 9b2d1f0a41](https://console.cloud.google.com/logs/query;...)`.
Cite only links that were attached. Prefer the one pinned to the incident window
and filtered to the failing trace.

**A code location.** Write `path:line` or `path:start-end` in backticks:
`checkout/orders/repository.py:24`. You may drop leading directories
(`repository.py:24`), but never add ones the attached path doesn't have. Cite
only lines inside the attached snippets.

Only backticked citations are checked; a `path:line` in plain prose is invisible
to grounding. A backticked token counts as code if it names an attached file,
contains a `/`, or ends in a source, config or build extension (`.py`, `.java`,
`.sql`, `.properties`, `.xml`, `.gradle`, ...), so `` `pom.xml:42` `` is checked
like any source line, while `` `db-primary.internal:5432` `` and
`` `10.0.4.12:8080` `` are never mistaken for code. A stack frame copied from the
logs (`` `PaymentClient.java:881` `` appearing in an attached log entry) is
evidence, not an invented citation, outside `## Code`. The match is exact:
`` `PaymentClient.java:88` `` is not that frame, and a range such as
`` `PaymentClient.java:881-890` `` is never a frame. Under `## Code` there is no
exemption: that section claims you read the line in the attached code.

**A code quote.** Put quotes under a `## Code` heading, one per line:

```markdown
## Code
- `path:line` — `the exact line` — why it matters
- `path:start-end` — `first part` … `last part` — why it matters
```

The quote is the backticked text right after the citation, and must be verbatim
at that location. Whitespace is ignored, `…` joins fragments, and fragments must
appear in order. A hyphen inside the backticks is part of the quote. Backticks in
the third field are ordinary inline code, not quotes. An entry under `## Code`
with a citation but no quote fails.

If the code you need is not attached, say so and name the file you would need,
**without a line number**. A line number on an unattached file is an invented
citation. Never reconstruct code from memory.

## The checks

Deterministic checks are decided in code (`scripts/grounding.py`), not by a
judge: a string match is not a judgment call. Judged checks go to the judge.

| Check | Kind | Fails when |
|---|---|---|
| `gr_link_cited` | code | no attached link is cited |
| `gr_no_invented_link` | code, **hard fail** | a cited link was never attached |
| `gr_link_pinned` | code | a cited link uses a relative range ("last hour"), so it will show different logs later |
| `gr_link_scopes_evidence` | code | a cited link misses the symptom window, or filters a trace that is not in the evidence |
| `gr_code_cited` | code | no location inside the attached code is cited |
| `gr_no_invented_code` | code, **hard fail** | a cited `path:line` is not in the attached code |
| `gr_quotes_verbatim` | code, **hard fail** | a quote under `## Code` is not verbatim at its location |
| `gr_code_supports_mechanism` | judge | the cited code is real but does not contain the blamed mechanism |
| `gr_log_to_code` | judge | logs and code are discussed separately, never tied together |
| `gr_link_claim_matches` | judge | the RCA says a link shows something the evidence does not |

A check is `n/a` when its inputs are not attached, so a ticket-only case is
never marked down for lacking links or code.

## Why a hard fail

A made-up code line reads exactly like a real one, and it is the line a reader
copies into a fix. One invented citation makes every other citation in the
document suspect. So a hard fail blocks handoff whatever correctness and
quality say. `score_rca.py` exits 2, the same as a wrong conclusion.

A real link that points at the wrong day is a *miss*, not a fabrication: it costs
points but does not block handoff.

## In the optimizer

Grounding is a constraint, not a term in the objective:

- An edit that adds **any** fabrication the best skill did not have is
  discarded, even if it fixes a different one.
- An edit that lowers grounding is discarded.
- Otherwise an edit is kept if the objective rises, or if the objective is
  unchanged and it strictly removes fabrications.
- A run is not "converged" at 100% while any fabrication remains.

Grounding can veto an edit but never pay for a regression elsewhere. Invented
evidence goes to the analyst as a high-priority failure, and the run's results
report `grounding_pct` and `fabricated`.

## Golden cases

`references/rca-golden-set.json` has three cases for this:

- `gcp-grounded-links-and-code`: fully grounded.
- `gcp-invented-code-line`: identical except for one plausible code line that
  isn't attached. It must hard-fail while quality stays high.
- `gcp-link-wrong-window`: cites a real attached link, but for the previous day.
  It loses points without counting as a fabrication.

Each declares `expected_grounding`, and `tests/test_golden_grounding.py` checks
the deterministic checks reproduce it with no model involved.
