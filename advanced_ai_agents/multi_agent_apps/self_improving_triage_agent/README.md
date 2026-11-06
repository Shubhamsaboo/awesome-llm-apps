# 🔀 Self-Improving Triage Agent

A triage skill that rewrites itself. Three agents run a measure → diagnose →
edit → re-measure loop over a `SKILL.md`, and **only edits that measurably raise
the score survive**.

The skill being improved is [`agent_skills/triage-issue`](../../../agent_skills/triage-issue/),
a standard drop-in agent skill: it routes non-prod issues to the owning team and
writes evidence-grounded RCAs. This app is the optimizer around it, and it works
for any other skill in [`agent_skills/`](../../../agent_skills/) too.

## Features

- **Two golden sets, two modes.** *Team assignment* scores routing against
  labeled tickets; *RCA evaluation* has the skill write a fresh RCA per case and
  scores correctness, quality and grounding separately.
- **Any skill, one loop.** A small `Scorer` interface separates *what is
  measured* from the loop, backends and tracing. Routing, RCA, and the
  skill-creator `evals.json` every repo skill ships are three scorers.
- **Noise-aware.** Edits must clear a minimum gain; held-out cases expose
  overfitting; unparseable model replies are counted, never scored as real
  results.
- **No API key needed.** Use OpenAI, Anthropic or Gemini through LiteLLM, or
  your local **Claude Code** login.
- **Traced.** Every run is one OpenTelemetry trace, browsable in the app with
  thumbs-up/down feedback on any call, edit or session.

## How to Run

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/self_improving_triage_agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run optimizer/app.py
```

In the sidebar, choose **Team assignment** or **RCA evaluation**, then a backend:

- **API key**: pick a provider and paste its key. The key stays in your
  session and is sent with each call; it is never written to the process
  environment, so sessions on a shared server cannot use each other's keys.
- **Claude Code**: uses your `claude` CLI login. It runs headless `claude -p`
  from an empty directory with no tools, settings, MCP servers or CLAUDE.md, so
  only the skill under test shapes the answer. Calls count against your plan.

Then in **3 · Run**, **Evaluate skill** scores the current skill once and
**Start optimization** runs the loop. **4 · Results** shows scores, the diff,
every round's outcome, and (for RCA) each generated report. The improved
`SKILL.md` is offered as a download; nothing is written back to disk.

### Command line

```bash
# routing accuracy; exit 1 below the threshold (a CI gate), 2 if replies were unparseable
python scripts/score_routing.py --model gpt-4o-mini --min-accuracy 75
python scripts/score_routing.py --model claude_code/sonnet

# the skill's RCA scorer, plus the Claude Code backend and tracing
python scripts/score_rca.py --rca incident.md --evidence bundle.json --model claude_code/sonnet

# score or improve ANY skill in agent_skills/ against its evals.json
python scripts/optimize_skill.py ../../../agent_skills/scope-creep-detector
python scripts/optimize_skill.py ../../../agent_skills/scope-creep-detector \
    --optimize --rounds 5 --min-gain 5 --holdout 0.3 --out /tmp/SKILL.md
```

`TRIAGE_SKILL_DIR` points the app at a copy of the triage skill elsewhere.

## How It Works

```
  ┌──────────────────────────────────────────────────────────────────────────┐
  │ Entry points   optimizer/app.py · scripts/score_routing.py               │
  │                scripts/score_rca.py · scripts/optimize_skill.py          │
  └──────────────┬───────────────────────────────────────────────────────────┘
                 │ SkillOptimizer.optimize(skill_md, scorer, cases, holdout=…)
  ┌──────────────▼───────────────────────────────────────────────────────────┐
  │ Loop                       optimizer/skill_optimizer.py                  │
  │   baseline → [diagnose → mutate → score → keep?] × N → held-out check    │
  └──────────────┬──────────────────────────────┬────────────────────────────┘
                 │ what "better" means          │ every model call: _ask()
  ┌──────────────▼──────────────────┐  ┌────────▼─────────────────────────────┐
  │ Scorer (pluggable)              │  │ Backends                             │
  │  RoutingScorer   routing        │  │  claude_code/<alias>  claude -p      │
  │  RcaScorer       RCA, uses the  │  │  anything else        LiteLLM        │
  │                  skill's        │  └────────┬─────────────────────────────┘
  │                  score_rca.py   │           │ spans
  │  ExpectationsScorer  evals.json │  ┌────────▼─────────────────────────────┐
  └─────────────────────────────────┘  │ Telemetry  optimizer/telemetry.py    │
                                       │  SQLite (.traces/) + optional OTLP   │
                                       └──────────────────────────────────────┘
