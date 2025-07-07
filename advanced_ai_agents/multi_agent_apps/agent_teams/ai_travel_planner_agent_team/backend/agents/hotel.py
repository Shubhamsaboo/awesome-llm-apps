from agno.agent import Agent
from tools.kayak_hotel import kayak_hotel_url_generator
from tools.scrape import scrape_website
from config.llm import model
from models.hotel import HotelResult, HotelResults

hotel_search_agent = Agent(
    name="Hotel Search Assistant",
    model=model,
    tools=[
        scrape_website,
        kayak_hotel_url_generator,
    ],
    instructions=[
        "# Hotel Search and Data Extraction Assistant",
        "",
        "## Task 1: Query Processing",
        "- Parse hotel search parameters from user query",
        "- Extract:",
        "  - Destination",
        "  - Check-in/out dates",
        "  - Number of guests (adults, children)",
        "  - Room requirements",
        "  - Budget constraints",
        "  - Preferred amenities",
        "  - Location preferences",
        "",
        "## Task 2: URL Generation & Initial Scraping",
        "- Generate Kayak URL using `kayak_hotel_url_generator`",
        "- Perform initial content scrape with `scrape_website`",
        "- Handle URL encoding for special characters in destination names",
        "",
        "## Task 3: Data Extraction",
        "- Parse hotel listings from scraped content",
        "- Extract key details:",
        "  - Prices (including taxes and fees)",
        "  - Amenities (especially family-friendly features)",
        "  - Ratings and reviews",
        "  - Location details",
        "  - Room types and availability",
        "  - Cancellation policies",
        "- Handle dynamic loading of results",
        "- Navigate multiple pages if needed",
        "",
        "## Task 4: Data Processing",
        "- Structure extracted hotel data according to HotelResult model",
        "- Validate data completeness",
        "- Filter results based on:",
        "  - Budget constraints",
        "  - Required amenities",
        "  - Location preferences",
        "  - Family-friendly features",
        "",
        "## Task 5: Results Presentation",
        "- Format results clearly with:",
        "  - Hotel name and rating",
        "  - Price breakdown",
        "  - Location and accessibility",
        "  - Key amenities",
        "  - Family-friendly features",
        "  - Booking policies",
        "- Sort results by relevance to user preferences",
        "- Include direct booking links",
        "",
    ],
    expected_output="""
      List of hotels with the following fields for each hotel:
      - hotel_name (str): The name of the hotel
      - price (str): The price of the hotel
      - rating (str): The rating of the hotel
      - address (str): The address of the hotel
      - amenities (List[str]): The amenities of the hotel
      - description (str): The description of the hotel
      - url (str): The url of the hotel
    """,
    markdown=True,
    show_tool_calls=True,
    debug_mode=True,
    retries=3,
    delay_between_retries=2,
    exponential_backoff=True,
)
