# ⚖️ LLM Panel Agent Team

Several models review the same thing independently, then argue about it. One script, one
API key, three vendors.

A single reviewer has a single blind spot. Ask three models the same question in the same
chat and the second one anchors on the first. This team keeps them apart: every model
gets the identical prompt at the same moment and none of them can see the others. Then,
optionally, each one is shown the other answers with the names stripped and has to
UPHOLD, REJECT, CONCEDE or MISSED every finding that touches its own.

It is not a voting machine. The panel generates candidate defects; you still check each
one against the code. What it adds is independence in round one and, in round two, a
wrong finding that has to survive being argued with.

## How it works

```
                 ┌──────────────────┐
   same prompt ─▶│ gpt-5.4-mini     │──▶ answer 1 ─┐
                 ├──────────────────┤              │   round 2 (--rebut):
   same prompt ─▶│ claude-haiku-4.5 │──▶ answer 2 ─┼─▶ each model sees the OTHER answers
                 ├──────────────────┤              │   as "Reviewer A", "Reviewer B" ...
   same prompt ─▶│ gemini-3.8-flash │──▶ answer 3 ─┘   (shuffled per model) and takes a
                 └──────────────────┘                   position on each finding
      round 1: parallel, no model                             │
      sees another's answer                                   ▼
                                              positions regrouped BY FINDING,
                                              disagreements marked CONTESTED
```

1. **Round 1**: a thread pool sends the prompt to every model at once. Each answer prints
   in full as it lands, with its latency. A model that errors gets an `error` row, and the
   others still finish.
2. **Round 2** (`--rebut`): for each model, the other answers are shuffled and lettered
   A, B, C... The shuffle is per model, so neither the letter nor the position gives away
   which vendor wrote which review. The model is asked to start every point with one of
   four labels and a reference like `B3`, and is told two rules: do not concede just
   because someone disagreed, and do not invent agreement.
3. **Grouping**: those `LABEL: B3` lines are parsed and regrouped by the finding they
   answer, so you read "what did everyone say about finding 3" instead of three documents.
   A finding with both a REJECT and an UPHOLD is marked CONTESTED. That is where to look
   first.
4. **Scoreboard**: tokens and the cost OpenRouter billed, per model and in total.

## Requirements

