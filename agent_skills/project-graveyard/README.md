# 🪦 Project Graveyard Agent Skill

**Every developer has the folder. Twenty-something dead projects, each abandoned for reasons nobody wrote down.**

This skill reads the git history of every abandoned project on your machine and answers three questions:

**Why did each one die?** Evidence, not vibes. The last commits touch Stripe files: it died at the payments wall. Another repo's first commit lands three days after this one's last: the killer gets named.

**What's your pattern?** Your projects die at day 19. Four of six were abandoned within 48 hours of starting something new.

**Which one still has a pulse?** Somewhere in that folder is a project that's 90% done: built, documented, never shipped. This finds it, checks what got easier since it died, and writes the short list of steps between it and a URL.

A representative scan (invented projects, real classifier verdicts). Your agent turns it into the funeral: an epitaph per corpse, your patterns named, and an offer to start resurrecting the strongest pulse right now. Yours will hurt more.

<img width="1672" height="941" alt="ChatGPT Image Jul 9, 2026, 06_46_05 PM" src="https://github.com/user-attachments/assets/b80456c7-cd6f-49d8-adcf-641230d4c601" />

## What it detects

Cause of death, read from git history:

| Cause | How it knows |
|---|---|
| **shiny object** | Another repo you own had its first commit within days of this one's last. The killer is named. |
| **deploy fear** | README done, 20+ commits, real code, zero deploy config. It worked. It never shipped. |
| **payments / auth wall** | The final commits touch stripe/billing or oauth/login code. |
| **boilerplate wall** | 60%+ of all file changes were config files. It died configuring. |
| **rewrite spiral** | Multiple rewrite/migrate commits; rebuilt instead of finished. |
| **scope explosion** | 100+ files, no deploy config. It grew instead of shipping. |
| **slow fade** | Commit gaps stretched until they stopped. No wall, no killer; it drifted. |

It also separates the **finished** (deployed, pushed, documented; done, not abandoned) from the **unversioned** (no git, so no autopsy). Then it ranks the dead by **pulse**, how close each is to shipping, and the agent takes over:

- **Autopsy interview**: ambiguous deaths get a question; git evidence is marked *(forensic)*, your answers *(confirmed)*.
- **World-check**: before prescribing a dig, it checks what changed since the death: the API that now has an SDK, the model that's 20x cheaper.
- **Resurrection**: a ≤7-step plan ending at *shipped*, and an offer to start on step 1 right now.
- **Relapse watch**: resurrections are recorded (`--state` + `--mark-resurrected`); every later scan reports whether the patient is holding.
- **Necromancer mode**: ask your agent to build something new and it checks the graveyard first; you may have built 60% of it in 2024.

## Install (10 seconds)

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/project-graveyard
```

The [skills CLI](https://skills.sh) installs it into whatever agents you have (Claude Code, Codex, Cursor, Copilot, Antigravity, and others); or copy this folder into your agent's skills dir. Then: *"run the graveyard on ~/dev and ~/projects"*.

Standalone, no agent required:

```bash
python3 project-graveyard/scripts/graveyard.py ~/dev ~/projects
```

## Scope and privacy

Everything runs locally: one plain-Python file, stdlib only, zero network calls, read-only. It reads git metadata (commit dates, messages, filenames), never your code's contents. Name folders and it scans only those; given none, it checks a fixed list of usual project spots (`DEFAULT_ROOTS`, line 30 of the script), never "everything on your machine." Want to post your report? `--redact` swaps project names for `project-1..n`.

Prove it works before installing, from a clone of this repo:

```bash
python3 agent_skills/evals/project-graveyard/test_graveyard.py   # 16 checks, ~10 seconds
```

Limits: no git means no autopsy (counted, not diagnosed). "Dead" is 45+ days silent, tunable with `--days`. Tested on macOS and Linux.

## Files

```
project-graveyard/                  # ← this is all that gets copied
├── SKILL.md                        # agent instructions: report format, epitaph rules, resurrection protocol
├── README.md                       # this file
├── scripts/graveyard.py            # scanner + autopsy + pulse ranking (Python 3.8+, stdlib, offline)
└── references/causes-of-death.md   # the taxonomy: signals, confidence, resurrection strategy per cause
```

Part of [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) · Apache-2.0 · Last verified: July 2026