```

### The loop

1. **Baseline.** Score the current `SKILL.md` on the training cases. If cases
   are held out, score them too, once.
2. **Round.** The scorer's analyst reads the failures and the edits already
   tried, and names one root cause. The mutator makes one edit. The scorer
   re-measures.
3. **Keep or discard.** Each round ends in one outcome:

   | Outcome | When |
   |---|---|
   | kept | the scorer says it improves by at least `min_gain` points |
   | discarded | it does not |
   | inconclusive | scoring it produced more unparseable replies than the best had, so the number is partly noise |
   | skipped | the analyst's or mutator's reply could not be parsed, so there was no real edit to try |
   | unchanged | the mutator returned the same skill |

4. **Stop** when the scorer says it has converged, after `patience` rounds
   without a kept edit, or at `max_rounds`.
5. **Held-out check.** Held-out cases never decide which edit is kept. The final
   skill is scored on them; a drop is reported as likely overfitting.

**Why the guards.** The shipped routing set has 8 cases, so one flipped case
moves the score 12.5 points. Without a minimum gain and held-out cases, a lucky
run on a model whose temperature cannot be set (Claude) gets locked in.

### Adding a scorer

Implement the `Scorer` protocol in `optimizer/skill_optimizer.py`, usually by
subclassing `BaseScorer`:

```python
class MyScorer(BaseScorer):
    kind = "my-skill"
    objective_label = "my metric %"

    async def score(self, client, skill_md, cases) -> dict:
        # -> {"pass_rate", "passed", "total", "per_eval", "failures", "parse_errors"}
        ...

    async def diagnose(self, client, skill_md, failures, mutation_log) -> dict:
        # -> {"diagnosis", "mutation_strategy", "target_section", "suggested_change"}
        ...
```

Override `improves()` to add vetoes (`RcaScorer` vetoes any edit that invents
a citation or lowers grounding), `converged()` to demand more than 100%, and
`extra_results()` to surface extra metrics. Use `client._ask_json(...,
fallback=...)` for model calls: an unparseable reply returns the fallback
marked with `PARSE_ERROR`, which the scorer should count in `parse_errors`.

### RCA evaluation

`RcaScorer` has the skill write an RCA from each case's evidence bundle or
ticket and intake, then grades it with the skill's own
[`score_rca.py`](../../../agent_skills/triage-issue/scripts/score_rca.py), so a
gain measured here reproduces under the skill's CLI. The objective is
`0.6 × correctness + 0.4 × quality`; grounding is a veto, not a term.

The RCA golden set also holds stored sample RCAs and human scores for **judge
calibration**, some deliberately wrong. `generation_cases()` keeps only the
incident inputs, the documented cause and the target verdict;
`expected_generated_correctness` overrides the calibration verdict where they
differ (`aws-wrong-conclusion` has a wrong sample but expects a correct fresh
RCA). `true_root_cause` goes to the judge, never to the RCA writer.

### Any skill: `ExpectationsScorer`

Every skill in `agent_skills/` ships `agent_skills/evals/<skill>/evals.json` in
Anthropic skill-creator's schema. `ExpectationsScorer` runs the skill on each
prompt and has a judge check each expectation; the objective is the share of
expectations met. The executor has no tools, so it describes any script it
would run. Confirm a gain with the skill's deterministic tests before shipping.

## Reading the output

| Signal | Means |
|---|---|
| Score climbs then flatlines | Working. `patience` stops it after N barren rounds. |
| Every edit discarded | The analyst cannot see the pattern: usually an ambiguous roster or label, not a bad skill. |
| Held-out score dropped | The kept edits fit the training cases. Add cases or raise the minimum gain. |
| `inconclusive` rounds | The model's JSON is unreliable. Try another model before trusting scores. |
| `overconfident` non-empty | The skill concluded on a case with no evidence. Fix that before anything else. |
| Quality up, correctness flat | It is learning to format, not to reason. |

## Observability

Every run is one trace: `optimizer.session` → `optimizer.baseline` /
`optimizer.round` / `optimizer.holdout` → `llm.call`. CLI runs are one trace
each. Each `llm.call` records its role, backend, model, tokens, latency, cost,
prompt and response.

- **Sessions tab.** Browse runs, step through rounds, read every call, and rate
  a call, an edit or a whole session. Ratings are stored beside the spans and
  emitted as `human.feedback` spans.
- **Local store.** `.traces/traces.db` (gitignored); set `TRIAGE_TRACE_DB` to
  use another.
- **Any OTLP collector.** `export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`.
- **Prompt content** is recorded clipped to 20k characters. Set
  `TRIAGE_TRACE_CONTENT=0` to record sizes only.

## Tests

```bash
python -m unittest discover -s tests -v                      # this app
for t in ../../../agent_skills/evals/triage-issue/test_*.py; do python3 "$t"; done   # the skill
```

No network and no credentials: `claude` and LiteLLM are faked. App tests cover
the backends and their isolation, per-call API keys, the loop's guards, all
three scorers, both UI modes, the Sessions tab and the CLIs. The skill's tests
run in the repo's skill-evals CI with no dependencies installed.

## Project Structure

```
self_improving_triage_agent/
├── optimizer/
│   ├── skill_optimizer.py      # model client, Scorer protocol, the loop
│   ├── routing_scorer.py       # team assignment
│   ├── rca_scorer.py           # RCA correctness, quality, grounding
│   ├── expectations_scorer.py  # any skill's evals.json
│   ├── skill_paths.py          # where agent_skills/triage-issue lives
│   ├── telemetry.py            # OpenTelemetry spans, SQLite store, feedback
│   ├── sessions_view.py        # Sessions tab
│   └── app.py                  # Streamlit UI
├── scripts/                    # score_routing.py, score_rca.py, optimize_skill.py
└── tests/
```

## Notes

- `temperature=0.0` for executing and judging, `0.4` for mutation. Models that
  reject sampling params get them dropped (`litellm.drop_params`), so their
  scores vary between runs; that is what the minimum gain and held-out cases
  are for.
- LiteLLM is imported through `_import_litellm()`: its first import can
  deadlock with Streamlit's logging thread otherwise.
- Re-baseline after editing the judge prompt or rubric. Scores from before and
  after are not comparable.
- Cost per RCA round ≈ (1 + judge runs) calls per case, plus 2 for diagnose and
  mutate.
