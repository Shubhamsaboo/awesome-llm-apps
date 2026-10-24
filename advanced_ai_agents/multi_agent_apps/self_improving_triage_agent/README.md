# 🔀 Self-Improving Triage Agent

A triage skill that rewrites itself. Three agents run a measure → diagnose →
mutate → re-measure loop over `SKILL.md`, and **only edits that raise the score
survive**.

Three things get measured:

| | Question | Scored by |
|---|---|---|
| **Routing** | did the issue reach the owning team? | `scripts/score_routing.py` |
| **RCA** | did the analysis reach the real cause, and is it evidenced? | `scripts/score_rca.py` |
| **Grounding** | does the RCA cite the attached log links and code, and only those? | `scripts/score_rca.py` |

Provider-agnostic via **LiteLLM** — OpenAI, Anthropic, or Gemini with one string.
Vendor-agnostic for logs — **GCP and AWS** normalize to one shape.

---

## The three ideas that make it work

### 1. Ask before investigating

The skill opens with an intake step: trace IDs, the user's own theory, the
symptom window, where the signals live, what they already ruled out.

The user's theory is treated as **the first hypothesis to falsify, never the
answer**. `references/rca-golden-set.json` includes the case that enforces this:
a confident, plausible pool-exhaustion theory from the engineer who actually
wrote the service — and it is wrong. A sycophantic agent agrees with them and
scores zero.

### 2. Declining is a first-class outcome

A Jira ticket with no telemetry cannot produce an evidenced RCA — it fails
`ev_quotes_log`, `ev_correlation_id` and `ev_no_fabrication` by construction. So
the skill returns `insufficient_evidence` plus the exact query to run.

Correctness is scored against **what the case should have produced**, not against
a fixed "correct":

| Expected | Actual | Credit |
|---|---|---|
| insufficient_evidence | insufficient_evidence | 1.00 |
| insufficient_evidence | correct | 0.30 |
| insufficient_evidence | wrong | 0.00 |

An unevidenced right answer earns partial credit at most: it teaches the reader
to trust the next unevidenced answer, and that one will be wrong.

### 3. Correctness and quality are never averaged

`aws-wrong-conclusion` in the golden set scores **89 quality, `wrong`
correctness** — well-structured, well-cited, and it blames the wrong thing. One
blended number would report ~70 and hide the only fact that matters.

The optimizer climbs `0.6 × correctness + 0.4 × quality`, so a perfectly
formatted wrong RCA caps at 40.

---

## Architecture

