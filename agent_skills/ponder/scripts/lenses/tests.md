---
name: tests
unit: behaviour
enumerate: |
  1. Derive the behaviour list from the contract, never from the test tree.
  2. Write each promise as a sentence: "When <condition>, <subject> <outcome>."
  3. Add one behaviour per declared failure mode: throw, catch, timeout,
     early return.
  4. Add one behaviour per bug fix in the last year of git history.
  5. Only now open the test tree and map tests onto behaviours, not the
     other way round.
  6. A behaviour with no test is a unit too, and it scores 1 on
     behaviour-coverage.
  7. Collapse duplicates: two sentences describing one observable promise
     are one unit.
  8. Calibrate every grep. Silence means the pattern is wrong until you
     prove otherwise.
  9. Coverage is 1.0 when every behaviour has a grade. Line coverage is not
     this number.
dimensions: [behaviour-coverage, failure-mode-coverage, honesty, speed, isolation, fixture-realism, assertion-specificity]
scale:
  1: the test cannot fail, or does not exist
  2: passes for the wrong reason
  3: catches the obvious break
  4: catches the realistic break, fast and in isolation
  5: exemplary - verified by mutation, and it names the promise when it goes red
---

# tests lens

The subject of this lens is **the promises the system makes**, not the files in `test/`. A
suite is a means. Grading files produces a comfortable number and misses the only question
worth asking: if this behaviour broke tomorrow, would anything go red, and would the red
thing tell you what broke.

## What a unit is

A unit is **one behaviour**: one observable promise, written as a sentence with a condition,
a subject and an outcome.

> When `coverage < 1.0`, `ponder decide stop` exits 2 and names every ungraded unit.

> When the OCA DSN is unreachable, every `oca/bridge.js` export returns `null`, appends a
> line to `oca.log`, and never throws.

> When a delta arrives with an empty `why`, `ponder delta` rejects the whole file and applies
> nothing.

Consequences of that definition:

- **A test file with forty assertions about one promise is one unit.** Forty assertions might
  make it a good test of that one behaviour. They do not make it forty behaviours.
- **An untested behaviour is a unit.** It is the most important kind. A lens that only
  enumerates what the suite already covers can never find the hole it exists to find.
- **A private helper's return shape is not a behaviour.** It is an implementation detail. If
  changing it breaks nothing observable, it promises nothing.
- **One behaviour can be covered by several tests at different levels** — a unit test, an
  integration test and an end-to-end test. That is still one unit, and its grade reflects the
  whole set.

**Unit ids.** `behaviour.<area>.<verb-phrase>`, lowercase dotted, stable across passes:
`behaviour.verdict.blocked-on-partial-coverage`, `behaviour.bridge.never-throws`,
`behaviour.delta.rejects-empty-why`, `behaviour.ledger.append-only`,
`behaviour.cli.next-line-on-every-command`.

## How to enumerate exhaustively

Enumerate from the contract first. Opening `test/` first anchors you to what already exists
and guarantees you miss the gaps.

### 1. From the contract

Every normative sentence in the spec is a candidate behaviour.

```sh
grep -nE '\b(must|never|always|refuses?|blocks?|rejects?|exits?|cannot|may not)\b' SPEC.md
```

For ponder specifically, section 8 is a hand-written behaviour list — every non-negotiable is
a unit, and each one should be checkable by a test that goes red when the guarantee is broken.

### 2. From the public surface

```sh
grep -rhoE '^export (async )?(function|class|const) [A-Za-z0-9_$]+' lib/ oca/ \
  | awk '{print $NF}' | sort -u
```

Each export contributes at least three behaviours: the documented success outcome, the
documented failure outcome, and the boundary (empty input, missing input, hostile input).

### 3. From the CLI surface

Every command crossed with every exit code it can produce.

```sh
grep -rnE 'process\.exit\(|process\.exitCode\s*=' lib/*.js
grep -rn "NEXT:" lib/*.js | wc -l
```

The spec says every command exits 0, 1 or 2, and every command prints a `NEXT:` line. That is
`commands × 3` plus `commands × 1` behaviours, and most suites cover the 0 column only.

### 4. From the branch points

Every branch that changes user-visible output is a promise about which side you land on.

