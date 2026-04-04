import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

event_mcp = FastMCP("Event MCP")

DATA_DIR = Path(__file__).parent / "data"

def matches_location(location: str, city: str, country: str) -> bool:
    """Check if location matches city or country using flexible matching."""
    loc = location.lower().strip()
    if not loc:
        return True
    city_lower = city.lower().strip()
    country_lower = country.lower().strip()
    # Direct substring match in either direction
    if loc in city_lower or city_lower in loc:
        return True
    if loc in country_lower or country_lower in loc:
        return True
    # Match against city parts split by comma (e.g. "New York, NY" -> ["New York", "NY"])
    city_parts = [p.strip() for p in city.split(",")]
    for part in city_parts:
        part_lower = part.lower()
        if loc in part_lower or part_lower in loc:
            return True
    return False

def matches_date(date: str, from_date: str, to_date: str) -> bool:
    """Check if a date falls within the from_date and to_date range (YYYY-MM-DD)."""
    if not from_date and not to_date:
        return True
    if not from_date:
        return date <= to_date
    if not to_date:
        return from_date <= date
    return from_date <= date <= to_date

seats = None

def _get_seats():
    global seats
    if seats is None:
        seats = load_json("seats.json")
    return seats

def load_json(filename: str) -> list:
    path = DATA_DIR / filename
    if path.exists() and path.stat().st_size > 0:
        with open(path) as f:
            return json.load(f)
    return []

@event_mcp.tool(name="get_events_by_artist", description="Search events database by artist name. Optionally filter by from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), and location if provided in user context; omit or pass empty strings to return all matching events.")
async def get_events_by_artist(artist: str, from_date: str = "", to_date: str = "", location: str = "") -> str:
    """Get available events for a given artist filtered by date range and location. Use from_date, to_date, and location from the user context if available, otherwise omit them."""
    events = load_json("events.json")
    results = []
    for event in events:
        if artist.lower() not in event["artist"].lower():
            continue
        filtered_details = [
            d for d in event["details"]
            if matches_date(d["date"], from_date, to_date)
            and matches_location(location, d["city"], d["country"])
        ]
        if filtered_details:
            results.append({**event, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No events found for artist '{artist}'"})

@event_mcp.tool(name="get_events_by_genre", description="Search events database by genre. Available genres: R&B, Pop, Dance, Neo-Soul, Afrobeats, Rock, Comedy, Basketball, Soccer, Tennis, MMA, Motorsport, Baseball, Hockey, Wrestling, Boxing, Musical, Drama, Hip-Hop, Electronic, Indie, EDM, House, Techno, Folk, Country, Trance, Dubstep, Amapiano, Dancehall, Ice Show, Live Show, Circus, Acrobatics, Educational, Performance Art, Children's Music, Interactive, Exhibition, Action, Thriller, Sci-Fi, Romance, Adventure, Horror, Animation, Family, Crime, Historical, Mystery, Documentary. Optionally filter by from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), and location if provided in user context; omit or pass empty strings to return all matching events.")
async def get_events_by_genre(genre: str, from_date: str = "", to_date: str = "", location: str = "") -> str:
    """Get available events for a given genre filtered by date range and location. Use from_date, to_date, and location from the user context if available, otherwise omit them."""
    events = load_json("events.json")
    results = []
    for event in events:
        if genre.lower() not in [g.lower() for g in event["genre"]]:
            continue
        filtered_details = [
            d for d in event["details"]
            if matches_date(d["date"], from_date, to_date)
            and matches_location(location, d["city"], d["country"])
        ]
        if filtered_details:
            results.append({**event, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No events found for genre '{genre}'"})

@event_mcp.tool(name="get_events_by_type", description="Search events database by event type. Available types: Concert, Standup Comedy, Sports, Theater, Music Festival, Family and Children, Movie. Optionally filter by from_date (YYYY-MM-DD), to_date (YYYY-MM-DD), and location if provided in user context; omit or pass empty strings to return all matching events.")
async def get_events_by_type(event_type: str, from_date: str = "", to_date: str = "", location: str = "") -> str:
    """Get available events for a given event type filtered by date range and location. Use from_date, to_date, and location from the user context if available, otherwise omit them."""
    events = load_json("events.json")
    results = []
    for event in events:
        if event_type.lower() not in event["type"].lower():
            continue
        filtered_details = [
            d for d in event["details"]
            if matches_date(d["date"], from_date, to_date)
            and matches_location(location, d["city"], d["country"])
        ]
        if filtered_details:
            results.append({**event, "details": filtered_details})
    if results:
        return json.dumps(results)
    return json.dumps({"error": f"No events found for type '{event_type}'"})

@event_mcp.tool(name="get_seats", description="Get available seats for an event, optionally filtered by tier (Front, Middle, Back).")
async def get_seats(event_id: str, tier: str = None) -> str:
    """Get seats for a given event ID. Optionally filter by tier (Front, Middle, Back)."""
    all_seats = _get_seats()
    event_seats = next((s for s in all_seats if s["event_id"] == event_id), None)
    if not event_seats:
        return json.dumps({"error": f"No seats found for event '{event_id}'"})
    rows = event_seats["section"]["rows"]
    rows = [r for r in rows if r.get("status") == "available"]
    if tier:
        rows = [r for r in rows if r["tier"].lower() == tier.lower()]
    if not rows:
        return json.dumps({"error": f"No seats found for tier '{tier}' on event '{event_id}'"})
    return json.dumps({
        "event_id": event_seats["event_id"],
        "section": {
            "id": event_seats["section"]["id"],
            "rows": rows,
        },
    })

@event_mcp.tool(name="get_addons", description="Get all available add-ons and upgrades for an event booking. Returns items grouped by category: access (VIP lounge, parking, meet & greet), food, beverage, merch (merchandise), and insurance. Optionally filter by category.")
async def get_addons(category: str = None) -> str:
    """Get available add-ons, optionally filtered by category (access, food, beverage, merch, insurance)."""
    addons = load_json("addons.json")
    if category:
        addons = [a for a in addons if a["category"].lower() == category.lower()]
        if not addons:
            return json.dumps({"error": f"No add-ons found for category '{category}'"})
    return json.dumps(addons)

@event_mcp.tool(name="get_fees", description="Get all applicable fees for a specific event by its ID. Fees include service fee, convenience fee, facility fee, and sales tax with descriptions of how each is calculated.")
async def get_fees(event_id: str) -> str:
    """Get all fees applicable to the given event_id."""
    fees = load_json("fees.json")
    result = next((f for f in fees if f["event_id"] == event_id), None)
    if result:
        return json.dumps(result)
    return json.dumps({"error": f"No fees found for event_id {event_id}"})

if __name__ == "__main__":
    event_mcp.run()
