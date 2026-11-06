# 🧾 notary

**No receipt, no number.** Every figure your agent reports must point to where it came from (the file and exact quote, the command output it actually saw, or the arithmetic), and `scripts/notary.py` checks each receipt against the real files and logs. Unmeasured values are `N/A`, never `0`.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/notary
```

## The failure it is for: numbers that drift between turns

Current models write a careful one-shot results summary. They fail **across turns**. An agent evaluates a run, the run is re-done, and later it writes the summary from the number it remembers. That number came from a real command in the same session, so it reads exactly like a correct one.

| Condition (Claude Code 2.1.310, Opus 5.5, 6 runs each) | Reported the stale number |
|---|---|
| no skill | 6/6 |
| one-line instruction: "every number must come from a file you read or a command you ran in this session" | 6/6 |
| notary skill | 1/6 (the miss never invoked the skill) |
| notary skill + Claude Code hooks | **0/6** |

The fix is that **receipts expire**. A `cmd` receipt fails when a file its command read has changed since the output was logged. On single-turn summaries the bare model already avoided every planted trap, so there notary only adds cost (2 to 3 times the tokens). Scoring was deterministic (regexes over the reply against an answer key, no model judge), and every arm ran isolated from the operator's own CLAUDE.md, skills and plugins.

## How it checks

| kind | points to | checked against |
|---|---|---|
| `file` | path + exact quote | the file as it is now |
| `cmd` | command + exact output quote | real output logged by `notary.py run -- <command>` (or the Claude Code hook); expires if its input files changed |
| `calc` | arithmetic over other receipt ids | recomputed |
| `user` | the user's words | the transcript |
| `na` | why it was not measured | value must be `N/A` |

## Optional: Claude Code hooks

The 0/6 row uses two hooks: PostToolUse logs real tool output, and Stop sends back a reply with an unbacked number once. Add to `.claude/settings.json`, with the path pointing at wherever your agent installed the skill:

```json
{"hooks": {
  "PostToolUse": [{"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": "python3 ~/.claude/skills/notary/scripts/notary.py hook-log"}]}],
  "Stop": [{"hooks": [{"type": "command", "command": "python3 ~/.claude/skills/notary/scripts/notary.py hook-stop"}]}]
}}
```

Both fail open and never loop. Turn them off with `NOTARY=off`.

## Privacy

Local only, no network. The hook writes tool output to `.notary/log.jsonl` in your project (capped at 20 MB, rotated).
