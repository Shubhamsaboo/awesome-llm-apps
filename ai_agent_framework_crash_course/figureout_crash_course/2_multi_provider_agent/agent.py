"""Tutorial 2: Multi-Provider Agent

Runs the same query against multiple LLM providers to demonstrate
that FigureOut is fully provider-agnostic — swap llm + llm_version
and everything else stays the same.

Set the API keys you have in your .env file, then run:
    python agent.py
"""

import asyncio
import os

from dotenv import load_dotenv
from figureout import FigureOut, RoleDefinition

load_dotenv()

# ---------------------------------------------------------------------------
# Shared role definition — identical across all providers
# ---------------------------------------------------------------------------
roles = {
    "summarizer": RoleDefinition(
        prompt=(
            "You are a concise summarizer. "
            "Given a topic, provide a brief 2-3 sentence summary."
        ),
        schema='{"summary": "str", "key_points": ["str"]}',
        guideline="requests to summarize or explain a topic",
    )
}

# ---------------------------------------------------------------------------
# Provider configurations
# Edit this list to include only providers you have API keys for
# ---------------------------------------------------------------------------
PROVIDERS = [
    {
        "name": "OpenAI",
        "llm": "openai",
        "llm_version": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY"),
    },
    {
        "name": "Claude",
        "llm": "claude",
        "llm_version": "claude-haiku-4-5-20251001",
        "api_key": os.getenv("ANTHROPIC_API_KEY"),
    },
    {
        "name": "Gemini",
        "llm": "gemini",
        "llm_version": "gemini-2.0-flash",
        "api_key": os.getenv("GEMINI_API_KEY"),
    },
]

QUERY = "Summarize what machine learning is"


async def run_provider(config: dict) -> dict:
    """Run the query on a single provider."""
    if not config["api_key"]:
        return {"name": config["name"], "skipped": True}

    agent = FigureOut(
        llm=config["llm"],
        llm_version=config["llm_version"],
        roles=roles,
        api_key=config["api_key"],
    )
    result = await agent.run(QUERY)
    return {"name": config["name"], "result": result}


async def main():
    print(f"Query: {QUERY}\n{'=' * 50}")

    tasks = [run_provider(cfg) for cfg in PROVIDERS]
    results = await asyncio.gather(*tasks)

    for item in results:
        if item.get("skipped"):
            print(f"\n[{item['name']}] Skipped — no API key set")
            continue

        response = item["result"].get("response", item["result"])
        print(f"\n[{item['name']}]")
        print(f"  Summary:     {response.get('summary', '')}")
        print(f"  Key points:  {response.get('key_points', [])}")


if __name__ == "__main__":
    asyncio.run(main())