```sh
grep -rnE '\bif \(|\bswitch \(|\?\?|&& |\|\| ' lib/verdict.js

# every place the code gives up. Find the idiom first — `throw new` is one dialect.
grep -rhoE 'throw [A-Za-z.]+\(' lib/ oca/ | sort | uniq -c | sort -rn
grep -rnE 'throw (new [A-Za-z]*Error|userError|stateError)\(' lib/ oca/

# every deadline. Grep the word, not one implementation of it.
grep -rniE 'timeout|deadline|abortcontroller|abortsignal|signal:|SIGKILL' lib/ oca/
```

Both of those greps fail silently in the obvious form, and both failures cost you the
behaviours this lens exists to find:

- `grep -rn 'throw new' lib/ oca/` returns **zero** hits on ponder, which throws from dozens
  of sites — all of them through the `userError()` / `stateError()` factories. An enumerator
  that returns nothing has told you about itself, not about the code.
- `grep -rnE 'setTimeout|AbortController|signal:'` also returns **zero**, while the bridge
  has two real deadlines: `PROBE_TIMEOUT_MS = 2000` and `CALL_TIMEOUT_MS = 5000`, both
  delivered through `execFile`'s own `timeout` option. The 5s timeout is the failure mode
  SPEC 6.3 names explicitly and the one the `failure-mode-coverage` score-5 anchor below
  demands a test for. A grep for one implementation of a deadline missed both.

The verdict rules in spec section 4.1 are eight ordered branches. Eight behaviours, plus the
ordering itself — "rule 1 wins over rule 4 when both match" is its own promise and is the one
that usually has no test.

### 5. From history

```sh
git log --oneline --since='1 year ago' -E --grep='fix|bug|regression|broke' -i
```

Pass `-E` and a plain `|`. The `\|` form returns nothing at all for anyone who has
`grep.patternType = extended` set in their gitconfig, and an empty result here reads as "this
project has never shipped a bug", which is never the finding.

Every fix in that list was a behaviour somebody assumed. Each one is a unit; whether a
regression test exists is what you are grading.

### 6. Only now, the test tree

Find the runner before you grep for test names — the suite is not always where the language's
default runner would look. ponder's own suite is `test/lib.sh`, a shell harness, so
`node --test test/` reports a failure that says nothing about ponder.

```sh
# what actually runs the tests
sed -n '/"scripts"/,/}/p' package.json 2>/dev/null
ls test/ tests/ spec/ 2>/dev/null; grep -rn 'run:' .github/workflows/*.yml 2>/dev/null

# then the test names, in whichever dialect that runner uses
grep -rhoE "(test|it)\(\s*['\"\`][^'\"\`]+" test/ | sed -E "s/.*\(\s*['\"\`]//" | sort

# a shell suite names its tests through its own helper. The most-repeated leading call is it:
grep -rhoE "^[a-z_]+ [\"']" test/*.sh 2>/dev/null | sort | uniq -c | sort -rn | head
```

On ponder that last line returns `44 run_test '`, and `grep -h "run_test" test/*.sh` is then
the real list of test names. Two minutes spent finding the declaration helper is the
difference between enumerating 44 tests and enumerating none.

Map each test name onto a behaviour from steps 1–5. Two outcomes matter:

- Behaviours with no test → the units that carry this lens.
- Tests that map to no behaviour → either you missed a behaviour (add it) or the test asserts
  an implementation detail (a Skeptic `delete` candidate, and a hint that the test blocks
  refactoring for no return).

### Line coverage, and what it is actually for

Whatever your runner's coverage flag is — `node --test --experimental-test-coverage test/`,
`pytest --cov`, `go test -cover`, `cargo llvm-cov`. A suite with no coverage tooling at all is
one finding, not a reason to skip the step.

Run it. Then use it **only as a negative signal**. A file at 0% contains behaviours nobody
enumerated — that is real information. A file at 95% tells you which lines executed, and
execution is not verification: a test with no assertions executes every line it touches. High
line coverage is compatible with a suite that cannot fail.

If a finding on this lens cites a coverage percentage as its evidence and names no behaviour,
it is not a finding.

### Closing the universe

Coverage is 1.0 when every behaviour from steps 1–5 has a grade — including every behaviour
with zero tests. A pass that grades the 40 behaviours the suite already covers and skips the
12 it does not has coverage 0.77 and should be `blocked`.

Two engine mechanics decide whether this session can ever stop:

