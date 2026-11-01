---
# ─────────────────────────────────────────────────────────────────────────────
# name — the lens's identity. Lowercase, one word, no spaces. It is written into
#   session.json as `lens`, appears in report.md, and becomes the OCA domain
#   (`ponder:<slug>`). Pick a noun for the subject area, not a verb for the
#   activity: `observability`, not `observe`.
name: observability

# unit — the singular noun for one gradable thing. This word shows up in every
#   coverage message the agent will read for the rest of the session, so it has
#   to be a thing you can point at and count. See "Choosing a unit" below.
#   A unit is NOT necessarily a file. Here it is a question about production.
unit: signal

# enumerate — the procedure for finding every unit, written as an ordered list
#   the agent follows at the `survey` phase. This is the most important field in
#   the file. coverage = graded units ÷ enumerated units, and coverage < 1.0
#   blocks `stop` with no override — so a weak `enumerate` does not produce a
#   weak score, it produces a *false* score, because the units that were never
#   enumerated can never be graded and never show up as missing.
#   Rules: keep it to numbered steps, and end with a stopping condition that
#   says when the universe is closed. One step per LINE.
#   `ponder start` prints this block at the terminal's own width (COLUMNS, or
#   the window, or 88 off a terminal), and it is safe to write what you mean:
#   a command-shaped line (quotes, a trailing \, a pipe, a flag) is printed
#   verbatim with its own indentation, so a continuation line still reads as
#   the continuation it is and a copied command still runs; prose wraps, and a
#   wrapped numbered step hangs under its own text instead of reading as a new
#   step. Because this is a block scalar, a `#` in here is a character and not
#   a comment, so hex colours, `git log` format strings and trailing `# notes`
#   all survive intact.
#   One authoring rule follows from that: keep every line in here to 78
#   characters or fewer. ponder prints the block under a two-space indent, so
#   78 is exactly what fits an 80-column terminal. A command is never
#   re-flowed, and the eager command-shape test counts a sentence containing a
#   quote as a command too, so anything longer is left to the terminal to
#   soft-wrap wherever it likes.
enumerate: |
  1. List every SLO and every alert rule. Each implies a question someone asks.
  2. List every failure mode the code declares: throw, catch, timeout, retry.
  3. List every dependency. Each adds three questions: up, slow, and lying.
  4. Mine the last ten incident write-ups for every "we could not tell".
  5. Record the telemetry that answers each question, or that none exists.
  6. Deduplicate by question, not by dashboard. Four dashboards, one unit.
  7. Close the universe: every alert, mode and dependency maps to a question.

# dimensions — the rubric axes, lowercase kebab-case slugs. Each becomes the
#   `dimension` field on a finding, so keep them short and stable; renaming one
#   later orphans every finding that used the old name. Five to twelve of them.
#   Fewer than five and you are grading vibes; more than twelve and no pass ever
#   finishes, so the agent starts skipping dimensions and coverage lies again.
#   What makes a dimension good rather than vague is the whole subject of the
#   "Writing dimensions" section below — read it before you edit this line.
dimensions: [answerability, time-to-answer, attribution, alert-actionability, cost-fit, ownership]

# scale — what each rung of 1-5 means for THIS subject. The engine only cares
#   that scores are integers 1-5; these labels are for the agent doing the
#   grading. Keep the spec's spine (1 = broken, 3 = acceptable, 5 = exemplary)
#   and say it in the vocabulary of your subject, so that "3" means something
#   specific rather than "fine, I guess".
scale:
  1: blind - the question cannot be answered at all
  2: answerable only by luck or by reproducing it live
  3: answerable with effort, by someone who knows where to look
  4: answerable quickly by anyone on call
  5: already answered - the signal is on the page that pages you
---

# Custom lens template

Copy this file, rename it, rewrite it for your subject, and run:

```sh
bin/ponder start "our production visibility" --lens custom --rubric lenses/observability.md
```

`--lens custom --rubric <file>` loads any file with the front-matter shape above. Everything
else in ponder — phases, deltas, the four perspectives, the convergence rules, the coverage
gate — works identically whatever the lens says.

The `#` lines in the front matter are ordinary YAML comments explaining each field. Delete
them once you have read them; a lens you keep should read as tersely as the built-in packs
it sits beside.

The rest of this file is two things at once: **instructions for writing a good lens**, and a
**worked example** — an `observability` lens, complete enough to run today. Read the
instructions, then read how the example follows them.

---

