# ⚰️ Project Graveyard

**Every developer has the folder. Twenty-something dead projects, each one abandoned for reasons nobody wrote down. You don't open it, because it has nothing nice to say.**

This skill opens it. It reads the git history of every abandoned project on your machine and answers three questions you've never had answers to:

**Why did each one die?** Not vibes — evidence. The last commits touch Stripe files: it died at the payments wall. 78% of all changes were config: it spent its life setting up webpack and never met its own idea. Another repo's first commit lands three days after this one's last: the killer gets named.

**What's your pattern?** Across the whole graveyard: your projects die at day 19. Four of six were abandoned within 48 hours of starting something new. You have never once quit from too little ambition.

**Which one still has a pulse?** Somewhere in that folder is a project that's 90% done — built, documented, and never shipped. This finds it, checks what got easier since it died, writes the handful of steps between it and a URL — and your agent starts on step one.

```
          .--------.
         /          \
        |   R.I.P.   |
        |    your    |
        |    side    |
        |  projects  |
     ___|____________|___
    ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~

GRAVEYARD REPORT — 2026-07-07
════════════════════════════════════════════════════════════
repos scanned: 23 · alive: 3 · finished: 2 · dead: 7
combined lifespan of the dead: ~9 months of your life
oldest corpse: crypto-price-alerts, silent since Nov 2024

THE DEAD                     lived   commits   cause of death
────────────────────────────────────────────────────────────
invoice-radar                 41d      63      payments wall
tab-sensei                    12d      54      deploy fear
recipe-snap                   19d      31      shiny object
markdown-zen                   6d      22      boilerplate wall
crypto-price-alerts           23d      35      shiny object
devlog-cli                    88d      47      slow fade
weekend-todo                   1d       9      single burst

PATTERNS
────────────────────────────────────────────────────────────
· median lifespan of a dead project: 19 days — week three
  is where you lose them
· 2 of 7 were killed by a newer project, and both killers
  are also dead. It's a chain.
· payments code appears in the final commits of 2 corpses.
  Stripe is your wall.

STRONGEST PULSE --------/\_/\--------
────────────────────────────────────────────────────────────
tab-sensei · 84/100
  54 commits, tests present, README done — and no deploy
  config anywhere. It worked. It just never shipped.
  to ship: needs deploy config
```

A representative scan (the projects are invented; the verdicts are exactly what the classifiers produce). Your agent turns it into the actual product — the funeral:

> ## ⚰️ Your graveyard — 7 dead, ~9 months of your life
>
> **⚰️ tab-sensei** · Apr–May 2026 · 54 commits · *deploy fear (forensic)*
> *"Fifty-four commits, tests green, README polished — and no deploy config ever came. It worked. It just never shipped."*
>
> **⚰️ recipe-snap** · Mar 2026 · 31 commits · *shiny object (confirmed — you left it for invoice-radar, which is also dead)*
> *"Survived by its killer. Briefly."*
>
> ...plus 3 one-day experiments, buried in a shared plot.
>
> **Patterns:** your projects die at day 19 — week three is where you lose them. And payments code shows up in the final commits of two corpses: the walls aren't random, they're *your* wall.
>
> **🩺 Strongest pulse: `tab-sensei` (84/100).** What got easier since May: the extension API that stalled you now has an official types package. Three steps to the store. Step 1 takes 20 minutes — **want me to start right now?**

Yours will hurt more.

## What it actually detects

Cause of death, read from the git history — not guessed:

| Cause | How it knows |
|---|---|
| **shiny object** | Another repo you own had its first commit within days of this one's last. The killer is named. |
| **deploy fear** | README done, 20+ commits, real code, zero deploy config. It worked. It never shipped. |
| **payments / auth wall** | The final commits before death touch stripe/billing or oauth/login code. |
| **boilerplate wall** | 60%+ of all file changes were config files. It died configuring, never met its problem. |
| **rewrite spiral** | Multiple rewrite/migrate commits — it kept being rebuilt instead of finished. |
| **scope explosion** | 100+ files, no deploy config. It grew instead of shipping. |
| **slow fade** | Commit gaps stretched until they stopped. No wall, no killer — it drifted. |

