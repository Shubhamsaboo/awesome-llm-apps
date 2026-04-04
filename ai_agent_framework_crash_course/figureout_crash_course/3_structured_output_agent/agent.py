"""Tutorial 3: Structured Output Agent

A product review agent that returns a rich, schema-validated JSON response
with title, summary, pros, cons, verdict, and score.

Run:
    python agent.py
"""

import asyncio
import json
import os

from dotenv import load_dotenv
from figureout import FigureOut, RoleDefinition

load_dotenv()

# ---------------------------------------------------------------------------
# Rich JSON schema — design it to match exactly what your app needs to render
# ---------------------------------------------------------------------------
REVIEW_SCHEMA = json.dumps({
    "title": "str (product name + 'Review')",
    "summary": "str (2-3 sentence overview)",
    "pros": ["str"],
    "cons": ["str"],
    "verdict": "str (1 sentence conclusion)",
    "score": "int (1-10)",
})

roles = {
    "product_review": RoleDefinition(
        prompt=(
            "You are an expert product reviewer. "
            "Analyze the product mentioned by the user and return a balanced, "
            "honest review with clear pros, cons, and a final verdict. "
            "Be specific and concise."
        ),
        schema=REVIEW_SCHEMA,
        guideline="requests to review, rate, or evaluate a product",
    ),
}

agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    api_key=os.getenv("OPENAI_API_KEY"),
)

# ---------------------------------------------------------------------------
# Run the agent and print the structured response
# ---------------------------------------------------------------------------
def print_review(response: dict):
    print(f"\n{'=' * 50}")
    print(f"  {response.get('title', '')}")
    print(f"{'=' * 50}")
    print(f"\nSummary: {response.get('summary', '')}")
    print(f"\nPros:")
    for pro in response.get("pros", []):
        print(f"  + {pro}")
    print(f"\nCons:")
    for con in response.get("cons", []):
        print(f"  - {con}")
    print(f"\nVerdict: {response.get('verdict', '')}")
    print(f"Score:   {response.get('score', '')}/10")


if __name__ == "__main__":
    products = [
        "Review the MacBook Pro M4",
        "Review the Sony WH-1000XM5 headphones",
    ]

    for query in products:
        print(f"\nQuery: {query}")
        result = asyncio.run(agent.run(query))
        response = result.get("response", result)
        print_review(response)
