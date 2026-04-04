"""Tutorial 4: Tool Using Agent with MCP

A weather agent backed by a FastMCP tool server. FigureOut automatically
calls the appropriate tool based on the user's query.

Run:
    python agent.py
"""

import asyncio
import os
import random

from dotenv import load_dotenv
from fastmcp import FastMCP
from figureout import FigureOut, RoleDefinition

load_dotenv()

# ---------------------------------------------------------------------------
# 1. Define MCP tools
# ---------------------------------------------------------------------------
# These are the tools the LLM can call. FigureOut passes the MCP server
# to the agent, and the role's prompt tells the LLM when to use each tool.

mcp = FastMCP("weather-server")

# Simulated weather data — replace with a real API in production
WEATHER_DB = {
    "new york": {"temp_c": 18, "condition": "Partly cloudy", "humidity": 65},
    "london": {"temp_c": 12, "condition": "Overcast", "humidity": 80},
    "tokyo": {"temp_c": 24, "condition": "Sunny", "humidity": 55},
    "sydney": {"temp_c": 20, "condition": "Clear", "humidity": 60},
    "paris": {"temp_c": 15, "condition": "Light rain", "humidity": 75},
}


@mcp.tool()
async def get_current_weather(city: str) -> dict:
    """Get the current weather conditions for a city."""
    city_key = city.lower()
    if city_key in WEATHER_DB:
        return {"city": city, **WEATHER_DB[city_key]}
    # Fallback with random data for unknown cities
    return {
        "city": city,
        "temp_c": random.randint(10, 30),
        "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Windy"]),
        "humidity": random.randint(40, 90),
    }


@mcp.tool()
async def get_weather_forecast(city: str, days: int = 3) -> list:
    """Get a multi-day weather forecast for a city."""
    conditions = ["Sunny", "Partly cloudy", "Overcast", "Light rain", "Clear"]
    forecast = []
    for i in range(1, days + 1):
        forecast.append({
            "day": i,
            "condition": random.choice(conditions),
            "high_c": random.randint(15, 30),
            "low_c": random.randint(5, 15),
        })
    return forecast


# ---------------------------------------------------------------------------
# 2. Define roles
# ---------------------------------------------------------------------------
roles = {
    "weather": RoleDefinition(
        prompt=(
            "You are a weather assistant. "
            "Use the `get_current_weather` tool to fetch current conditions "
            "and `get_weather_forecast` to fetch multi-day forecasts. "
            "Always call the relevant tool before responding."
        ),
        schema=(
            '{"city": "str", "current_temp_c": "int", "condition": "str", '
            '"humidity": "int", "summary": "str"}'
        ),
        guideline="questions about weather, temperature, forecast, or climate conditions",
    ),
}

# ---------------------------------------------------------------------------
# 3. Create the agent with the MCP server attached
# ---------------------------------------------------------------------------
agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    api_key=os.getenv("OPENAI_API_KEY"),
    mcp_server=mcp,
    interpret_tool_response=True,  # LLM interprets raw tool output before structuring
    verbose=True,
)

# ---------------------------------------------------------------------------
# 4. Run queries
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    queries = [
        "What's the weather like in Tokyo right now?",
        "Is it going to rain in London this week?",
        "How hot is New York today?",
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        result = asyncio.run(agent.run(query))

        response = result.get("response", result)
        debug = result.get("debug", {})

        print(f"City:        {response.get('city', '')}")
        print(f"Temperature: {response.get('current_temp_c', '')}°C")
        print(f"Condition:   {response.get('condition', '')}")
        print(f"Summary:     {response.get('summary', '')}")
        print(f"Tools used:  {debug.get('tools_used', [])}")
