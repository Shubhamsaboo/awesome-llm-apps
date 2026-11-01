---
name: docs
unit: document
enumerate: |
  1. List every document that exists, including the ones that are not files.
  2. Add a "gap." unit per undocumented export, env var and missing runbook.
  3. A hole is only a unit when you can name its audience and the question
     it answers.
  4. For each document, record the code path it describes. No pair, no
     accuracy grade.
  5. For each hole, record the command that proved it. It is re-runnable
     evidence.
  6. Deduplicate: one drift repeated in four documents is one finding at its
     source.
  7. Calibrate each enumerator. One that returns nothing is a broken grep
     until proven.
  8. Coverage stays a lie until all three gap enumerators come back empty.
dimensions: [accuracy, completeness, audience-fit, discoverability, runnable-examples, staleness]
scale:
  1: absent or actively wrong
  2: present but misleading
  3: correct and usable
  4: correct, complete and findable
  5: exemplary and drift-resistant
---

# docs lens

Documentation is graded against the code, not against taste. The failure this lens exists
to catch is **drift**: a document that was true once, is trusted now, and is wrong. A wrong
document is worse than a missing one, because a missing document sends the reader to the
source and a wrong document sends them into a wall while blaming themselves.

## What a unit is

A unit is **one document, or one thing that should have a document and does not**.

Two kinds, graded on the same rubric:

| Kind | Meaning | Example id |
|---|---|---|
| `doc` | A document that exists and has a job. | `doc.readme.install` |
| `gap` | A document-shaped hole with a named audience and a named question. | `gap.runbook.oca-unreachable` |

A `gap` unit scores 1 on `completeness` and `discoverability` by construction. That is not
the interesting part. The interesting part is its `severity` — a missing JSDoc comment and a
missing 3am runbook are both score 1 and they are not the same problem.

Documents are not only markdown files. All of these are units:

- `README.md`, `CONTRIBUTING.md`, `docs/**`, ADRs, changelogs, migration guides.
- `--help` output and CLI usage strings. They are the most-read documentation in any tool.
- Docstrings / JSDoc / type-level documentation on exported symbols.
- Schema comments — `COMMENT ON COLUMN`, `.proto` comments, JSON Schema `description`.
- Error messages that teach ("OCA unreachable at <dsn>; set PONDER_OCA=off to stop trying").
- `.env.example` and config templates, which are the de facto environment-variable reference.
- Wiki / Notion / Google Doc pages that the team actually opens, even though they live off-repo.

Split a document into several units when its sections have different audiences. `README.md`
is usually three units — `doc.readme.pitch` (a stranger deciding whether to care),
`doc.readme.install` (someone with a terminal open) and `doc.readme.reference` (someone
already using it). Grading them as one produces a mush score of 3 that hides a broken
install section.

**Unit ids.** `doc.<area>.<name>` and `gap.<area>.<name>`, lowercase dotted, stable across
passes: `doc.oca.bridge`, `doc.cli.reference`, `gap.env.ponder-oca-dsn`,
`gap.api.record-observation`, `gap.runbook.psql-missing`.

## How to enumerate exhaustively

### 1. The documents that exist

```sh
find . -type f \( -name '*.md' -o -name '*.mdx' -o -name '*.rst' -o -name '*.adoc' -o -name '*.txt' \) \
  -not -path '*/node_modules/*' -not -path '*/.git/*' | sort
```

Then the documentation that is not a document file:

```sh
# CLI help text, the most-read doc in the project
bin/ponder --help

# Per-command help. Confirm by eye that `--help` is a real flag before running the loop:
# if it is not recognised, this does not print help, it RUNS every command in the list,
# and `apply`, `report` and `abort` change state. Enumeration is read-only or it is not
# enumeration. Test with a read-only command first.
bin/ponder status --help
for c in start units predict grade deliberate delta judge decide status report apply doctor; do
  echo "== $c"; bin/ponder "$c" --help 2>&1 | head -20
done

# doc comments on exported symbols
grep -rn -B3 --include='*.js' -E '^export (async )?(function|class|const) ' lib/ oca/ \
  | grep -c '\*'

# schema-level documentation
grep -rn 'COMMENT ON' --include='*.sql' .
```

### 2. Public API surface with no reference

