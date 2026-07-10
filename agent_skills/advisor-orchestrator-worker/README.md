# Advisor Orchestrator Worker

**One model is a bottleneck. A team with one brain, twenty hands, a tie-breaker, and a board advisor is not.**

This skill turns your coding agent into the orchestrator of a five-tier model team. Big tasks get split into self-contained briefs, cost-estimated before dispatch, reviewed by a mandatory Fable advisor at plan and taste, blasted across cheap parallel workers, verified one by one — with **Papa** (Gemini Pro-tier) stepping in only when workers conflict or advisor and orchestrator cannot align.

## What changed in 1.1

- **Cost control** — Flash pre-flight estimate with token-saving optimizations; soft target tracking via `cost_tracker.sh` (advisory, non-blocking)
- **Papa** — conflict and disagreement resolver only (different provider than Fable); not a gate on every advisor consult
- Mandatory advisor plan review and taste pass **unchanged** from v1.0

## Architecture (v1.1)

```mermaid
flowchart TD
  Orch[Orchestrator]
  Plan[Plan]
  Est[CostEstimator_Flash]
  User[UserApproval]
  Adv[Advisor_Fable]
  Work[Workers_Flash]
  Track[cost_tracker.sh]
  Papa[Papa_Pro_tiebreak]

  Orch --> Plan --> Est --> User --> Adv
  Adv --> Work
  Work --> Verify[Verify]
  Verify --> Synth[Synthesize]
  Synth --> Adv2[Advisor_taste_pass]
  Verify -->|conflict| Papa
  Adv -->|disagreement| Papa
  Adv2 -->|disagreement| Papa
  Work --> Track
  Adv --> Track
  Papa --> Track
```

<img width="3004" height="1408" alt="advisor_skill" src="https://github.com/user-attachments/assets/6f5dc5e8-6828-4598-b23c-72ede97fa238" />

*Original 3-tier diagram (v1.0) — v1.1 adds cost estimate and Papa for conflicts/disagreements only.*

## The team

| Role | Default model <sub>(July 2026, swap freely)</sub> | What it does | What it never does |
|---|---|---|---|
| **Orchestrator** | GPT-5.6 | Frames success criteria, plans waves, dispatches briefs, verifies every result, synthesizes the deliverable | Worker-level grunt work |
| **Cost control** | Gemini 3.5 Flash + `scripts/cost_tracker.sh` | Pre-flight estimate + optimizations; tracks spend vs soft target | Block dispatch or demand approval gates |
| **Papa** | Gemini 3.5 Pro (`PAPA_MODEL=gemini-3.1-pro-preview` for current APIs) | Breaks ties on worker conflicts or advisor–orchestrator disagreement | Execute, rewrite deliverables, or gate routine advisor consults |
| **Workers** | Gemini 3.5 Flash | One self-contained subtask each, in parallel, stateless | Talk to each other, expand scope |
| **Advisor** | Claude Fable 5 | Mandatory plan review and taste pass; judgment on commitment boundaries | Execute anything |

Papa uses a different model family than the advisor so tie-breaking stays independent.

## Why it doesn't fall apart

- **Stateless briefs** ([references/worker-brief.md](references/worker-brief.md)): full inputs inline, temp files only.
- **Cost visibility + optimization** ([references/cost-estimate.md](references/cost-estimate.md), [references/cost-control.md](references/cost-control.md)): estimate, suggest savings, track actuals — never gate the loop.
- **Papa on deadlock only** ([references/papa-routing.md](references/papa-routing.md)): conflicts and advisor–orchestrator splits — not routine routing.
- **Verify before merge**: PASS / FIX / ESCALATE per subtask.
- **Advisor is a critic** ([references/advisor-consult.md](references/advisor-consult.md)): verdict, risks, fixes; every note applied or rebutted.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/advisor-orchestrator-worker
```

Or copy this folder into your agent's skills dir.

**Needs:** `agy`, `claude` CLI, `jq`, `python3`, `scripts/cost_tracker.sh`, `scripts/parse_estimate.sh`, `scripts/parse_papa_route.sh`. API keys: `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) for workers, estimator, and Papa; `ANTHROPIC_API_KEY` for advisor.

## Files

```
advisor-orchestrator-worker/
├── SKILL.md
├── README.md
├── scripts/cost_tracker.sh
├── scripts/parse_estimate.sh
├── scripts/parse_papa_route.sh
├── references/worker-brief.md
├── references/advisor-consult.md
├── references/papa-routing.md
├── references/cost-estimate.md
├── references/cost-control.md
├── references/pricing.json
└── references/fallbacks.md
```

Evals live repo-side in `agent_skills/evals/advisor-orchestrator-worker/`.

Part of [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) · Apache-2.0 · Last verified: July 2026
