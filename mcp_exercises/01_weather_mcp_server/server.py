"""
Weather MCP Server
==================
An MCP server that provides weather lookup tools using the Open-Meteo API.
Demonstrates: async tools, API integration, structured responses, resources.

No API key required -- uses the free Open-Meteo geocoding and weather APIs.
"""

import json
from datetime import datetime

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather MCP Server")

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────


async def geocode_city(city: str) -> dict | None:
    """Look up latitude/longitude for a city name."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
        )
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]
        return None


# ──────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────


@mcp.tool()
async def get_current_weather(city: str, unit: str = "celsius") -> str:
    """Get the current weather for a city.

    Args:
        city: Name of the city (e.g., "London", "New York", "Tokyo")
        unit: Temperature unit - "celsius" or "fahrenheit" (default: celsius)
    """
    location = await geocode_city(city)
    if not location:
        return f"Error: Could not find city '{city}'. Please check the spelling."

    temp_unit = "fahrenheit" if unit.lower() == "fahrenheit" else "celsius"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            WEATHER_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "temperature_unit": temp_unit,
                "wind_speed_unit": "kmh",
            },
        )
        data = response.json()

    current = data.get("current", {})
    weather_code = current.get("weather_code", 0)
    description = WMO_WEATHER_CODES.get(weather_code, "Unknown")
    unit_symbol = "F" if temp_unit == "fahrenheit" else "C"

    return json.dumps(
        {
            "city": location["name"],
            "country": location.get("country", "Unknown"),
            "temperature": f"{current.get('temperature_2m', 'N/A')}{unit_symbol}",
            "humidity": f"{current.get('relative_humidity_2m', 'N/A')}%",
            "wind_speed": f"{current.get('wind_speed_10m', 'N/A')} km/h",
            "condition": description,
            "coordinates": {
                "latitude": location["latitude"],
                "longitude": location["longitude"],
            },
        },
        indent=2,
    )


@mcp.tool()
async def get_weather_forecast(city: str, days: int = 3, unit: str = "celsius") -> str:
    """Get a multi-day weather forecast for a city.

    Args:
        city: Name of the city (e.g., "Paris", "Berlin", "Sydney")
        days: Number of forecast days (1 to 7, default: 3)
        unit: Temperature unit - "celsius" or "fahrenheit" (default: celsius)
    """
    if days < 1 or days > 7:
        return "Error: Forecast days must be between 1 and 7."

    location = await geocode_city(city)
    if not location:
        return f"Error: Could not find city '{city}'. Please check the spelling."

    temp_unit = "fahrenheit" if unit.lower() == "fahrenheit" else "celsius"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            WEATHER_URL,
            params={
                "latitude": location["latitude"],
                "longitude": location["longitude"],
                "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_sum",
                "temperature_unit": temp_unit,
                "forecast_days": days,
            },
        )
        data = response.json()

    daily = data.get("daily", {})
    unit_symbol = "F" if temp_unit == "fahrenheit" else "C"

    forecast_days = []
    dates = daily.get("time", [])
    for i, date in enumerate(dates):
        weather_code = daily.get("weather_code", [0])[i] if i < len(daily.get("weather_code", [])) else 0
        forecast_days.append(
            {
                "date": date,
                "high": f"{daily.get('temperature_2m_max', [None])[i]}{unit_symbol}",
                "low": f"{daily.get('temperature_2m_min', [None])[i]}{unit_symbol}",
                "condition": WMO_WEATHER_CODES.get(weather_code, "Unknown"),
                "precipitation": f"{daily.get('precipitation_sum', [0])[i]} mm",
            }
        )

    return json.dumps(
        {
            "city": location["name"],
            "country": location.get("country", "Unknown"),
            "forecast": forecast_days,
        },
        indent=2,
    )


@mcp.tool()
async def compare_weather(cities: str) -> str:
    """Compare current weather across multiple cities.

    Args:
        cities: Comma-separated list of city names (e.g., "London, Tokyo, New York")
    """
    city_list = [c.strip() for c in cities.split(",") if c.strip()]
    if len(city_list) < 2:
        return "Error: Please provide at least 2 cities separated by commas."
    if len(city_list) > 5:
        return "Error: Maximum 5 cities allowed for comparison."

    results = []
    for city in city_list:
        weather_json = await get_current_weather(city)
        results.append(json.loads(weather_json))

    return json.dumps({"comparison": results}, indent=2)


# ──────────────────────────────────────────────
# Resources
# ──────────────────────────────────────────────


@mcp.resource("weather://supported-units")
def supported_units() -> str:
    """List the supported temperature units."""
    return json.dumps(
        {
            "temperature_units": ["celsius", "fahrenheit"],
            "wind_speed_unit": "km/h",
            "precipitation_unit": "mm",
        }
    )


@mcp.resource("weather://weather-codes")
def weather_codes() -> str:
    """List all WMO weather interpretation codes."""
    return json.dumps(WMO_WEATHER_CODES, indent=2)


# ──────────────────────────────────────────────
# Prompts
# ──────────────────────────────────────────────


@mcp.prompt()
def travel_weather_check(destination: str, travel_date: str) -> str:
    """Generate a prompt to check weather conditions for travel planning."""
    return f"""I'm planning to travel to {destination} around {travel_date}.
Please:
1. Get the current weather in {destination}
2. Get a 7-day forecast for {destination}
3. Based on the weather, suggest what to pack and any weather advisories."""


@mcp.prompt()
def weather_comparison(cities: str) -> str:
    """Generate a prompt to compare weather across cities."""
    return f"""Please compare the current weather in these cities: {cities}

Create a summary table and recommend the best city to visit today based on weather conditions."""


# ──────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
