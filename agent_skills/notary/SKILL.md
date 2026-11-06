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
  sources", "where does this number come from", "don't make up numbers".
license: MIT
metadata:
  author: ruijiezh67
  version: "0.2.0"
  source: https://github.com/Shubhamsaboo/awesome-llm-apps
---

# Notary

A number without a receipt is a guess wearing a lab coat. Every figure you state
must point to where it came from, and that pointer must check out.

## The rules (always)

1. **No receipt, no number.** For each result number in your reply, there is a
   receipt in `.notary/turn.json` with that exact value string. If you cannot
   write one, drop the number or say what you would need to measure it. (What
   the checker enforces by default is listed under "What needs a receipt".)
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
| `cmd` | `command` (exactly as you ran it), `quote` | the logged output of that same command in `.notary/log.jsonl`. A quote you typed yourself, or one from another command's output, will not be found. **Receipts expire**: if a file named in the command has changed since that output, run it again |
| `calc` | `expr` over receipt ids (`+ - * / **`) | recomputed; fails if any input fails or is N/A |
| `user` | `quote` | the user's messages in the transcript. Only the Stop hook (or `check --transcript`) can see it; without one the receipt shows as `??` unchecked, not `ok` |
| `na` | `why`; value `N/A` | that it is not dressed up as a number |

## Workflow

1. Gather: run the commands and read the files that hold the numbers. If
   `.notary/log.jsonl` does not exist after you run a command, the
   hooks are not installed. Then run every measuring command as
   `python <skill-dir>/scripts/notary.py run -- <command>`, so that its real
   output is logged and `cmd` receipts can be checked. Pass the files a command
   reads as arguments (`python eval.py runs/aug/preds.csv`, not a script that
   finds them itself): expiry only sees files named in the command.
2. Write `.notary/turn.json`.
3. Run `python <skill-dir>/scripts/notary.py check --message <draft.md>` (or
   without `--message` to check only the receipts). Fix every `BAD` line and every
   uncovered number. Add `--all` to also check small integers.
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

The checker and the Stop hook enforce this for numbers with a decimal point, a
percent sign, a thousands separator or an exponent, for `0`, and for integers of
100 or more. Integers from 1 to 99 ("3 seeds", "12 files") pass without a
receipt unless you run `check --all`. Write receipts for the ones that are
results anyway.