## Part 1 — how to write the lens

### Choosing a unit

The unit is the atom of the whole session. Findings join to units by `id`, coverage is
measured in units, and the `blocked` verdict names ungraded units by id. Choose badly and
every downstream number is wrong.

A good unit passes five tests.

1. **Countable.** You can produce a finite list of them and know when the list is finished.
   "The codebase" is not a unit. "One module" is.
2. **Gradable.** A single unit can meaningfully score 1 through 5 on every dimension. If a
   dimension does not apply to some of your units, either the unit is too broad or the
   dimension is too narrow.
3. **Stably identifiable.** The same thing gets the same id next pass and next month. Ids
   derived from line numbers, array positions or file paths that get renamed are not stable.
4. **Mutually exclusive.** Two units do not overlap. If the same defect could reasonably be
   filed against either of two units, the boundary is in the wrong place.
5. **Inclusive of absence.** The unit list must be able to contain things that do not exist
   yet. This is the test most lenses fail. If your units come only from a directory listing,
   you can never find what is missing, and the missing thing is usually the finding that
   matters most.

Test 5 is why the built-in lenses define units the way they do: `docs` units include the
document-shaped holes, `tests` units are behaviours rather than test files, `copy` units
include the empty state nobody designed. This template's units are questions, and a question
with no telemetry behind it is the highest-value unit in the set.

**Id convention.** Lowercase, dotted, hierarchical, with an optional prefix that separates
kinds: `signal.checkout.tenant-attribution`, `gap.signal.queue-backlog-by-tenant`. Write the
convention down in the lens body so the next pass produces the same ids as this one.

### Writing `enumerate` so coverage means something

Coverage is `graded units ÷ enumerated units`, and `coverage < 1.0` blocks `stop` with no
override. That gate is the reason ponder exists — but it only protects you from missing units
you enumerated. Units you never thought of do not lower coverage; they are invisible.

So `enumerate` must **close the universe**: end with an explicit condition that says when the
list is complete, phrased so it can be checked rather than felt.

Good closing conditions look like this:

- "Every alert rule, every declared failure mode and every dependency maps to an enumerated
  question."
- "The three gap enumerators return empty against the unit list."
- "Every route in the router appears exactly once."

Bad closing conditions are the ones that stop at what already exists: "when every file in
`docs/` has a grade", "when every test file has been read". Those measure diligence against
the easy half.

Four more rules for `enumerate`:

- **Prefer commands to judgement.** A command re-runs identically next pass and next quarter.
  A heuristic drifts with whoever reads it.
- **Enumerate from the contract before the artefact.** Deriving the list from what exists
  anchors you to what exists. Derive it from what is promised, then map the artefacts on.
- **Keep enumeration read-only.** An enumeration step that runs the subject's own commands can
  change the thing being graded — and if the subject is a tool with state, it can change *this
  session*. `ponder decide`, `delta`, `apply`, `report` and `abort` all commit, and they
  default to the most recently touched open session in the current project, which mid-review
  is yours. Probe in a throwaway directory, or read the behaviour from source.
- **Calibrate before you trust.** An enumerator that returns nothing on its first run is a
  broken pattern until proven otherwise. Check it finds one hit you already know about, then
  believe the empty result. Every built-in lens carries an example of this failing in real
  life: `grep 'throw new'` finds none of ponder's throws, which all go through a factory
  function; `git log --grep='a\|b'` returns nothing for anyone whose gitconfig sets
  `grep.patternType = extended`. Both fail as silence, which reads exactly like good news.

### The three coverage mechanics every lens author has to know

`coverage` is the gate the whole tool is built around, and three details of how the engine
computes it decide whether your lens can ever reach 1.0.

**A unit is graded when it carries at least one finding that is not `retracted`.** Not one
finding per dimension — one finding, any dimension. So a unit you examined and found perfect
counts as ungraded, coverage never reaches 1.0, and `stop` is refused with no override for the
rest of the session. Say so in your lens body, in as many words: *record a finding even when
the unit is good* — score 5, severity `note`, the anchor, one line on what was checked.

**Retracting a unit's last live finding un-grades that unit.** The Skeptic's merge-the-
duplicates move drops coverage whenever the retracted finding was the only one on its unit,
and the session re-blocks at `decide`. The clean alternatives are `unit-delete` (retire the
unit, which removes it from the denominator and is recorded in the ledger with a `why`) or
`change`ing the finding's status to `resolved`, which still counts as graded.

