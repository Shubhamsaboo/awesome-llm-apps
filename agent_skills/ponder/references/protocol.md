# Ponder protocol - commands, JSON shapes, verdict rules

The authority for all of this is `~/code/ponder/SPEC.md`. This file is the working reference:
what to type, what to hand it, what comes back. Where this file and SPEC.md disagree, SPEC.md wins.

## Invocation

`bin/ponder` is a POSIX `sh` shim that execs `node lib/cli.js`. Put it on PATH once:

```sh
ln -s ~/code/ponder/bin/ponder ~/.local/bin/ponder    # ~/.local/bin is already on PATH
```

Every command accepts:

| Flag | Meaning |
|---|---|
| `--session <slug>` | Which session to act on. Defaults to the most recently touched **open** session in the current project. |
| `--json` | Machine-readable output on stdout. Use this whenever you are going to parse the result. |
| `--help` | Usage for that command. Same as `ponder help <command>`. |

Exit codes: `0` success, `1` user error (bad flag, missing file, malformed JSON, a delta the engine
refuses), `2` state-machine violation (wrong phase, `decide stop` under a `blocked` verdict, or state
that does not reconcile with the ledger).

**Every command ends with a `NEXT:` line** naming the phase you now owe and the literal command that
satisfies it. That line is the engine driving the agent, and it is what survives a context compaction.

## State layout

