# Skill Evals

How this repo checks that its skills actually work — before they ship and on
every change after. Layout: one folder per skill, `evals/<skill-name>/`,
mirroring the skill's name. These files never ship in an install; the skill
folders contain only what runs at runtime.

Two tiers (vocabulary borrowed from
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/tree/main/evals),
which formalized the pattern):

| Tier | What it checks | Runs | Cost |
|---|---|---|---|
| 1. Deterministic | The skill's scripts do what they claim — every classifier, edge case, and output shape, asserted against synthetic fixtures | CI on every PR, and by hand before installing | Free, ~10s |
| 2. Trigger | The skill activates on the prompts it should and stays quiet on near-misses | By hand, in an agent session (needs a model) | Tokens |

## Running

```bash
# Tier 1 — deterministic, no dependencies beyond git + Python
python3 awesome_agent_skills/evals/project-graveyard/test_graveyard.py
```

Tier 2 is a manual protocol for now: each skill's `trigger-cases.json` lists
the prompts that must activate it (and the near-misses that must not). Install
the skill in a fresh agent session, paste each prompt, check activation
matches `should_trigger`. Re-run whenever a skill's `description` changes —
that field is the entire trigger surface.

## Track record

Not theater: tier 1 caught a symlink-path bug that silently disabled relapse
detection on macOS, and an external reviewer running it in a clean Linux
checkout caught a filesystem-ordering bug that mis-attributed the kill-chain.
Both fixed before merge. That's the job.

## Adding a skill

New skill → new `evals/<skill-name>/` with at minimum a deterministic
`test_<skill>.py` (self-contained, tempdir fixtures, exit 0/1) and a
`trigger-cases.json`. CI picks up `test_*.py` automatically.
