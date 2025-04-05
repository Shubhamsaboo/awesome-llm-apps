from typing import Any, Dict, Optional
from agno.agent import Agent
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import httpx
import os
from rich.console import Console

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("reviews")

# Initialize rich console for output
console = Console()

# Get API keys
YELP_API_KEY = os.getenv("YELP_API_KEY")
TRIPADVISOR_API_KEY = os.getenv("TRIPADVISOR_API_KEY")

if not YELP_API_KEY or not TRIPADVISOR_API_KEY:
    console.print("[bold red]❌ Missing YELP_API_KEY or TRIPADVISOR_API_KEY in .env file.[/bold red]")
    exit(1)

class ReviewsAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Reviews Agent",
            description="Fetches ratings and reviews for restaurants, hotels, and attractions.",
            tools=[mcp],
            system_message="""
                You are ReviewsAgent. Your task is to gather online ratings for restaurants, hotels, and attractions
                using Yelp and TripAdvisor APIs.

                Format your results in Markdown:

                ### 📝 Reviews:

                1. 📍 <Business Name> - <Rating>⭐ (Yelp)
                2. 🌍 <Attraction Name> - <Rating>⭐ (TripAdvisor)

                Only include results with ratings. No commentary or analysis.
            """
        )

    def run(self, query: str, **kwargs):
        console.rule(f"[bold magenta]🧾 Running: {self.__class__.__name__}")
        return super().run(query, **kwargs)

async def fetch_reviews(api_url: str, params: Dict[str, Any], headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Fetch review data from a third-party API."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            console.print(f"[red]❌ Failed to fetch from {api_url}: {e}[/red]")
            return None

@mcp.tool(name="Get Reviews", description="Get reviews from Yelp and TripAdvisor.")
async def get_reviews(query: str, location: str) -> str:
    """Get reviews for a restaurant, hotel, or attraction in a specified location."""
    yelp_url = "https://api.yelp.com/v3/businesses/search"
    tripadvisor_url = "https://api.tripadvisor.com/api/search"

    params = {"term": query, "location": location}
    yelp_headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    trip_headers = {"Authorization": f"Bearer {TRIPADVISOR_API_KEY}"}

    # Fetch data from both APIs
    yelp_data = await fetch_reviews(yelp_url, params, yelp_headers)
    trip_data = await fetch_reviews(tripadvisor_url, params, trip_headers)

    # Format and combine results
    results = []

    if yelp_data:
        results += [f"📍 {biz['name']} - {biz['rating']}⭐ (Yelp)" for biz in yelp_data.get("businesses", [])]

    if trip_data:
        results += [f"🌍 {item['name']} - {item['rating']}⭐ (TripAdvisor)" for item in trip_data.get("results", [])]

    return "\n".join(results) if results else "No reviews found."

if __name__ == "__main__":
    import sys
    if "--server" in sys.argv:
        mcp.run(transport='stdio')
    else:
        console.print("[bold yellow]⚠️ To run the MCP server, use: python reviews.py --server")