This is the first gap enumerator. Extract the exported surface, extract the documented
names, subtract.

```sh
grep -rhoE '^export (async )?(function|class|const) [A-Za-z0-9_$]+' lib/ oca/ \
  | awk '{print $NF}' | sort -u > /tmp/ponder-exports.txt

grep -rhoE '[A-Za-z0-9_$]{3,}' README.md docs/ 2>/dev/null | sort -u > /tmp/ponder-documented.txt

comm -23 /tmp/ponder-exports.txt /tmp/ponder-documented.txt
```

Every name that survives `comm` is a `gap.api.<name>` unit — 116 of them on ponder today,
which is too many to be a useful finding set until you separate the surface from the
plumbing. An export is public when something outside its own file uses it:

```sh
while read -r n; do
  [ "$(grep -rlw --include='*.js' -- "$n" lib/ oca/ bin/ 2>/dev/null | wc -l)" -gt 1 ] \
    && echo "$n"
done < /tmp/ponder-exports.txt > /tmp/ponder-public.txt

comm -23 /tmp/ponder-exports.txt /tmp/ponder-public.txt   # exported, used by nobody else
```

75 crossed a module boundary; the other 41 are exported and used only where they are
defined. Both lists are findings and they are not the same finding: the first is
`gap.api.<name>` at `should` or `must`, the second is "exported for no reason", which the
Builder resolves by unexporting rather than by writing a document.

The same shape works per language: `go doc ./... | grep '^func'`,
`python -c "import m; print(dir(m))"`, `cargo doc --no-deps` then diff the generated index
against the prose.

Do the same for the CLI surface — flags are API:

```sh
bin/ponder --help | grep -oE '\-\-[a-z][a-z-]+' | sort -u > /tmp/ponder-flags.txt
grep -rhoE '\-\-[a-z][a-z-]+' README.md docs/ SPEC.md 2>/dev/null | sort -u > /tmp/ponder-flags-doc.txt
comm -23 /tmp/ponder-flags.txt /tmp/ponder-flags-doc.txt
```

### 3. Environment variables with no reference

The second gap enumerator. Environment variables are the most commonly undocumented public
interface in any project, because they are added by whoever needed one and never surface in
a signature.

The read sites in code are unambiguous and are the authority:

```sh
grep -rhoE 'process\.env\.[A-Z][A-Z0-9_]+|process\.env\[.[A-Z][A-Z0-9_]+' \
  --include='*.js' --include='*.mjs' . | grep -oE '[A-Z][A-Z0-9_]{2,}' | sort -u \
  > /tmp/ponder-env-used.txt
```

The shell and manifest sweep is not. `$VAR` matches a script's own local variables as
readily as an environment input, so subtract the names the scripts assign — a local is
always assigned before it is read:

```sh
grep -rhoE '\$\{?[A-Z][A-Z0-9_]{2,}\}?' --include='*.sh' --include='*.yml' --include='*.yaml' . \
  | grep -oE '[A-Z][A-Z0-9_]{2,}' | sort -u > /tmp/ponder-env-shell.txt

grep -rhoE '^[[:space:]]*(export[[:space:]]+)?[A-Z][A-Z0-9_]{2,}=' --include='*.sh' . \
  | grep -oE '[A-Z][A-Z0-9_]{2,}' | sort -u > /tmp/ponder-env-locals.txt

comm -23 /tmp/ponder-env-shell.txt /tmp/ponder-env-locals.txt >> /tmp/ponder-env-used.txt
sort -u -o /tmp/ponder-env-used.txt /tmp/ponder-env-used.txt

grep -rhoE '[A-Z][A-Z0-9_]{2,}' README.md docs/ .env.example 2>/dev/null | sort -u \
  > /tmp/ponder-env-doc.txt

comm -23 /tmp/ponder-env-used.txt /tmp/ponder-env-doc.txt
```

The subtraction is the whole difference between a usable enumerator and a pile of noise. On
ponder's own tree the raw `$VAR` sweep returns 57 names, of which 54 are locals in
`test/lib.sh`; minus the assignments it returns 3, and all 3 are real inputs (`NO_COLOR`,
`PONDER_NODE`, `TMPDIR`). Filter the remaining acronyms by hand (`JSON`, `HTTP`, `NODE`),
then every survivor is a `gap.env.<name>` unit. For each one, the document owes four things:
default, accepted values, what changes when you set it, and what happens when you set it wrong.

