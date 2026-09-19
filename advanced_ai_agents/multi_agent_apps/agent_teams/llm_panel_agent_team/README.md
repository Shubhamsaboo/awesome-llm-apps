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
                 ┌───────────────────────┐
   same prompt ─▶│ ~openai/gpt-mini-...  │──▶ answer 1 ─┐
                 ├───────────────────────┤              │  round 2 (--rebut):
   same prompt ─▶│ ~anthropic/claude-... │──▶ answer 2 ─┼▶ each model sees the OTHER
                 ├───────────────────────┤              │  answers as "Reviewer A",
   same prompt ─▶│ ~google/gemini-...    │──▶ answer 3 ─┘  "Reviewer B" ... (shuffled
                 └───────────────────────┘                 per model) and takes a
                                                           position on each finding
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
    --models openai/gpt-5.4,anthropic/claude-sonnet-5,google/gemini-3.8-flash,deepseek/deepseek-v4-flash
```

Any [OpenRouter model id](https://openrouter.ai/models) works. The full panel, including
both rounds in full, is written to `panel.md` (`--out` to change that).

**On the default roster.** The defaults are OpenRouter's rolling aliases —
`~openai/gpt-mini-latest`, `~anthropic/claude-haiku-latest`, `~google/gemini-flash-latest`
— each of which always redirects to the current model in that vendor's family. A pinned
id like `openai/gpt-5.4-mini` is whichever version was current the day it was written, and
providers retire versions, so a pinned default would eventually greet a new reader with a
"not a valid model ID" error before they ever saw the panel work. Pin ids yourself, as in
the command above, when you want a run to be reproducible rather than current — and if any
id ever stops resolving, the run reports it per model and points you at the catalogue:

```
## openai/gpt-5.4-mini-retired-example  (error, 0.5s)

