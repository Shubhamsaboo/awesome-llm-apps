# Autonomous Task Executor with Adversarial Verification

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-green)](https://openai.com)

An LLM agent that **breaks any plain-English task into steps, executes them, then
adversarially verifies its own output** — accepting only results that survive
independent scrutiny. All tasks, plans, steps, and tool calls are logged to a
local SQLite database so you can audit every decision.

---

## Features

- **Structured plan with typed steps** — each step carries a falsifiable success criterion
- **Pre-execution review gate** — catches unsafe or infeasible plans before spending tokens
- **Sandboxed tool set** — agents can only read files, write files, and HTTP GET; no shell execution
- **Adversarial cold verifier** — independent pass that cannot be fooled by executor self-reporting
- **Confidence threshold** — configurable floor (default 0.75) below which results are auto-rejected
- **Full audit trail** — every task, step, and tool call logged to `~/.task_executor/tasks.db`
- **Streamlit web UI** — visual pipeline progress, per-step results, verdict display, and task history
- **CLI mode** — run from the terminal via `task_executor.py` with color-coded output via `rich`

---

## How the Adversarial Verification Pattern Works

Most LLM agents just run steps and return whatever the last call produced.
This one adds a fourth stage where a **separate LLM prompt acts as a skeptical
reviewer** — it reads the evidence cold, with no memory of executing the steps,
and judges whether the success criteria were actually met.

```
User task
    │
    ▼
1. Plan Generation
   └─ LLM decomposes task into ≤12 typed steps with falsifiable success criteria
    │
    ▼
2. Plan Review Gate
   └─ Separate LLM prompt checks safety (no file deletion, no shell execution),
      feasibility, and clarity — can revise or reject before a single token is spent
    │
    ▼
3. Step Execution (loop)
   └─ Each step gets its own tool-use loop (read_file / write_file / fetch_url)
      Results accumulate as rolling context for subsequent steps
    │
    ▼
4. Adversarial Verification
   └─ Cold verifier asks: "Was the success criterion actually met, or just claimed?"
      Returns per-step verdicts + overall confidence score (0.0–1.0)
    │
    ▼
ACCEPTED (confidence ≥ 0.75)  —or—  REJECTED (confidence < 0.75 or verifier says no)
```

**Why this matters:** LLMs are fluent liars. An executor can confidently report
"done" after a tool call returns an error. The adversarial verifier has no stake
in the outcome — its only job is to find gaps between what was claimed and what
the evidence shows.

### Accept / Reject Decision Logic

The verifier produces a JSON response containing:
- `confidence` — float 0.0–1.0 (how certain the verifier is the task succeeded)
- `verdict` — `"accept"` or `"reject"`
- `step_verdicts` — list of `{index, passed, note}` objects
- `overall_reason` — human-readable explanation

A result is **ACCEPTED** only when:
1. `confidence >= 0.75` **AND**
2. `verdict == "accept"`

Otherwise it is **REJECTED** — the task output is marked failed and the full
verifier reasoning is displayed so you know exactly what evidence was missing.

---

## Requirements

- Python 3.10+
- `OPENAI_API_KEY` environment variable (or enter it in the sidebar)
- Internet access (for `fetch_url` tool calls)

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the Streamlit app
streamlit run app.py
```

Enter your OpenAI API key in the sidebar, describe a task, and click **Run Task**.
Results are stored in `~/.task_executor/tasks.db` and visible in the **History** tab.

### CLI mode

```bash
# Set your API key
export OPENAI_API_KEY=sk-...

# Run a task from the terminal
python task_executor.py "Research the top 3 Python async frameworks and write a comparison to /tmp/async_compare.md"

# List past tasks
python task_executor.py --list-tasks

# Inspect a specific task by ID prefix
python task_executor.py --task-id a3f2

# Use a different model (default: gpt-4o-mini)
python task_executor.py --model gpt-4o "Summarize https://example.com and save to /tmp/summary.txt"
```

---

## Estimated LLM Cost Per Task Run

Using the default model (`gpt-4o-mini`, priced at $0.15/M input · $0.60/M output):

| Task complexity | Approx tokens | Estimated cost |
|---|---|---|
| Simple (2–3 steps, no web fetches) | ~8 000 in / 2 000 out | ~$0.003 |
| Typical (5 steps, 1–2 URL fetches) | ~18 000 in / 4 000 out | ~$0.005 |
| Complex (10 steps, multiple fetches) | ~40 000 in / 8 000 out | ~$0.011 |

Token counts are dominated by **tool call round-trips** (each fetched URL can
add 10 000–50 000 tokens to the context window). Switching to `gpt-4o` raises
costs roughly 15× for the same task.

---

## Example Output

### Accepted result

```
────────────── Task ──────────────
Research the top 3 Python async frameworks and write a comparison
to /tmp/async_compare.md

Goal: A saved markdown file at /tmp/async_compare.md comparing asyncio,
Trio, and AnyIO across maturity, API style, and ecosystem support.

  1. [fetch]     Fetch asyncio docs overview
  2. [fetch]     Fetch Trio homepage
  3. [fetch]     Fetch AnyIO README
  4. [synthesize] Write comparison markdown to /tmp/async_compare.md
  5. [verify]    Read /tmp/async_compare.md to confirm content

Review: APPROVED (92%)

────────── Step 1/5: Fetch asyncio docs overview ──────────
[content returned from docs.python.org ...]

... (steps 2–4) ...

────────── Step 5/5: Read file to confirm ──────────
# Python Async Frameworks Comparison
...

────────────── Adversarial Verification ──────────────
ACCEPTED (88%)

All five steps produced verifiable evidence. The file exists at the
expected path and contains structured comparison content for all three
frameworks. Minor gap: version numbers not cited, but success criterion
did not require them.

  ✓ Step 1: asyncio overview fetched (15 KB)
  ✓ Step 2: Trio homepage fetched (8 KB)
  ✓ Step 3: AnyIO README fetched (12 KB)
  ✓ Step 4: File written — tool returned "OK: wrote 2341 chars"
  ✓ Step 5: File read back, content matches expectation

Task ID: a3f2c1d8-...
```

---

### Rejected result

```
────────────── Task ──────────────
Download the latest stock price for AAPL and save it to /tmp/aapl.txt

Goal: A file at /tmp/aapl.txt containing the current AAPL stock price.

  1. [fetch]  Fetch real-time AAPL price from finance API
  2. [write]  Save price to /tmp/aapl.txt
  3. [verify] Read /tmp/aapl.txt to confirm

Review: APPROVED (80%)

────────── Step 1/3: Fetch AAPL price ──────────
ERROR: HTTP 403

────────── Step 2/3: Save price to file ──────────
OK: wrote 12 chars to /tmp/aapl.txt

────────── Step 3/3: Read file ──────────
"price unknown"

────────────── Adversarial Verification ──────────────
REJECTED (31%)

Step 1 returned HTTP 403 — no real price data was retrieved. The agent
wrote a placeholder string ("price unknown") rather than actual data.
The file exists but does not satisfy the success criterion.

  ✗ Step 1: Fetch failed (HTTP 403) — no evidence of price retrieval
  ✗ Step 2: Content written is a placeholder, not a stock price
  ✗ Step 3: File read confirms invalid content

Task ID: b8e7a2f1-...
```

---

## Architecture

### Pipeline stages

```
┌─────────────────────────────────────────────────────────────────┐
│              app.py (UI) + task_executor.py (core)              │
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  Stage 1 │    │   Stage 2    │    │       Stage 3        │  │
│  │  Planner │───▶│ Review Gate  │───▶│   Step Executor      │  │
│  │          │    │              │    │  (tool-use loop ×N)  │  │
│  │ JSON mode│    │ JSON mode    │    │                      │  │
│  │ ≤12 steps│    │ approve/     │    │  read_file           │  │
│  │ typed    │    │ revise/      │    │  write_file          │  │
│  │ success  │    │ reject       │    │  fetch_url (httpx)   │  │
│  │ criteria │    │              │    │                      │  │
│  └──────────┘    └──────────────┘    └──────────┬───────────┘  │
│                        │                        │              │
│                  REJECTED ──────────────────────▼              │
│                  (abort)              ┌──────────────────────┐  │
│                                      │       Stage 4        │  │
│                                      │  Adversarial Verify  │  │
│                                      │                      │  │
│                                      │  cold verifier       │  │
│                                      │  per-step verdicts   │  │
│                                      │  confidence 0.0–1.0  │  │
│                                      └──────────┬───────────┘  │
│                                                 │              │
│                                   ┌─────────────▼──────────┐  │
│                                   │        Stage 5         │  │
│                                   │    Accept / Reject     │  │
│                                   │  confidence ≥ 0.75 AND │  │
│                                   │  verdict == "accept"   │  │
│                                   └────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  SQLite  │  tasks  │  steps  │  tool_calls              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Module map

```
app.py               Streamlit frontend — sidebar config, pipeline progress, history
task_executor.py     Core logic — plan, review, execute, verify, CLI
├── Database         sqlite3 (stdlib) — tasks / steps / tool_calls
├── LLM              openai — JSON-mode completions + function calling
├── HTTP             httpx — fetch_url tool, 50 KB cap, 15 s timeout
├── UI               rich (optional) — color rules, tables, prompts
└── CLI              argparse — run / --list-tasks / --task-id / --model
```

`sqlite3` ships with Python's standard library — no install needed.
