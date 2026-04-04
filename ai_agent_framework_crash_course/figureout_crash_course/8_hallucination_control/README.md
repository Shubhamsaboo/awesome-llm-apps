# 🗓️ Tutorial 8: Hallucination Control with `inject_date`

LLMs have no built-in clock. When a user asks "what dates fall on this weekend?" or "how many days are left this month?", the model has to either guess, hedge, or hallucinate a plausible-sounding date. FigureOut's `inject_date` feature solves this by appending today's date to every system prompt automatically.

## 🎯 What You'll Learn

- Why relative time expressions cause LLM hallucinations
- How `inject_date` grounds the LLM to the actual current date
- The difference in output quality with and without date injection
- When to disable `inject_date` (and why the default is `True`)

## 🧠 Core Concept: Date Injection

When `inject_date=True` (the default), FigureOut appends the following line to every role's system prompt before the LLM call:

```
Today's date is 2025-04-03.
```

This single line of context lets the LLM correctly resolve expressions like:

| User says             | LLM resolves to           |
|-----------------------|---------------------------|
| "this weekend"        | "Saturday Apr 5 – Sun Apr 6" |
| "next Monday"         | "Monday Apr 7"            |
| "end of this month"   | "Thursday Apr 30"         |
| "in 30 days"          | "Friday May 2"            |
| "yesterday"           | "Wednesday Apr 2"         |

Without date injection the LLM cannot resolve any of these — it either hedges ("I don't have access to today's date") or silently invents a date.

## 🔧 Usage

```python
from figureout import FigureOut, RoleDefinition

agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles={"qa": my_role},
    api_key="...",
    inject_date=True,   # default — append today's date to system prompts
)
```

To disable (e.g. in unit tests with deterministic prompts):

```python
agent = FigureOut(..., inject_date=False)
```

You can also control this via the environment variable:

```bash
export FIGUREOUT_INJECT_DATE=false
```

## 📁 Project Structure

```
8_hallucination_control/
├── README.md         # This file
├── requirements.txt  # Dependencies
└── agent.py          # Side-by-side comparison: inject_date=True vs False
```

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key**:
   ```bash
   export OPENAI_API_KEY=sk-your_key_here
   ```

3. **Run the agent**:
   ```bash
   python agent.py
   ```

## 🧪 Sample Output

```
Actual date today: 2025-04-03

============================================================
Query: What dates fall on this weekend?
============================================================

  [WITH inject_date=True  (grounded)]
  Answer:         This weekend falls on Saturday, April 5 and Sunday, April 6, 2025.
  Resolved dates: 2025-04-05, 2025-04-06

  [WITH inject_date=False (ungrounded)]
  Answer:         I don't have access to today's date, so I can't tell you
                  the exact dates for this weekend.
  Resolved dates: unknown

============================================================
Query: If I start a 2-week project today, what is the deadline?
============================================================

  [WITH inject_date=True  (grounded)]
  Answer:         Starting today (April 3), a 2-week project ends on April 17, 2025.
  Resolved dates: 2025-04-17

  [WITH inject_date=False (ungrounded)]
  Answer:         Without knowing today's date I cannot calculate the exact deadline.
  Resolved dates: unknown
```

## 💡 When This Matters Most

- **Scheduling assistants** — "book me a slot this Friday"
- **Deadline trackers** — "alert me 3 days before end of month"
- **Event finders** — "what's happening this weekend near me?"
- **Finance / billing** — "when does my 30-day trial expire?"
- **Any agent that reads or writes calendar data**

## ⚠️ When to Disable `inject_date`

- **Deterministic test suites** — date injection changes the system prompt on every run, making snapshot tests flaky
- **Historical Q&A** — if the user is asking about past events and you do not want the current date to influence the response
- **Custom date handling** — if you are injecting a specific reference date yourself via the role prompt

## 🔗 What's Next?

You've completed the full FigureOut crash course! Explore:

- **[FigureOut GitHub](https://github.com/balajeekalyan/figureout)** — source code and full API reference
- **[Full Demo App](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/advanced_ai_agents/multi_agent_apps/figureout_multi_llm_orchestrator)** — a complete Events & Booking assistant using all FigureOut features
