# 🔀 Triage Issue Agent Skill

Triages non-prod incidents and bug reports the way a careful on-call engineer
would: ask first, investigate the evidence, test the reporter's theory rather
than adopt it, route to the one team that owns the fix, and score the RCA
before handing it off.

Want the skill to improve itself against your own labeled tickets and RCAs? The
[Self-Improving Triage Agent](../../advanced_ai_agents/multi_agent_apps/self_improving_triage_agent/)
app runs a measure → diagnose → edit → re-measure loop over this `SKILL.md`.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/triage-issue
```

Then ask your agent: `triage this staging bug and route it to the owning team`,
`write an RCA from these logs`, or `score this RCA before I hand it off`.

## The three ideas that make it work

**1. Ask before investigating.** The skill opens with one grouped intake
question: trace IDs, the user's own theory, the symptom window, where the
signals live, what they already ruled out. The user's theory is **the first
hypothesis to falsify, never the answer**. `references/rca-golden-set.json`
includes a confident, plausible pool-exhaustion theory from the engineer who
wrote the service, and it is wrong. A sycophantic agent agrees and scores zero.

**2. Declining is a first-class outcome.** A ticket with no telemetry cannot
produce an evidenced RCA, so the skill returns `insufficient_evidence` plus the
exact query to run. Correctness is credited against what the case *should* have
produced:

| Expected | Actual | Credit |
|---|---|---|
| insufficient_evidence | insufficient_evidence | 1.00 |
| insufficient_evidence | correct | 0.30 |
| insufficient_evidence | wrong | 0.00 |

**3. Correctness, quality and grounding are never averaged.** A well-structured,
well-cited RCA that blames the wrong thing scores high on quality and fails
correctness. A blended number would hide the only fact that matters.

## What's inside

```
triage-issue/
├── SKILL.md                      # router: intake → path → write → score
├── references/
│   ├── intake-ticket.md          # Jira/GitHub path + per-vendor query templates
│   ├── evidence-schema.md        # the one normalized log shape
│   ├── team-roster.md            # routing targets + precedence
│   ├── examples.md               # routing cases, annotated
│   ├── golden_set.json           # labeled routing cases
│   ├── rca-golden-set.json       # labeled RCAs across GCP/AWS/ticket
│   ├── rca-rubric.json           # 25 binary checks, 3 profiles, credit matrix
│   ├── rubric.md                 # why the rubric is shaped this way
│   ├── judge-prompt.md           # judge templates + hygiene rules
│   ├── validation-methods.md     # 8 techniques, and which settles which dispute
│   ├── grounding.md              # how to cite links and code; the 10 checks
│   └── rca-template.md           # RCA document format
└── scripts/
    ├── normalize_evidence.py     # GCP | AWS → one bundle; --link / --code attach
    ├── log_links.py              # parse Logs Explorer links offline
    ├── grounding.py              # are links and code really cited?
    ├── session_link.py           # optional AgentsView replay link for the RCA header
    └── score_rca.py              # correctness + quality + grounding, or --calibrate
```

`SKILL.md` is a thin router: it names which reference to load per path, and
nothing loads up front.

## Run the scripts directly

Everything except the LLM judge in `score_rca.py` is offline and standard
library only. The judge uses [LiteLLM](https://github.com/BerriAI/litellm), so
any provider works with its usual API key variable (`OPENAI_API_KEY`,
`ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, ...).

```bash
# normalize logs from either vendor (auto-detects GCP or AWS)
gcloud logging read '<filter>' --format=json \
  | python3 scripts/normalize_evidence.py - --symptom "checkout 500s" -o bundle.json

# score an RCA: exit 2 if wrong or it cites something never attached, 1 if weak
python3 scripts/score_rca.py --rca incident.md --evidence bundle.json
python3 scripts/score_rca.py --rca incident.md --profile returning-owner --model gpt-4o-mini

# check the judge against the human labels before trusting absolute numbers
python3 scripts/score_rca.py --calibrate
```

A judge reply that cannot be parsed is counted and reported, never silently
scored as a real failing verdict.

### Grounding

When an incident comes with Logs Explorer links and code, the RCA must cite
them, and only them. Seven checks run in code (was an attached link cited? is
every cited link and `path:line` really attached? is each quote verbatim? does
each link pin an absolute time covering the symptom window?) and three are
judged. Citing a link or line that was never attached is a hard fail that
blocks handoff. See `references/grounding.md`.

### Profiles

Same checks, reweighted for who is reading (`--profile`):

- **`balanced`**: handoff gating (default)
- **`returning-owner`**: you built it, moved on, got tagged a year later.
  Weights context, timeline and hypothesis-handling over falsification paperwork.
- **`curious`**: you want the mechanism. Weights causal chain and readability.

## Making it yours

1. **`references/team-roster.md`**: your teams and how ties resolve.
2. **`references/golden_set.json`**: 20–30 of your own tickets, labeled with the
   team that *actually* fixed it, not the first assignee.
3. **`references/rca-golden-set.json`**: your real RCAs with their true root
   causes. Swap the content, keep the shape.

Label from resolution, not from the ticket, or you train the agent to reproduce
today's mis-routes. Add pairs, not singletons: the shipped sets pair two blank
dashboards with different owners, and an RCA that is well-written and wrong
against one that is right, so a rule that fixes one half and breaks the other
shows up as a flat score.

## Evals

[`../evals/triage-issue/`](../evals/triage-issue/) holds the deterministic tests
CI runs on every change (link parsing, every grounding check, evidence
normalization, the golden set's grounding labels, and the scorer with a faked
judge), plus trigger cases and skill-creator `evals.json` behavioral cases.

```bash
for t in agent_skills/evals/triage-issue/test_*.py; do python3 "$t"; done
```