The app is four layers. Each only talks to the one below it, and the model backend
is the only part that knows which provider is in use.

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │ Entry points                                                           │
  │   optimizer/app.py (Streamlit)    scripts/score_routing.py             │
  │   · backend switch                scripts/score_rca.py                 │
  │   · golden set + loop controls    scripts/session_link.py              │
  │   · Run / Results / Sessions tabs scripts/normalize_evidence.py        │
  └───────────────┬────────────────────────────────────────────────────────┘
                  │ one TriageOptimizer per run
  ┌───────────────▼────────────────────────────────────────────────────────┐
  │ Optimizer           optimizer/triage_optimizer.py, rca_optimizer.py    │
  │   Executor  routes an issue (or writes an RCA) using the SKILL.md      │
  │   Analyst   diagnoses the failures, picks ONE mutation strategy        │
  │   Mutator   applies exactly one edit to the SKILL.md                   │
  │   Scorer    deterministic checks in code, judge calls for the rest     │
  └───────────────┬────────────────────────────────────────────────────────┘
                  │ every model call goes through one method: _ask()
  ┌───────────────▼────────────────────────────────────────────────────────┐
  │ Model backends (picked by the model string's prefix)                   │
  │   claude_code/<alias>   headless `claude -p`, your Claude Code login   │
  │   anything else         LiteLLM: OpenAI, Anthropic, Gemini via API key │
  └───────────────┬────────────────────────────────────────────────────────┘
                  │ every call and every loop step emits a span
  ┌───────────────▼────────────────────────────────────────────────────────┐
  │ Telemetry          optimizer/telemetry.py                              │
  │   OpenTelemetry spans → SQLite (.traces/) and, optionally, OTLP        │
  │   human feedback stored beside the spans, re-emitted as spans          │
  └────────────────────────────────────────────────────────────────────────┘
```

### The loop

1. **Baseline.** Score the current `SKILL.md` over every golden-set scenario.
2. **Round.** The Analyst reads the failures and the mutations already tried and
   names one root cause. The Mutator makes one edit. The Scorer re-measures.
3. **Keep or discard.** The edit survives only if the score rises. A discarded
   edit goes into the "already attempted" list so the Analyst stops re-proposing it.
4. **Stop** at 100%, after `patience` rounds without a gain, or at `max_rounds`.

Routing and RCA share this loop. They differ only in the Scorer and the
Analyst's strategy list (`rca_optimizer.py` overrides `_score` and `_analyze`),
so a gain measured in the app reproduces under the CLI scorer.

### One seam for every model call

`TriageOptimizer._ask()` is the only place a model is called. It picks the
backend from the model string, records a span, and returns text. That is why the
rest of the code is provider-neutral, and why tracing needs no per-agent wiring.

Provider API keys are the standard path. **Claude Code** is an optional local
backend that runs `claude -p` as a subprocess from an empty directory with
  no tools, skills, MCP servers, settings files or saved session. The executor
  must route using only the skill under test, so none of your own Claude Code
  setup (CLAUDE.md, hooks, memory) may reach it. `--bare` would be simpler, but it
  accepts only an API key, which is exactly what this backend avoids.

Sampling parameters can't be set through the Claude Code CLI, and some newer
models reject them, so `litellm.drop_params` is on. The loop's temperatures are hints.

### What a trace looks like

```
optimizer.session                   one run; final score, backend, model
├─ optimizer.baseline               score of the starting skill
│   └─ llm.call × scenarios         role, prompt, response, tokens, cost
└─ optimizer.round × N              strategy, edit, score before → after, kept?
    ├─ llm.call  analyst
    ├─ llm.call  mutator
    └─ llm.call  executor.route × scenarios
```

CLI runs and **Generate scenarios** are one trace each (`cli.score_routing`,
`optimizer.generate`, ...). Calls inside `asyncio.gather` still nest under their
step, because OpenTelemetry context follows asyncio tasks.

Human feedback is keyed by span, so you can rate a single call, a round's edit or
a whole session. Each rating is stored in SQLite and emitted as a `human.feedback`
span under the span it rates, so an OTLP collector sees the verdict next to the
trace it is about.

### Log evidence flow (RCA path)

```
gcloud logging read / aws logs ──► normalize_evidence.py ──► evidence bundle (one shape)
Logs Explorer links  --link ──────►      │                     + attached links + code
code snippets        --code ──────►      │                                   │
                                                                             │
         incident writeup ───────────────────────────────────────────────────┤
                                                                             ▼
                                          score_rca.py: correctness · quality · grounding
```

Both vendors reduce to the same bundle (`references/evidence-schema.md`), so the
rubric and golden set never branch on vendor. The three scores are reported
separately and never averaged.

### Grounding: evals for links and code

When an incident comes with Logs Explorer links and related code, the RCA must
cite them, and only them. `scripts/grounding.py` scores this as a third number.
`references/grounding.md` has the full check list and the citation format.

- **Checked in code, not by a judge.** Seven checks are string and structure
  matches, so the result doesn't vary between runs. `scripts/log_links.py` parses
  each link offline into its project, query, time window and trace IDs.
  - Was an attached link cited?
  - Is every cited link and `path:line` really attached?
  - Is each code quote verbatim?
  - Does each link pin an absolute time, cover the symptom window, and filter on a trace from the evidence?
- **Judged.** Three checks need reading:
  - Does the cited code contain the blamed mechanism?
  - Is a logged error tied to a specific line?
  - Does each link show what the RCA claims?
- **Hard fail.** Citing a link or code line that was never attached, or a quote
  that isn't verbatim, blocks handoff. `score_rca.py` exits 2, the same as a
  wrong conclusion.
- **In the optimizer,** grounding is a veto, not a term in the objective. An edit
  that raises the score but invents a citation, or lowers grounding, is discarded.
- **Golden cases.** Three GCP cases cover this: one fully grounded RCA, its twin
  with one invented code line (must hard-fail while quality stays high), and one
  citing a real link for the wrong day (loses points, not a fabrication). The
  deterministic results are pinned by tests.

### Where the pieces live

| Concern | File |
|---|---|
| The loop, agents, `_ask()`, backends | `optimizer/triage_optimizer.py` |
| RCA scorer and analyst | `optimizer/rca_optimizer.py` |
| Spans, SQLite store, feedback, OTLP | `optimizer/telemetry.py` |
| Sessions tab | `optimizer/sessions_view.py` |
| UI | `optimizer/app.py` |
| Judge, rubric, golden sets | `scripts/score_rca.py`, `references/` |

LiteLLM is imported through `_import_litellm()`, not a bare `import litellm`.
LiteLLM's first import is slow, and a log record from another thread during it
(Streamlit's server thread does this) deadlocks its own redaction filter. The
guard drops records for that window and keeps redaction on.

---

## Structure

`SKILL.md` is a thin router: it names which reference to load per path and
nothing loads up front.

```
self_improving_triage_agent/
├── SKILL.md                      # router: intake → path → write → score
├── references/
│   ├── intake-ticket.md          # Jira/GitHub path + per-vendor query templates
│   ├── evidence-schema.md        # the one normalized log shape
│   ├── team-roster.md            # routing targets + precedence
│   ├── golden_set.json           # labeled routing cases
│   ├── examples.md               # routing cases, annotated
│   ├── rca-rubric.json           # 25 binary checks, 3 profiles, credit matrix
│   ├── rca-golden-set.json       # labeled RCAs across GCP/AWS/ticket
│   ├── rubric.md                 # why the rubric is shaped this way
│   ├── judge-prompt.md           # judge templates + hygiene rules
│   ├── validation-methods.md     # 8 techniques, and which settles which dispute
│   ├── grounding.md              # how to cite links and code; the 10 checks
│   └── rca-template.md           # RCA document format
├── scripts/
│   ├── normalize_evidence.py     # GCP | AWS → one bundle; --link / --code attach
│   ├── log_links.py              # parse Logs Explorer links offline
│   ├── grounding.py              # third score: are links and code really cited?
│   ├── session_link.py           # AgentsView replay link for the RCA header
│   ├── score_routing.py          # routing accuracy (CI gate)
│   └── score_rca.py              # correctness + quality + grounding, or --calibrate
├── optimizer/
│   ├── triage_optimizer.py       # the loop; routing scorer; backends
│   ├── rca_optimizer.py          # same loop, RCA scorer
│   ├── telemetry.py              # OpenTelemetry traces + human feedback store
│   ├── sessions_view.py          # Sessions tab: browse traces, give feedback
│   └── app.py                    # Streamlit UI (team assignment + RCA evaluation)
└── tests/                        # python -m unittest discover -s tests
```

## Setup

From this directory, create an environment, install dependencies, and configure a
provider API key. The example uses OpenAI; set `ANTHROPIC_API_KEY` or
`GEMINI_API_KEY` instead when choosing a model from those providers.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
python scripts/score_routing.py --model gpt-4o-mini
streamlit run optimizer/app.py
```

### Using your Claude Code login (no API key)

Pick **Claude Code** in the app's sidebar, or pass `claude_code/<alias>` to the
CLIs (`sonnet`, `opus`, `haiku`; each resolves to the latest model in that family
on your plan). Run the same golden set on an API provider and on Claude Code,
then compare the two sessions in the **Sessions** tab.

```bash
python scripts/score_routing.py --model claude_code/sonnet
```

- Each call runs headless `claude -p` from an empty directory with no tools,
  skills, MCP servers, settings files or saved session. Your own Claude Code
  setup (CLAUDE.md, hooks, memory) can't leak into the routing decision.
- Calls count against your Claude Code plan's usage limits. Each one starts a CLI
  process, so it is slower than an API call; lower "Parallel scenario calls" if
  you hit rate limits.
- `temperature` can't be set through the CLI, so it is not applied here.
  Expect some run-to-run variance.

```bash
# normalize logs from either vendor (auto-detects)
gcloud logging read '<filter>' --format=json \
  | python scripts/normalize_evidence.py - --symptom "checkout 500s" -o bundle.json

# score an RCA
python scripts/score_rca.py --rca incident.md --evidence bundle.json
python scripts/score_rca.py --rca incident.md --profile returning-owner

# check the judge against your human labels before trusting absolute numbers
python scripts/score_rca.py --calibrate

# routing accuracy; exits 1 below the threshold, so it gates a merge
python scripts/score_routing.py --min-accuracy 75

# UI (team assignment and RCA evaluation)
streamlit run optimizer/app.py

# optional: replay links in RCAs (https://github.com/kenn-io/agentsview)
agentsview daemon start
python scripts/session_link.py      # -> http://127.0.0.1:8080/sessions/<id>
```

## Two evaluation modes in the UI

Use **Evaluation** in the sidebar to switch between:

| Mode | Golden set | What the skill produces | What gets scored |
|---|---|---|---|
| **Team assignment** | `references/golden_set.json` | Team, severity, and routing rationale for each ticket | Routing checks, including exact team matching |
| **RCA evaluation** | `references/rca-golden-set.json` | A fresh RCA from each evidence bundle or ticket and its intake | Correctness against the documented cause, rubric quality, and evidence grounding |

Each mode has its own golden-set editor and results. Switching modes preserves
your dataset edits and does not show a routing result as an RCA result. The
starting skill is shared. Edits in the UI do not overwrite the source files.

1. Choose **Team assignment** or **RCA evaluation** and a model backend.
   **Claude Code** works with your CLI login instead of an OpenAI API key.
2. Review the skill in **1 · Skill** and the mode's labels in **2 · Golden set**.
   RCA mode also offers a scoring profile and judge-run count in the sidebar;
   its rubric is visible in the golden-set tab.
3. In **3 · Run**, choose **Evaluate skill** to score once without editing the
   skill, or **Start optimization** to run the improvement loop.
4. In **4 · Results**, inspect the scores and failures. RCA results include
   separate correctness, quality, and grounding metrics, each generated report,
   its check details, and a JSON download. Improved skills can be downloaded;
   they are not automatically written back to disk.

RCA optimization uses `0.6 × correctness + 0.4 × quality` as its objective,
while grounding remains a separate veto. A fabricated citation is reported as a
handoff failure even if correctness and quality are high.

### Generation targets versus judge calibration

The RCA golden set also contains stored `rca` examples, `human_quality` scores,
and `expected_correctness` verdicts for **judge calibration**. Some samples are
deliberately wrong; the skill should not learn to reproduce them.

For the UI's generation task, `generation_cases()` keeps only incident inputs,
the documented cause, and the target verdict. A case can set
`expected_generated_correctness` to override the calibration verdict—for example,
`aws-wrong-conclusion` has a wrong sample RCA but expects a **correct** freshly
generated RCA. Ticket-only cases still expect **insufficient_evidence**.
The RCA editor displays these generation targets as `expected_correctness`.
Stored sample RCAs and human scores are excluded, and `true_root_cause` is
passed to the judge, never to the RCA writer.

## Profiles

Same checks, reweighted for who is reading. `--profile`:

- **`balanced`** — handoff gating (default)
- **`returning-owner`** — you built it, moved to other projects, got tagged a
  year later. Weights context, timeline, and hypothesis-handling over
  falsification paperwork.
- **`curious`** — you want the mechanism. Weights causal chain and readability.

## Making it yours

1. **`references/team-roster.md`** — your teams and how ties resolve.
2. **`references/golden_set.json`** — ~20–30 of your own tickets, labeled with the
   team that *actually* fixed it, not the first assignee.
3. **`references/rca-golden-set.json`** — your real RCAs with their true root
   causes. Swap the content, keep the shape.
4. **`SKILL.md`** — the loop improves it; it does not need to be good yet.

### The golden set is the ceiling

The loop optimizes toward your labels and inherits their mistakes.

- **Label from resolution, not from the ticket.** Otherwise you train the agent
  to reproduce your current mis-routes.
- **Add pairs, not singletons.** The shipped sets pair deliberately: two blank
  dashboards with different owners; two post-deploy bugs where only one is a
  pipeline defect; one RCA that is well-written and wrong against one that is
  right; one case with a user hypothesis against one without. A rule that fixes
  one half and breaks the other shows up as a flat score and gets discarded — a
  singleton would have let it through.

## Reading the output

| Signal | Means |
|---|---|
| Accuracy climbs then flatlines | Working. `patience` stops it after N barren rounds. |
| Every mutation discarded | The Analyst cannot see the pattern — usually an ambiguous roster, not a bad skill. |
| `overconfident` non-empty | The skill concluded on a case with no evidence. Fix that before anything else. |
| `unstable_checks` recurring | That check is ambiguous. Reword it; don't just raise `--runs`. |
| Quality up, correctness flat | It is learning to format, not to reason. |
| Calibration bias > 10 pts | Reword the checks the judge misreads before trusting absolute scores. |

**A gain on a handful of cases is not a gain.** With 5 RCA cases one lucky
mutation moves the objective 20 points. Confirm on held-out cases the loop never
saw before committing a new `SKILL.md`.

## Observability

Every run is one OpenTelemetry trace:
`optimizer.session` → `optimizer.baseline` / `optimizer.round` → `llm.call`.
CLI runs (`cli.score_routing`, `cli.score_rca`) are one trace each too. Each
`llm.call` records:
- its role (executor, judge, analyst, mutator), backend and model
- tokens, latency and cost (Claude Code reports list-price cost)
- the prompt and response

**Sessions tab.** Open **5 · Sessions** in the app to:
- browse runs and step through baseline and rounds
- read every call
- rate any call, a round's SKILL.md edit, or the whole session, with thumbs and a comment

Ratings are saved next to the spans and also emitted as `human.feedback` spans
under the span they rate, so a collector sees them too.

**Local store.** Spans go to `.traces/traces.db`, which is gitignored. Point
`TRIAGE_TRACE_DB` somewhere else to keep separate stores.

**Any OTLP collector.** Set the standard variable and spans are sent there as well:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318   # Jaeger, Tempo, Phoenix, ...
```

**Prompt content.** Prompts and responses contain incident text, so they are
recorded clipped to 20k characters. Set `TRIAGE_TRACE_CONTENT=0` to record sizes
only.

## Tests

```bash
python -m unittest discover -s tests -v
```

These need no network and no credentials: `claude` and LiteLLM are faked, and
the OTLP test uses a throwaway local collector. They cover:
- backend selection and Claude Code isolation flags
- span nesting across parallel calls
- feedback storage and the Sessions UI
- a CLI run producing one trace
- link parsing, every grounding check, and the third score in `score_rca.py`
- the golden set's grounding labels, reproduced with no model
- the optimizer's grounding veto
- separate team/RCA UI datasets, score-only runs, RCA optimization, generated
  reports, and calibration-label isolation

## Notes

- `temperature=0.0` for routing, scoring and judging; `0.4` for mutation — the
  loop needs a stable ruler and a creative editor. Models that reject sampling
  params (newer Claude accepts only `temperature=1`) get them dropped via
  `litellm.drop_params`, so their scores vary a little between runs. Compare
  against the golden set, not against a single prior run.
- The optimizer calls the same scorer as the CLI, so a measured gain reproduces
  under `score_rca.py` instead of being an artifact of a second code path.
- Re-baseline after editing `judge-prompt.md` or the rubric. Scores from before
  and after are not comparable.
- Cost per RCA round ≈ (1 + runs) calls per case, plus 2 for analyse/mutate.
- The Streamlit app supports both team assignment and RCA evaluation, using
  `TriageOptimizer` and `RcaOptimizer` respectively.
