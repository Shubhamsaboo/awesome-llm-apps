---
name: project-graveyard
description: >-
  Scans the developer's machine for dead side projects, autopsies each one from
  its git history (died at the payments wall, killed by a newer project,
  finished but never shipped), surfaces their personal death patterns, and picks
  the corpse most worth resurrecting — then helps ship it. Use when the user
  mentions abandoned, unfinished, or old side projects, asks "what should I
  finish", wants to revive or resurrect a project, says "run the graveyard",
  wonders why they never finish anything, or is about to start a new project
  that sounds like one they already built. Runs entirely locally.
license: Apache-2.0
metadata:
  author: "Shubham Saboo"
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
---

# Project Graveyard

Every developer has a folder full of dead projects. Nobody has ever gotten an
autopsy report. This skill scans the machine for abandoned repos, works out why
each one died from its git history, finds the user's personal death patterns,
and picks the one corpse worth digging up — then helps ship it.

Everything runs locally. No API, no network, nothing leaves the machine.

## When to use

- The user asks about abandoned/unfinished/old side projects, or what to finish
- The user wants to revive, resurrect, or "finally ship" something
- The user asks why they never finish projects
- The user proposes a new project — check the graveyard first (see Necromancer
  mode). There's a decent chance they already built half of it.

## When not to use

- Cleaning up disk space or node_modules — that's `kondo`/`npkill`, not this
- Archiving repos on GitHub — this works on local clones and never-pushed work
- Analyzing one specific repo's history in depth — just read the git log

## Run it

```bash
python3 scripts/graveyard.py ~/dev ~/projects
```

Point it at wherever projects actually live. If you don't know where that
is, ask — one question beats sweeping someone's home directory uninvited.
No args scans the usual suspects (~/dev, ~/projects, ~/code, ~/Desktop, ...).
Useful flags:

- `--days 90` — how long silent before a repo counts as dead (default 45)
- `--json report.json` — full machine-readable data
- `--me work@email.com` — claim commits made under other emails (repeatable);
  without it, projects committed via a work identity or a builder tool get
  skipped as "not yours"
- `--include-foreign` — also include repos the user barely committed to
  (skipped by default: clones, forks, work checkouts are not their corpses)
- `--state FILE` — remember scans and resurrections; enables relapse watch

The script is read-only. It never writes inside a scanned repo.

## Reading the report

The script gives you four blocks: census, the dead (with cause of death),
patterns, and the top 3 by "pulse" (resurrectability score). Causes are
evidence-based guesses, not verdicts — each comes with the evidence line that
justifies it. If a cause looks wrong, check the evidence before repeating it.
The cause taxonomy and what each one means for resurrection is in
`references/causes-of-death.md` — read it before writing the report.

## The autopsy interview

The script can only read git. You can ask. For corpses whose primary cause is
`unknown` or `slow_fade` — the low-confidence verdicts — ask the user one
question each, two or three total at most:

> "`recipe-scraper` — the history just shows it drifting. Do you remember
> what actually stopped you?"

Blend the answers in, and label verdicts honestly in the report:
**(forensic)** for what git showed, **(confirmed)** for what the user told
you. Testimony beats a forensic guess — update the tombstone, not just the
prose. Two questions is a conversation; five is a deposition.

## Writing the tombstone report

Turn the script output into a report the user will actually feel. Format:

1. **The census.** Deaths, combined lifespan, oldest corpse. Plain numbers —
   they land on their own.
2. **Tombstones.** One per dead project, worst-to-best pulse. Name, lifespan,
   commit count, cause of death with its evidence, and a one-line epitaph.
   Above ~10 corpses, give full tombstones only to the 6-8 most interesting
   (highest pulse, most distinctive deaths) and bury the rest together in one
   line — "...plus 11 one-day experiments, buried in a shared plot." A wall
   of 23 tombstones kills the funeral.
3. **The patterns.** This is the part they'll remember. "Your projects die at
   day 19." "Four of six were killed by a newer project." Quote the script's
   numbers; add anything you can see that it can't.
4. **The resurrection.** One project. Not three. See below.

Carve the resurrection pick (and only it) as an ASCII tombstone card —
stone is earned, not sprayed; every other corpse stays a line in the table:

```
        .------------------------.
       /                          \
      |        tab-sensei          |
      |      Apr — May 2026        |
      |   54 commits · 12 days     |
      |                            |
      |   died of deploy fear      |
      |                            |
      |   "It worked. It just      |
      |     never shipped."        |
   ___|____________________________|___
      ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~
```

