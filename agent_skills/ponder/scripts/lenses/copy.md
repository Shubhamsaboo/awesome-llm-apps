---
name: copy
unit: string
enumerate: |
  1. Sweep every surface that puts words in front of a person, not only the
     screens.
  2. Extract the literals mechanically first. Grepping finds the strings you
     forgot.
  3. Group into families. Grade the family as one unit when consistency is
     at stake.
  4. Walk the ten-state matrix per surface. Every empty cell is a "gap." unit
     scoring 1 on state-honesty.
  5. Record the trigger for every unit. Out of context, a string is a style
     opinion.
  6. Probe read-only. Never reach a state with a command that commits the
     live session.
  7. Coverage is 1.0 when the matrix is complete, not when every string is
     scored.
dimensions: [clarity, voice-consistency, next-action, state-honesty, tone-under-failure, jargon-leakage, length-resilience]
scale:
  1: wrong, dishonest or a dead end
  2: technically true, practically unusable
  3: clear, correct and unremarkable
  4: clear, correct, in voice, and points somewhere
  5: exemplary - the reader is better off than before they read it
---

# copy lens

Copy is the part of the product that talks. It is also the part that gets written last, by
whoever was closest, at the moment they were least interested in it — which is why the worst
strings in most products are the ones a person reads at their worst moment.

This lens grades strings against the reader's situation, not against a style guide. The two
failures it exists to catch are **dead ends** (a message that names a problem and offers no
exit) and **dishonesty** (a message that describes something other than what happened).

## What a unit is

A unit is **one string, or one string family**.

A **family** is a set of strings that must agree with each other to work: all the empty
states in an app, every validation message on one form, the seven steps of first-run, the
`NEXT:` lines across every CLI command. When consistency is the property at stake, the family
is the unit — grading its members separately produces seven scores of 4 and misses that they
are written in four different voices.

Split a string out of its family when it has its own job. The payment failure message belongs
to the error family for voice, and it is also a unit of its own, because getting it wrong
costs money.

A **`gap.` unit** is a string that should exist and does not: the empty state nobody designed,
the offline banner, the undo affordance, the sentence explaining why this screen is legitimately
empty on day one. Missing strings are the most common defect on this lens and they never show
up in a grep, only in a state matrix.

Surfaces that count as copy:

- Button labels, headings, field labels, placeholders, helper text, tooltips.
- Error messages, validation messages, toasts, banners, confirmation dialogs.
- Empty states, loading states, partial states, zero-results states.
- CLI output: usage strings, `--help`, progress lines, warnings, the `NEXT:` line.
- Emails, push notifications, in-app notifications, digest subjects.
- Onboarding, first-run, upgrade prompts, deprecation warnings.
- Log lines a human is expected to read during an incident.

Not copy for this lens: `--json` payload keys, debug logs, internal telemetry field names.
Those have a machine audience, and grading them against a human-readability ideal is noise
the Skeptic should delete.

**Unit ids.** `copy.<surface>.<slot>` for a single string, `family.<surface>.<set>` for a
family, `gap.copy.<surface>.<slot>` for one that should exist:
`copy.errors.oca-unreachable`, `copy.empty.billing-invoices`,
`family.validation.signup-form`, `family.cli.next-lines`, `gap.copy.offline.banner`.

## How to enumerate exhaustively

### 1. Extract the literals mechanically

```sh
# CLI output, every literal that reaches a terminal
grep -rnE "console\.(log|error|warn)\(" lib/ | wc -l
grep -rhoE "console\.(log|error|warn)\(\s*[\`'\"][^\`'\"]+" lib/ \
  | sed -E "s/console\.[a-z]+\(\s*[\`'\"]//" | sort -u

# every thrown message, which becomes copy the moment it reaches a person.
# Find the idiom before you grep for it — `throw new SomethingError('...')` is one dialect,
# and on ponder it matches zero of its error strings, which all go through userError().
grep -rhoE 'throw [A-Za-z.]+\(' lib/ oca/ | sort | uniq -c | sort -rn
grep -rnoE "(throw new [A-Za-z]*Error|userError|stateError)\(\s*[\`'\"][^\`'\"]+" lib/ oca/

# process-level messages people actually read
grep -rn 'NEXT:' lib/
grep -rnE 'usage:|Usage:' lib/

# i18n catalogues, where they exist - this is the complete list by construction
jq -r 'paths(scalars) as $p | "\($p|join(".")) = \(getpath($p))"' locales/en.json 2>/dev/null | sort

# JSX literal text, a rough first cut that finds more than reading does
grep -rnE '>[A-Z][^<>{}]{3,}<' --include='*.tsx' --include='*.jsx' src/ 2>/dev/null
grep -rnE '(label|placeholder|title|aria-label|alt)=["'\''][^"'\'']+' --include='*.tsx' src/ 2>/dev/null
```

