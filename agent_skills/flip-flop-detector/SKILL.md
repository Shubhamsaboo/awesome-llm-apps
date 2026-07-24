---
name: flip-flop-detector
description: >-
  Detects code regions that keep getting rewritten back and forth instead of
  settling — the same lines oscillating between two or more prior states
  across many commits. Surfaces indecision hotspots: unresolved
  disagreements, unclear requirements, or repeated reverts hiding in a
  repo's commit log. Use when the user asks why a file keeps changing,
  whether a design was ever settled, wants to find the most argued-over
  code in a repo, or says something like "keeps getting reverted" or "we
  can never agree on this." Runs entirely locally against git log output,
  no network calls.
license: Apache-2.0
metadata:
  author: "Shubham Jiyani"
  version: "1.0.0"
  source: "https://github.com/Shubhamsaboo/awesome-llm-apps"
---

# Flip-Flop Detector

Every codebase has at least one block of code that keeps getting rewritten:
fixed one way, reverted, fixed a different way, reverted again. `git blame`
only shows the *last* rewrite. This skill walks the full commit history of a
file, finds the exact regions that oscillate between prior states, and turns
that oscillation into a ranked list of indecision hotspots — the places a
team never actually agreed on.

Everything runs locally. The script makes no network calls and never
modifies the working tree, index, commits, or branches — it only reads
history with `git log` and `git show`.

## When to use

- Before a refactor, to find code that has never actually stabilized
- When the user asks why a file or function keeps changing
- When onboarding to a legacy codebase and wanting to know what's contentious
- To find evidence of unresolved design disagreement before writing a design doc
- When a bug keeps "coming back" and the fix history looks suspicious

## When not to use

- Reviewing a single diff or pull request for scope creep
- Explaining why one specific line currently exists from its origin commit
- Finding dead code, unused exports, or straightforward static-analysis smells
- Making any changes automatically — this skill only reports, it never edits

## Run the detector

Run from this skill directory and point `--repo` at the target repository.

Default: scan the whole repo, auto-discovering the most-changed source files:

```bash
python3 scripts/flip_flop.py --repo /path/to/repo --top 10
```

Scope to specific files or directories (much faster on large repos, and
exhaustive rather than frequency-filtered):

```bash
python3 scripts/flip_flop.py --repo /path/to/repo --paths src/parser.py src/api/
```

Limit to recent history and require more oscillation before reporting:

```bash
python3 scripts/flip_flop.py --repo /path/to/repo --since "2 years ago" --min-flips 2
```

Machine-readable output for further processing:

```bash
python3 scripts/flip_flop.py --repo /path/to/repo --json
```

## Interpret the output

Read [references/anchor-heuristics.md](references/anchor-heuristics.md)
before trusting a result — the detector uses a deterministic but
approximate anchor heuristic, and the reference explains exactly what it can
and cannot see.

- `flip_count`: how many times the block returned to a state it had held at
  least two changes earlier (a genuine oscillation, not just any edit)
- `change_count`: total number of times that block changed at all
- `authors`: everyone who touched that exact spot — more distinct authors is
  weaker evidence of one person second-guessing themselves and stronger
  evidence of real, unresolved disagreement
- `sample_states`: up to two of the alternating text states, for a quick look

A high flip count with multiple authors across a long time span is the
strongest signal of genuine unresolved disagreement. A high flip count from
a single author over a few days is more often one person iterating quickly
— still worth a look, but a different story. State plainly which case a
hotspot looks like, using the evidence above, not intuition.

## Write the report

1. Rank hotspots by flip count, then name the file and the anchor's context
2. Name every commit and author involved, not just the most recent one
3. Show the alternating states side by side so the disagreement is visible
4. Recommend a next step: a short design note, a decision record, or a
   direct conversation with the authors involved — never edit the code
5. Say plainly whether a hotspot looks like one author iterating alone or
   several authors disagreeing, and say when the evidence is ambiguous

## Files

- `scripts/flip_flop.py`: deterministic git-history walker and oscillation detector
- `references/anchor-heuristics.md`: anchor algorithm, thresholds, and known limitations