**Units you never enumerated do not lower coverage — they are invisible.** This is why the
closing condition above is load-bearing, and why a lens whose `gap.`-style units all come back
empty on pass 1 should treat that as evidence the enumerator was skipped rather than evidence
the subject is clean.

### Writing dimensions — good, not vague

This is where most custom lenses fail. A vague dimension produces scores that feel meaningful,
converge quickly, and mean nothing — and because they converge, the loop stops and reports
success.

A good dimension passes six tests.

**1. Observable.** Two people with the same evidence reach the same score. If the score comes
from taste, the dimension is a mood. `elegance` fails this. `time-to-answer`, measured in
minutes with a stopwatch, passes.

**2. Independent.** It can move while the others hold still. If `clarity` and `readability`
always rise and fall together, they are one dimension with two names, and having both
double-counts the same defect in every score.

**3. Named failure mode.** You can describe, from memory, a real score-1 case that has
actually happened and cost somebody something. If you cannot, you do not yet know what this
dimension measures.

**4. Anchored at 1, 3 and 5 with instances, not adjectives.** This is the single highest-value
thing in the whole file. `3: adequate` is not an anchor — it is the word "3" spelled
differently. `3: the alert fires on a real symptom, but the page body is the raw query, so the
responder starts from zero at 3am` is an anchor: it names a situation, and a grader can hold a
real unit next to it and say yes or no.

Write the 1 first. It is the easiest to make concrete and it sets the scale for the rest. Then
write the 5 as something you have actually seen, not an ideal. Then the 3 is whatever sits
between them, and it is the rung that does the most work, because most real units land there.

**5. Actionable at the score.** Knowing a unit scored 2 on this dimension tells you what to do
next. If the score leaves you asking "so what would I change?", the dimension describes a
symptom rather than a property.

**6. Not a synonym for severity.** A dimension measures *quality*; `severity` measures *how
much it matters*. `importance`, `priority` and `risk` are not dimensions — they are the
severity field. Keeping them separate is what lets a lens say "this scores 1 and it is a
`note`", which is a sentence a good rubric needs to be able to make.

**Before you ship the lens**, grade three real units with it by hand:

- If two dimensions always tie, merge them.
- If a dimension never scores below 4, it is measuring nothing; cut it or sharpen the anchor.
- If you cannot recall a dimension's score-1 case without rereading, the anchor is too
  abstract.
- If grading one unit takes more than a few minutes, you have too many dimensions and the
  agent will start skipping them silently.

### What the body owes the agent

Per SPEC section 7, the body of a lens covers five things. Everything below is the worked
example doing exactly that.

1. What a unit is for this lens.
2. How to enumerate exhaustively, with real commands.
3. What each dimension means, with a concrete 1 / 3 / 5.
4. What evidence looks like.
5. What each of the four perspectives is hunting for.

Add severity calibration and a list of the lens's own failure modes. Both pay for themselves
by pass two.

---

## Part 2 — the worked example: `observability`

### What a unit is

A unit is **one question about the running system that somebody will need answered, together
with whatever telemetry answers it today**.

> "Which tenant caused the queue backlog?"

> "Did the 14:02 error spike start before or after the deploy?"

> "Is the OCA Postgres refusing connections, or is it accepting them and answering slowly?"

Consequences:

- A question with no telemetry behind it is still a unit, and it scores 1 on `answerability`.
  These are the units this lens exists to surface.
- A dashboard is not a unit. A dashboard is evidence about several questions, and grading
  dashboards means grading the answers somebody already thought of.
- A metric is not a unit either. An emitted metric that answers no question anyone asks is a
  cost with no benefit, and it shows up here as a bad score on `cost-fit` against whichever
  question it was supposed to serve.
- One question answered by three signals is one unit. Its score reflects the best available
  path to the answer.

**Unit ids.** `signal.<area>.<question-slug>` for a question with telemetry, and
`gap.signal.<area>.<question-slug>` for one without:
`signal.queue.backlog-by-tenant`, `signal.deploy.spike-correlation`,
`gap.signal.oca.refused-vs-slow`.

### How to enumerate exhaustively

The paths below — `ops/alerts/`, `ops/slo/`, `ops/grafana/`, `src/`, `docs/incidents/` — are
this worked example's stack, not ponder's. Run them in this repo and every one reports
`No such file or directory`. That is the point of a template: replace the paths with your
own, keep the *shape* of each enumerator, and keep the closing condition at the end.

