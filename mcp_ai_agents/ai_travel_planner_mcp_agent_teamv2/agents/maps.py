from typing import Any, List, Dict
import googlemaps
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from agno.agent import Agent
from rich.console import Console

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("maps")

console = Console()

# Get API key from environment variables
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

if not GOOGLE_MAPS_API_KEY:
    print("[bold red]❌ GOOGLE_MAPS_API_KEY not set. Please check your .env file.[/bold red]")
    exit(1)


# Initialize Google Maps client
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None

class MapsAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Maps Agent",
            description="Handles map-related queries like finding places, directions, and details",
            tools=[mcp],  # ✅ This is the correct way to register all @mcp.tool functions,
            system_message="""
                You are MapsAgent. Your job is to find **hotel suggestions** for a destination city.

                Respond ONLY in the following format, using Markdown:

                ### 🏨 Hotels in <City>:

                **Luxury Hotels:**
                1. Hotel Name: Description
                2. ...

                **Mid-Range Hotels:**
                1. Hotel Name: Description
                2. ...

                **Budget Hotels:**
                1. Hotel Name: Description
                2. ...

                DO NOT include weather or anything unrelated to hotels.
                """
        )
    def run(self, query: str, **kwargs):
        console.rule(f"[bold cyan]🛰️ Running: {self.__class__.__name__}")
        return super().run(query, **kwargs)
    

def format_place(place: Dict[str, Any]) -> str:
    """Format a place result into a readable string."""
    return f"""
Name: {place.get('name', 'Unknown')}
Address: {place.get('formatted_address', 'Unknown')}
Rating: {place.get('rating', 'No rating')} ({place.get('user_ratings_total', 0)} reviews)
Types: {', '.join(place.get('types', ['Unknown']))}
"""

def format_directions(steps: List[Dict[str, Any]]) -> str:
    """Format direction steps into readable instructions."""
    formatted_steps = []
    for i, step in enumerate(steps, 1):
        formatted_steps.append(f"{i}. {step['html_instructions']} ({step['distance']['text']})")
    return "\n".join(formatted_steps)

@mcp.tool(name="Search Places", description="Find places like restaurants, cafes, etc.")
async def search_places(query: str, location: str = None) -> str:
    """Search for places using Google Maps.

    Args:
        query: Search query (e.g. "restaurants", "coffee shops")
        location: Optional location to center the search (e.g. "New York, NY")
    """
    if not gmaps:
        return "Google Maps API key not configured. Please set GOOGLE_MAPS_API_KEY environment variable."

    try:
        # If location is provided, geocode it first
        location_bias = None
        if location:
            geocode_result = gmaps.geocode(location)
            if geocode_result:
                location_bias = {
                    'lat': geocode_result[0]['geometry']['location']['lat'],
                    'lng': geocode_result[0]['geometry']['location']['lng']
                }

        # Perform the places search
        places_result = gmaps.places(
            query,
            location=location_bias if location_bias else None
        )

        if not places_result['results']:
            return f"No places found for '{query}'"

        # Format the top 5 results
        places = [format_place(place) for place in places_result['results'][:5]]
        return "\n---\n".join(places)

    except Exception as e:
        return f"Error searching places: {str(e)}"

@mcp.tool()
async def get_directions(origin: str, destination: str, mode: str = "driving") -> str:
    """Get directions between two locations.

    Args:
        origin: Starting location (address or place name)
        destination: Ending location (address or place name)
        mode: Transportation mode (driving, walking, bicycling, transit)
    """
    if not gmaps:
        return "Google Maps API key not configured. Please set GOOGLE_MAPS_API_KEY environment variable."

    try:
        # Get directions
        directions_result = gmaps.directions(
            origin,
            destination,
            mode=mode
        )

        if not directions_result:
            return f"No directions found from '{origin}' to '{destination}'"

        # Get the first (usually best) route
        route = directions_result[0]
        legs = route['legs'][0]

        # Format the overall journey information
        summary = f"""
Journey from {legs['start_address']} to {legs['end_address']}
Total distance: {legs['distance']['text']}
Estimated duration: {legs['duration']['text']}

Step by step directions:
"""
        # Format the step-by-step directions
        steps = format_directions(legs['steps'])
        
        return summary + steps

    except Exception as e:
        return f"Error getting directions: {str(e)}"

@mcp.tool()
async def get_place_details(place_name: str, location: str = None) -> str:
    """Get detailed information about a specific place.

    Args:
        place_name: Name of the place to search for
        location: Optional location to help narrow down the search
    """
    if not gmaps:
        return "Google Maps API key not configured. Please set GOOGLE_MAPS_API_KEY environment variable."

    try:
        # First, search for the place to get its place_id
        search_params = {
            'input': place_name,
            'inputtype': 'textquery',
            'fields': ['place_id', 'name', 'formatted_address']
        }
        
        if location:
            geocode_result = gmaps.geocode(location)
            if geocode_result:
                search_params['locationbias'] = {
                    'lat': geocode_result[0]['geometry']['location']['lat'],
                    'lng': geocode_result[0]['geometry']['location']['lng']
                }

        place_search = gmaps.find_place(**search_params)

        if not place_search['candidates']:
            return f"Could not find place: {place_name}"

        # Get detailed information using the place_id
        place_id = place_search['candidates'][0]['place_id']
        place_details = gmaps.place(
            place_id,
            fields=['name', 'formatted_address', 'rating', 'formatted_phone_number',
                   'opening_hours', 'website', 'price_level', 'review']
        )

        details = place_details['result']
        
        # Format the details
        formatted_details = f"""
Name: {details.get('name', 'Unknown')}
Address: {details.get('formatted_address', 'Unknown')}
Phone: {details.get('formatted_phone_number', 'Not available')}
Rating: {details.get('rating', 'No rating')}
Website: {details.get('website', 'Not available')}
Price Level: {'$' * details.get('price_level', 0) if 'price_level' in details else 'Not available'}
"""

        # Add opening hours if available
        if 'opening_hours' in details and 'weekday_text' in details['opening_hours']:
            formatted_details += "\nOpening Hours:\n" + "\n".join(details['opening_hours']['weekday_text'])

        return formatted_details

    except Exception as e:
        return f"Error getting place details: {str(e)}"

if __name__ == "__main__":
    import sys
    if "--server" in sys.argv:
        mcp.run(transport='stdio')
    else:
        console.print("[bold yellow]⚠️ To run the MCP server, use: python maps.py --server")
