import asyncio
import os

from agno.agent import Agent
from agno.team.team import Team
from agno.tools.mcp import MultiMCPTools
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

async def run_agent(message: str) -> None:
    """Run the Airbnb, Google Maps, Weather and Calendar agent with the given message."""

    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    accuweather_key = os.getenv("ACCUWEATHER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    google_maps_key = os.getenv("GOOGLE_CLIENT_ID")
    if not google_maps_key:
        raise ValueError("🚨 Missing GOOGLE_MAPS_API_KEY in environment variables.")
    elif not accuweather_key:
        raise ValueError("🚨 Missing ACCUWEATHER_API_KEY in environment variables.")
    elif not openai_key:
        raise ValueError("🚨 Missing OPENAI_API_KEY in environment variables.")
    elif not google_maps_key:
        raise ValueError("🚨 Missing GOOGLE_CLIENT_ID in environment variables.")
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
            "/Users/priyanshmaheshwari/Desktop/EchovibeLabs/awesome-llm-apps/mcp_ai_agents/ai_travel_planner_mcp_agent_team/calendar_mcp.py" # ✅ Calendar mcp added

        ],
        env=env,
    ) as mcp_tools:
        
        #Define sepcialized agents
        maps_agent = Agent(
            tools=[mcp_tools],
            name="Maps Agent",
            goal="Integrates with Google Maps server to provide routing information, travel time estimates, and points of interest proximity analysis"
        )

        weather_agent = Agent(
            tools=[mcp_tools],
            name="Weather Agent",
            goal="Pulls data from OpenWeatherMap to provide weather forecasts for planned dates and locations, allowing for weather-appropriate activity planning."
        )

        booking_agent = Agent(
            tools=[mcp_tools],
            name="Booking Agent",
            goal="Connects to Booking.com and Airbnb APIs to search and filter accommodations based on user preferences (price range, amenities, location)"
        )

        calendar_agent = Agent(
            tools=[mcp_tools],
            name="Calendar Agent",
            goal="Creates calendar events for travel plans, including reminders and location details."
        )

        team = Team(
            members=[maps_agent, weather_agent, booking_agent, calendar_agent],
            name="Travel Planning Team",
            markdown=True,
            show_tool_calls=True
        )

        await team.aprint_response(message, stream=True)

# -------------------- Terminal Interaction Loop --------------------

if __name__ == "__main__":  # ✅ correct

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