The census also separates what *isn't* dead: **finished** projects (deployed + pushed + documented — silent because they're done, not abandoned) and **unversioned** folders (a `package.json` but no git — died before their first commit; no history, no autopsy).

Then it ranks the dead by **pulse** — how close each one is to actually shipping — and this is where the agent takes over from the script:

- **The autopsy interview** — for ambiguous deaths, it asks you what actually happened and corrects the record: git evidence marked *(forensic)*, your answers marked *(confirmed)*.
- **The world-check** — before prescribing a dig, it searches what changed since the project died: the API that now has an SDK, the model that's 20x cheaper, or the three funded products that shipped your idea while it slept.
- **The resurrection** — a ≤7-step plan ending at *shipped*, and the agent offers to start on step 1 right now.
- **Relapse watch** — resurrections get recorded (`--state` + `--mark-resurrected`); every later scan reports whether the patient is holding or going silent again. No tool follows up on its own prescription. This one does.
- **Necromancer mode** — tell your agent to build something new and it checks the graveyard first; there's a decent chance you already built 60% of it in 2024.

## Install (10 seconds)

One command — the [skills CLI](https://skills.sh) installs it into whatever agents you have (Claude Code, Codex, Cursor, Copilot, Antigravity, OpenClaw, Hermes, and other coding agents):

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/project-graveyard
```

Or clone and copy — which also lets you run the eval first (below):

```bash
git clone --depth 1 https://github.com/Shubhamsaboo/awesome-llm-apps.git
cp -r awesome-llm-apps/agent_skills/project-graveyard ~/.claude/skills/
# other agents: ~/.openclaw/skills/, ~/.hermes/skills/, or .agents/skills/ in your project
```

Then: *"run the graveyard on ~/dev and ~/projects"*.

Or run the scanner standalone, no agent required:

```bash
python3 project-graveyard/scripts/graveyard.py ~/dev ~/projects
```

## Where it looks — exactly

No GitHub, no cloud, no special access. Your agent runs the script on your machine with your normal user permissions — the same access as any command you type yourself.

- **Tell it where your projects live and it looks only there**: `"run the graveyard on ~/dev"` scans `~/dev`, nothing else. The skill tells your agent to ask rather than guess.
- **Given no folders**, it checks a fixed list of the usual project spots — `~/dev`, `~/projects`, `~/code`, `~/src`, `~/Desktop`, `~/Documents/GitHub`, `~/Downloads` — max 4 levels deep, skipping `node_modules`/venvs/caches. That list is `DEFAULT_ROOTS`, line 30 of the script. It is never "everything on your machine."
- **What it reads**: git metadata only — commit dates, messages, author emails, filenames. Not your code's contents. Read-only; it never writes inside a scanned repo.

## Privacy — and don't take our word for it

Everything runs locally — plain Python, stdlib only, zero network calls. The report prints to your terminal and stops there. It sees your never-pushed 2am projects precisely *because* it doesn't go through the GitHub API. Want to post your report? `--redact` swaps project names for `project-1..n` and keeps the confession.

Skeptical? Good — you should be, about anything you install into an agent. The script is one readable file, and you can prove the whole thing works before pointing it at your machine:

```bash
# from the cloned repo, before you install anything:
python3 agent_skills/evals/project-graveyard/test_graveyard.py
# builds a synthetic graveyard in a temp dir, asserts all 16 behaviors, ~10 seconds
```

Known limits, stated plainly: only git repos can be *autopsied* — project folders with no git at all are counted ("died before their first commit") but there's no history to diagnose. "Dead" is a 45-day threshold you can change (`--days`), and it's tested on macOS and Linux.

## Files

You install exactly what runs — nothing else rides along:

```
project-graveyard/                  # ← this is all that gets copied
├── SKILL.md                        # agent instructions: report format, epitaph rules, resurrection protocol
├── README.md                       # this file
├── scripts/graveyard.py            # scanner + autopsy + pulse ranking (Python 3.8+, stdlib, offline)
└── references/causes-of-death.md   # the taxonomy: signals, confidence, resurrection strategy per cause
```

The test suite stays in the repo (`agent_skills/evals/project-graveyard/`) — run it before installing; don't carry it around after.

Part of [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) · Apache-2.0 · Last verified: July 2026
