from typing import Any
import httpx
from agno.agent import Agent
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from rich.console import Console

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("weather")

console = Console()

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"
NWS_API_KEY = os.getenv('NWS_API_KEY')

class WeatherAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Weather Agent",
            description="Provides weather forecasts and alerts.",
            tools=[mcp],  # Register all @mcp.tool functions,
            system_message="""
                You are WeatherAgent. You provide seasonal weather summaries for cities in India.

                Respond ONLY in the following format:

                ### 🌦️ Weather in <City>:

                • Winter (Month to Month): Summary  
                • Summer (Month to Month): Summary  
                • Monsoon (Month to Month): Summary

                Keep the response clean, accurate, and don't include hotel or travel details.
            """
        )
    def run(self, query: str, **kwargs):
        console.rule(f"[bold cyan]🛰️ Running: {self.__class__.__name__}")
        return super().run(query, **kwargs)

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json",
        "Authorization": f"Bearer {NWS_API_KEY}" if NWS_API_KEY else None
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""

@mcp.tool(name="Weather Alerts", description="Get weather alerts")
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
        {period['name']}:
        Temperature: {period['temperature']}°{period['temperatureUnit']}
        Wind: {period['windSpeed']} {period['windDirection']}
        Forecast: {period['detailedForecast']}
        """
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

if __name__ == "__main__":
    import sys
    if "--server" in sys.argv:
        mcp.run(transport='stdio')
    else:
        console.print("[bold yellow]⚠️ To run the MCP server, use: python maps.py --server")