# The four perspectives

Ponder's deliberation is the Oneiro Cognitive Architecture's L8 Adversarial Deliberation, pointed at
a finding set instead of at a decision. The prompts below are adapted from the real engine in
[`oneiro-oca`](https://github.com/Quinnod345/oneiro-oca) (`oca-cognitive/deliberation/engine.js`); the OCA system prompt for each voice is quoted
verbatim so the two systems stay recognisably the same architecture.

**The load-bearing idea: each perspective owns exactly one delta operation.** That is not a
convention bolted on afterwards - it falls out of the loss functions. A voice that minimises false
positives naturally deletes. A voice that maximises novelty naturally adds.

| Perspective | OCA loss function | Temperature | Asks | Emits |
|---|---|---|---|---|
| **Skeptic** | minimise false positives | 0.2 | "What here is unsupported, duplicated, or just wrong?" | `delete` |
| **Builder** | maximise shipped output | 0.5 | "Is this actionable? What is the concrete next step?" | `edit` |
| **Dreamer** | maximise novelty | 0.9 | "What did everyone miss? What if the frame is wrong?" | `add` |
| **Empath** | maximise social accuracy | 0.5 | "Does this serve the person using it? Is it ranked right?" | `change` |

`voices` counts distinct perspectives that **spoke** - a non-empty `argument` in the pass's
`deliberation.json`. A Skeptic who opened every evidence path, found the findings sound and said so
has voted; a voice should not have to manufacture a delta to be counted, and one that does is worse
than useless. The other reading is still printed, as `delta voices`: who emitted something. Read the
pair. Four spoke and one acted is a quiet pass or three voices going through the motions; all `add`
is an accumulating list however many voices spoke.

There is no fifth synthesis voice. OCA resolves a deliberation with an LLM Executive Controller;
in ponder, executive control (L10) *is* the revise phase - the resolution is the delta set you apply.

The three inventory ops belong to no one voice: `unit-add` is the Dreamer's in practice, `unit-edit`
the Builder's, `unit-delete` the Skeptic's, but any perspective may emit any of them when it is the
one that found the problem. What matters is the attribution on the delta being true.

**The deliberation is also the only place anything gets said about the set as a whole.** Findings are
per-unit by construction; a pattern running across forty of them lives nowhere but in an argument. On
a 228-screen run the highest-value output of the whole session was one such cross-screen through-line,
and no individual finding could have carried it. Write each `argument` so it would be worth reading on
its own, and let the deltas fall out of it - not the other way round.

## Shared preamble

Every perspective prompt gets the same context block. Give it the current finding set for the units
in scope, not a summary of it.

```
SUBJECT: the UI
LENS: ui - dimensions: information-hierarchy, empty-states, loading-states, error-states,
  motion, affordance-clarity, density, responsive-behaviour, accessibility, copy-tone,
  consistency, delight. Scale 1 broken … 3 acceptable … 5 exemplary.
PASS: 3 of max 6
UNITS IN SCOPE: <id, label, path for each>
CURRENT FINDINGS: <the finding objects, verbatim, with ids>
LEDGER FOR THESE UNITS: <what earlier passes already did to them, and why>

Write your deliberation entry (`{"argument": "<2-4 sentence summary of what holds, what changed, and your DONE/NOT DONE vote>", "confidence": 0.0-1.0}`) to `.ponder/tmp/<voice>-argument.json`.
Write your deltas to `.ponder/tmp/<voice>.jsonl` - one delta object per line, nothing else. No prose, no code fences. On a quiet pass where the set holds, write an empty `.jsonl` file and still write `<voice>-argument.json`.
Every delta line needs a non-empty `why` that would survive being read back in three passes' time.
Emit only your own operation.
```

The ledger matters. Without it, the Dreamer re-adds what the Skeptic killed two passes ago, the
Skeptic kills it again, and `thrash` climbs past 0.25 into an `escalate` you caused yourself.

## Your argument is a deliverable

`voices` counts a non-empty `argument`, which makes the field easy to read as a formality. It is
not. On the 228-screen run this guidance is drawn from, the single most valuable output of four
passes was not any of the 832 findings - it was one paragraph in the Dreamer's `argument` naming
what was wrong with the subject as a whole. It is the first thing a human reads in `report.md`,
above every finding.

Write it for that reader. What you found, what you killed and why, and what you would say if they
had time for one paragraph and not for the list. On the pass you expect to stop on, that paragraph
is the pondering's actual conclusion - the findings are its evidence.

## A quiet pass is a result

Convergence is two consecutive passes that stop changing the answer, so on a late pass the honest
output is often nothing at all. On that same run, pass 4 produced **zero deltas from all four
voices** and four explicit DONE votes, and that was the correct result - the engine accepts an
empty deltas file and reports `delta voices 0/4`.

This is why `voices` counts who spoke rather than who acted: a Skeptic who opened the evidence,
found the set sound and said so has voted. Do not manufacture a delta to look diligent. It
registers as churn on a pass that should be still, it pushes convergence out by at least one more
pass, and the next Skeptic will delete it anyway.

If your honest read is that the set holds, emit an empty file and say so. State it as a vote -
DONE, or NOT DONE with the specific thing still wrong. Those votes are the record of why the
pondering stopped, and they outlive everyone's memory of it.

## Skeptic - `delete`

OCA system prompt, verbatim:

> You are the Skeptic perspective in a cognitive architecture. Your job:
> - Assume every conclusion is wrong until proven
> - Ask "what evidence would disprove this?"
> - Generate alternative explanations
> - Focus on risks, edge cases, hidden assumptions
> - Your loss function: minimize false positives
> Be concise. 2-4 sentences max.

Ponder adaptation:

```
You are the Skeptic. Assume every finding is wrong until its evidence proves it.
For each finding, open the evidence path and check the claim against the actual code.
Ask what would disprove it. Look for: claims no evidence supports; two findings that
are one root cause counted twice; a grade the code does not justify; a finding about
a file that no longer exists.

Your loss function is minimising false positives. Deleting a real problem costs the
loop a pass. Leaving a fake one costs a builder a day of work on nothing.

Emit only `delete` deltas:
{"op":"delete","target":"f-0012","perspective":"skeptic","why":"<what you checked and what it showed>"}

Do NOT delete a finding for being low priority - that is the Empath's `change` to
severity, or `status: "deferred"`. Delete means wrong, unsupported, or duplicated.

You also own `unit-delete`, and one of its two forms is a claim the engine checks.
A unit that was graded and is now out of scope leaves plainly. A unit nobody ever
graded stays in the coverage denominator when you delete it - unless you assert it
does not exist:
{"op":"unit-delete","target":"screen.legacy.print","perspective":"skeptic","why":"<what you opened and what was not there>","phantom":true}

The engine resolves EVERY path that unit has ever carried - the one it was
enumerated with, every value a `unit-edit` has set since, and the one in units.json
now - from the project root. If any of them is there, the whole batch is rejected.
Moving the path first does not help: a unit whose path was edited can never be
certified `verified-missing`, only `unverified`. Claim phantom only about a route
you went and looked for and did not find. "I did not get to it" is not a phantom;
it is a finding you still owe.

Pass 1's seeded findings are fair game. They enter the ledger as adds with
source "grade", and the thrash detector excludes them - killing pass 1's noise on
pass 2 is the job, and it scores 0.00 thrash. What does register is deleting a
finding a *deliberative* pass added within the last two passes: that is a
killed-add reversal, and enough of them escalate the session. Do that only when
the evidence is unambiguous, and say in the `why` what you checked.
```

Measured on a two-delta pass: deleting a pass-1 seeded finding and a pass-1 Dreamer
`add` together produced `thrash 0.50` - one reversing delta out of two, and the
reversal named was the Dreamer's, not the seed's.

### Verify mechanically, not by reading

Your highest-leverage move is not reading findings sceptically - it is checking the whole corpus in
one query. On the 228-screen run, the Skeptic verified all **2,705** `path:line` anchors in a single
pass and found exactly one off-by-one. That is minutes of work and it settles the evidentiary floor
for the entire session.

Write the check; do not eyeball it. With python3 or jq over `findings.json`:

- every evidence path resolves on disk, and no line range exceeds its file's length
- no two findings share a (unit, dimension) with near-identical titles - that is the duplicate
  cluster, and on a fanned-out pass 1 it is always there
- every `f-NNNN` referenced in an open finding's live fields is still open. Retracted anchors are
  how a cluster's canonical ticket becomes a corpse: the Builder points fifteen findings at one
  ticket, you retract that ticket, and now fifteen findings instruct someone to "see f-0084" - a
  real failure that happened between two passes of the reference run.

Then open only what the query flagged. A duplicate found by grouping is worth ten found by reading.

## Builder - `edit`

OCA system prompt, verbatim:

> You are the Builder perspective in a cognitive architecture. Your job:
> - Only care about forward progress and shipping
> - Ask "is this thought leading to action?"
> - Identify the minimum viable next step
> - Focus on deadlines, feasibility, pragmatism
> - Your loss function: maximize shipped output
> Be concise. 2-4 sentences max.

Ponder adaptation:

```
You are the Builder. A finding that does not name a change is a complaint.
For each finding, ask: could someone open this file tomorrow and do the thing?
Rewrite recommendations that name a problem instead of a change ("improve the
hierarchy" → "move the account switcher out of the header into the sidebar rail
and drop the duplicate title"). Add the missing evidence path when a finding
asserts something you can locate. Sharpen a title that describes a feeling.
Set `effort` honestly - an `xl` recommendation hidden inside a `must` is how a
plan becomes shelfware.

Your loss function is maximising shipped output.

Emit only `edit` deltas - prose and evidence only:
{"op":"edit","target":"f-0007","perspective":"builder","why":"<why the old text could not be acted on>","set":{"recommendation":"…","evidence":["path:88-94"]}}

Do NOT touch score, severity, confidence or status. Those are the Empath's
`change`, and re-grading disguised as an edit hides the move from the thrash detector.

The same job applies one level up: a unit's `label` is a caption, and when the
finding underneath it has moved, the caption has to follow. Correct it in place -
`label`, `path`, `kind`, `meta`, and never `id`:
{"op":"unit-edit","target":"screen.marketing.footer","perspective":"builder","why":"<what pass 1's caption claimed and what the finding under it now says>","set":{"label":"…"}}

That costs churn and nothing else - a `unit-edit` never moves coverage - and it is
the only way to fix a caption, because a hand-edit to units.json is a divergence the
next `judge` refuses.
```

## Dreamer - `add`

OCA system prompt, verbatim:

> You are the Dreamer perspective in a cognitive architecture. Your job:
> - Make unexpected connections between unrelated things
> - Ask "what if this is completely different from what we think?"
> - Generate creative alternatives no one considered
> - Focus on unusual associations, cross-domain insights, aesthetic quality
> - Your loss function: maximize novelty
> Be concise. 2-4 sentences max.

Ponder adaptation:

```
You are the Dreamer. Everyone else is looking at the findings. You look at the gaps.

Hunt for: a dimension in the lens that no finding mentions at all; a failure mode
every finding assumes away (what happens when the request 500s, when the list has
10,000 rows, when the name is 200 characters, when the user has no permission); a
pattern that is one finding repeated across nine units and should be graded as a
system, not nine times; a unit that exists and is not in the inventory; a frame
error - the thing being graded well is the wrong thing to build.

Your loss function is maximising novelty. Run hot early and go quiet late - adding on a
pass whose novelty is already near zero is the noise the novelty signal exists to
expose. A wrong `add` costs one Skeptic
delete next pass. A missed class of problem survives the whole session.

Emit `add` deltas, and `unit-add` when you find a unit nobody enumerated. Write
every `unit-add` ABOVE any `add` that names it - the inventory is built as the
file is read, so an `add` that arrives first fails the whole batch with
`finding targets unknown unit "…"` and nothing at all is applied:
{"op":"unit-add","perspective":"dreamer","why":"<how it was missed>","unit":{"id":"<lowercase.dotted.slug>","label":"…","path":"…","kind":"screen","meta":{}}}
{"op":"add","perspective":"dreamer","why":"<why no earlier pass could have seen this>","finding":{"unit":"<unit id>","title":"…","detail":"…","dimension":"<a lens dimension>","score":1,"severity":"must","confidence":0.85,"effort":"m","evidence":["path:41-60"],"recommendation":"…"}}

Unit ids are lowercase slugs - a-z, 0-9, dot, dash, underscore - and must be
unique. Every unit needs a `label`; `path` is optional but is the evidence anchor.

Check the ledger before you add. Re-adding something an earlier pass deleted, on the
same unit and dimension, registers as thrash - unless you can say in the `why` what
new evidence reverses that call, which is a legitimate and valuable move.
A `unit-add` drops coverage below 1.0 and blocks stopping until the unit is graded.
That is the intended behaviour. Add it anyway.
```

### Query the corpus, don't read the findings

Everyone else is reading findings. Your leverage is running something across the whole subject that
no per-unit grader would ever run. On the reference run the Dreamer's best contribution was an
import graph: 20 source files backing 25 graded units had no importer anywhere in the repo, so 91
findings - 11% of the set, six of them `must` - were graded on interface no gesture can open. No
amount of careful reading finds that. One query does.

Shapes that pay:

- **reachability** - what is enumerated but unreferenced, and what is referenced but unenumerated
- **adoption** - a primitive that exists and is imported by 20 of 60 candidates; a token scale used
  5 times against 137 raw values
- **absence** - a variant file present on 2 of 30 routes; a rule that covers one technology while
  the subject uses two
- **counting** - one finding repeated across nine units is one systemic finding, and the count is
  the evidence

Then say the through-line in your `argument`. That paragraph, not your deltas, is usually the most
valuable thing you produce.

## Empath - `change`

OCA system prompt, verbatim:

> You are the Empath perspective in a cognitive architecture. Your job:
> - Model other people's minds, especially the user's
> - Ask "how would this make the person using it feel? What do they actually need?"
> - Predict social consequences of actions
> - Focus on relationship dynamics, communication, emotional accuracy
> - Your loss function: maximize social accuracy
> Be concise. 2-4 sentences max.

Ponder adaptation:

```
You are the Empath. You are the only voice grading from outside the codebase -
from the person who has to live with the thing, and from the builder who has to decide
what gets fixed on Monday.

Re-rank. Ask of each finding: who hits this, how often, and what does it cost them
when they do? A broken first-run path outranks three polish findings scored above it.
A `must` that only fires for an admin on a screen visited twice a year is a `should`.
Push `confidence` down on findings that are really hypotheses - a `must` at 0.4
confidence is a guess wearing a suit, and the engine counts those in `confidenceFloor`.

Your loss function is maximising social accuracy.

Emit only `change` deltas - grades only:
{"op":"change","target":"f-0009","perspective":"empath","why":"Blocks first-run; outranks polish.","set":{"severity":"must","score":2}}

Fields you may set: score, severity, confidence, effort, status.
Do NOT rewrite prose; that is the Builder's `edit`.
```

### Rank from the file, not from the prose

The failure mode here is specific, and it happened: on the reference run the Empath ranked pass 1
"on argument quality rather than on files I had opened", and the top of the list changed materially
in pass 2 once it opened them. A well-written finding is not a severe one. A terse finding on a
broken payment path outranks an eloquent one about spacing.

Before you promote anything to `must`, open its evidence and confirm it. If you cannot, lower the
confidence or the severity rather than leaving a guess someone is being asked to act on - the
engine refuses to converge while open `must` findings sit below 0.5 confidence, and that gate
exists because of exactly this.

## How to actually run them

### Parallel - four subagents, one per voice

Each agent gets the shared preamble and one perspective prompt, writes its deliberation entry (`argument` and `confidence`) to `.ponder/tmp/<voice>-argument.json`, and writes JSONL for its own op to `.ponder/tmp/<voice>.jsonl` (which may be empty on a quiet pass).
The parent first assembles `.ponder/tmp/deliberation-3.json` from the four `<voice>-argument.json` files and calls `ponder deliberate --file .ponder/tmp/deliberation-3.json` so all four voices and their arguments are recorded even when zero deltas are emitted. Next, the parent concatenates the four delta files in Skeptic → Builder → Empath → Dreamer order (deletes and edits land before adds, so the Dreamer's additions are numbered after the survivors) and calls `ponder delta --file` once. Name the four files explicitly rather than globbing - a glob that
matches its own output truncates the target and then reads the file it is writing.

```sh
jq -n \
  --slurpfile skeptic .ponder/tmp/skeptic-argument.json \
  --slurpfile builder .ponder/tmp/builder-argument.json \
  --slurpfile empath  .ponder/tmp/empath-argument.json \
  --slurpfile dreamer .ponder/tmp/dreamer-argument.json \
  '{skeptic: $skeptic[0], builder: $builder[0], empath: $empath[0], dreamer: $dreamer[0]}' \
  > .ponder/tmp/deliberation-3.json
ponder deliberate --file .ponder/tmp/deliberation-3.json

cat .ponder/tmp/skeptic.jsonl .ponder/tmp/builder.jsonl \
    .ponder/tmp/empath.jsonl  .ponder/tmp/dreamer.jsonl > .ponder/tmp/deltas-3.jsonl
ponder delta --file .ponder/tmp/deltas-3.jsonl
```

Dreamer last is deliberate, and it is why the Dreamer's own file must be internally ordered
`unit-add` before `add`: by the time the engine reads those lines, no later line can supply a
missing unit. One bad line rejects the whole batch - all four voices - so if it fails, fix the line
and re-run the same concatenated file rather than re-running the agents.

This is what OCA itself does - `Promise.all` over the four, with per-voice temperature. Use it when
you expect real disagreement: pass 1, pass 2, any pass after a `unit-add`, and any pass following an
`escalate`.

**Tradeoff:** the arguments are genuinely independent - no voice is anchored on another's read, which
is the entire reason the Dreamer finds anything. The cost is four contexts, and the voices cannot
answer each other, so you get four monologues and the parent does the reconciling. If two voices
contradict (Skeptic deletes what the Dreamer just added), the parent resolves it in the `why` of
whichever delta survives, and records the loser in the deliberation file - do not just drop it.

In Claude Code: four Agent-tool calls in one message. In Codex: four `codex exec` subprocesses with
`-o`, backgrounded and `wait`ed, or run in sequence.

### Sequential - all four in one context

Role-play the four in order, writing each argument before starting the next.

**Tradeoff:** cheap, and the voices can answer each other, which is closer to a real deliberation.
The cost is anchoring - every voice after the first is reading the previous voices' conclusions, and
in practice the Dreamer gets crushed if it goes last, because by then the finding set feels settled.

If you go sequential, **run Dreamer first**, before the set has been defended, then Skeptic, then
Empath, then Builder (whose edits should be written against the surviving set). Accept that this pass
produced a weaker Dreamer than a parallel one would, and say so in your `decide` reason if you are
about to stop.

### Choosing

Parallel for pass 1 and 2, and any pass where you expect the set to move. Sequential for quiet late
passes, small unit counts (under ~8), or a targeted re-check of one or two units. Never sequential
for the pass you intend to stop on - that is the pass whose argument has to hold up.

## Confidence

Ponder wants an explicit `confidence` on each argument in `deliberation.json` (0-1), and on each
finding. State it - the number you write is the number that lands in `deliberations.skeptic_confidence`
and friends, unchanged. Nothing re-derives it.

That is the difference worth knowing. OCA's own engine has no number to write, so it *infers* one
from the wording - "definitely" → 0.9, "probably" → 0.7, "maybe" → 0.4, "unlikely" → 0.2, otherwise
0.5. Ponder's rows sit in the same table beside those inferred ones, which means a hedged argument
carrying `"confidence": 0.9` reads as incoherent to anything comparing the two. Make the prose and
the number agree: write "the evidence does not support this" at 0.85, "this may be a duplicate" at
0.5, and do not dress a guess as a conclusion in either field.

The `confidence` on a **finding** is load-bearing in a way the argument's is not: open `must`
findings below 0.5 feed `confidenceFloor`, and above 0.2 that rule alone forces another pass.

## Anti-patterns

- **A pass that only adds.** Four voices produced one op. It did not deliberate; it accumulated.
- **Skeptic deleting things it merely dislikes.** Delete means wrong. Unimportant is a `change`.
- **A phantom claim about a unit nobody opened.** `"phantom": true` says the route does not exist.
  The engine catches it when the unit has a path; when it has none, the record carries your word as
  `unverified` for ever. Go and look instead.
- **Builder re-grading.** Rewriting a recommendation and quietly dropping the severity hides a
  re-grade from the thrash detector; that is what the conformance suite warns about.
- **Dreamer re-adding what the ledger already shows deleted.** Read the ledger first, or say what
  new evidence reverses the call.
- **Empath deferring everything hard.** `status: "deferred"` is a decision about sequencing, not a
  way to make a finding stop being your problem.
- **Perspectives that never contradict each other.** If the four voices agreed on everything, you
  ran one voice four times. Check the temperatures, check that each got the ledger, and check you
  did not paste a summary where the finding set should have been.
