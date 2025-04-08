import asyncio
import os

from agno.agent import Agent
from agno.tools.mcp import MultiMCPTools
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

async def run_agent(message: str) -> None:
    """Run the Airbnb, Google Maps, Weather agent with the given message."""

    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    accuweather_key = os.getenv("ACCUWEATHER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if not google_maps_key:
        raise ValueError("🚨 Missing GOOGLE_MAPS_API_KEY in environment variables.")
    elif not accuweather_key:
        raise ValueError("🚨 Missing ACCUWEATHER_API_KEY in environment variables.")
    elif not openai_key:
        raise ValueError("🚨 Missing OPENAI_API_KEY in environment variables.")
    env = {
        **os.environ,
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
        "ACCUWEATHER_API_KEY": os.getenv("ACCUWEATHER_API_KEY"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }

    async with MultiMCPTools(
        [
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt", # ✅ Airbnb mcp added
            "npx -y @modelcontextprotocol/server-google-maps", # ✅ Google Maps mcp added
            "uvx --from git+https://github.com/adhikasp/mcp-weather.git mcp-weather", # ✅ Weather mcp added
            # "https://www.gumloop.com/mcp/gcalendar",

        ],
        env=env,
    ) as mcp_tools:
        agent = Agent(
            tools=[mcp_tools],
            markdown=True,
            show_tool_calls=True,
        )

        await agent.aprint_response(message, stream=True)

# -------------------- Terminal Interaction Loop --------------------

if _name_ == "_main_": # type: ignore
    print("🌍 Travel Planning Agent — Airbnb, Maps, Weather, Calendar (type 'exit' to quit)\n")
    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("👋 Bye!")
                break
            asyncio.run(run_agent(user_input))
    except KeyboardInterrupt:
        print("\n👋 Interrupted. Exiting...")