### 4. Runbook-shaped gaps

The third gap enumerator, and the highest-severity one. A runbook gap is an operational
procedure that someone will have to perform under pressure, with no written procedure.
Enumerate from four sources.

```sh
# operational verbs the project already supports
ls scripts/ bin/ 2>/dev/null; grep -nE '^[a-z-]+:' Makefile 2>/dev/null

# failure modes the code itself declares - each one is a question someone will ask at 3am.
# Find the throw idiom FIRST. `throw new SomethingError(...)` is one dialect among many.
grep -rhoE 'throw [A-Za-z.]+\(' lib/ oca/ | sort | uniq -c | sort -rn
# then extract with whatever that returned:
grep -rnE 'throw (new [A-Za-z]*Error|userError|stateError)\(' lib/ oca/

# anything scheduled, which fails while nobody is watching
grep -rnE 'cron|schedule|launchd|systemd|LaunchAgents' --include='*.yml' --include='*.yaml' \
  --include='*.json' --include='*.plist' . 2>/dev/null

# procedures that were performed but never written down
git log --since='180 days ago' --oneline -E \
  --grep='hotfix|incident|rollback|revert|restore|manual' -i
```

Two traps in that block, both of which fail silently and both of which cost you the highest-
severity units in the lens:

- **The throw idiom.** `grep -rn 'throw new' lib/ oca/` returns **zero** hits on ponder, which
  never uses that form — every throw goes through the `userError()` / `stateError()` factories
  in `lib/session.js`. Grep for the dialect the project actually speaks, not the one from the
  language tutorial. Same for Python (`raise X` vs a `fail()` helper), Go (`errors.New` vs
  `fmt.Errorf` vs a sentinel), Rust (`bail!`, `?`, `panic!`).
- **`--grep` alternation.** `git log --grep='a\|b'` returns nothing at all for anyone who has
  `grep.patternType = extended` in their gitconfig — the `\|` becomes a literal. Pass `-E`
  and plain `|`, as above, and the command means the same thing on every machine.

The git command is the highest-yield gap enumerator in this lens. Every hotfix in the log is
a procedure a human executed from memory. If the log shows it happened twice, the runbook is
a `must`.

### 5. Drift detection, to feed `accuracy`

Two mechanical sweeps that find wrongness without reading a word. Both are **candidate
generators, not finding generators** — triage before you file.

```sh
# file paths named in the docs that no longer exist
find . -type f -not -path '*/.git/*' -not -path '*/node_modules/*' | sed 's|^\./||' \
  > /tmp/ponder-tree.txt
grep -rhoE '~?/?[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)+\.(js|ts|tsx|py|go|rs|sql|ya?ml|json|md|sh)' \
  README.md docs/ SPEC.md 2>/dev/null | sed "s|^~|$HOME|" | sort -u \
  | while read -r p; do
      case "$p" in .ponder/*|*/.ponder/*|passes/*) continue ;; esac  # created at runtime
      [ -e "$p" ] && continue                                        # exists as written
      grep -qF -- "/$p" /tmp/ponder-tree.txt && continue             # a real path, truncated
      echo "CANDIDATE: $p"
    done
```

Three filters, each removing a false-positive class the naive version drowns in. Requiring a
`/` drops bare filenames the docs use as session-relative names (`session.json`, `report.md`)
and fragments of paths that contain spaces (`docs/Ponder — Project Status.md` yields
`Status.md`). Expanding `~` and testing for a real path with the candidate as a suffix drops
`~/code/ponder/SPEC.md`, which the regex otherwise truncates into a path that has never
existed. Skipping the tool's own state directory drops everything under `.ponder/`. Measured
on ponder's own tree: 34 candidates and zero real drift without the filters, 7 candidates and
2 real ones with them.

```sh
# commands named in the docs that the CLI no longer accepts.
# Compare against the CLI's own usage text. Never verify a command by running it.
bin/ponder --help > /tmp/ponder-usage.txt 2>&1
grep -rhoE '`ponder [a-z]+|^ *ponder [a-z]+' README.md docs/ SPEC.md 2>/dev/null \
  | tr -d '`' | awk '{print $2}' | sort -u \
  | while read -r c; do
      grep -qE "^ *$c( |$)" /tmp/ponder-usage.txt || echo "NOT A COMMAND: $c"
    done
```