A project without an i18n catalogue has no complete list of its own words. That absence is
itself worth a finding — not because you need translation, but because you cannot review what
you cannot enumerate.

For a terminal product, read the strings the way a terminal will render them. Colour is not
copy, but a string that only makes sense in colour is a broken string the moment it lands in
a log file, a CI transcript or a pipe:

```sh
ponder status | cat          # non-TTY: does the meaning survive without colour or width?
NO_COLOR=1 ponder status     # the convention every CLI is expected to honour
ponder status --json | head  # machine surface: nothing human should be mixed into it
```

A word carrying meaning that only colour supplies — a red `failed` that reads as a neutral
`failed` when piped — is a `clarity` finding with the pipe as its trigger.

### 2. Walk the state matrix

This is where the missing strings are. For every surface, ask whether a string exists for each
state, and open a `gap.` unit for every empty cell.

| State | The question the reader is asking |
|---|---|
| empty (first-run) | "Is this broken, or have I just not done anything yet?" |
| empty (zero results) | "Did I filter wrong, or is there genuinely nothing?" |
| loading | "Is it working? How long?" |
| partial / degraded | "Which part of this can I trust?" |
| success | "Did it save? Where did it go? Can I undo?" |
| error, recoverable | "What do I do now?" |
| error, unrecoverable | "Did I lose work? Who do I tell?" |
| offline | "Is it me or them?" |
| permission denied | "Am I asking the wrong thing, or the wrong person?" |
| destructive confirm | "What exactly am I about to destroy, and can I get it back?" |

Ten states per surface. Most products have written three of them.

### 3. Find the triggers

Every unit needs a reproducible trigger, because the same words score differently in different
contexts.

```sh
# what condition prints this string. Grep a fragment, not your memory of the sentence:
# 'OCA unreachable' matches nothing here, because the string is "the OCA is unreachable at".
grep -rn -B5 'unreachable' lib/ oca/
```

**Never reach a state by running a command against the session you are pondering in.**
`decide`, `delta`, `apply`, `report` and `abort` all commit state, and they default to the
most recently touched open session in the current project — which, mid-review, is yours.
`ponder decide stop --why "deliberately too short"` does not print the short-`--why` error
it looks like it should print (22 characters clears the 12-character floor); it stops your
session, writes an override into `verdict.json`, and puts the words "deliberately too short"
in `report.md` under **Overrides**, permanently. `ponder delta --file /dev/null` does not
error either; it applies zero deltas and advances the phase.

Probe in a throwaway project instead. Every line below is read-only with respect to the
session you care about:

```sh
probe=$(mktemp -d) && cd "$probe"   # `ponder` here is the installed binary, not ./bin/ponder

# a dependency that is down, on a command that only reads
PONDER_OCA=on PONDER_OCA_DSN=postgres://localhost:1/nope ponder doctor

# a lens that does not exist — the error that has to list the ones that do
ponder start "probe" --lens nope

# an out-of-order command — the phase-machine error, the most-seen error in the tool
ponder start "probe" --lens copy --slug probe && ponder delta --stdin </dev/null

# a missing input file, then a malformed one
ponder predict --churn 0.1 --claim "probe" && ponder units --file ./nope.json
printf '{"units":[' > bad.json && ponder units --file bad.json

cd - && rm -rf "$probe"
```

Some states are only reachable at the end of a scripted session — the short-`--why` refusal
needs a session sitting at `decide`, which costs six commands to build. When a state costs
that much, record the **condition and the source anchor** in `detail` instead of a command,
and say that the string was read at its throw site rather than seen. That is honest evidence.
Substituting a command that mutates the live session is not.

Record the trigger in the finding's `detail`. "Reproduce with `<command>`" turns a copy
opinion into a copy finding.

### 4. Substitute the real values

Every string with a placeholder is really a family of strings, one per plausible value. Pull
the real values before grading.

