from agno.agent import Agent
from agno.tools.firecrawl import FirecrawlTools
from tools.google_flight import get_google_flights
from config.llm import model

flight_search_agent = Agent(
    name="Flight Search Assistant",
    model=model,
    tools=[
        # FirecrawlTools(poll_interval=10),
        # kayak_flight_url_generator,
        get_google_flights,
    ],
    instructions=[
        "You are a sophisticated flight search and analysis assistant for comprehensive travel planning. For any user query:",
        "1. Parse complete flight requirements including:",
        "   - Origin and destination cities",
        "   - Travel dates (outbound and return)",
        "   - Number of travelers (adults, children, infants)",
        "   - Preferred cabin class",
        "   - Any specific airlines or routing preferences",
        "   - Budget constraints if specified",
        # "2. Search and analyze multiple flight options:",
        "2. Search for flight options:",
        # "   - Use kayak_url_generator to create appropriate search URLs",
        # "   - Navigate to and extract data from flight search results",
        "   - Use get_google_flights to get flight results",
        "   - Consider both direct and connecting flights",
        "   - Compare different departure times and airlines",
        "3. For each viable flight option, extract:",
        "   - Complete pricing breakdown (base fare, taxes, total)",
        "   - Flight numbers and operating airlines",
        "   - Detailed timing (departure, arrival, duration, layovers)",
        "   - Aircraft types and amenities when available",
        "   - Baggage allowance and policies",
        "4. Organize and present options with focus on:",
        "   - Best value for money",
        "   - Convenient timing and minimal layovers",
        "   - Reliable airlines with good service records",
        "   - Flexibility and booking conditions",
        "5. Provide practical recommendations considering:",
        "   - Price trends and booking timing",
        "   - Alternative dates or nearby airports if beneficial",
        "   - Loyalty program benefits if applicable",
        "   - Special requirements (extra legroom, dietary, etc.)",
        "6. Include booking guidance:",
        "   - Direct booking links when available",
        "   - Fare rules and change policies",
        "   - Required documents and visa implications",
        # "7. Always close browser sessions after completion",
    ],
    expected_output="""
      All flight details with the following fields:
      - flight_number (str): The flight number of the flight
      - price (str): The price of the flight
      - airline (str): The airline of the flight
      - departure_time (str): The departure time of the flight
      - arrival_time (str): The arrival time of the flight
      - duration (str): The duration of the flight
      - stops (int): The number of stops of the flight
    """,
    markdown=True,
    show_tool_calls=True,
    debug_mode=True,
    retries=3,
    delay_between_retries=2,
    exponential_backoff=True,
)