**Alerts and SLOs.** Everything that can page someone implies a question.

```sh
grep -rnE '^\s*(alert|expr|for|severity|annotations):' ops/alerts/*.yml
grep -rnE 'objective|slo|budget' ops/slo/*.yml 2>/dev/null
```

**Declared failure modes.** Every place the code gives up is a question someone will ask.

```sh
grep -rn 'throw new' lib/ oca/ src/
grep -rnE 'catch \(|\.catch\(' --include='*.js' src/ lib/
grep -rnE 'setTimeout|AbortController|retr(y|ies)|backoff|circuit' --include='*.js' src/ lib/
```

**External dependencies.** Three questions each — up, slow, lying.

```sh
grep -rhoE 'https?://[a-zA-Z0-9._-]+' --include='*.js' --include='*.yml' src/ lib/ ops/ | sort -u
grep -rnE 'postgres://|redis://|amqp://' --include='*.js' --include='*.env*' .
```

**What is emitted today.** The map from questions to answers.

```sh
grep -rnoE 'logger\.(debug|info|warn|error)\(|metrics\.(increment|timing|gauge|histogram)\(' src/ \
  | sed -E 's/.*(logger|metrics)\.//' | sort | uniq -c | sort -rn
ls ops/grafana/dashboards/*.json 2>/dev/null
jq -r '.panels[].title' ops/grafana/dashboards/*.json 2>/dev/null | sort -u
```

**What the last incidents wished for.** The highest-yield enumerator in this lens.

```sh
git log --since='12 months ago' --oneline -E --grep='incident|postmortem|outage' -i -- docs/
grep -rniE 'could not tell|we did not know|no visibility|had to guess' docs/incidents/
```

**Closing the universe.** Every alert rule, every `throw`, and every external dependency maps
to at least one enumerated question. Run the three greps again at the end of `survey` and
check that each hit is accounted for. If a `throw` maps to no question, either the question is
missing from the list or the failure is genuinely unobservable — which is itself a finding.

### The dimensions

#### answerability

Can the question be answered at all with what is emitted today, at any cost.

- **1** — "Which tenant caused the queue backlog?" — the worker logs job counts and no
  tenant identifier appears anywhere in the pipeline. The question cannot be answered after the
  fact at any price; the only route is reproducing it live and watching.

- **3** — Answerable, but only by SSHing to the host and grepping raw log files, which
  requires production access that three people have and none of them is on call tonight.

- **5** — Answerable from one query on a signal that exists by design.
  `sum by (tenant) (queue_depth)` is on the queue dashboard and quoted in the alert annotation,
  so the answer arrives with the page.

#### time-to-answer

Minutes from question to answer for the person actually on call, including the tool-hopping.
Measured, not estimated — walk it with a stopwatch during a game day.

- **1** — Forty minutes, because answering requires correlating a log line that carries no
  request id against a metric scraped every five minutes, by hand, in two different tools.

- **3** — Six minutes: one dashboard, then one manual log search with a filter you have to
  remember. Acceptable at noon, expensive at 3am, and the six minutes are spent while the
  incident continues.

- **5** — Under sixty seconds. The alert links directly to the panel already filtered to
  the failing dimension, so the first click is also the answer.

#### attribution

Does the signal say *which* — which request, tenant, version, region, route. Volume without
attribution is noise: ten thousand identical errors tell you no more than one.

- **1** — Every error logs `request failed` with no request id, no route, no deploy version
  and no tenant. The only available response is to restart something and see.

- **3** — Request id is present at the HTTP boundary but is not propagated across the async
  boundary into the worker, so every trace ends at the queue and the second half of every
  investigation starts from scratch.

- **5** — Request id, deploy version, tenant and route on every error path, propagated
  through queue and retry, so one identifier stitches the whole story from the click to the
  failed write.

#### alert-actionability

If it pages, is the page worth a human's sleep, and does it tell them what to do.

- **1** — An alert on CPU > 80% for five minutes on a batch host. It fires every night
  during the batch window, everyone has muted the channel, and it will be the first thing
  ignored on the night it means something.

- **3** — Fires on a real user-visible symptom — error rate above 2% — but the page body is
  the raw PromQL query. The responder is awake, correctly, and starts from zero.

- **5** — Fires on a user-visible symptom with an SLO-derived threshold; the page names the
  symptom, the likely causes in order of prior probability, a link to the pre-filtered dashboard
  and a link to the runbook. It has fired four times in six months and every fire was worth
  waking someone.

