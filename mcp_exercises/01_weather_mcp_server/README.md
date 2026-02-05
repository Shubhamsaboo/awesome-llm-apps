# Weather MCP Server

An MCP server that provides weather lookup tools using the free [Open-Meteo API](https://open-meteo.com/). No API key required.

## Features

**Tools:**
- `get_current_weather` - Get real-time weather for any city (temperature, humidity, wind, conditions)
- `get_weather_forecast` - Get 1-7 day forecasts with daily highs, lows, and precipitation
- `compare_weather` - Compare current weather across up to 5 cities

**Resources:**
- `weather://supported-units` - Available measurement units
- `weather://weather-codes` - WMO weather interpretation codes

**Prompts:**
- `travel_weather_check` - Check weather for travel planning
- `weather_comparison` - Compare weather across cities

## Concepts Demonstrated

- Async tools with `httpx` for non-blocking HTTP requests
- External API integration (geocoding + weather)
- JSON structured responses
- Error handling for invalid city names
- Resources for reference data

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py

# Test with MCP Inspector
npx -y @modelcontextprotocol/inspector
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["/absolute/path/to/01_weather_mcp_server/server.py"]
    }
  }
}
```

## Example Tool Calls

```
get_current_weather(city="Tokyo")
get_weather_forecast(city="Paris", days=5, unit="celsius")
compare_weather(cities="London, New York, Sydney")
```