Anchoring to a backtick or a line start is what keeps `ponder the`, `ponder exists` and
`ponder each` out of the results — nine of the twenty-three hits on ponder's own docs are
English prose, and an enumerator that files those burns the next pass on retractions.

### 6. Staleness signals

```sh
# doc last touched vs the code it describes
git log -1 --format='doc  %ad %h %s' --date=short -- docs/oca.md
git log -1 --format='code %ad %h %s' --date=short -- oca/bridge.js

# how far behind every doc is, in commits to the tree it describes
git log --oneline --since="$(git log -1 --format=%ad --date=short -- docs/oca.md)" -- oca/ | wc -l

# do the doc and its code ever change in the same commit
git log --format=%H -- docs/oca.md   | sort > /tmp/ponder-doc-commits.txt
git log --format=%H -- oca/bridge.js | sort > /tmp/ponder-code-commits.txt
comm -12 /tmp/ponder-doc-commits.txt /tmp/ponder-code-commits.txt | wc -l
```

A zero from that last command is the strongest staleness signal available: the document has
never once been updated in the same commit as the code it describes, so nothing in the
process keeps them together.

### Closing the universe

Coverage hits 1.0 only when every existing document has a grade **and** all three gap
enumerators (exported surface, environment variables, operational verbs) return empty
against the unit list. A pass that grades ten markdown files and calls coverage complete has
graded the easy half and skipped the half that hurts.

Two mechanics of the engine that decide whether you can ever stop:

**Every unit needs a finding, including the good ones.** A unit counts as graded when it
carries at least one finding that is not `retracted`. A document you read and found correct
produces no finding by instinct — and then coverage never reaches 1.0, and `stop` is refused
for the rest of the session with no override. Record it: score 4 or 5, severity `note`, one
line naming what you checked and against what.

**Retracting a unit's last live finding un-grades the unit.** This lens's favourite Skeptic
move — collapsing one drift reported in four documents into a single finding at the source —
drops coverage the moment one of those four was the only finding on its unit. Either leave a
one-line pointer finding on each unit that lost its last one, or `change` their status to
`resolved` instead of retracting them; `resolved` still counts as graded, `retracted` does
not.

**If pass 1 produced no `gap.` units at all, the gap enumerators were not run.** Nothing in
the engine can tell the difference between a project with no documentation holes and a pass
that skipped step 2, because both produce the same coverage number. Treat a gap-free survey
as the pass's first finding and go back.

## The dimensions

The anchors below are written against ponder's own tree so they can be checked rather than
admired. They are examples of what a finding at that score looks like, not claims about the
current state of this repo.

### accuracy

Does the document match the code as it is right now. This is the top-severity dimension in
this lens. A score of 1 or 2 on `accuracy` for a document a reader follows literally — an
install section, a runbook, an API reference — is a `must`, regardless of anything else.

**Evidence required:** two anchors. The doc line and the code line that contradicts it. A
drift finding without a code anchor is an opinion.

- **1** — `README.md:14` says `npm install ponder`. The package has zero dependencies and
  is run as `bin/ponder`; there is nothing on npm under that name. The first thing a new reader
  types fails, and the failure looks like their mistake.

- **3** — The flags documented in `docs/cli.md` all exist and behave as described, but the
  default for `--max-passes` is written as 5 while `lib/session.js` declares `maxPasses = 6`.
  The reader gets a working system and one wrong expectation, which surfaces later as confusion
  about why the loop kept going.

- **5** — Every claim traces to a line of code, and the examples are verified mechanically:
  `test/docs.test.js` extracts every fenced `console` block from `README.md`, runs it against a
  temp project, and fails the build when output diverges. Drift cannot survive a green suite.

### completeness

Every question the named audience arrives with is answered, and every question deliberately
not answered is marked out of scope with a pointer to where it is answered.

- **1** — `oca/bridge.js` exports nine functions. The docs mention `probe()` and stop.
  Callers read the source or guess, and the guesses differ.

- **3** — All nine are listed with signatures and one-line descriptions, but the failure
  semantics — every function returns `null` on any failure and never throws — appear nowhere.
  A caller writes a `try/catch` that can never fire and believes it is defensive.

