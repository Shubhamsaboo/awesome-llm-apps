#!/bin/bash

echo "🚀 Starting all MCP servers..."

python mcp_servers/weather/server.py & 
echo "🌦️ Weather MCP started"

python mcp_servers/booking/server.py & 
echo "🏨 Booking MCP started"

python mcp_servers/reviews/server.py & 
echo "🌟 Reviews MCP started"

python mcp_servers/calendar/server.py & 
echo "📅 Calendar MCP started"

echo "✅ All servers launched!"