#### cost-fit

Is the telemetry proportionate to the value of the question — cardinality, volume, retention.

- **1** — A metric labelled with raw user id: two million active series, the single largest
  line on the observability bill, and it appears on no dashboard and in no alert. It is pure
  cost.

- **3** — Cardinality is bounded and reasonable, but debug-level logs are retained for 400
  days and nothing has ever been queried past day three. Nobody is hurt except the budget, and
  the budget is what gets the useful signals cut next quarter.

- **5** — Cardinality bounded by design — tenants bucketed, no unbounded labels — and
  retention set per signal by how far back the question is ever actually asked: thirteen months
  for the SLO series so year-over-year comparisons work, seven days for debug logs.

#### ownership

Somebody is named, and the signal is exercised. An unowned signal decays silently and is
discovered dead at the worst possible moment.

- **1** — The alert routes to a Slack channel with no members. Nobody can name who responds,
  and the last three fires went unread.

- **3** — A team owns it in the routing config, but the runbook link 404s and the person
  who understood the signal left in March. Ownership exists on paper.

- **5** — A named owning team, a runbook that was followed during the last real incident and
  corrected afterwards, and a routing path that is exercised — a quarterly test fire or a real
  fire — so it is known to work rather than assumed to.

### What evidence looks like

| Finding kind | Required evidence |
|---|---|
| `answerability` = 1 | The code path that produces the state, plus the grep proving the identifier is absent: `["src/worker/queue.js:88", "grep -rn 'tenant' src/worker/ → 0 hits"]` |
| `time-to-answer` | A measured number and the route taken, step by step, in `detail` |
| `attribution` | The log or metric emission site, plus the boundary where the context is dropped |
| `alert-actionability` | The alert rule anchor (`ops/alerts/api.yml:31`) plus its fire count over a stated window |
| `cost-fit` | Series count or byte volume, with the query that produced it |
| `ownership` | The routing config anchor plus the last time the path was exercised |

Every finding on this lens needs at least one anchor in version-controlled configuration or
source. "The dashboard is bad" with a screenshot cannot be re-checked next pass.

### Severity calibration

| Situation | Severity |
|---|---|
| A question raised by a past incident that still cannot be answered | `must` |
| An alert that pages and is not actionable — the mute is already happening | `must` |
| No attribution on the failure path of a multi-tenant system | `must` |
| A dependency with no up/slow/lying signal at all | `should` |
| `time-to-answer` above ten minutes on a question that arrives during incidents | `should` |
| Unbounded cardinality with no consumer | `should` |
| Retention longer than anyone queries | `could` |
| A dashboard panel nobody has opened in six months | `note` |

### What each perspective hunts

**Skeptic — `delete`.** Questions nobody has ever actually asked, invented because a metric
existed. Findings whose evidence is a screenshot with no config anchor. `cost-fit` findings
with no measured series count. The same missing attribution filed once per log line — one
finding, at the boundary where the context is dropped, with several anchors.

**Builder — `edit`.** Turn "we need better visibility" into the emission: the field name, the
call site, the label set, and the query that will answer the question once it exists. Turn "the
alert is noisy" into the replacement expression and threshold. A finding on this lens is
actionable when someone could open the file and write the line.

**Dreamer — `add`.** The questions nobody enumerated: the deploy-correlation question, the
"is it us or them" question for every dependency, the "did the retry succeed" question that
hides behind every retry loop, the cost question about the observability stack itself. And the
reframe: this question is unanswerable because the architecture has no seam there — a finding
proposing the seam is worth more than five proposing dashboards.

**Empath — `change`.** Re-rank toward the person holding the pager at 3am with a partial
mental model. A question that arrives during an incident outranks one asked in a planning
meeting, whatever the raw scores say. Raise anything that makes an on-call responder guess.
Lower the completionist urge to instrument code paths nobody will ever ask about.

### Common failure modes of this lens

1. **Enumerating dashboards.** Then coverage 1.0 means "we reviewed the answers we already
   built", which is the opposite of the point.
2. **Grading emitted telemetry instead of answered questions.** A system can emit an enormous
   amount and answer nothing.
3. **Skipping the incident enumerator** because reading old write-ups is slow. It is the only
   enumerator that finds questions from outside the team's current imagination.
4. **Confusing `cost-fit` with severity.** Expensive telemetry that answers a critical question
   scores well on `cost-fit` if the cost is proportionate. The bill is not the rubric.