```sh
# the actual lengths a template will be asked to hold
psql -d oneiro -At -c "select max(length(content)) from episodic_memory" 2>/dev/null
grep -rhoE '\{[a-zA-Z_]+\}|\$\{[a-zA-Z_]+\}' locales/en.json | sort -u
```

### Closing the universe

Coverage hits 1.0 when the state matrix is complete for every surface — every cell either has
a graded string or a graded `gap.` unit. Grading only the strings that already exist means
grading only the states somebody already thought about, which are exactly the states that are
fine.

Two engine mechanics decide whether this session can ever stop:

**A string you have nothing to say about still needs a finding.** A unit counts as graded when
it carries at least one finding that is not `retracted`. The strings that are simply good
generate nothing by instinct, so they finish the pass ungraded, coverage lands short of 1.0,
and `stop` is refused with no override. Record them: score 4 or 5, severity `note`, the
anchor, and the trigger you read them under.

**Retracting a unit's last live finding un-grades the unit.** Collapsing a family reported
once per member into a single `family.` finding — which this lens tells the Skeptic to do —
retracts findings, and every member that had no other finding falls out of coverage. Retire
the collapsed member *units* with `unit-delete` deltas so the family unit carries them, rather
than retracting the findings that were holding their coverage up.

**If the survey produced no `gap.` units, the state matrix was not walked.** Nothing in the
engine can tell the difference between a product with all ten states written and a pass that
graded the strings it could grep. Both report the same coverage. A gap-free survey on this
lens is the pass's first finding.

## The dimensions

### clarity

A reader who does not know the system understands the sentence on the first read. Measured
against the actual reader of that surface, not against a general audience.

- **1** — `Error: state machine violation.` The reader does not know there is a state
  machine, what they violated, whether their work survived, or what happens next. Every word in
  the sentence is about the implementation.

- **3** — `Wrong phase: expected deliberate.` Accurate, and parseable by someone who has
  internalised the phase model. Opaque to everyone else, and the reader who needs it most is the
  one who has not internalised the phase model.

- **5** — `This session owes a deliberate step before delta will be accepted. Run
  'ponder deliberate --file <path>', or skip it with '--skip --why "<reason>"'.` One sentence of
  what, one of how, no vocabulary the reader has not already met on the command line.

### voice-consistency

The product sounds like it was written by one person who cared. Voice is a family property —
grade it on the family unit, not string by string.

- **1** — Three registers on one screen: `Oops! Something went wrong 😅`, `Invalid
  credential payload`, and `We were unable to process your request at this time.` A jokey one,
  a machine one and a corporate one, within a hundred pixels of each other. The reader learns
  that nobody is in charge.

- **3** — Consistent within each surface, drifting across them: the CLI is terse and
  imperative, the docs are chatty, the transactional emails are formal in a way nothing else is.
  Nothing is wrong; the product just does not feel like one thing.

- **5** — One documented voice applied everywhere, including the surfaces that usually
  escape review — `--help` text, error strings, deprecation warnings, the subject line of the
  receipt email. A stranger cannot tell which strings were written by which person or in which
  year.

### next-action

An error tells the reader what to do next, not only what happened. This is the dimension that
separates a message from a dead end.

- **1** — `Failed to record pass.` No cause, no remedy, no statement of whether the work
  survived. The reader's only available action is to try again and hope, or to leave.

- **3** — `Failed to record pass: OCA unreachable.` Cause named, remedy missing. The reader
  does not know whether this is fatal, whether their pass was lost, or that `PONDER_OCA=off`
  makes it stop happening.

- **5** — `OCA unreachable at postgres://localhost/oneiro — the pass was recorded locally
  and nothing was lost. Run 'ponder doctor' to diagnose, or set PONDER_OCA=off to stop trying.`
  Cause, impact on the reader's work, and two concrete exits, in that order.

The rule: **cause, impact, exit.** A message missing "impact" leaves the reader unsure whether
to panic, and a message missing "exit" leaves them stuck regardless of how well you explained
the cause.

### state-honesty

The string describes what actually happened. This is the highest-severity dimension on the
lens: a product that misreports its own state teaches the reader not to believe any of its
words, and that is unrecoverable.

