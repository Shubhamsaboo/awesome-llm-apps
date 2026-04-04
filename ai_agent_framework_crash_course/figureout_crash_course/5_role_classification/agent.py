"""Tutorial 5: Role Classification

A customer support agent with 4 specialist roles. FigureOut automatically
classifies incoming queries and routes them to the right specialist.

Run:
    python agent.py
"""

import asyncio
import os

from dotenv import load_dotenv
from figureout import FigureOut, RoleDefinition

load_dotenv()

# ---------------------------------------------------------------------------
# Define multiple specialist roles
# Each role has a unique guideline — the classifier uses these to decide
# which role handles a given query.
# ---------------------------------------------------------------------------
roles = {
    "account_support": RoleDefinition(
        prompt=(
            "You are an account support specialist. "
            "Help users with login issues, password resets, account settings, "
            "profile changes, and two-factor authentication. "
            "Provide clear, numbered steps."
        ),
        schema=(
            '{"issue": "str", "steps": ["str"], '
            '"escalate": "bool", "estimated_time": "str"}'
        ),
        guideline=(
            "questions about account access, login problems, password resets, "
            "profile settings, or two-factor authentication"
        ),
    ),

    "billing_support": RoleDefinition(
        prompt=(
            "You are a billing and payments specialist. "
            "Help users with subscription plans, invoices, payment methods, "
            "refunds, and pricing questions. Be accurate and helpful."
        ),
        schema=(
            '{"topic": "str", "answer": "str", '
            '"action_required": "bool", "links": ["str"]}'
        ),
        guideline=(
            "questions about billing, payments, invoices, subscriptions, "
            "pricing, refunds, or charges"
        ),
    ),

    "technical_support": RoleDefinition(
        prompt=(
            "You are a technical support engineer. "
            "Help users troubleshoot bugs, errors, and performance issues. "
            "Ask clarifying questions if needed and provide diagnostic steps."
        ),
        schema=(
            '{"error_type": "str", "diagnosis": "str", '
            '"fix_steps": ["str"], "severity": "str (low/medium/high)"}'
        ),
        guideline=(
            "questions about bugs, errors, crashes, slow performance, "
            "API issues, or technical troubleshooting"
        ),
    ),

    "off_topic": RoleDefinition(
        prompt=(
            "You are a helpful assistant. The user's query is outside the scope "
            "of this support system. Politely let them know what topics you can help with: "
            "account issues, billing, and technical support."
        ),
        schema='{"message": "str"}',
        guideline="anything not related to account, billing, or technical support",
    ),
}

agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    api_key=os.getenv("OPENAI_API_KEY"),
    verbose=True,   # required for debug dict (roles_selected, tokens, etc.)
)

# ---------------------------------------------------------------------------
# Test queries — each should route to a different role
# ---------------------------------------------------------------------------
TEST_QUERIES = [
    "How do I reset my password?",
    "I was charged twice this month — can I get a refund?",
    "The app keeps crashing when I upload a file larger than 10MB",
    "What's the best recipe for banana bread?",   # off_topic
]


if __name__ == "__main__":
    for query in TEST_QUERIES:
        result = asyncio.run(agent.run(query))
        response = result.get("response", result)
        debug = result.get("debug", {})
        roles_selected = debug.get("roles_selected", [])
        role = roles_selected[0] if roles_selected else "off_topic"

        print(f"\nQuery:         {query}")
        print(f"Role selected: {role}")
        print(f"Response:      {response}")
