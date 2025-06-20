from config.logger import logger_hook
from typing import Optional
from agno.tools import tool
from models.flight import FlightSearchRequest
from loguru import logger

@tool(
    name="kayak_flight_url_generator",
    show_result=True,
    tool_hooks=[logger_hook]
)
def kayak_flight_url_generator(
    departure: str, destination: str, date: str, return_date: Optional[str] = None, adults: int = 1, children: int = 0, cabin_class: Optional[str] = None, sort: str = "best"
) -> str:
    """
    Generates a Kayak URL for flights between departure and destination on the specified date.

    :param departure: The IATA code for the departure airport (e.g., 'SOF' for Sofia)
    :param destination: The IATA code for the destination airport (e.g., 'BER' for Berlin)
    :param date: The date of the flight in the format 'YYYY-MM-DD'
    :return_date: Only for two-way tickets. The date of return flight in the format 'YYYY-MM-DD'
    :param adults: The number of adults (default 1)
    :param children: The number of children (default 0)
    :param cabin_class: The cabin class (first, business, premium, economy)
    :param sort: The sort order (best, cheapest)
    :return: The Kayak URL for the flight search
    """
    request = FlightSearchRequest(
        departure=departure,
        destination=destination,
        date=date,
        return_date=return_date,
        adults=adults,
        children=children,
        cabin_class=cabin_class,
        sort=sort)

    logger.info(f"Request: {request}")

    logger.info(f"Generating Kayak URL for {departure} to {destination} on {date}")
    URL = f"https://www.kayak.com/flights/{departure}-{destination}/{date}"
    if return_date:
        URL += f"/{return_date}"
    if cabin_class and cabin_class.lower() != "economy":
        URL += f"/{cabin_class.lower()}"
    URL += f"/{adults}adults"
    if children > 0:
        URL += f"/children"
        for _ in range(children):
            URL += "-11"


    URL += "?currency=USD"
    if sort.lower() == "cheapest":
        URL += "&sort=price_a"
    elif sort.lower() == "best":
        URL += "&sort=bestflight_a"
    logger.info(f"URL: {URL}")
    return URL
