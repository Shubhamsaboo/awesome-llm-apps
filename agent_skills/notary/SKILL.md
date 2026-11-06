---
name: notary
description: >
  Makes every number in a report traceable. Before stating results, metrics,
  counts, timings or any other figure, the agent writes a receipt for each one
  (the file and exact quote, the logged command output, the calculation, or the
  user's words) and a checker verifies them against the real files and tool
  output. Unmeasured values are written N/A, never 0. Use when reporting
  experiment results, benchmarks, metrics, data analysis, test counts, costs or
  any summary full of numbers, and when the user says "notary", "receipts", "show your
  sources", "where does this number come from", "don't make up numbers",
  "数字要有出处", "别编数字", "没测的写N/A".
license: MIT
metadata:
  author: ruijiezh67
  version: "0.1.0"
  source: https://github.com/Shubhamsaboo/awesome-llm-apps
---

# Notary

A number without a receipt is a guess wearing a lab coat. Every figure you state
must point to where it came from, and that pointer must check out.

## The rules (always)

1. **No receipt, no number.** For each number in your reply, there is a receipt
   in `.notary/turn.json` with that exact value string. If you cannot write one,
   drop the number or say what you would need to measure it.
2. **Never write 0 for something not measured.** A run that crashed, a metric
   that was not logged, a test that was not run: the value is `N/A`, with an `na`
   receipt saying why. `0` means "measured, and it was zero".
3. **Quote, don't paraphrase.** `quote` is copied character for character from
   the file or the command output, and it contains the source number.
4. **Read before you cite.** Run the command or open the file in this session.
   A number remembered from earlier in the conversation, from a README table or
   from a config default is not a measurement of the current state. Re-read it.
5. **Rounding is honest rounding.** 0.8472 may become 84.7% or 0.85, never 85.2%.
   Anything else (a difference, a ratio, seconds to minutes) is a `calc` receipt.

## Receipt format

Write `.notary/turn.json` (overwrite it for each report):

```json
{"receipts": [
  {"id": "r1", "value": "84.7%", "claim": "aug val accuracy", "kind": "file",
   "path": "runs/aug/metrics.json", "quote": "\"val_acc\": 0.8472"},
  {"id": "r2", "value": "0.829", "claim": "aug test accuracy", "kind": "cmd",
   "command": "python eval_test.py runs/aug/preds.csv", "quote": "accuracy 0.8290"},
  {"id": "r3", "value": "0.806", "claim": "baseline test accuracy", "kind": "cmd",
   "command": "python eval_test.py runs/baseline/preds.csv", "quote": "accuracy 0.8060"},
  {"id": "r4", "value": "2.3", "claim": "gain in points", "kind": "calc", "expr": "(r2 - r3) * 100"},
  {"id": "r5", "value": "N/A", "claim": "aug-lr test accuracy", "kind": "na",
   "why": "crashed at epoch 7 (CUDA OOM, runs/aug-lr/train.log); no predictions"},
  {"id": "r6", "value": "8", "claim": "workers", "kind": "user", "quote": "use 8 workers"}
]}
```

| kind | needs | checked against |
|---|---|---|
| `file` | `path` (relative to project), `quote` | the file as it is now |
| `cmd` | `command`, `quote` | real tool output logged by the hook in `.notary/log.jsonl`. A quote you typed yourself will not be found. **Receipts expire**: if a file the command read has changed since that output, run it again |
| `calc` | `expr` over receipt ids (`+ - * / **`) | recomputed; fails if any input fails or is N/A |
| `user` | `quote` | the user's messages in the transcript |
| `na` | `why`; value `N/A` | that it is not dressed up as a number |

## Workflow

1. Gather: run the commands and read the files that hold the numbers. If
   `.notary/log.jsonl` does not exist after you run a command, the
   hooks are not installed. Then run every measuring command as
   `python <skill-dir>/scripts/notary.py run -- <command>`, so that its real
   output is logged and `cmd` receipts can be checked.
2. Write `.notary/turn.json`.
3. Run `python <skill-dir>/scripts/notary.py check --message <draft.md>` (or
   without `--message` to check only the receipts). Fix every `BAD` line and every
   uncovered number.
4. Reply. Keep the prose clean: no inline citations needed. End with one line,
   `🧾 N/N receipts check out (.notary/turn.json)`, so the reader knows where
   to look.

With the Claude Code hooks installed (see README.md), a Stop hook runs the same check on your final reply
and sends it back once if a number has no receipt or a receipt fails. Treat that
as a bug report: fix the receipt or fix the number. Never edit a source file to
make a receipt pass.

## What needs a receipt

Results, metrics, counts, sizes, durations, costs, percentages, deltas. Not:
numbers inside code blocks or inline code, dates, versions, `file:line`
references, list numbering, step numbers.