**A well-tested behaviour still needs a finding.** The engine counts a unit as graded when it
carries at least one finding that is not `retracted`. The behaviours with excellent tests are
exactly the ones you have nothing to say about — so they end the pass ungraded, coverage
lands at 0.9, and `stop` is refused with no override. Record them: score 5, severity `note`,
the test anchor, and the mutation you used to confirm the test can fail. That note is not
bureaucracy; it is the only durable record that somebody verified this promise on purpose.

**Retracting a unit's last live finding un-grades the unit.** Merging two duplicate behaviours
into one — which this lens tells the Skeptic to do — retracts a finding, and if it was the
only one on its unit, coverage falls and the session re-blocks. Retire the duplicate *unit*
with a `unit-delete` delta rather than retracting the finding that was holding its coverage
up, or leave a one-line pointer finding behind.

## The dimensions

### behaviour-coverage

Is this promise checked at all, at the level it is made. Not "is there a test near it" —
is the promise, whole, verified.

- **1** — "Blocked cannot be overridden by `stop`" has zero tests. The only thing holding
  that guarantee up is that somebody read the spec once and wrote an `if`.

- **3** — One happy-path test asserts exit code 2 when a single unit is ungraded. The
  multi-unit case, the `--json` output shape, and the second half of the promise — "names every
  ungraded unit" — are unchecked. Half the guarantee is decorative.

- **5** — The whole promise is checked: exit code 2, stderr naming all three ungraded
  units, the `--json` payload shape, that `decide continue` still succeeds in the same state,
  and that `--why` cannot buy an override. A stranger reading the test learns the rule.

### failure-mode-coverage

The ways this behaviour breaks under conditions that actually occur — not exotic conditions,
real ones: the dependency is down, the disk is full, the input is malformed, the call times
out, the binary is missing from `PATH`.

- **1** — `oca/bridge.js` is tested only against a reachable Postgres. Its entire contract
  is "returns `null` on any failure, never throws", and not one failure is exercised: no
  unreachable DSN, no missing `psql`, no timeout, no garbage on stdout. The contract's whole
  point is untested, and the one guarantee the engine depends on is unverified.

- **3** — Unreachable DSN is covered and returns `null`. Timeout and non-JSON stdout are
  not, so a hang or a parse throw still reaches the engine in production — which is exactly the
  failure the contract was written to prevent.

- **5** — One test per documented failure mode: connection refused, DSN pointing at a
  firewalled host so the 5s timeout fires, `psql` absent from `PATH`, non-JSON on stdout,
  non-zero exit with content on stderr. Each asserts `null`, asserts no throw, and asserts a
  line was appended to `oca.log`.

### honesty

Does the test fail when the behaviour breaks. **A test that cannot fail scores 1 no matter
how thorough it looks.** This is the dimension that separates a suite from a ritual.

- **1** — `assert.ok(result)` against a function that returns `{}` on every path including
  the error path. Empty the function body and the test still passes. Also 1: an assertion inside
  a `catch` block that is never entered, so the test passes by never reaching its own check; a
  snapshot regenerated to match the bug it should have caught; a test whose only assertion is
  `assert.ok(true)` after a call that cannot throw.

- **3** — The test fails if the function throws, but not if it returns the wrong value —
  it asserts shape, not content. Change `severity: 'must'` to `'should'` in the implementation
  and it stays green. It catches crashes and nothing else.

- **5** — Verified by mutation. Change the rule-1 gate in `lib/verdict.js` from
  `if (metrics.coverage < 1)` to `if (metrics.coverage < 0.9)` and exactly this test goes red,
  with a message naming the promise. The cheap manual version is the same discipline: break the
  code on purpose, run the suite, confirm something red points at the right rule. Record the
  mutation in the test's own comment — as an expression, not a line number, because line
  numbers move and the next person needs to re-verify in ten seconds, not go looking.

### speed

Fast enough that the suite is a feedback loop instead of a gate. Speed is a correctness
property — a suite nobody runs before pushing does not protect anything.

- **1** — The only check on this behaviour lives in a 4-minute end-to-end run that requires
  a live Postgres. Nobody runs it locally, so it fails in CI twenty minutes after the push, on
  someone else's branch, and gets skipped by whoever is unblocking the queue.