Sessions live in `<project>/.ponder/<slug>/`, falling back to `~/.ponder/<slug>/` when the project
path is not writable. Which directory `<project>` is - and what decided that - is under
[`ponder start`](#ponder-start-subject---lens-lens); it is printed every time, and it is what every
relative path in the session resolves against.

```
.ponder/<slug>/
  session.json          identity, config, status, pass history
  units.json            the inventory
  findings.json         the live finding set - current truth
  ledger.jsonl          append-only; every delta ever applied, forever
  passes/NN/
    predict.json        this pass's prediction, written before the work
    deliberation.json   the four perspectives' arguments
    deltas.jsonl        the deltas this pass applied
    metrics.json        computed convergence signals
    verdict.json        engine advice + agent decision + reason
  report.md             written by `ponder report`
  oca.log               every OCA bridge failure, for debugging only
```

Nothing is ever deleted from `findings.json` or `ledger.jsonl`. A `delete` delta sets
`status: "retracted"`. Retraction is a state, not an erasure - a later pass must be able to see, and
reverse, what an earlier pass killed.

**`ledger.jsonl` is written before the state files**, every time. `units.json`, `findings.json` and
`passes/NN/deltas.jsonl` are a view of it, and a crash mid-command can only leave the ledger ahead of
its own view - which `ponder verify --repair` rebuilds deterministically. See
[The ledger is the authority](#the-ledger-is-the-authority).

## Phase machine

`session.phase` names what you owe next. A command that arrives out of order exits `2` and names the
expected phase.

```
predict → survey → appraise → deliberate → revise → judge → decide → (next pass) predict
```

| Phase | Pass 1 | Pass 2+ |
|---|---|---|
| predict | `ponder predict` | `ponder predict` |
| survey | `ponder units` | skipped automatically; amend with `unit-add` / `unit-edit` / `unit-delete` deltas |
| appraise | `ponder grade` | `ponder delta` (same call satisfies revise) |
| deliberate | `ponder deliberate` (or `--skip --why`) | same |
| revise | `ponder delta` | satisfied by the appraise call |
| judge | `ponder judge` | same |
| decide | `ponder decide` | same |

So the command sequence is **predict → units → grade → deliberate → delta → judge → decide** on
pass 1, and **predict → deliberate → delta → judge → decide** on every pass after.

## Commands

### `ponder start "<subject>" --lens <lens>`

```sh
ponder start "the UI" --lens ui --max-passes 6 --min-passes 2
ponder start "our error handling" --lens custom --rubric ./rubrics/errors.md --slug errors-aug
```

| Flag | Default | Meaning |
|---|---|---|
| `--lens <name>` | required | `ui`, `architecture`, `docs`, `tests`, `product`, `copy`, `custom` |
| `--rubric <file>` | - | required with `--lens custom`; any file with the lens front-matter shape |
| `--project <path>` | resolved (below) | The root every relative path in the session resolves against, and where `.ponder/` is rooted |
| `--slug <slug>` | `<subject-slug>-<date>` | Session id. Derived from the *subject*, not the lens, with leading stopwords dropped: `"the UI"` → `ui-2026-08-24`, `"our error handling"` → `error-handling-2026-08-24`. A collision gets a `-2` suffix; an explicit `--slug` that already exists exits `1` |
| `--max-passes N` | 6 | Hitting it produces a `stop` with reason `budget`, never `converged` |
| `--min-passes N` | 2 | Below it, `judge` always advises `continue` |

Ponder has one mode. It deliberates and produces a plan; `ponder apply` is a separate, explicit step
that emits an ordered work plan and still never edits your source.

**The project root, and why the `project` line is worth reading.** Every relative path in the
session - every unit `path`, every finding's `evidence` anchor, every phantom claim checked against
one - resolves from `session.project`. Without `--project`, the engine walks up from the working
directory: first for a project marker (`.git`, `.hg`, `.svn`, `package.json`, `go.mod`,
`Cargo.toml`, `pyproject.toml`, `deno.json(c)`, `Gemfile`, `pom.xml`, `build.gradle(.kts)`,
`composer.json`, `mix.exs`, `*.xcodeproj`, `*.xcworkspace`) - the nearest hit is the root, full
stop - and only if there is no marker anywhere above you, again for an existing `.ponder` to adopt.
Failing both, the working directory. `.ponder` never competes with a marker: it is where sessions
are kept, not what makes something a project.

`start` prints the answer and what decided it, and `session.json` records it in `projectFrom`
(`how`: `explicit` | `marker` | `ponder` | `cwd`):

```
  project   /Users/x/app  (cwd is /Users/x/app/src; matched .git)
  store     /Users/x/app/.ponder/ui-2026-08-24
```

A root from `--project` or a marker is **established**; one adopted from a `.ponder` or fallen back
to is **guessed**, and `start` and `status` warn when it is. A guessed root cannot certify an
absence, so a phantom claim under one is refused (see `ponder delta`). If the printed root is not
where the software lives, start again with `--project <path>` before doing the work.

Creates the session and prints **Prior pondering** - up to five earlier ponder episodes on a similar
subject, read from the OCA's `episodic_memory`. Read them; that is where the last session left off.
No OCA, no section, no problem.

### `ponder predict --churn <0-1> --claim "<one line>"`

```sh
ponder predict --churn 0.35 --claim "Pass 1 over-graded polish and never opened the error paths."
```

Written before you look at anything. `--churn` is your estimate of this pass's `churn` metric
(deltas ÷ live findings), `--claim` is one line about what the pass will find. Scored at `judge` as
`surprise = |predicted − actual|`. Sandbagging the estimate destroys the only signal that says
whether you model the subject yet.

**`--churn` is validated to 0 ≤ n ≤ 1 and exits `1` outside it.** On pass 1 the number does not
matter much: there is no previous pass, so the engine reports no churn and scores no surprise. Write
the honest guess anyway - `--claim` is the part that carries, and the pair is recorded in
`passes/01/predict.json` and in `report.md`. The scoring starts at pass 2, where `churn` exists and
`surprise` is the distance from it. `--claim` is required and must be non-empty - an unstated
expectation cannot be scored.

### `ponder units --file <units.json>` / `--stdin`

Pass 1 only. Later passes amend the inventory with `unit-add`, `unit-edit` and `unit-delete` deltas -
add what the survey missed, correct what it got wrong, remove what is out of scope.

The inventory is written to the ledger too, as a single `unit-seed` record carrying every unit id in
order and every unit body as stored. That is what makes the coverage denominator auditable: an
unledgered inventory is a denominator taken on trust. `unit-seed` is a seed, not a delta - it is
excluded from every convergence ratio and from the delta counts, exactly like `grade` seeding.

### `ponder grade --file <findings.json>` / `--stdin`

Pass 1 only. Seeds the finding set. Every seeded finding is written to the ledger as an `add` with
`source: "grade"`, so the ledger holds every creation - the thrash detector reads those creation
values as the first setting of each field. They are excluded from every ratio, though: a seed is
something the pass created, not something it changed, and counting it as movement is what used to
pin pass 1's numbers near the ceiling. `metrics.json` reports the count separately as
`deltas.seeded`. Grade-sourced adds are also excluded from thrash's killed-add rule, so pass 2
deleting pass 1's noise reads as the Skeptic working, not as the loop oscillating. A seeded finding
may carry its own `why`, which becomes that ledger entry's reason.

### `ponder deliberate --file <deliberation.json>` / `--stdin`

```sh
ponder deliberate --file .ponder/tmp/deliberation-2.json
ponder deliberate --skip --why "Pass 4 was a two-unit re-check; nothing to argue about."
```

`--skip` is legal and is recorded as a `deliberation_skipped` metacognitive observation against the
session. It shows up in `report.md`.

### `ponder delta --file <deltas.jsonl>` / `--stdin`

Applies the pass's revisions in file order, **all-or-nothing**: one bad line on line 40 means nothing
in the batch is applied, and every problem is listed at once with its line number. Every delta needs a
non-empty `why` and a `perspective`. A `unit-add` must sit above any `add` that names the unit it
creates, and above any `unit-edit` or `unit-delete` that targets it - the inventory is built as the
file is read, so the reverse order fails with `unknown unit "…"`.

`--file` also accepts a JSON array of delta objects, not only JSONL. Blank lines are ignored.

### `ponder judge`

Computes the metrics for the current pass, writes `passes/NN/metrics.json`, folds in any open OCA
metacognitive observations as a tie-breaker toward `escalate`, and prints advice. Advice only -
nothing is committed until `decide`.

### `ponder decide <continue|stop|escalate> --why "<reason>"`

Commits your call, closes the pass, and opens the next one (or closes the session on `stop`).

- Every decision needs a `--why`, override or not. It is written to `verdict.json` and, for
  overrides, surfaced permanently in `report.md` under **Overrides**.
- You may override the advice, **except**: `stop` exits `2` and prints the ungraded units whenever
  coverage is below 1.0. There is no flag for it. Note what the gate actually reads - not the verdict
  label on disk, but coverage recomputed from `units.json` and `findings.json` at decision time, so
  a stale or hand-edited `metrics.json` / `verdict.json` changes nothing. `escalate` while blocked is
  legal and warns that coverage still has to reach 1.0 before the session can stop.
- Overriding requires at least 12 characters of `--why`.
- `stop` while `voices < 3` warns and proceeds, naming which perspectives actually spoke in the
  pass's deliberation. A pass that skipped deliberation heard nobody, so it always warns.
- Only a `stop` on reason `converged` closes the session as `converged`; every other stop -
  `budget`, `perseveration`, an override - closes it as `stopped`, and `report.md` says which.

### `ponder status`

Where you are and what you owe: session identity, pass number, phase, unit and finding counts, last
verdict + decision + reason, the project root and what decided it, and the ungraded unit list when
there is one. `--json` for the same thing parseable. **This is the resumption command.** Run it
before concluding anything about a session you did not personally start ten minutes ago - and read
the `project` line while you are there: a session whose root was guessed has been resolving every
path in it against a directory nobody chose, and it says so.

### `ponder verify [--repair]`

Replays `ledger.jsonl` from line 1, derives the state those records must have produced, and compares
it against what `units.json` and `findings.json` actually contain - then compares the ledger against
the per-pass `deltas.jsonl` files, which are the same records written a second time. Exit `0` and a
summary when the session reconciles; exit `2` and the full diagnosis when it does not.

```
ponder verify - ui-2026-08-24
  ledger    41 records - 1 unit-seed, 24 add, 1 unit-add, 2 unit-edit, 1 unit-delete
  passes    41 of those records also in the per-pass delta files, across 4 pass directories
  units     12 in units.json, 12 derived from the ledger
  findings  29 in findings.json, 29 derived from the ledger
  result    reconciles - every unit and every finding is accounted for by a ledger record
```

**Run it first on any session you did not personally start**, and after any interruption. Without
`--repair` it never writes anything, and it takes no lock - it is the one command whose locking
depends on a flag. Full mechanics - what is reconciled, what `--repair` rebuilds and what it refuses
- are under [The ledger is the authority](#the-ledger-is-the-authority) below.

`--json` carries `divergences`, `ledgerProblems`, `unionProblems`, `ledgerSkipped`, `repaired`,
`rebuilt`, `unrepairable` and `counts`, and a failure returns the usual
`{ "ok": false, "error", "detail", "code": 2, "next" }`.

### `ponder report [--out <path>]`

Regenerates the readable summary from current state, in this order: **Convergence**, **Overrides**,
**Prediction vs reality**, **Coverage** (with **Corrected \<units\>** and **Phantom units** under
it), **Findings** grouped by unit, **Retracted**, **Deliberation** pass by pass, and the full
**Ledger**. Safe to run mid-loop.
`--out` redirects it: the report is written to that path **instead of** `.ponder/<slug>/report.md`,
not as well as, so run `ponder report` on its own first if you want the session's own copy refreshed
too. Either way the command prints where it wrote.

### `ponder apply [--dry-run] [--severity must,should]`

Separate and explicit; never part of a pass. Selects `status: open` findings at or above the given
severity (default `must`) and emits an ordered work plan grouped by unit, with evidence paths and
recommendations. `--dry-run` prints it and touches nothing. Without `--dry-run` it prints it, writes
`apply-plan.md`, marks the session `applied` - a terminal status - and records an OCA episodic entry.
**It refuses (exit `2`) without `--dry-run` while the session is still open**, so it cannot close a
pondering behind your back, and **it refuses (exit `2`) either way on an aborted session**
(`session <slug> was aborted; there is no plan to apply.`) - a pondering abandoned mid-loop has
findings nobody finished arguing with, and must not be able to quietly become an applied one. **Ponder never edits the subject's source.** It hands you a plan; you do the work.

### `ponder list` / `ponder abort --why "<reason>"` / `ponder doctor` / `ponder version` / `ponder help`

`list` shows every session both stores can see from here - this project's `.ponder/` and the
`~/.ponder/` fallback - with slug, status, pass, phase, coverage, lens and subject, and prints the
store roots it searched. It takes no arguments; use it to recover a slug you have forgotten. `abort` closes a
session as `aborted` with a permanent reason - use it when the subject changed under you, rather
than silently re-scoping an open session. `doctor` prints node version, `psql` presence, the DSN it
would use, whether the OCA is reachable, where state will be written, the project root it resolves
from here and what decided it, **and whether every session it can see reconciles with its own
ledger** - a session that does not is named under **Problems** with the
`ponder verify --session <slug>` that diagnoses it. A project root adopted from an ancestor
`.ponder` rather than established by a project marker is a **Problem** too, in this directory or in
any session it can see: that is the configuration in which a path that fails to resolve means
nothing, and it is worth knowing before you trust one. Run it first in an unfamiliar harness.

`ponder version` - or `ponder --version` - prints the engine version (`ponder 1.0.0`) and nothing
else; `--json` wraps it in the usual envelope as `version`. `ponder help` lists
every command with its usage line; `ponder help <command>` prints one, and `--help` works on any
command as a flag. Everything the engine can do is discoverable from those two - a command that runs
but is documented nowhere is a command nobody can find.

## File shapes

### `units.json`

```json
{
  "version": 1,
  "lens": "ui",
  "units": [
    { "id": "screen.settings.billing",
      "label": "Settings → Billing",
      "path": "src/routes/settings/billing.tsx",
      "kind": "screen",
      "meta": { "route": "/settings/billing" } }
  ]
}
```

`id` is required, unique, lowercase dotted slug, and **the one field nothing can change** - it is the
join key for findings, so moving it would orphan every finding hanging off that unit. A `unit-edit`
that tries is rejected, exit `1`. `path` is optional but strongly preferred: it is the evidence
anchor, and it is what lets the engine check a phantom claim. `addedInPass` is stamped by the engine.

`label`, `path`, `kind` and `meta` are all correctable by a later pass with a `unit-edit` delta - see
below. A unit that has left the inventory also carries `removedInPass`, `removalKind`
(`appraised` | `removed-ungraded` | `phantom`), and on a phantom `phantomVerification` and
`phantomPath`. All of those are engine-stamped and all of them are reconciled against the ledger.

### `findings.json` (what `ponder grade` takes)

```json
{
  "version": 1,
  "findings": [
    { "unit": "screen.settings.billing",
      "title": "Empty state is a bare 'No invoices' string",
      "detail": "No illustration, no explanation of when invoices appear, no primary action.",
      "dimension": "empty-states",
      "score": 2,
      "severity": "must",
      "confidence": 0.8,
      "effort": "s",
      "evidence": ["src/routes/settings/billing.tsx:88-94"],
      "recommendation": "Add an empty state with cause, expectation and a primary action." }
  ]
}
```

| Field | Values | Notes |
|---|---|---|
| `unit` | a unit `id` | Must exist in the inventory |
| `dimension` | one of the lens's dimensions | Drives duplicate detection and reversal detection |
| `score` | integer 1-5 | 1 broken, 3 acceptable, 5 exemplary; the lens defines each rung |
| `severity` | `must` \| `should` \| `could` \| `note` | |
| `confidence` | 0-1 | Below 0.5 it is a hypothesis, not a conclusion |
| `effort` | `xs` \| `s` \| `m` \| `l` \| `xl` | |
| `evidence` | array of `path:line-line` | The thing that makes a finding arguable instead of an opinion |
| `status` | `open` \| `resolved` \| `retracted` \| `deferred` | Engine-managed; starts `open` |

The engine assigns `id` (`f-NNNN`, never reused), `status`, `createdInPass`, `lastTouchedPass` and
`history`. Do not send them.

### `deliberation.json`

```json
{
  "question": "Does the pass-1 finding set survive a second reading of the code?",
  "skeptic": { "argument": "…", "confidence": 0.85 },
  "builder": { "argument": "…", "confidence": 0.7 },
  "dreamer": { "argument": "…", "confidence": 0.75 },
  "empath":  { "argument": "…", "confidence": 0.7 }
}
```

The four keys and their `argument` / `confidence` map one-to-one onto the OCA `deliberations`
columns (`skeptic_argument`, `skeptic_confidence`, …), which is why this is the shape to write.
`argument` must be a non-empty string; `confidence` is optional and must be 0-1 if present. Fewer
than four keys is accepted, and `deliberate` warns which voices were silent - those are exactly the
ones missing from this pass's `voices`, so a two-key file is a pass that will warn again at
`decide stop`.

Two other shapes are tolerated and mean the same thing - `{"perspectives": {"skeptic": {…}, …}}`
and an array of `{"perspective": "skeptic", "argument": …}` entries. The engine's own error message
advertises the `perspectives` wrapper, so do not be surprised by it; the flat form above is fine.

`question` is optional. It is stored in `passes/NN/deliberation.json` and goes no further - the
`deliberations` row's `decision` column is a string the bridge synthesises (`ponder <slug> pass N:
revise the finding set for "<subject>"`), not your question. The pass's delta summary becomes
`resolution`, with `resolution_method = 'ponder-pass'` - in ponder, the executive-control synthesis
*is* the revise phase.

### `deltas.jsonl` and `ledger.jsonl`

One JSON object per line. You supply `op`, `perspective`, `why`, and the op's payload; the engine
stamps `pass` and `at`.

```
{"op":"delete","target":"f-0012","perspective":"skeptic","why":"Duplicate of f-0004."}
{"op":"add","perspective":"dreamer","why":"No pass had looked at loading states as a set.","finding":{"unit":"screen.dashboard","title":"…","detail":"…","dimension":"loading-states","score":2,"severity":"should","confidence":0.7,"effort":"s","evidence":["src/routes/dashboard.tsx:20-31"],"recommendation":"…"}}
{"op":"edit","target":"f-0007","perspective":"builder","why":"Recommendation was not actionable.","set":{"recommendation":"…"}}
{"op":"change","target":"f-0009","perspective":"empath","why":"Blocks first-run, outranks polish.","set":{"severity":"must","score":2}}
{"op":"unit-add","perspective":"dreamer","why":"Route was missed in pass 1.","unit":{"id":"screen.invite.accept","label":"Accept invite","path":"src/routes/invite/accept.tsx","kind":"screen","meta":{"route":"/invite/:token"}}}
{"op":"unit-edit","target":"screen.marketing.footer","perspective":"builder","why":"Pass 1's label said both links 404; the finding under it now says the opposite, and says it correctly.","set":{"label":"Marketing footer - /privacy-policy resolves","meta":{"route":"/"}}}
{"op":"unit-delete","target":"screen.legacy.print","perspective":"skeptic","why":"Route was removed in #1841; the file is dead.","phantom":true}
```

Seven ops. Four revise the finding set, three amend the inventory.

| Op | Carries | Owner | For |
|---|---|---|---|
| `add` | `finding` (a whole finding object, no `id`) | Dreamer | Ground nobody had covered |
| `edit` | `set` (partial finding) | Builder | Prose and evidence - `title`, `detail`, `recommendation`, `evidence` |
| `change` | `set` (partial finding) | Empath | Grades - `score`, `severity`, `confidence`, `effort`, `status` |
| `delete` | `target` | Skeptic | Unsupported, duplicated, or wrong. Sets `status: "retracted"` |
| `unit-add` | `unit` | any | Inventory amendment. **Drops coverage below 1.0 until the unit is graded** |
| `unit-edit` | `target` (a unit id) + `set` (partial unit) | any | Correcting a unit in place - `label`, `path`, `kind`, `meta`. **Never touches coverage** - see below |
| `unit-delete` | `target` (a unit id), optionally `phantom` | any | Inventory amendment. What it costs coverage depends entirely on whether the unit was ever graded - see below |

The engine does not enforce which fields go with which op, but the conformance suite warns when a
`change` edits only prose - that hides re-grading from the thrash detector. `delete` is for findings
that are wrong, not findings that are unimportant; unimportant is a `change` to `severity`, or
`status: "deferred"`.

### `unit-edit` - correcting a unit in place

A unit's `label` is a caption on the inventory, and captions go stale. Pass 1 writes
`"Billing - both links 404"`; pass 3 opens the file, finds one of them resolves, and rewrites the
finding underneath. Without `unit-edit` the caption keeps saying 404 for ever, and `report.md` ships a
headline contradicting the finding it sits above.

```json
{"op":"unit-edit","target":"screen.marketing.footer","perspective":"builder",
 "why":"Pass 1's label said both links 404; the finding under it now says the opposite, and says it correctly.",
 "set":{"label":"Marketing footer - /privacy-policy resolves","meta":{"route":"/"}}}
```

(Wrapped here to read. In the file it is one object on one line, like every other delta.)

| Field | Rule |
|---|---|
| `target` | a **live** unit id. Unknown unit → rejected. A unit already removed → rejected: *"a unit that has left the inventory is not edited back into shape, it is re-added"* |
| `set` | non-empty object. May set `label`, `path`, `kind`, `meta` - and nothing else. An unknown field is rejected by name: `"note" is not a settable unit field (label, path, kind, meta)` |
| `set.id` | **always rejected, exit `1`**, by name rather than as an unknown field. The id is the join key between `units.json` and `findings.json`; moving it orphans every finding on that unit. If the id itself is wrong, `unit-delete` it and `unit-add` the corrected one, and accept what that costs coverage |
| `why` | required and non-empty, like every delta |

Value rules: `label` must be a non-empty string. `path` and `kind` take a non-empty string or `null`
(clearing a path clears the anchor, not the *history* of the anchor - see the phantom rule below).
`meta` must be an object.

**`meta` merges key by key.** Every other field replaces wholesale. Correcting
`{"route":"/settings/billing"}` on a unit whose meta is `{"route":"/billing","state":"empty"}` leaves
`state` sitting exactly where it was - fixing a route must not silently wipe the state marker beside
it. Replay applies the same merge, so the ledger derives byte-identical state.

What it costs:

- **Coverage: nothing.** A `unit-edit` is neither an addition nor a removal, so the numerator and the
  denominator are both exactly what they were. This is the whole reason it exists: correcting a
  caption with `unit-delete` + `unit-add` would drop coverage below 1.0 and block the stop, which
  turns a wrong caption into a reopened session.
- **Churn: yes.** It is a revising delta. It goes on the ledger, it counts toward `churn`, and it
  participates in thrash detection - a label moved in pass 2 and put back in pass 3 is a
  `field-revert` exactly like a severity flipped back and forth. Reversal is judged on the
  *effective* value, so two edits touching different `meta` keys are not a false reversal.
- **The record: permanent.** Every `unit-edit` appears in `report.md` under **Corrected \<units\>**
  with its pass, its perspective, each field's new value and its `why` - the same treatment a removal
  gets. A hand-edited label in `units.json` with no ledger record behind it is a divergence, and
  every decision-point command refuses the session until it reconciles - which `verify --repair`
  does by putting the ledger's value back. The hand edit loses; that is the design.

### `unit-delete` and the phantom rule

`unit-delete` is the only op that can shorten the ungraded list, which makes it the only op with an
obvious route past the coverage gate: enumerate twelve screens, look at eleven, delete the twelfth.
The engine closes that route. Three outcomes, decided by the engine, not by you:

| The unit | `phantom` | What happens |
|---|---|---|
| carries at least one finding (a retracted one counts - withdrawing a judgment does not un-see the thing) | omitted | **`appraised`** removal. An honest scope change: it leaves the inventory *and* the coverage denominator |
| was never graded | omitted | **`removed-ungraded`**. It leaves the inventory but **stays in the coverage denominator**, still listed as ungraded. Coverage does not move and the gate does not open |
| was never graded | `true` | **`phantom`**, once the engine has checked the claim. Then it leaves the denominator |

A `phantom` claim is checked against **every path the unit has ever carried**, not just the one
`units.json` holds now: the original from its `unit-seed` or `unit-add` ledger record, plus every
value any `unit-edit` has set since, plus the current one - resolved from the project root,
deduplicated, and including a path set earlier in the *same* delta batch.

That is not belt and braces. `unit-edit` can move a `path`, so a claim checked only against the
current value would be a two-delta route through the coverage gate: point a real unit at a filename
that does not exist, then claim the unit never existed and let the engine certify the absence. One
surviving path sinks the claim.

| The unit's paths | Result |
|---|---|
| **any** of them exists | **the whole batch is rejected, exit `1`.** The message names the path found and how it got there: `unit "<id>" is claimed phantom, but a path it has carried exists: <abs> (set by a unit-edit in pass 3). Something you can open is not something pass 1 imagined. A phantom claim is checked against every path the unit has ever had, so editing the path first does not clear it.` |
| exactly one, never edited, and it does not exist | accepted · `verified-missing`, with the checked absolute path recorded |
| the path was ever edited and no version of it exists | accepted · **`unverified`, never `verified-missing`.** Every version was checked and every one was missing, but the engine will not certify an absence about a target that moved. The ledger record carries `pathsChecked`, and `ponder delta` and `report.md` both say so |
| the unit never had a path | accepted · `unverified` - nothing could be checked at all |

Those rows describe a root the engine is sure of: `--project`, or one a project marker established.
Under a **guessed** root - an adopted ancestor `.ponder`, or a working-directory fallback (see
`ponder start`) - a unit with paths and no path that resolves is refused, exit `1`, naming the root
and `--project`: `none of the 2 paths it has carried … resolves under <root> - but that project root
was guessed, not established`. Nothing was really checked, and a file missing from the wrong
directory is not a screen that never existed. A unit that never had a path is unaffected.

So editing a path is never a way to *strengthen* a phantom claim. At best it leaves the claim exactly
where it would have been with no path at all; at worst it is refused outright.

Also refused: `"phantom": true` on a unit that carries a finding (`it cannot also be a unit that never
existed`), `phantom` on any op other than `unit-delete`, a `phantom` that is not a boolean, and a
second `unit-delete` on a unit already removed - with exactly one exception, which is upgrading a
`removed-ungraded` unit to a checked phantom claim once you have gone and looked.

Every accepted phantom is named permanently in `report.md` under **Phantom units**, with its
verification state and your `why` quoted underneath - and the two unverified cases are written
differently there, because they are different claims: *"this unit had no path, so nothing could be
checked"* versus *"this unit's path was edited, so every version of it was checked and none was
found, but the engine will not certify an absence about a target that moved."* A unit deleted while
ungraded is named too, in the **Ungraded** list it never left. That is the deal: you may narrow the
subject, and the narrowing is on the record for ever.

**`phantom` means the route does not exist. It does not mean you ran out of patience.** The engine can
only catch the lie when there is a path to check; the unverified case runs on your word.

### `metrics.json`, `verdict.json` and `judge --json`

`ponder judge --json` prints one envelope. Every command's `--json` has the same outer shape -
`ok`, `command`, `session`, the command's own payload, `warnings`, `next` - and nothing else reaches
stdout, including warnings, which move into the `warnings` array:

```json
{ "ok": true, "command": "judge", "session": "ui-2026-08-24",
  "metrics": { "…": "the metrics.json object, inline" },
  "verdict": "blocked", "reason": "coverage",
  "message": "1 of 12 screen has never been graded. Stopping is not permitted.",
  "ungraded": ["screen.invite.accept"],
  "observations": [],
  "warnings": [],
  "next": { "phase": "decide", "command": "ponder decide continue --why \"<reason>\" …" } }
```

On failure the envelope is `{ "ok": false, "error", "detail", "code", "next" }` and the process exits
with `code`.

`metrics.json` keys: `version`, `pass`, `at`, the eight signals (`coverage`, `novelty`, `churn`,
`thrash`, `surprise`, `stall`, `confidenceFloor`, `voices`), plus `voiceNames`,
`deliberationSkipped`, `deltaVoices`, `deltaVoiceNames`, `predictedChurn`, `claim`, `units`
(`enumerated`, `graded`, `removed`, `removedUngraded`, `phantom`), `ungraded`, `removedUngraded`,
`phantoms`, `findings` counts, `deltas` (`total`, `byOp`, `seeded`, `revisions`), `reversals` (a note
per reversing delta), `shakyMustFindings`, `minPasses`, `maxPasses`. Numbers are rounded to four
places, so the table `judge` prints (two places) and the file disagree in the last digit - trust the
file. On pass 1, `novelty`, `churn`, `thrash` and `surprise` are `null`, not `0`.

`verdict.json` keys: `version`, `pass`, `verdict`, `reason`, `rule`, `message`, `notes`, `ungraded`,
`signals` (the eight, copied, plus `deltaVoices`), `removedUngraded`, `phantoms`, `advisedAt`, then
after `decide`: `decision`, `why`, `override`, `warnings`, `decidedAt`, `coverageAtDecision`.

`reason` is a stable label, not prose - one of `coverage`, `min-passes`, `thrash`, `perseveration`,
`low-confidence`, `converged`, `budget`, `oca-observations`, `default`. The human sentence is in
`message`.

## The ledger is the authority

Everything above governs what the *engine* will do. None of it governs a text editor. `units.json` and
`findings.json` are ordinary files: forge a `removalKind`, delete a unit's entry, invent a finding,
flip a status from `open` to `resolved`. So the state is not trusted, it is **recomputed**.

**Reconciliation** replays `ledger.jsonl` from line 1, derives the state those records must have
produced, and compares:

| Document | Reconciled |
|---|---|
| `findings.json` | which ids exist; and per finding `unit`, `title`, `detail`, `dimension`, `score`, `severity`, `confidence`, `effort`, `evidence`, `recommendation`, `status`, `createdInPass` |
| `units.json` | which ids exist; and per unit `label`, `path`, `kind`, `meta`, `addedInPass`, `removedInPass`, `removalKind`, `phantomVerification`, `phantomPath` |

`label`, `path`, `kind` and `meta` are in that list *because* `unit-edit` replays them, key-by-key
`meta` merge included. Correcting a caption on the record is cheap; correcting one off the record is
not possible. Not reconciled: `lastTouchedPass`, a finding's `history`, timestamps, and `session.json`
- derived bookkeeping and the phase machine, neither of which can buy anyone coverage.

It then checks the ledger against itself. `ledger.jsonl` is the ordered union of the per-pass
`deltas.jsonl` files - one call writes both copies - so those files are an independent second copy of
every record. That is what catches a plausible line appended to `ledger.jsonl` alone, a reordered
ledger, a truncated one, or a pass directory deleted out from under it.

**`judge`, `decide`, `report` and `apply` reconcile before they act**, and a divergence is exit `2`
naming what diverged. Those four turn state into a claim - a verdict, a decision, a document, a work
plan. The rest of the loop does not pay the cost: `predict`, `units`, `grade`, `delta`, `status` and
`list` run without it.

### Write ordering - ledger first, always

Every command that changes state appends to `ledger.jsonl` **first** and writes `units.json`,
`findings.json` and `passes/NN/deltas.jsonl` **after**. The asymmetry is deliberate:

- **Ledger ahead** - fully recoverable. Every record determines what the state files must contain, so
  replaying derives what they have not caught up to. Deterministic, no guessing.
- **State ahead** - unrecoverable. The extra data exists in exactly one place and there is nothing to
  rebuild it from.

So the only crash state reachable is the recoverable one. A torn write never costs a pass's work.

### `ponder verify --repair`

Repairs a ledger-ahead session: replays the ledger, rewrites `units.json` and `findings.json` to the
state those records must have produced, appends the missing tail to any `passes/NN/deltas.jsonl` that
holds a strict prefix, then re-reconciles and prints line by line what it rebuilt.

```
Repaired from the ledger
  - units.json - 12 units rebuilt from the ledger (screen.auth.sso, screen.billing were behind it)
  - passes/03/deltas.jsonl - 2 records appended to catch it up to the ledger
```

| What `--repair` found | What it does |
|---|---|
| a unit or finding the ledger created that the state file lacks, or a field whose stored value is behind the ledger's | rebuilds it |
| a `passes/NN/deltas.jsonl` holding a strict prefix of the ledger's records for that pass | appends the missing tail |
| a unit or finding in a state file that **no ledger record ever created** | **refuses** - the data exists in no other copy. Forgery or unrecoverable loss; both are a hard error |
| a duplicated or unidentified entry in a state file | **refuses** - same reason |
| a `passes/NN/deltas.jsonl` holding a record the ledger does not, or a different record at the same position | **refuses** - two copies of an append-only log disagreeing, not one lagging |
| a problem inside `ledger.jsonl` itself, or a line that will not parse | **refuses** - repair rebuilds *from* the ledger, so a broken ledger is nothing to rebuild from |

Every refusal stays exit `2`, and `--repair` prints what it cannot rebuild before it refuses. A
repaired session is byte-identical to what the interrupted command would have written. Without
`--repair`, `verify` writes nothing.

**What this does not guarantee.** It is not a signature and not a hash chain. Someone who edits all
three copies consistently - the state file, `ledger.jsonl`, and the matching `passes/NN/deltas.jsonl`
at the right position - defeats it, and that is outside the threat model, said plainly rather than
implied away. What it does is raise the cost of a dishonest stop from one edit to a consistent forgery
across three files, one of them an append-only log that `report.md` quotes.

Two boundaries worth knowing before you meet them. `session.json` is not reconciled and `--repair`
does not rebuild it - the ledger records operations on units and findings, not the phase machine. And
a session whose inventory was seeded before `unit-seed` existed has no ledger record for its units,
so it will never reconcile: re-seed it rather than working around it.

## Convergence signals

| Signal | Formula | Reads as |
|---|---|---|
| `coverage` | graded units ÷ enumerated units | Did we actually look at everything? |
| `novelty` | revising `add` deltas ÷ live findings - **null on pass 1** | Still finding new ground? |
| `churn` | revising deltas ÷ live findings - **null on pass 1** | How much moved this pass? |
| `thrash` | revising deltas that reverse an earlier delta on the same target ÷ revising deltas - **null on pass 1** | Oscillating instead of converging? |
| `surprise` | \|predicted churn − actual churn\| - **null on pass 1** | How well the loop models itself |
| `stall` | consecutive passes with `churn < 0.02` | Perseveration guard |
| `confidenceFloor` | fraction of `open` + `must` findings with `confidence < 0.5` | Are the important calls still guesses? |
| `voices` | distinct perspectives that **spoke in this pass's deliberation** | Did the pass argue with itself? |

**Pass 1 reports `null` for `novelty`, `churn`, `thrash` and `surprise`** - printed as `-` in the
signal table, and `-` is not a zero. All four measure change against a previous pass, and pass 1 has
none: every finding is new because there was nothing there before, and there is no actual churn to
score the prediction against. They start reading at pass 2. `coverage`, `confidenceFloor`, `stall` and
`voices` describe a state rather than a change, so they read from pass 1 onward.

The numerator for `novelty` and `churn` is **revising** deltas - the seed `add`s that `ponder grade`
writes are excluded, so the numbers describe what a pass *changed*, not what it created. The
denominator is the **live** finding count, total minus retracted, so retracting noise does not dilute
the next pass's signal. `confidenceFloor`'s denominator is only the `open` + `must` findings.

`thrash` is the odd one out: **both** halves of it are revising deltas, not total deltas, so it reads
as the share of this pass's own revisions that undid earlier work. A `unit-add`, `unit-edit` or
`unit-delete` is a revising delta like any other - inventory amendments count in `churn`, because they
moved the pondering, and never in `novelty`, because they are not `add`s of findings.

**Coverage is the one signal a `unit-edit` cannot move.** Correcting a unit is neither an addition nor
a removal, so the numerator and the denominator come out of the pass exactly as they went in.

`voices` counts the perspectives that **argued**, read from `passes/NN/deliberation.json`: a
perspective with a non-empty `argument` spoke, whatever it did or did not go on to emit. A Skeptic
who checked the evidence, found the finding sound and said so has voted - the deliberation heard it.
A pass that skipped deliberation (`ponder deliberate --skip`) heard nobody, and its `voices` is 0.

The old reading is still available and still worth watching: `judge` prints a **`delta voices`** row
under `voices`, and `metrics.json` carries `deltaVoices` / `deltaVoiceNames`. Read the two together.
`voices 4/4` with `delta voices 1/4` is four perspectives arguing and one acting - sometimes a genuine
quiet pass, sometimes three voices going through the motions. `voices 0/4` with a healthy
`delta voices` is deltas nobody argued for.

A delta **reverses** an earlier one when, on the same target, an earlier pass set a field to X, a
later pass changed it, and this pass sets it back to X - on a unit's `label`, `path`, `kind` or `meta`
via `unit-edit` exactly as on a finding's fields, with seeded and added values counting as the first
setting and `meta` compared on its merged value rather than on the partial object submitted; or when
this pass `add`s a finding materially matching one an earlier pass `delete`d (same `unit` + same
`dimension`); or when it `delete`s one added within the previous two passes.

## Verdict rules, in order

First match wins.

1. `coverage < 1.0` → **`blocked`**. Stopping is not permitted; the verdict names every ungraded
   unit, and names apart the ones deleted without ever being graded, saying why they still count.
   No override exists.
2. `pass < minPasses` → **`continue`**. A single pass is an opinion, not a pondering.
3. `thrash > 0.25` → **`escalate`**. Another identical pass will not help - rotate perspectives,
   widen the evidence, or split the subject. Skipped when `thrash` is null.
4. **Evidence and review guard (`confidenceFloor > 0` or `voices < 3`):** any open `must` finding
   below 0.5 confidence (`confidenceFloor > 0`) or fewer than three reviewing perspectives
   (`voices < 3`) blocks convergence → if `pass >= maxPasses`, **`stop`** with reason `budget`;
   else if `stall >= 2`, **`escalate`**; else **`continue`** with reason `low-confidence` or
   `insufficient-perspectives`. Stillness with unresolved uncertainty does not earn convergence,
   and no quiet pass bypasses this guard.
5. `novelty < 0.05` and `churn < 0.10`, with `voices >= 3` and `confidenceFloor == 0`, sustained
   two consecutive passes → **`stop`**, reason `converged` (engine rule id `6`). Checked before
   the fallback perseveration stop so two fully reviewed, confident quiet passes earn `converged`.
6. `stall >= 2` and `coverage == 1.0` → **`stop`**, reason `perseveration` (engine rule id `4`).
   Nothing is moving, and the two-pass convergence check did not match (for example, because the
   prior pass lacked full perspective review or confidence). `stall` only counts passes whose churn
   was a number, so a pass with no churn cannot feed it.
7. `pass >= maxPasses` → **`stop`**, reason `budget`. Report it as a budget stop, never as
   convergence.
8. otherwise → **`continue`**, reason `default` - unless the OCA is holding open metacognitive
   observations of high severity about this loop, which tip an otherwise-`continue` into
   **`escalate`**, reason `oca-observations`.

Pass 1 reports no `churn`, `novelty` or `thrash`, so rules 3, 5 and 6 have nothing to fire on there,
and the skip is explicit rather than a null comparison happening to come out false. Rule 1 still
applies in full - coverage is computed from the inventory and the finding set, not from the ledger,
and it blocks pass 1 exactly as hard as pass 6.

## Lens packs

`lenses/<name>.md`, read by the agent at survey and appraise:

```yaml
---
name: ui
unit: screen
enumerate: |
  How to find every unit. Concrete commands and heuristics.
dimensions: [information-hierarchy, empty-states, loading-states, error-states,
             motion, affordance-clarity, density, responsive-behaviour,
             accessibility, copy-tone, consistency, delight]
scale: { 1: broken, 2: bad, 3: acceptable, 4: good, 5: exemplary }
---
```

The body defines what a unit is, how to enumerate exhaustively, each dimension with concrete 1 / 3 / 5
examples, what counts as evidence, and what each of the four perspectives should hunt for.
`--lens custom --rubric <file>` loads any file with the same front-matter shape.

## OCA bridge

Optional, silent when absent, zero npm dependencies - it shells out to `psql`.

| Variable | Default | Meaning |
|---|---|---|
| `PONDER_OCA` | `auto` | `auto` probes once per process and disables itself on failure; `on` makes an unreachable OCA a hard error; `off` skips it entirely |
| `PONDER_OCA_DSN` | `postgres://localhost/oneiro` | |

Timeout is 5s per call. Any non-zero exit, timeout or parse failure is logged to
`.ponder/<slug>/oca.log` and returns `null`. **The bridge can never break the engine** - if a pass
behaves strangely, the OCA is not the reason; check `oca.log` and move on.

What it buys you: `start` prints prior pondering on the same subject; each pass writes a scored
prediction to `episodic_memory` and `hypotheses`; deliberations land in `deliberations`; stuck,
perseverating, thrashing and low-confidence passes raise `metacognitive_observations` that `judge`
reads back as a tie-breaker toward `escalate`. The cognitive-loop process on `:3333` is **not**
running and nothing here depends on it - the bridge talks to Postgres directly.

## Common errors

Messages below are the literal ones the engine prints. Errors go to stderr; the `NEXT:` line still
goes to stdout, so a failed command still tells you where you are.

| Exit | Message | Cause | Fix |
|---|---|---|---|
| `2` | `out of order: "ponder judge" satisfies judge, but this session owes decide.` | A phase skipped or repeated | Do what `NEXT:` says. The state machine is correcting your memory, not malfunctioning |
| `2` | `cannot stop: coverage is 0.67, not 1.0. 1 screen has never been graded.` | The coverage gate | Grade the named units. A `unit-delete` does not shorten this list unless the unit was graded or is a verified phantom |
| `2` | `session <slug> is still open on pass N (<phase>).` | `ponder apply` without `--dry-run` on an open session | `--dry-run` to preview, or finish the pondering first |
| `2` | `session <slug> was aborted; there is no plan to apply.` | `ponder apply` on an aborted session, with or without `--dry-run` | Nothing to fix. An abandoned pondering is not a plan - start a fresh session |
| `2` | `pass N has not been judged.` | The session owes `decide` but `passes/NN/metrics.json` is missing - the phase machine catches an ordinary `decide`-before-`judge` first, so this one means the pass artefacts were disturbed | `ponder judge` again |
| `1` | `N problems in this delta batch - nothing was applied.` + `delta line 4: every delta needs a non-empty "why" - an unexplained revision is not a revision.` | A delta without a reason | Every delta carries a `why`. Nothing in the batch applied, so fix and re-run the whole file |
| `1` | `delta line 1: finding targets unknown unit "u.two" - add it first with a unit-add delta.` | An `add` naming a unit that is not in the inventory *yet* | Move the `unit-add` line above the `add`. Same file is fine; order is not optional |
| `1` | `unit "<id>" is claimed phantom, but a path it has carried exists: <abs> (carried by the unit-add that created it in pass 4).` | A `"phantom": true` on a unit that has, at some point, pointed at a file you can open | Go and grade it. The file is right there. The check runs against every path the unit ever had, so moving the path first does not clear it |
| `1` | `unit "<id>" is claimed phantom and none of the 2 paths it has carried (…) resolves under <root> - but that project root was guessed, not established (…).` | A `"phantom": true` under a project root no `--project` and no project marker established | Check the `project` line from `ponder start` / `ponder status`. If the root is wrong, start again with `--project <path>`; if it is right, the claim is still uncheckable from there and the unit needs grading |
| `1` | `unit-edit may never set "id". The unit id is the join key between units.json and findings.json…` | A `unit-edit` trying to rename a unit | Ids do not move. If the id itself is wrong, `unit-delete` it and `unit-add` the corrected one, and pay the coverage |
| `1` | `"note" is not a settable unit field (label, path, kind, meta).` | A `unit-edit` setting something that is not one of the four | Those four, and nothing else |
| `1` | `unit "<id>" was removed in pass 3 - a unit that has left the inventory is not edited back into shape, it is re-added.` | A `unit-edit` on a removed unit | `unit-add` it back if it belongs in the subject |
| `2` | `session <slug> does not reconcile with its ledger - 2 divergences.` | `judge`, `decide`, `report` or `apply` on state that disagrees with the ledger | `ponder verify --session <slug>` for the diagnosis, then `ponder verify --repair` if the ledger is merely ahead. A state-ahead session is a hard error by design |
| `1` | `--churn must be between 0 and 1 (got 1.2).` | A prediction outside the 0-1 range the metric lives in | Pick a number in range. `0` and `1.0` are both legal. On pass 1 nothing scores it - write the honest guess and put the content in `--claim` |
| `1` | `overriding the "continue" advice with "stop" needs a --why of at least 12 characters (got 4).` | Thin override reason | Write the actual reason. It is permanent in `report.md` |
| `1` | `session "ui-2026-08-24" already exists at …` | `--slug` collision | Pick another slug, or resume: `ponder status --session <slug>` |
| `1` | `<path> line 1 is not valid JSON: …` | A truncated or fenced JSONL line | Ask the batch agent for JSONL and nothing else - no prose, no code fences |
| `0` | No **Prior pondering** section | OCA unreachable, or nothing matched | Expected. `ponder doctor` if you care |

One failure prints no error at all: a `unit-delete` on a never-graded unit succeeds, and coverage does
not move. That is not a bug to route around. The unit left the inventory and stayed in the coverage
denominator, exactly as designed - grade it, or claim `"phantom": true` and let the engine check.