- **5** — Each export documented with signature, return shape, failure mode, and the
  one-line reason it exists; plus an explicit "what this deliberately does not do" list
  (no retries, no connection pooling, no throwing) that closes the obvious wrong questions
  before they are asked.

### audience-fit

Written for the person who will actually read it, at the moment they will read it. Same
content, wrong moment, is a real defect.

- **1** — `docs/runbooks/oca-down.md` opens with three paragraphs on why the bridge shells
  out to `psql` instead of using a driver. The reader is on call, the loop is failing, and the
  first command is 400 words down the page.

- **3** — Correct content, but one document serves both the first-time user and the
  maintainer. The newcomer wades through internals to find the install step; the maintainer
  wades through the install step to find the internals. Neither is wrong, both are slow.

- **5** — Split by moment of need. `README.md` answers "what is this and can I run it in
  sixty seconds". `docs/oca.md` answers "how do I wire the bridge". `docs/runbooks/oca-down.md`
  opens with the symptom, then the command, then the explanation — in that order, because the
  reader's attention budget shrinks as their situation gets worse.

### discoverability

Can the reader find the document without already knowing it exists. Documentation nobody can
route to is a private note.

- **1** — The only description of what `PONDER_OCA=on` does differently from `auto` is in
  the header comment of `oca/bridge.js`. To find it, you must already know the file and the
  flag — and nothing that prints when the bridge fails points at either.

- **3** — `docs/oca.md` exists and is correct, and nothing links to it — not the README
  index, not `ponder doctor`'s failure output, not the module that implements it. It is found
  by `ls docs/` and by nothing else.

- **5** — Linked from the README's index, named in the `ponder doctor` failure message
  ("OCA unreachable — see docs/oca.md"), and cross-referenced from the top of `oca/bridge.js`.
  Three independent routes, at least one of which appears at the moment the reader needs it.

### runnable-examples

The examples run, unmodified, in the environment the reader actually has. This is a distinct
dimension from `accuracy` because prose can be perfectly true and the examples still unusable
end to end.

- **1** — The quickstart's first command uses `--rubric-file`, a flag that was renamed to
  `--rubric` two months ago. Nothing in the example works.

- **3** — Every command is real, but the walkthrough silently assumes a session already
  exists. A reader following top to bottom gets `no open session in this project` at step three
  and has to reverse-engineer the missing `ponder start`.

- **5** — Every fenced block is copy-pasteable from a clean checkout, in order, with no
  hidden state — and a test harvests the blocks and executes them, so a rename breaks CI before
  it reaches a reader.

### staleness

Signals that the document has fallen behind, independent of any specific error already found.
`accuracy` grades known wrongness; `staleness` grades the probability of unknown wrongness.
A stale document that happens to still be correct is a 3, not a 5, because nothing is keeping
it correct.

- **1** — Last touched 14 months ago. The module it describes has 60 commits since,
  including a file rename, and the document still names the old path. The `comm -12` commit
  check returns zero shared commits.

- **3** — Four months behind. Describes the current shape correctly, but presents a
  deprecated flow as if it were the recommended one, so a reader picks the wrong path for
  reasons that are nobody's fault.

- **5** — The document changes in the same commit as the code it describes — verifiable,
  not aspirational — and carries a `verified against: <commit>` marker plus a CI check that
  fails when the code path changes and the doc does not.

## What evidence looks like

Evidence is `path:line` or `path:line-line`, never a bare filename.

| Finding kind | Required evidence |
|---|---|
| Drift (`accuracy`) | Doc anchor **and** code anchor: `["README.md:14", "package.json:1-9"]` |
| Missing surface (`gap.api.*`) | Code anchor plus the enumerator command that found it |
| Missing env var (`gap.env.*`) | Every `process.env.X` read site: `["lib/cli.js:22", "oca/bridge.js:9"]` |
| Runbook gap | The failure mode in code plus the git evidence it has happened: `["oca/bridge.js:64", "git:9f2c1ab"]` |
| Staleness | Both `git log -1` outputs, as a note in `detail`, with the doc path as evidence |
| Audience-fit / discoverability | The doc anchor plus the route that should exist and does not |

A finding whose evidence is only the document — no code anchor, no command, no commit — is a
style preference. The Skeptic should delete it.