BadRequestError: Error code: 400 - {'error': {'message': 'openai/gpt-5.4-mini-retired-example
is not a valid model ID', 'code': 400}, ...}
  -> `openai/gpt-5.4-mini-retired-example` is not a model id OpenRouter serves. Pick a
     current one from https://openrouter.ai/models.
```

## Example output

A real run on `sample_diff.patch`, shortened. Round one, all three landing within eight
seconds:

```
## ~openai/gpt-mini-latest  (ok, 3.0s)

1. `orders.py:12-16` -- `discount_for()` now uses `total > threshold` instead of `>=`, so
   orders exactly at a discount threshold (e.g. 100, 500, 1000) no longer receive ...
2. `orders.py:12-16` -- Reversing `DISCOUNT_TIERS` and returning on the first match ...
3. `orders.py:19-27` -- `load_orders()` catches all exceptions and silently returns `[]` ...
4. `orders.py:19-27` -- The default argument `seen=[]` is a mutable shared list ...
5. `orders.py:28-31` -- `recent()` now excludes orders with `ts == cutoff` ...

## ~anthropic/claude-haiku-latest  (ok, 2.5s)

1. **orders.py, line 17**: The `seen=[]` default argument uses a mutable list that will be
   shared across all function calls ...
2. **orders.py, line 11**: The condition changed from `total >= threshold` to
   `total > threshold` ... may break existing behavior at exact threshold boundaries.
3. **orders.py, line 21**: Bare `except Exception` silently catches all exceptions ...

## ~google/gemini-flash-latest  (ok, 7.3s)

1. `orders.py`, line 13: The comparison `total > threshold` excludes totals that equal the
   threshold, whereas tier thresholds should be inclusive (`>=`).
2. `orders.py`, line 18: Using a mutable default argument (`seen=[]`) ...
```

Round two. The models disagree about the broad `except`, and about whether the `>` on the
`recent()` cutoff matters at all:

```
## ~anthropic/claude-haiku-latest rebuts  (ok)

UPHOLD: A1 -- The change from `>=` to `>` at line 11 is a logic error. An order totaling
exactly 100 should qualify for the 0.05 discount tier, but `total > threshold` excludes it.
REJECT: B2 -- This is overstated. The code uses `reversed(tiers)` to iterate from highest
to lowest threshold, which is a valid approach *if* the input `tiers` are sorted ascending
(as `DISCOUNT_TIERS` is) ... This is sound logic, not a defect.
...

## ~google/gemini-flash-latest rebuts  (ok)

* **REJECT: A3** -- The catch block is not silent since it logs via `log.warning()`, and
  catching `Exception` to return a fallback empty list is a design strategy rather than a
  functional defect.
* **REJECT: B5** -- `cutoff` is computed from `datetime.now().timestamp()`, a microsecond-
  precision float, making exact equality essentially impossible in real data and the
  difference between `>` and `>=` inconsequential.
...
```

The positions regrouped by the finding under dispute, and the bill:

```
| finding                          | positions                            | contested |
|----------------------------------|--------------------------------------|-----------|
| ~anthropic/claude-haiku-latest #1 | MISSED (gpt-mini); UPHOLD (gemini)  |           |
| ~anthropic/claude-haiku-latest #2 | UPHOLD (gpt-mini); UPHOLD (gemini)  |           |
| ~anthropic/claude-haiku-latest #3 | MISSED (gpt-mini); REJECT (gemini)  | CONTESTED |
| ~google/gemini-flash-latest #1    | UPHOLD (claude-haiku)               |           |
| ~google/gemini-flash-latest #2    | UPHOLD (claude-haiku)               |           |
| ~openai/gpt-mini-latest #1        | UPHOLD (claude-haiku); UPHOLD (gemini) |        |
| ~openai/gpt-mini-latest #2        | REJECT (claude-haiku); REJECT (gemini) |        |
| ~openai/gpt-mini-latest #3        | UPHOLD (claude-haiku); REJECT (gemini) | CONTESTED |
| ~openai/gpt-mini-latest #4        | UPHOLD (claude-haiku); UPHOLD (gemini) |        |
| ~openai/gpt-mini-latest #5        | UPHOLD (claude-haiku); REJECT (gemini) | CONTESTED |

| model                         | status | time | tokens in/out | cost    |
|-------------------------------|--------|------|---------------|---------|
| ~openai/gpt-mini-latest       | ok     | 3.0s | 1,573/374     | $0.0029 |
| ~anthropic/claude-haiku-latest| ok     | 2.5s | 1,848/519     | $0.0044 |
| ~google/gemini-flash-latest   | ok     | 7.3s | 1,786/4,989   | $0.0200 |
| total                         |        |      |               | $0.0274 |
```

(The `positions` column is abbreviated here to fit the page; the script prints the full
model id.)

Reading it: the two planted bugs (`>` for `>=` on the tier threshold, the mutable default
`seen=[]`) were found by all three and upheld by all. Three findings are contested, and
those are the ones a human should look at. One of them is the broad `except` that hides
malformed data: claude-haiku called it a defect, gpt-mini had missed it and agreed once
shown, and gemini rejected it twice on the grounds that `log.warning()` makes it not
silent. Whether that is a defect depends on what the caller does with an empty list, which
is exactly the kind of question a panel surfaces and does not settle. The panel points at
where to look; it does not decide for you.

## Things worth knowing

- **Anonymity is best effort.** A model that writes in a recognisable style, or names
  itself in its review, is identifiable to the others no matter what letter it gets.
- **Round two is the expensive one.** Each rebuttal prompt carries the material again,
  plus the model's own review and the others' reviews, so it is several times the size of
  the round-one prompt. Costs scale with that.
- **Grouping only sees positions that cite a reference.** A position that restates a
  finding in its own words without `B3` is still printed but cannot be matched, so it
  argues with nobody. The instructions say this to the model; some ignore it. When a
  rebuttal arrives but yields no readable position at all, the grouping says so by name
  rather than leaving the model quietly out of the table.
- **One key, many vendors.** OpenRouter is used so the roster can mix vendors without a
  key per vendor. Any OpenAI-compatible endpoint works if you change `base_url`, but then
  the `cost` column depends on that endpoint reporting it.
