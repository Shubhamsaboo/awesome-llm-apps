

from config.logger import setup_logging
setup_logging(console_level="INFO")
from loguru import logger

logger.info("Starting the application")
logger.info("Loading environment variables")
from dotenv import load_dotenv
load_dotenv()
logger.info("Loaded environment variables")

logger.info("Loading agents")
from agents.flight import flight_search_agent
from agents.hotel import hotel_search_agent
logger.info("Loaded agents")

# structured_output_agent = Agent(
#     name="Structured Output Generator",
#     model=model2,
#     instructions="Generate structured output in the specified schema format. Parse input data and format according to schema requirements. DO NOT include any other text in your response.",
#     expected_output=dedent("""\
#            A JSON object with the following fields:
#       - status (str): Success or error status of the request (success or error)
#       - message (str): Status message or error description
#       - data: Object containing the flight results
#         - flights: A list of flight results
#           Each flight has the following fields:
#             - flight_number (str): The flight number of the flight
#             - price (str): The price of the flight
#             - airline (str): The airline of the flight
#             - departure_time (str): The departure time of the flight
#             - arrival_time (str): The arrival time of the flight
#             - duration (str): The duration of the flight
#             - stops (int): The number of stops of the flight

#     **DO NOT include any other text in your response.**
#         }"""),
#     markdown=True,
#     show_tool_calls=True,
#     debug_mode=True,
#     response_model=FlightResults,
# )

# response = flight_search_agent.run("""
#     Give me flights from Mumbai to Singapore for premium economy on 1 july 2025 for 2 adults and 1 child and sort by cheapest
# """)

# print(response.content)

response = hotel_search_agent.run("""
    Give me hotels in Singapore for 2 adults and 1 child on 1 july 2025 to 10 july 2025 and sort by cheapest
""")

print(response.content)