# Runway Monte Carlo Agent Skill

"How long does our cash last?" has a naive answer (cash ÷ burn) and a true one:
a distribution. Burn wobbles, revenue growth compounds or doesn't, and the gap
between the median path and the unlucky decile is the gap between a calm
fundraise and a bridge round. This skill runs the actual simulation — thousands
of paths, drawn by the bundled zero-dependency script, never by token
generation — and reports runway as percentiles with a month-by-month death
curve.

It also writes a real `.xlsx` whose Assumptions cells are live: edit the burn
number in the spreadsheet and the naive-runway formula recalculates.

## What the script computes

- **P10 / P50 / P90 runway** in months, alongside the naive cash÷net-burn
  number for contrast
- **Death curve** — % of simulated paths out of cash by each month
- **Survival probability** at the horizon (default 36 months)
- A 7-sheet `.xlsx` with the assumptions, percentiles, and per-month
  probabilities

Model, stated plainly: `burn_t ~ Normal(burn, burn·σ)` clamped ≥ 0; revenue
compounds with noisy growth; net burn floors at 0 when revenue exceeds burn.
Honest limits, in the SKILL.md and the output: normal noise (no fat tails), no
seasonality, no fundraise events — model the round separately. Deterministic
with `--seed`.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/runway-monte-carlo
```

Then ask your agent: `we have $2.4M and burn $210k/mo — when do we die?`

## Run the script directly

```bash
python3 agent_skills/runway-monte-carlo/scripts/runway_sim.py run out.xlsx \
  --cash 2400000 --burn 210000 --burn-vol 0.12 \
  --revenue 60000 --rev-growth 0.05 --seed 7
```

Python 3.9+, standard library only — no pip install, no network access.

## Privacy

Everything runs locally. The script reads flags (or a `--config` JSON), writes
one `.xlsx`, and makes no network calls.

## Source

Contributed from the MIT-licensed
[pm-claude-skills](https://github.com/mohitagw15856/pm-claude-skills) library,
where this skill is Production-tier: eval-cased, contract-tested on Python
3.9/3.11/3.13, and security-scanned in CI.