- **3** — 900ms, because each test spawns a real `psql` where a fake process boundary would
  do. The suite still runs, but people have started reaching for `--test-name-pattern`, which is
  where a suite goes to die.

- **5** — The behaviour is checked by a unit test in under 20ms with the process boundary
  faked, plus one slow end-to-end test that covers the real wiring, tagged so it can be run
  separately in CI. The fast test runs on every save; the slow test runs once per push.

### isolation

The result depends on the behaviour and nothing else — not test order, not the developer's
environment, not the previous run's leftovers, not a neighbour running in parallel.

- **1** — The test writes to `.ponder/` in the repo root. The second run fails on the
  session that already exists, and two tests in parallel corrupt each other's `ledger.jsonl`.
  It also inherits the developer's `PONDER_OCA`, so it behaves differently on a machine with a
  live Postgres.

- **3** — Uses a temp directory, but shares one module-level session slug across the file,
  so test order matters and a failure in test 2 cascades into 3 and 4. Debugging starts with
  "which one actually broke".

- **5** — Each test gets its own project root via `fs.mkdtemp(path.join(os.tmpdir(), …))`,
  tears it down in a `finally`, sets `PONDER_OCA=off` explicitly rather than inheriting it, and
  the whole file passes green under `node --test --test-concurrency=8` and again with the
  runner's shuffle.

### fixture-realism

The data in the test resembles the data in production closely enough that the test exercises
the code path production will take.

- **1** — The fixture finding set is three findings with `title: "test"`, no evidence, no
  history. Nothing in it can trip the thrash detector, because thrash needs a reversal against
  an earlier delta on the same target — so the detector is untested by construction while
  appearing covered.

- **3** — Individually realistic findings, unrealistic scale: 5 findings where a real
  session carries 80. The report's grouping, ordering and truncation behaviour never runs, and
  the first real session is the first time that code executes.

- **5** — Fixtures captured from a real session and redacted, including the awkward cases
  on purpose: a retracted finding, a finding with four history entries, a unit with no `path`,
  a 200-character title, a `why` containing a newline and a double quote, and a non-ASCII
  subject. The fixture is regenerated by a script so it can be refreshed when the shape changes.

### assertion-specificity

What the failure message tells you when it goes red. A red test is a message to a tired
person; grade it as one.

- **1** — `assert.ok(out.includes('error'))`. Passes on any error including the wrong one,
  passes on a stack trace, passes on the word "error" appearing in a path. The failure message
  is "expected true to be truthy", which tells the reader nothing at all.

- **3** — `assert.equal(code, 2)`. Right exit code, but four different rules exit 2. A red
  test tells you the state machine complained and leaves you to find out which rule fired.

- **5** — `assert.equal(code, 2)` plus
  `assert.match(stderr, /ungraded units: screen\.settings\.billing, screen\.login/)`. A red test
  names the broken promise, and the message is enough to start fixing without opening the test
  file.

## What evidence looks like

Evidence is `path:line` or `path:line-line`, and this lens needs two kinds of anchor.

| Finding kind | Required evidence |
|---|---|
| Weak or missing coverage | Implementation anchor (`lib/verdict.js:44-58`) **and** every test claimed to cover it (`test/verdict.test.js:12-30`), or the note that there is none |
| Dishonest test (`honesty` = 1) | The test anchor plus the exact mutation that leaves it green: `"set severity to 'should' at lib/verdict.js:51 — suite stays green"` |
| Failure-mode gap | The code that declares the failure mode (`oca/bridge.js:64`) plus the enumerator command that surfaced it |
| Speed | A measured number, from `node --test` output or `time`, in `detail`. No number, no finding |
| Isolation | The shared resource, by path or variable: `test/report.test.js:8` writing to `.ponder/` |
| Fixture realism | The fixture anchor plus the production shape it fails to resemble |
| Assertion specificity | The assertion line, and the failure message it currently produces |

A finding that says "needs more tests" with a coverage percentage and no behaviour sentence
has no evidence. The Skeptic deletes it.

## Severity calibration

| Situation | Severity |
|---|---|
| A dishonest test — score 1 on `honesty` | `must` |
| An untested behaviour that appears in the contract as a guarantee | `must` |
| An untested failure mode on a component whose contract *is* its failure behaviour | `must` |
| A behaviour covered only by a slow end-to-end test nobody runs locally | `should` |
| Order-dependence or shared state between tests | `should` |
| Unrealistic fixture scale | `could` |
| Vague assertion on a behaviour that is otherwise well covered | `could` |