Line numbers move between passes while the loop is running. When the anchor is a line in code
someone else is editing, quote the expression as well as the path — `lib/session.js` plus
`maxPasses = 6` survives a refactor that `lib/session.js:31` does not, and it is the quoted
text that lets the next pass re-locate the evidence instead of re-arguing it.

## Severity calibration

| Situation | Severity |
|---|---|
| Drift in a procedure a reader follows literally (install, runbook, API reference) | `must` |
| Missing runbook for a failure that has already happened at least once | `must` |
| Undocumented public API with external consumers | `must` |
| Undocumented environment variable that changes behaviour silently | `should` |
| Undocumented internal helper nobody calls from outside the module | `note` |
| Prose that is correct but wordy, headings, formatting, tone | `note` |

Confidence rule: a gap found by an enumerator command is `confidence: 0.9` or above — the
command is repeatable proof. A gap found by reading and reckoning is `0.6` at best until
someone runs a command.

## What each perspective hunts

### Skeptic — emits `delete`

- Findings with a doc anchor and no code anchor. Those are taste, not drift.
- The same drift reported once per document that repeats it. One source, one finding.
- "Undocumented" findings against private helpers, test fixtures and generated files.
- Gap units invented for audiences that do not exist ("a tutorial for new contributors" on a
  single-maintainer project with no contributors).
- Findings that would be resolved by deleting the document rather than writing more of it —
  those belong to the Builder as an `edit`, but a stale doc nobody should keep is a delete
  candidate for the *doc*, and the Skeptic should say so in `why`.

### Builder — emits `edit`

- Turn "the docs are incomplete" into a filename, an audience, and the three questions the
  document must answer in order.
- Turn "this is wrong" into the corrected sentence, written out in `recommendation`.
- Attach the mechanical fix to every drift finding: the test that would have caught it, the
  CI check, the `verified against` marker.
- A docs finding is not actionable until someone could write the document from the
  `recommendation` field alone without asking a question.

### Dreamer — emits `add`

- The document nobody thought to want: the one-page mental model, the failure-mode index, the
  ADR explaining why the bridge shells out to `psql`, the "what this deliberately does not do"
  page.
- The whole categories the survey skipped because they are not files: `--help` text, error
  messages, schema comments, `.env.example`, the first ten lines of a script.
- The reframe: this document is unwritable because the concept is bad. Six paragraphs
  explaining a confusing flag are evidence for changing the flag.

### Empath — emits `change`

- Re-rank by who gets hurt and when. The 3am runbook gap outranks the missing JSDoc every
  time, even when both score 1.
- Raise severity on any drift a reader will trust: copy-pasteable commands, install steps,
  anything with a dollar sign in front of it.
- Lower severity on completeness findings against documents whose real audience already knows
  the answer.
- Fix the ordering inside the report so the person reading it does the highest-pain work first.

## What a later pass does with this lens

Pass 1 builds the inventory. Passes 2 and 3 have a different job, and re-reading the same
documents is not it.

- **Re-run the three gap enumerators.** They are commands, so they are cheap, and their
  output changes as the code changes underneath the session. Anything new arrives as a
  `unit-add` delta, which is a legitimate way for coverage to fall on pass 3.
- **Check the accuracy findings against the tree again.** On a repo under active edit, drift
  found on pass 1 is sometimes fixed by pass 3 — that is a `change` to `status: resolved`,
  not a silent deletion, and the ledger has to record that it was ever true.
- **Spend the pass on the `gap.` units.** They are the ones with no document to re-read, so
  they are the ones a lazy pass drifts away from. If pass 3 touched only `doc.` units, the
  pass graded the easy half twice.

## Common failure modes of this lens

1. **Grading only files.** Coverage 1.0 across `docs/**` while `--help` is wrong and three
   environment variables are undocumented is not coverage, it is a rounding error.
2. **Grading the docs you wish existed.** A tutorial nobody would read is not a gap. Every
   `gap.` unit needs a named audience and a named question.
3. **Confusing accuracy with staleness.** A document can be old and right, or fresh and wrong.
   They are separate dimensions because they have separate fixes.
4. **Reporting drift per occurrence.** Four documents repeating one wrong default is one
   finding, at the source, with four evidence anchors.