- Python 3.10+
- An [OpenRouter](https://openrouter.ai/keys) API key. One key reaches every vendor, and
  the three default models are deliberately the cheap tier: the run below cost $0.03.

## Installation

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_ai_agents/multi_agent_apps/agent_teams/llm_panel_agent_team
pip install -r requirements.txt
export OPENROUTER_API_KEY=sk-or-...
```

## Usage

Review the sample diff, which has a few defects planted in it, with the rebuttal round:

```bash
python llm_panel_agent_team.py --file sample_diff.patch --rebut
```

Ask a question instead of reviewing a file, or pick your own roster:

```bash
python llm_panel_agent_team.py --question "Is optimistic locking or a queue the better fit for a booking system, and why?"
python llm_panel_agent_team.py --file my_change.diff --rebut \
    --models openai/gpt-5.4,anthropic/claude-sonnet-5,google/gemini-3.8-pro,deepseek/deepseek-v4-flash
```

Any [OpenRouter model id](https://openrouter.ai/models) works. The full panel, including
both rounds in full, is written to `panel.md` (`--out` to change that).

## Example output

A real run on `sample_diff.patch`, shortened. Round one, all three landing within ten
seconds:

```
## anthropic/claude-haiku-4.5  (ok, 2.5s)

1. **orders.py, line 17**: The mutable default argument `seen=[]` will be shared across
   all function calls ...
2. **orders.py, line 11**: The condition changed from `>=` to `>`, which changes the
   discount logic so orders exactly at a threshold no longer qualify ...
3. **orders.py, line 21**: Bare `except Exception` is too broad and will catch and
   suppress unexpected errors like `KeyboardInterrupt` or `SystemExit` ...

## openai/gpt-5.4-mini  (ok, 2.9s)

1. ... `>` instead of `>=`, so totals exactly on a tier threshold ... receive no discount.
2. ... Reversing the tiers and returning on the first match ... can skip the correct
   highest applicable tier if the list is not strictly ordered as expected.
3. ... catches all exceptions and returns `[]`, which hides real failures ...
4. ... `seen=[]` default argument is mutable and persists across calls ...
5. ... `seen` parameter is never used by callers ... making the new side effect dead code.
6. ... `recent()` now excludes cancelled orders and changes the cutoff comparison ...

## google/gemini-3.8-flash  (ok, 10.5s)

1. `orders.py`, line 13: Using `total > threshold` instead of `>=` incorrectly excludes ...
2. `orders.py`, line 18: `seen=[]` uses a mutable default argument ...
```

Round two. Note the third finding from claude-haiku: both other models reject it, and
they are right, since `KeyboardInterrupt` and `SystemExit` derive from `BaseException`
and are not caught by `except Exception`. That is the round doing its job.

```
## openai/gpt-5.4-mini rebuts  (ok, 3.7s)

UPHOLD: A2 -- `discount_for()` now uses `total > threshold` on line 13, so values exactly
equal to 100, 500, or 1000 no longer get the tier they previously qualified for.
UPHOLD: A1 -- `load_orders(path, seen=[])` on line 17 uses a mutable default list ...
REJECT: A3 -- The code catches `Exception`, which does not include `KeyboardInterrupt`
or `SystemExit`, so the claim that it suppresses those is incorrect.
...

## google/gemini-3.8-flash rebuts  (ok, 21.2s)

* REJECT: B2 -- The original implementation already assumed ascending tier order by
  iterating forward and overwriting `rate`, so traversing in reverse does not introduce
  an ordering dependency that wasn't already present.
* REJECT: B5 -- Callers can pass an explicit list to `seen` to track loaded paths, so
  appending to `seen` is not dead code; the issue is solely the mutable default argument.
...
```

The positions regrouped by the finding under dispute, and the bill:

```
| finding                       | positions                                              | contested |
|-------------------------------|--------------------------------------------------------|-----------|
| anthropic/claude-haiku-4.5 #1 | UPHOLD (gpt-5.4-mini); UPHOLD (gemini-3.8-flash)       |           |
| anthropic/claude-haiku-4.5 #2 | UPHOLD (gpt-5.4-mini); UPHOLD (gemini-3.8-flash)       |           |
| anthropic/claude-haiku-4.5 #3 | REJECT (gpt-5.4-mini); REJECT (gemini-3.8-flash)       |           |
| google/gemini-3.8-flash #1    | UPHOLD (gpt-5.4-mini); UPHOLD (claude-haiku-4.5)       |           |
| google/gemini-3.8-flash #2    | UPHOLD (gpt-5.4-mini); UPHOLD (claude-haiku-4.5)       |           |
| openai/gpt-5.4-mini #1        | UPHOLD (claude-haiku-4.5); UPHOLD (gemini-3.8-flash)   |           |
| openai/gpt-5.4-mini #2        | REJECT (claude-haiku-4.5); REJECT (gemini-3.8-flash)   |           |
| openai/gpt-5.4-mini #3        | UPHOLD (claude-haiku-4.5); REJECT (gemini-3.8-flash)   | CONTESTED |
| openai/gpt-5.4-mini #4        | UPHOLD (claude-haiku-4.5); UPHOLD (gemini-3.8-flash)   |           |
| openai/gpt-5.4-mini #5        | UPHOLD (claude-haiku-4.5); REJECT (gemini-3.8-flash)   | CONTESTED |
| openai/gpt-5.4-mini #6        | UPHOLD (claude-haiku-4.5); REJECT (gemini-3.8-flash)   | CONTESTED |

| model                      | status | time  | tokens in/out | cost    |
|----------------------------|--------|-------|---------------|---------|
| openai/gpt-5.4-mini        | ok     | 2.9s  | 1,599/466     | $0.0033 |
| anthropic/claude-haiku-4.5 | ok     | 2.5s  | 1,881/684     | $0.0053 |
| google/gemini-3.8-flash    | ok     | 10.5s | 1,813/5,245   | $0.0210 |
| total                      |        |       |               | $0.0296 |
```

Reading it: the two planted bugs (`>` for `>=` on the tier threshold, the mutable default
`seen=[]`) were found by all three and upheld by all. One false finding was rejected by
both peers. Three findings are contested, and those are the ones a human should look at:
one of them (the broad `except` that hides malformed data) is a real problem that
gemini-3.8-flash talked itself out of. The panel points at where to look; it does not
decide for you.

## Things worth knowing

- **Anonymity is best effort.** A model that writes in a recognisable style, or names
  itself in its review, is identifiable to the others no matter what letter it gets.
- **Round two is the expensive one.** Each rebuttal prompt carries the material again,
  plus the model's own review and the others' reviews, so it is several times the size of
  the round-one prompt. Costs scale with that.
- **Grouping only sees positions that cite a reference.** A position that restates a
  finding in its own words without `B3` is still printed but cannot be matched, so it
  argues with nobody. The instructions say this to the model; some ignore it.
- **One key, many vendors.** OpenRouter is used so the roster can mix vendors without a
  key per vendor. Any OpenAI-compatible endpoint works if you change `base_url`, but then
  the `cost` column depends on that endpoint reporting it.

## The full tool

This folder is the idea in one file. The same design, grown up, is
[llm-panel](https://github.com/musharna/llm-panel) (`pip install llm-panel`), which
drives the coding-agent CLIs you already have (Codex, Claude Code, opencode, ollama) so
the judges can read your whole repository rather than a pasted diff, renders the rebuttal
round as one HTML page grouped by finding, runs as a GitHub Action on every pull request,
and ships a recall benchmark that measures what a panel misses on real PRs. Disclosure:
the author of this tutorial is the author of llm-panel.
