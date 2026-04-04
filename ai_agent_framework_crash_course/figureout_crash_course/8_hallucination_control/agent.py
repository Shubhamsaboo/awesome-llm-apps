"""Tutorial 8: Hallucination Control with inject_date

Demonstrates FigureOut's inject_date feature. When enabled (the default),
today's date is appended to every system prompt so the LLM can correctly
resolve relative time expressions like "this weekend", "next Monday", or
"end of this month" instead of guessing or hallucinating a date.

This tutorial runs each query twice — once with inject_date=True (grounded)
and once with inject_date=False (ungrounded) — so you can compare how the
LLM handles temporal references with and without a date anchor.

Run:
    python agent.py
"""

import asyncio
import os
from datetime import date

from dotenv import load_dotenv
from figureout import FigureOut, RoleDefinition

load_dotenv()

# ---------------------------------------------------------------------------
# Role: temporal Q&A assistant
# ---------------------------------------------------------------------------
roles = {
    "temporal_qa": RoleDefinition(
        prompt=(
            "You are a helpful scheduling assistant. "
            "Answer questions about dates, deadlines, and time-relative events. "
            "When the user refers to 'this weekend', 'next week', 'end of month', etc., "
            "resolve them to actual calendar dates in your answer."
        ),
        schema='{"answer": "str", "resolved_dates": "str"}',
        guideline="any question involving relative time, dates, deadlines, or scheduling",
    ),
}

# ---------------------------------------------------------------------------
# Two agents — one grounded, one ungrounded
# ---------------------------------------------------------------------------
grounded_agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    api_key=os.getenv("OPENAI_API_KEY"),
    inject_date=True,   # today's date is injected into the system prompt
)

ungrounded_agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    api_key=os.getenv("OPENAI_API_KEY"),
    inject_date=False,  # no date — LLM must guess or hedge
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
async def compare(query: str):
    print(f"\n{'=' * 60}")
    print(f"Query: {query}")
    print(f"{'=' * 60}")

    # Run both agents concurrently
    grounded_result, ungrounded_result = await asyncio.gather(
        grounded_agent.run(query),
        ungrounded_agent.run(query),
    )

    for label, result in [
        ("WITH inject_date=True  (grounded)", grounded_result),
        ("WITH inject_date=False (ungrounded)", ungrounded_result),
    ]:
        response = result.get("response", result)
        print(f"\n  [{label}]")
        print(f"  Answer:         {response.get('answer', '')}")
        print(f"  Resolved dates: {response.get('resolved_dates', '')}")


# ---------------------------------------------------------------------------
# Queries with relative time expressions
# ---------------------------------------------------------------------------
QUERIES = [
    # weekend / week
    "What dates fall on this weekend?",
    "When does next week start and end?",
    # month boundaries
    "How many days are left in this month?",
    "When is the last day of this month?",
    # day-relative
    "What is the date three days from today?",
    "What was yesterday's date?",
    # planning
    "If I start a 2-week project today, what is the deadline?",
    "My subscription renews in 30 days. What is the renewal date?",
]


async def main():
    print("FigureOut — Hallucination Control Demo")
    print(f"Actual date today: {date.today().isoformat()}")
    print(
        "\nFor each query, compare how the LLM handles relative time expressions\n"
        "when it knows today's date (inject_date=True) vs when it does not.\n"
    )

    for query in QUERIES:
        await compare(query)

    print(f"\n{'=' * 60}")
    print("Demo complete.")
    print(
        "\nKey takeaway: with inject_date=True, the LLM resolves every relative\n"
        "time expression to a concrete calendar date. Without it, the LLM is\n"
        "forced to hedge ('I don't know today's date') or silently hallucinate."
    )


if __name__ == "__main__":
    asyncio.run(main())
