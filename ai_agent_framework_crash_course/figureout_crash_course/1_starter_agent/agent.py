"""Tutorial 1: Your First FigureOut Agent

A minimal single-role agent that answers general questions and returns
a structured JSON response with an answer and confidence level.

Run:
    python agent.py
"""

import asyncio
import os

from dotenv import load_dotenv
from figureout import FigureOut, RoleDefinition

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Define a role
# ---------------------------------------------------------------------------
# Each role has three parts:
#   - prompt:    the system prompt for the LLM when this role is selected
#   - schema:    the JSON schema the LLM must return
#   - guideline: used by the classifier to decide when to pick this role

qa_role = RoleDefinition(
    prompt=(
        "You are a knowledgeable Q&A assistant. "
        "Answer the user's question clearly and concisely. "
        "Be factual and accurate."
    ),
    schema='{"answer": "str", "confidence": "str"}',
    guideline="any general question or request for factual information",
)

# ---------------------------------------------------------------------------
# 2. Create the FigureOut agent
# ---------------------------------------------------------------------------
agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles={"qa": qa_role},
    api_key=os.getenv("OPENAI_API_KEY"),
)

# ---------------------------------------------------------------------------
# 3. Run a query
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    queries = [
        "What is the speed of light?",
        "Who wrote the theory of general relativity?",
        "What is the boiling point of water in Celsius?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        result = asyncio.run(agent.run(query))
        response = result.get("response", result)
        print(f"Answer:     {response.get('answer')}")
        print(f"Confidence: {response.get('confidence')}")
