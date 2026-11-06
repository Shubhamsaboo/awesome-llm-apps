# 🧾 notary

**No receipt, no number.** Every figure your agent reports must point to where it came from (the file and exact quote, the command output it actually saw, or the arithmetic), and `scripts/notary.py` checks each receipt against the real files and logs. Unmeasured values are `N/A`, never `0`.

## Install

```bash
npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/agent_skills/notary
```

## The failure it is for: numbers that drift between turns

Current models write a careful one-shot results summary. They fail **across turns**. An agent evaluates a run, the run is re-done, and later it writes the summary from the number it remembers. That number came from a real command in the same session, so it reads exactly like a correct one.

| Condition (notary 0.2.0, Claude Code 2.1.318, Opus 5.5, 6 runs each) | Reported the stale number | median cost per run |
|---|---|---|
| no skill | 6/6 | 0.25 USD |
| one-line instruction: "every number must come from a file you read or a command you ran in this session" | 6/6 | 0.27 USD |
| notary skill alone | 5/6 (5 replies show no sign of the skill; the 1 that cites receipts was right) | 0.23 USD |
| notary skill + Claude Code hooks | **0/6** | 0.92 USD |

**Install the hooks.** As a skill alone, the model rarely decides to use notary for a follow-up summary. The Stop hook makes the check happen anyway, at about 3.7 times the cost of an unchecked run.

The fix is that **receipts expire**. A `cmd` receipt fails when a file named in its command has changed since the output was logged. On single-turn summaries the bare model already avoided every planted trap, so there notary only adds cost (2 to 3 times the tokens).

Scoring is deterministic: regexes over the reply against an answer key, no model judge. Every run is isolated from the operator's own CLAUDE.md, skills and plugins. The fixture, prompts and scoring are in [`evals/notary/drift/`](../evals/notary/drift/). To re-run it (it calls the model, about 0.2 to 1 USD per run at list price):

```bash
python agent_skills/evals/notary/drift/run_drift.py --repeats 6 --jobs 2
```

## How it checks

| kind | points to | checked against |
|---|---|---|
| `file` | path + exact quote | the file as it is now |
| `cmd` | the exact command + an output quote | the logged output of that same command, from `notary.py run -- <command>` or the Claude Code hook. Expires if a file **named in the command** changed, so pass input files as arguments: a script that opens `preds.csv` internally never expires |
| `calc` | arithmetic over other receipt ids | recomputed |
| `user` | the user's words | the transcript. `check` without `--transcript` shows these as `??` unchecked; the Stop hook, which has the transcript, verifies them |
| `na` | why it was not measured | value must be `N/A` |

By default the checker requires receipts for numbers with a decimal point, a percent sign, a thousands separator or an exponent, for `0`, and for integers of 100 or more. Integers from 1 to 99 pass unless you run `check --all`.

## Optional: Claude Code hooks

The hooked row uses two hooks: PostToolUse logs real tool output, and Stop sends back a reply with an unbacked number once. Add to `.claude/settings.json`, with the path pointing at wherever your agent installed the skill:

```json
{"hooks": {
  "PostToolUse": [{"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": "python3 ~/.claude/skills/notary/scripts/notary.py hook-log"}]}],
  "Stop": [{"hooks": [{"type": "command", "command": "python3 ~/.claude/skills/notary/scripts/notary.py hook-stop"}]}]
}}
```

What installing them means:
- **The Stop hook checks every reply** in every project where these settings apply (all projects if you put them in `~/.claude/settings.json`). Any reply with a checked number and no passing receipt is sent back once, whatever the task.
- Both hooks fail open and never loop. Turn them off with `NOTARY=off`, or for one project with an empty `.notary/off` file.

## Privacy

Local only, no network. The PostToolUse hook writes the **full output of every Bash/PowerShell call** (up to 200,000 characters each) to `.notary/log.jsonl` in your project, capped at 20 MB and rotated. That can include secrets a command printed. Add `.notary/` to your `.gitignore`.
