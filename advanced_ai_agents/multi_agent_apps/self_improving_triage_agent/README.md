# 🔀 Self-Improving Triage Agent

A triage skill that rewrites itself. Three agents run a measure → diagnose →
mutate → re-measure loop over `SKILL.md`, and **only edits that raise the score
survive**.

Two things get measured:

| | Question | Scored by |
|---|---|---|
| **Routing** | did the issue reach the owning team? | `scripts/score_routing.py` |
| **RCA** | did the analysis reach the real cause, and is it evidenced? | `scripts/score_rca.py` |

Provider-agnostic via **LiteLLM** — OpenAI, Anthropic, or Gemini with one string.
Vendor-agnostic for logs — **GCP and AWS** normalize to one shape.

![One triage, start to finish](assets/demo.gif)

Open [`assets/demo.html`](assets/demo.html) in a browser for the interactive
version, with chapters you can jump between and pause. The walkthrough uses
cases from the evaluation set; the improvement-loop chart is an illustrative run.

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

## Structure

`SKILL.md` is a thin router: it names which reference to load per path and
nothing loads up front.

```
self_improving_triage_agent/
├── SKILL.md                      # router: intake → path → write → score
├── assets/
│   ├── demo.html                 # interactive walkthrough
│   └── demo.gif                  # the same walkthrough, recorded
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
│   └── rca-template.md           # RCA document format
├── scripts/
│   ├── normalize_evidence.py     # GCP | AWS → one bundle
│   ├── session_link.py           # AgentsView replay link for the RCA header
│   ├── score_routing.py          # routing accuracy (CI gate)
│   ├── score_rca.py              # correctness + quality, or --calibrate
│   └── copilot_login.py          # one-time GitHub Copilot sign-in
├── optimizer/
│   ├── triage_optimizer.py       # the loop; routing scorer; backends
│   ├── rca_optimizer.py          # same loop, RCA scorer
│   ├── copilot.py                # GitHub Copilot sign-in state + model list
│   ├── telemetry.py              # OpenTelemetry traces + human feedback store
│   ├── sessions_view.py          # Sessions tab: browse traces, give feedback
│   └── app.py                    # Streamlit UI (routing)
└── tests/                        # python -m unittest discover -s tests
```

## Setup

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...        # or ANTHROPIC_API_KEY / GEMINI_API_KEY
```

### Using GitHub Copilot (no API key)

A Copilot subscription works instead of a provider key. The models on offer are
whatever your Copilot plan and org policy enable.

```bash
python scripts/copilot_login.py     # one-time device sign-in; prints your models
export TRIAGE_MODEL=github_copilot/<model-id>
python scripts/score_routing.py     # CLIs read TRIAGE_MODEL or --model
streamlit run optimizer/app.py      # pick "GitHub Copilot" — no key field
```

- The token is cached in `~/.config/litellm/github_copilot`.
- Every call counts against your Copilot premium-request allowance. A routing
  round is about (scenarios × 2) + 2 calls, so 10 rounds over 8 scenarios is
  roughly 180 requests.
- This goes through Copilot's editor API, the same way the VS Code extension
  does. Use it for local experiments; don't build CI on it, because GitHub
  supports that API for editors and can change it.

### Using your Claude Code login (no API key)

Pick **Claude Code** in the app's sidebar, or pass `claude_code/<alias>` to the
CLIs (`sonnet`, `opus`, `haiku`; each resolves to the latest model in that family
on your plan). Run the same golden set on Copilot and on Claude Code, then
compare the two sessions in the **Sessions** tab.

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

# UI (routing optimization)
streamlit run optimizer/app.py

# optional: replay links in RCAs (https://github.com/kenn-io/agentsview)
agentsview daemon start
python scripts/session_link.py      # -> http://127.0.0.1:8080/sessions/<id>
```

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
- The Streamlit app currently covers routing only; RCA optimization is CLI and
  `optimizer/rca_optimizer.py`.
