---
name: runway-monte-carlo
description: "Cash runway as a distribution, not a number — Monte Carlo simulated. Use when someone asks how long their cash lasts, when to start fundraising, or how burn/revenue volatility changes their runway; especially when the naive cash÷burn answer is driving a decision. Produces P10/P50/P90 runway, month-by-month death probabilities, and a real .xlsx with editable assumptions and a live naive-runway formula — via the bundled zero-dependency simulator."
---

# Runway Monte Carlo

"Cash divided by burn" is one path through a fan of thousands. Real burn wobbles, revenue growth compounds or doesn't, and the difference between the median path and the unlucky-decile path is the difference between a calm raise and a bridge round. This skill runs the simulation — thousands of paths, actual random draws by the bundled script — and reports runway the way it actually behaves: as percentiles.

## Required Inputs

- **Cash today** and **monthly gross burn** — the two non-negotiables.
- **Monthly revenue** and **monthly revenue growth** (optional — zero for pre-revenue).
- **Volatility** (optional, defaults: burn σ 10%, growth σ 25% of the growth rate) — from the requester's history if they have it, defaults if not, stated either way.
- Horizon (default 36 months) and simulation count (default 5,000).

## Output Format

1. **The distribution** — P10 (unlucky), P50 (median), P90 (lucky) runway in months, the survival probability at the horizon, and the naive cash÷net-burn number alongside for contrast.
2. **The death curve** — % of simulated paths out of cash by each month; the months where it steepens are the danger window.
3. **The decision line** — the one that matters: **raise while P10 exceeds your fundraise time** (6-9 months for most), not P50. Say explicitly when the P10 clock crosses that line.
4. **Stated model limits** — normal noise (no fat tails), no seasonality, no fundraise events modelled. If their reality has lumpy enterprise revenue, say the P10 is optimistic.

## Programmatic Helper

This skill ships `scripts/runway_sim.py` — **zero dependencies**, deterministic with `--seed`:

```bash
python3 scripts/runway_sim.py run runway.xlsx --cash 2400000 --burn 210000 --burn-vol 0.12 \
    --revenue 60000 --rev-growth 0.05 --rev-vol 0.3
```

It prints the percentiles (`naive=16.0mo P10=19 P50=>36 P90=>36 survive(36mo)=56.8%`) and writes an `.xlsx` with an **Assumptions** sheet (editable cash/burn/revenue cells, live naive-runway formula) and a **Death curve** sheet. Requires a code-execution environment.

## Quality Checks

- [ ] The simulation actually ran (script output quoted) — percentiles were not eyeballed
- [ ] P10 is the headline, with the raise-timing implication stated in months and dates
- [ ] The naive cash÷burn number appears next to the distribution so the requester sees what volatility does to it
- [ ] Assumptions and their sources (history vs default) are listed — defaults are labelled as defaults
- [ ] Model limits stated: no fat tails, no seasonality, no modelled fundraise

## Anti-Patterns

- [ ] Do not report only the median — the median is the number that feels fine right up until the P10 path happens to you
- [ ] Do not silently invent volatility — a made-up σ changes the answer more than the burn does; label defaults
- [ ] Do not model the hoped-for fundraise inside the simulation — runway exists to time the raise, not assume it
- [ ] Do not extend the horizon to make survival look better — report the horizon with the number
- [ ] Do not present 56.8% survival as "about half" in one place and "likely fine" in another — one number, one interpretation, used consistently