A dishonest test outranks a missing test. A missing test is a known hole; a test that cannot
fail is a hole with a sign over it saying the hole is filled, and it actively prevents anyone
from writing the real one.

## What each perspective hunts

### Skeptic — emits `delete`

- "Behaviours" that are implementation details. If nothing observable changes when the detail
  changes, it is not a promise and the test that pins it is a refactoring tax.
- Duplicate behaviours: two sentences, one promise. Merge into the older id and retract the
  newer, so the ledger records that they were the same thing.
- Coverage findings whose only evidence is a percentage.
- Speed findings with no measured number, isolation findings with no named shared resource.
- Findings demanding exhaustive parametrisation of a behaviour with one real caller.

### Builder — emits `edit`

- Turn "needs a test" into the test: file, name, arrange, act, the exact assertion, and the
  mutation that must turn it red. That last part is not optional — a coverage recommendation
  without a stated mutation cannot be verified.
- Turn "this test is weak" into the replacement assertion, written out.
- Attach the mechanical enabler: the fixture factory, the temp-dir helper, the fake process
  boundary that makes the fast version possible.
- A finding on this lens is actionable when someone could write the test from the
  `recommendation` field without reading anything else.

### Dreamer — emits `add`

- The behaviour class nobody enumerated: concurrency (two `ponder` processes on one session),
  crash-mid-write (a truncated final line in `ledger.jsonl`), the empty case (zero units, zero
  findings, zero deltas), the huge case (400 findings in `report.md`), the hostile case (a
  `why` with a newline, a quote and a null byte).
- Promises made only in the README, or only in a `--help` string, that nobody thought to test
  because they are not in the code.
- The reframe: this behaviour is hard to test because the seam is in the wrong place. A
  finding proposing a seam is worth more than five findings proposing mocks.
- Cross-cutting invariants that no single test owns: the ledger is append-only across every
  command; every command prints `NEXT:`; no command ever removes a finding.

### Empath — emits `change`

- Re-rank toward the behaviours whose breakage reaches a person. The bridge silently
  swallowing a real error outranks a slow fixture, whatever the raw scores say.
- Raise `honesty` findings above coverage findings on the same unit. False confidence is more
  expensive than acknowledged ignorance.
- Raise anything that makes the suite untrustworthy — flakes, order-dependence — because
  their real cost is that people start ignoring red, and after that the whole suite is worth
  nothing.
- Lower the score-inflating urge to test the framework instead of the promise.

## What a later pass does with this lens

Pass 1 enumerates behaviours and grades them from reading. Pass 2 and pass 3 exist to convert
those readings into verified facts, and re-reading the same test files is not that.

- **Run the mutations you promised.** Every `honesty` finding graded from reading is capped at
  `confidence: 0.5`. A later pass breaks the code on purpose, runs the suite, and `change`s
  the score and the confidence to what the mutation proved. That is the highest-value delta
  this lens can produce, and it is only available to a pass that is not the first.
- **Re-run the suite and read the clock.** `speed` findings need a number. If pass 1 recorded
  one, pass 3 checks whether the number moved, because a suite that got slower between passes
  is a behaviour about the project, not about a test.
- **Retest the behaviours whose code changed underneath you.** The tree moves between passes.
  A behaviour graded 4 on pass 1 can be a 1 by pass 3 without anybody touching its test.
- **Expect churn to fall and honesty findings to rise.** A late pass whose deltas are all
  `add` never argued with itself; a late pass with no `change` never re-graded anything, which
  on this lens usually means nobody ran a mutation.

## Common failure modes of this lens

1. **Enumerating test files.** Then coverage 1.0 means "we looked at every file we already
   have", which is precisely the claim this lens exists to refuse.
2. **Substituting line coverage for behaviour coverage.** They are different measurements and
   only one of them is about promises.
3. **Grading the suite instead of the behaviours.** "The suite is slow" is not a finding
   against a unit. "This behaviour is only checked by a 4-minute run" is.
4. **Skipping the honesty check because it takes effort.** Mutating the code and re-running is
   the single highest-yield thing this lens does. A pass that never ran a mutation has not
   graded `honesty`, it has guessed at it — cap `confidence` at 0.5 and say so.