- **1** — `Converged.` printed when the loop stopped because `pass >= maxPasses`. It ran
  out of budget and the copy claims the opposite — it claims the intellectual result the whole
  tool exists to produce. Also 1: `Saved` rendered before the write resolves; `All set!` while a
  background step is still running; a progress bar that reaches 100% and then waits.

- **3** — `Stopped.` True, and flattened to uselessness. The reader cannot tell a budget
  stop from a perseveration stop from real convergence, so the one number they came for is the
  one thing the message withholds.

- **5** — `Stopped at pass 6 of 6 — budget, not convergence. Novelty was still 0.11 on the
  last pass and 2 must-findings remain below 0.5 confidence.` The copy reports the mechanism,
  including the part that makes the tool look worse. That is the whole trick.

### tone-under-failure

How the product behaves toward someone whose day just got worse. Tone is only worth grading at
the failure moment; anyone can sound fine on the success path.

- **1** — `Whoops! Our hamsters fell off the wheel 🐹` on a data-loss error. It jokes at the
  reader's expense, conceals the severity, gives them nothing to escalate with, and makes the
  company sound like it finds the outage charming.

- **3** — `An error occurred.` Neutral, inoffensive, useless. It does not insult anyone and
  it does not take responsibility either — it is the sound of a product declining to have a
  position on its own failure.

- **5** — `We could not write ledger.jsonl — the disk is full. Your findings are unchanged.
  Free some space and re-run 'ponder delta'.` Plain, specific, blame in the right place, no
  apology theatre, no emoji, and the reader's first question ("did I lose it?") answered before
  they ask.

Two tests for this dimension: read the string aloud to someone who has just lost an hour's
work, and check whether the string blames the reader for a thing the system did.

### jargon-leakage

Internal vocabulary reaching a reader who never learned it. Jargon is not a sin — it is
precision for people who share the vocabulary. Grade it against the actual audience.

- **1** — `Delta rejected: perspective missing on op=change` in a graphical interface where
  nobody has ever seen the words delta, perspective or op. Four internal nouns and an equals
  sign, aimed at someone who clicked a button.

- **3** — The jargon is used correctly and defined exactly once, in the docs, far from the
  string. The reader has to leave the surface to parse the sentence — which, at the moment they
  are reading an error, they will not do.

- **5** — The reader's vocabulary in the sentence, the system's vocabulary in the detail
  line for whoever needs it: `This revision needs a reason. Add --why explaining why the score
  changed.` Note that in ponder's CLI the reader *has* learned "delta" and "perspective" — they
  typed them — so using them there is precision, not leakage. The score is set by the audience,
  not by the word.

### length-resilience

The string survives real content: the longest real value, the longest real name, a translation
that runs 35% longer than English, and the narrowest viewport the surface actually meets.

- **1** — A fixed-width button labelled `Continue pondering this subject`, which renders as
  `Continue ponde…` at the width it is actually given. The label was written in a design file
  where the button was wider than it is in production.

- **3** — Fits English at typical values, breaks on a real substitution. `Stopped: {reason}`
  reads well as `Stopped: budget` and badly as `Stopped: coverage is below 1.0 and 7 units are
  ungraded`, which is the case that matters most.

- **5** — Written for the worst real case, verified with the longest value in the database
  and a machine-translated German string, with a deliberate truncation boundary and the full
  text still reachable — a tooltip, a details row, or `--json`. The design and the string were
  decided together.

## What evidence looks like

Evidence is `path:line` for the literal, plus the reproduction. Both, always.

| Finding kind | Required evidence |
|---|---|
| A single string | `["lib/cli.js:142"]` plus the trigger in `detail`: "reproduce with `ponder delta --file /dev/null`" |
| A family | Every member's anchor: `["lib/cli.js:142", "lib/cli.js:180", "lib/report.js:44"]` |
| A `gap.` unit | The code path that reaches the state with no string, plus the state-matrix cell it fills |
| `state-honesty` | The string anchor **and** the code anchor proving the claim is false: `["lib/report.js:44", "lib/verdict.js:88"]` |
| `length-resilience` | The longest real value, quoted, and where it came from — a query, a fixture, a production row |
| `voice-consistency` | At least two anchors in conflict. One string cannot be inconsistent by itself |

A finding whose evidence is a screenshot with no path and no trigger cannot be verified next
pass, and will be re-argued forever. The Skeptic deletes it.

## Severity calibration

