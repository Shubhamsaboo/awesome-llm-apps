"""Tutorial 7: In-Memory Caching

Demonstrates FigureOut's built-in cache. Repeated identical queries are
served from cache — no LLM call is made. The input_tokens and output_tokens
shown on a cache hit are carried over from the original LLM response; they
do NOT represent a new LLM call or any new token consumption.

Run:
    python agent.py
"""

import asyncio
import os
import time

from dotenv import load_dotenv
from figureout import FigureOut, RoleDefinition

load_dotenv()

# ---------------------------------------------------------------------------
# Define a simple Q&A agent
# ---------------------------------------------------------------------------
roles = {
    "qa": RoleDefinition(
        prompt=(
            "You are a knowledgeable assistant. "
            "Answer the user's question clearly and concisely."
        ),
        schema='{"answer": "str", "topic": "str"}',
        guideline="any general question or request for information",
    ),
}

agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    api_key=os.getenv("OPENAI_API_KEY"),
    verbose=True
)


# ---------------------------------------------------------------------------
# Helper to run a query and print cache + performance info
# ---------------------------------------------------------------------------
async def run_and_report(label: str, query: str):
    print(f"\n--- {label} ---")
    print(f"Query: {query}")

    start = time.perf_counter()
    result = await agent.run(query)
    elapsed = time.perf_counter() - start

    debug = result.get("debug", {})
    response = result.get("response", result)

    cached = debug.get('cached', False)
    print(f"Cached:        {cached}")
    print(f"Input tokens:  {debug.get('input_tokens', 0)}"
          + (" (from original LLM response — no new LLM call was made)" if cached else ""))
    print(f"Output tokens: {debug.get('output_tokens', 0)}"
          + (" (from original LLM response — no new LLM call was made)" if cached else ""))
    print(f"Time:          {elapsed:.3f}s")
    print(f"Answer:        {response.get('answer', '')[:80]}")


# ---------------------------------------------------------------------------
# Demonstrate cache behaviour across different scenarios
# ---------------------------------------------------------------------------
async def main():
    print("=" * 55)
    print("FigureOut In-Memory Cache Demo")
    print("=" * 55)

    # Scenario 1: Cold cache — LLM is called
    await run_and_report(
        "Run 1 — cold cache (LLM called)",
        "What is machine learning?",
    )

    # Scenario 2: Exact same query — served from cache, no LLM call
    await run_and_report(
        "Run 2 — identical query (cache hit)",
        "What is machine learning?",
    )

    # Scenario 3: Same query again — still a cache hit
    await run_and_report(
        "Run 3 — identical query again (cache hit)",
        "What is machine learning?",
    )

    # Scenario 4: Different query — cache miss, LLM called again
    await run_and_report(
        "Run 4 — different query (cache miss)",
        "What is deep learning?",
    )

    # Scenario 5: Rephrased version of Run 1 — still a cache miss
    # The cache matches on exact string, not semantic similarity
    await run_and_report(
        "Run 5 — rephrased query (cache miss — exact match only)",
        "Can you explain machine learning?",
    )

    # Scenario 6: First query repeated once more — still cached
    await run_and_report(
        "Run 6 — back to Run 1 query (cache hit)",
        "What is machine learning?",
    )


if __name__ == "__main__":
    asyncio.run(main())
