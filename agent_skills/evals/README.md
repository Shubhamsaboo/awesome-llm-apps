# Skill Evals

How this repo checks that its skills actually work — before they ship and on
every change after. Layout: one folder per skill, `evals/<skill-name>/`,
mirroring the skill's name. These files never ship in an install; the skill
folders contain only what runs at runtime.

The tier model follows
[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills/tree/main/evals)
— same names, same jobs — plus two tiers of our own, because skills here ship
executable code and his don't:

| Tier | What it checks | Runs | Cost |
|---|---|---|---|
| 1. Structural | Frontmatter, naming, name==dir, unfilled placeholders, text-only prompt dumps (`tools/skill_lint.py --strict`) | CI | Free |
| 1b. Security *(ours)* | Install lures, undeclared network calls, credential access, obfuscated payloads (`tools/skill_scanner.py`) | CI | Free |
| 2. Trigger & routing | Positive prompts clear near-miss negatives on description vocabulary; with 2+ skills, positives rank their own skill first and no two descriptions near-collide (`tools/run_trigger_evals.py`) | CI | Free |
| 2b. Deterministic scripts *(ours)* | The skill's bundled scripts do what they claim — every classifier, edge case, and output shape against synthetic fixtures (`<skill>/test_*.py`) | CI | Free, ~10s |
| 3. Behavioral | An agent following the skill satisfies its `expectations[]` — `evals.json` uses [skill-creator's schema](https://github.com/anthropics/skills/tree/main/skills/skill-creator) verbatim, so its `run_eval.py`, benchmarking, and eval viewer work against our files unmodified | On demand | Tokens |

## Running

```bash
# Tiers 1–2b, exactly what CI runs — deterministic, git + Python only
python3 agent_skills/evals/tools/skill_lint.py agent_skills/project-graveyard --strict
python3 agent_skills/evals/tools/skill_scanner.py agent_skills
python3 agent_skills/evals/tools/run_trigger_evals.py
python3 agent_skills/evals/project-graveyard/test_graveyard.py
```

Tier 3 is on demand and spends tokens: each skill's `evals.json` is in
skill-creator's schema, so run it with Anthropic's own tooling (install the
skill-creator plugin and point `run_eval.py` at the file), or by hand — fresh
agent session, paste each prompt, grade against `expectations[]`. Cases marked
`lexical: false` in `trigger-cases.json` (reasoning-triggered, e.g. necromancer
mode) are only covered here. Re-run tier 3 whenever `SKILL.md` behavior
changes; re-run tier 2 whenever a `description` changes.

## Track record

Not theater: tier 1 caught a symlink-path bug that silently disabled relapse
detection on macOS, and an external reviewer running it in a clean Linux
checkout caught a filesystem-ordering bug that mis-attributed the kill-chain.
Both fixed before merge. That's the job.

## Adding a skill

New skill → new `evals/<skill-name>/` with at minimum a deterministic
`test_<skill>.py` (self-contained, tempdir fixtures, exit 0/1) and a
`trigger-cases.json`. CI picks up `test_*.py` automatically.