| Situation | Severity |
|---|---|
| A string that misreports system state (`state-honesty` = 1) | `must` |
| A dead-end error on a blocking path — the reader cannot proceed and is told nothing | `must` |
| Copy that blames the reader for a system failure | `must` |
| Missing empty state on a surface every new user hits first | `must` |
| A string that hides data loss or its absence | `must` |
| Jargon leakage in a general-audience surface | `should` |
| Voice drift across families | `should` |
| Length breakage on a value that occurs in production | `should` |
| Voice drift within a rarely-seen surface, wordiness, punctuation | `could` / `note` |

Weight by moment, not by frequency. A string read once, during a payment failure, outranks a
string read a thousand times on the success path.

## What each perspective hunts

### Skeptic — emits `delete`

- Preferences dressed as findings. "I would say Sign in, not Log in" with no consistency
  argument and no evidence of a conflict is taste. With a second anchor showing both in use,
  it is a `voice-consistency` finding.
- Findings against strings no person reads: `--json` keys, debug logs, internal field names.
- One family reported once per member. Collapse to the family unit.
- Findings whose fix would break an accessibility requirement (removing a label because it
  looks redundant next to an icon) or a legal one (softening a required disclosure).
- Findings with no trigger. If nobody can reach the state, nobody can verify the fix.

### Builder — emits `edit`

- **Write the replacement string in `recommendation`.** A copy finding that recommends "make
  this clearer" is not actionable and never will be. The recommendation field holds the actual
  words, at the length the surface allows.
- Include the length budget you wrote to: "≤ 48 chars, the button is 180px at the narrowest
  breakpoint".
- Convert a `gap.` unit into the string plus the condition that should render it.
- Where the fix is structural — the message needs a value the code does not have at that point
  — say so, and name what has to be threaded through.

### Dreamer — emits `add`

- The strings that should exist and do not: the offline banner, the undo affordance, the
  sentence that explains why an empty screen is legitimately empty, the deprecation warning
  that gives a date.
- The surfaces the survey skipped: `--help`, notification titles, the email subject line, the
  first thing a CI log prints.
- The reframe that removes the string entirely: this error message is well written and should
  not exist, because the state that produces it should be unreachable. Six sentences explaining
  a confusing flag are evidence for renaming the flag.
- The sequence nobody read end to end: first-run steps 1 through 7 read in order, out loud, as
  one experience rather than seven strings.

### Empath — emits `change`

- Re-rank by moment. Copy read during failure, during first-run, and during payment outranks
  everything read during routine success.
- Raise anything that makes a person feel stupid, blamed, or unsure whether they lost work.
- Raise `state-honesty` findings above everything else on the same unit. A clear lie is worse
  than an unclear truth.
- Lower findings that optimise a string for an audience that does not read it.
- Fix the order in the report so that whoever reads it writes the words that matter most first,
  while they still care.

## What a later pass does with this lens

Pass 1 grades the strings that exist and opens the `gap.` units the state matrix exposed.
Later passes have three jobs, and re-reading the same grep output is none of them.

- **Read the families end to end, out loud.** Voice is only visible in sequence. Pass 1 grades
  strings one at a time; pass 3 reads first-run steps 1 to 7 in order, or every `NEXT:` line
  in the order a session actually emits them, and grades the family unit that no single string
  could have failed.
- **Write the missing strings.** A `gap.` unit stays score 1 until somebody writes the words.
  Turning gaps into drafted replacements in `recommendation` is the highest-value delta this
  lens produces and it is Builder `edit` work, which pass 1 rarely gets to.
- **Re-trigger the ones you changed your mind about.** A string graded from a grep line reads
  differently under its real trigger. When a later pass reaches the state for the first time,
  that is a `change` with the trigger as its `why`, not a quiet rescore.

## Common failure modes of this lens

1. **Grading strings out of context.** A label that reads badly alone often reads correctly
   under its heading. Always grade with the trigger, never from a grep line.
2. **Enumerating only the happy path.** The state matrix is the enumeration. Skipping it means
   coverage 1.0 over the strings somebody already worried about.
3. **Grading machine output as copy.** `--json` has a machine audience. Grading it here
   produces findings nobody should act on.
4. **Recommending adjectives.** "Friendlier", "clearer", "more concise" are not
   recommendations. The replacement string is.
5. **Treating voice as a per-string property.** One string cannot be inconsistent. Voice
   findings need a family and at least two conflicting anchors.