Center the text, keep the card under 44 columns so it never wraps, epitaph
last. If the graveyard is empty, no card — don't carve a stone for nobody.

Epitaph rules — this is where the whole thing lives or dies:

- Every epitaph must be traceable to evidence from the scan. "Died as it
  lived: configuring webpack" works because the config ratio was 78%. Made-up
  jokes about code you haven't seen don't work and the user will know.
- Punch at the pattern, not the person. "It worked. It just never shipped" is
  fine. "You were too scared to ship" is not.
- Dry beats wacky. One sentence. No puns unless they're earned.
- If a project deserves respect, give it. A 26-commit repo with a finished
  README that never shipped is a small tragedy, not a punchline.

Offer `--redact` framing if the user wants to share the report: project names
swapped for `project-1..n`, causes and patterns intact.

## The resurrection

Pick ONE corpse. Highest pulse wins unless its idea is dead in the world too.
Before deciding, read the top candidate's README and skim the code — then do
the **world-check**, the part only you can do because the script can't see
the present:

- Search whether what blocked it got easier since it died: the API it fought
  may have an official SDK now, the model that was too expensive may be 20x
  cheaper, the thing it hand-rolled may be a library today.
- Search whether the world shipped the idea. If three funded products do
  exactly this now, say so — that changes the plan from "ship it" to "ship it
  for yourself," or to "let it rest."

Cite what you find in the plan. "This got easier: X exists now" is the
strongest argument for digging; "the window closed" is the strongest for
leaving it buried.

Then write the resurrection plan. The per-cause dig strategy is in
`references/causes-of-death.md` (each cause has a "resurrection angle" —
deploy-fear corpses need shipping steps only, wall deaths need the managed
alternative, scope explosions get one feature extracted). Plan rules:

- At most 7 concrete steps, ending at *shipped* (a URL, a release, a
  published package — not "keep working on it")
- Step 0 is always: confirm it still runs. Deps rot; prove the install and
  the entry point before promising anything.
- Step 1 must be completable today — the first session has to end with
  visible progress
- Ask before touching the repo. Then offer to start on step 1 right now —
  that offer is the entire point of running this inside an agent.

**When to leave it buried** — say it plainly when it's true: the user doesn't
care anymore (a shrug at the interview is closure, not a project); the
window closed and the world shipped the idea; or every candidate is weak.
"Nothing here is worth digging up, and that's fine — here's what the patterns
say about the *next* project" is a legitimate and useful ending.

When the user commits to a resurrection, record it (ask once where to keep
the state file — `~/.project-graveyard.json` is a sane default):

```bash
python3 scripts/graveyard.py --state ~/.project-graveyard.json \
    --mark-resurrected /path/to/the/corpse
```

## Relapse watch

Scans run with `--state` hold past resurrections to their promise: the report
gains a RELAPSE WATCH block showing whether each resurrected project is
holding or going silent again. When one relapses, say it plainly and make the
user choose — recommit or bury it honestly. A second silent death is an
answer, not a failure; close the loop instead of prescribing a third attempt.
No tool follows up on its own prescription. This one does — that's the point
of keeping state.

## Necromancer mode

When the user proposes building something new, check the graveyard for prior
attempts before scaffolding anything — grep the state file (or a fresh
`--json` report) for name and README overlap. If there's a match:

> "You already built about 60% of this. It's called `project-14`, it died in
> March at the auth step, and its parser still works. Resurrect instead?"

Don't be preachy about it. Mention it once, let them choose, drop it.

## Gotchas

- **~/Desktop might itself be a git repo** (accidental `git init`, backup
  tools). The scanner handles nested repos, but if the census looks absurd,
  that's usually why.
- **Ownership filter uses git email.** If the user commits under multiple
  emails (work address, GitHub web edits, builder tools), real corpses get
  skipped as "not yours" — the census names what it skipped; claim yours with
  `--me that@email.com`.
- **"Dead" is a threshold, not a truth.** A stable finished tool looks dead at
  45 days. The script separates `finished` (deploy config + pushed + README)
  from dead, but the heuristic is rough — ask before eulogizing anything the
  user considers done.
- **One-day corpses are usually vibe-coded bursts**, not failures — a project
  built in one sitting and never reopened. The pattern worth surfacing is how
  many of them there are, not that each one "died."
- **Don't resurrect by default.** The report is the product; the resurrection
  is an offer. Some corpses should stay buried — see "When to leave it buried"
  above.

## Files

- `scripts/graveyard.py` — scanner + autopsy + pulse ranking (stdlib, offline, read-only)
- `references/causes-of-death.md` — the taxonomy: signals, confidence, and the per-cause resurrection strategy
