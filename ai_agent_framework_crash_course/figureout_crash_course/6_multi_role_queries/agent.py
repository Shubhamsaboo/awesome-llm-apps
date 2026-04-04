"""Tutorial 6: Multi-Role Queries

A financial assistant that can handle queries spanning multiple domains
(news + stock prices + market analysis) using FigureOut's max_roles parameter.

Run:
    python agent.py
"""

import asyncio
import os

from dotenv import load_dotenv
from figureout import FigureOut, RoleDefinition

load_dotenv()

# ---------------------------------------------------------------------------
# Define specialist roles for a financial assistant
# ---------------------------------------------------------------------------
roles = {
    "stock_price": RoleDefinition(
        prompt=(
            "You are a stock market data specialist. "
            "Provide current or recent stock price information, market cap, "
            "52-week highs/lows, and basic ticker information for companies. "
            "If you don't have real-time data, provide the most recent information "
            "available and note the date."
        ),
        schema=(
            '{"ticker": "str", "company": "str", "price_usd": "float", '
            '"change_pct": "float", "market_cap": "str", "note": "str"}'
        ),
        guideline="questions about stock prices, tickers, market cap, or share prices",
    ),

    "news": RoleDefinition(
        prompt=(
            "You are a financial news analyst. "
            "Summarize the latest relevant news about a company or market topic. "
            "Highlight the most impactful recent developments."
        ),
        schema=(
            '{"topic": "str", "headlines": ["str"], '
            '"sentiment": "str (positive/neutral/negative)", "summary": "str"}'
        ),
        guideline="questions about news, recent events, announcements, or developments for a company or sector",
    ),

    "market_analysis": RoleDefinition(
        prompt=(
            "You are a market analyst. "
            "Provide analysis of market trends, sector performance, "
            "economic indicators, and investment context."
        ),
        schema=(
            '{"subject": "str", "trend": "str", '
            '"key_factors": ["str"], "outlook": "str"}'
        ),
        guideline=(
            "questions about market trends, sector analysis, economic outlook, "
            "or investment strategy"
        ),
    ),

    "off_topic": RoleDefinition(
        prompt=(
            "The user's query is outside the scope of this financial assistant. "
            "Politely let them know you can help with stock prices, financial news, "
            "and market analysis."
        ),
        schema='{"message": "str"}',
        guideline="anything not related to stocks, financial news, or market analysis",
    ),
}

# ---------------------------------------------------------------------------
# Create two agents: single-role and multi-role, to compare behaviour
# ---------------------------------------------------------------------------
single_role_agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    api_key=os.getenv("OPENAI_API_KEY"),
    max_roles=1,   # default — only the best-matching role fires
    verbose=True
)

multi_role_agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    api_key=os.getenv("OPENAI_API_KEY"),
    max_roles=3,   # up to 3 roles can handle a query simultaneously
    verbose=True
)

# ---------------------------------------------------------------------------
# Test queries
# ---------------------------------------------------------------------------
SINGLE_DOMAIN_QUERY = "What is the current stock price of Tesla?"
MULTI_DOMAIN_QUERY = "Give me the latest news and stock price for Apple"


async def compare(query: str):
    print(f"\n{'=' * 60}")
    print(f"Query: {query}")

    # Single-role
    single_result = await single_role_agent.run(query)
    single_roles = single_result.get("debug", {}).get("roles_selected", [])
    print(f"\n[max_roles=1] Roles selected: {single_roles}")

    # Multi-role
    multi_result = await multi_role_agent.run(query)
    multi_roles = multi_result.get("debug", {}).get("roles_selected", [])
    print(f"[max_roles=3] Roles selected: {multi_roles}")

    print(f"\nMulti-role response: {multi_result.get('response', {})}")


if __name__ == "__main__":
    asyncio.run(compare(SINGLE_DOMAIN_QUERY))
    asyncio.run(compare(MULTI_DOMAIN_QUERY))
