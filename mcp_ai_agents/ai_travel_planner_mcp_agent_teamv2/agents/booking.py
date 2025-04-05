from typing import Any, Dict, Optional
from agno.agent import Agent
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import os
from rich.console import Console

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("booking")

# Setup console for logging
console = Console()

# Load API keys
BOOKING_API_KEY = os.getenv("BOOKING_API_KEY")
AIRBNB_API_KEY = os.getenv("AIRBNB_API_KEY")

if not BOOKING_API_KEY or not AIRBNB_API_KEY:
    console.print("[bold red]❌ Missing BOOKING_API_KEY or AIRBNB_API_KEY in .env file.[/bold red]")
    exit(1)

class BookingAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Booking Agent",
            description="Handles hotel and accommodation bookings.",
            tools=[mcp],
            system_message="""
                You are BookingAgent. You help users find accommodations by searching Booking.com and Airbnb.
                You respond only with formatted listings.

                Format:
                ### 🛏️ Accommodation Options:

                1. 🏨 <Hotel Name> - <Price> (Booking.com)
                2. 🏠 <Listing Title> - <Price> (Airbnb)
                
                Only include listings that have a name/title and price.
            """
        )

    def run(self, query: str, **kwargs):
        console.rule(f"[bold blue]🏨 Running: {self.__class__.__name__}")
        return super().run(query, **kwargs)

async def fetch_accommodations(api_url: str, params: Dict[str, Any], headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Fetch accommodation data from API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[red]❌ Failed to fetch from {api_url}: {e}[/red]")
            return None

@mcp.tool(name="Search Accommodations", description="Search hotels and Airbnb listings.")
async def search_accommodations(location: str, price_range: str = "", amenities: str = "") -> str:
    """Search for accommodations using Booking.com and Airbnb."""
    booking_url = "https://api.booking.com/search"
    airbnb_url = "https://api.airbnb.com/search"

    params = {"location": location, "price_range": price_range, "amenities": amenities}
    booking_headers = {"Authorization": f"Bearer {BOOKING_API_KEY}"}
    airbnb_headers = {"Authorization": f"Bearer {AIRBNB_API_KEY}"}

    booking_data = await fetch_accommodations(booking_url, params, booking_headers)
    airbnb_data = await fetch_accommodations(airbnb_url, params, airbnb_headers)

    results = []

    if booking_data:
        results += [f"🏨 {item['name']} - {item['price']} (Booking.com)" for item in booking_data.get("results", [])]

    if airbnb_data:
        results += [f"🏠 {item['title']} - {item['price']} (Airbnb)" for item in airbnb_data.get("results", [])]

    return "\n".join(results) if results else "No accommodations found."

if __name__ == "__main__":
    import sys
    if "--server" in sys.argv:
        mcp.run(transport="stdio")
    else:
        console.print("[bold yellow]⚠️ To run the MCP server, use: python booking.py --server")
