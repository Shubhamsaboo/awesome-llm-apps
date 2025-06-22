from config.logger import logger_hook
from typing import Optional
from agno.tools import tool
from models.hotel import HotelSearchRequest
from loguru import logger

@tool(
    name="kayak_hotel_url_generator",
    show_result=True,
    tool_hooks=[logger_hook]
)
def kayak_hotel_url_generator(
    destination: str, check_in: str, check_out: str, adults: int = 1, children: int = 0, rooms: int = 1, sort: str = "recommended"
) -> str:
    """
    Generates a Kayak URL for hotels in the specified destination between check_in and check_out dates.

    :param destination: The destination city or area (e.g. "Berlin", "City Center, Singapore", "Red Fort, Delhi")
    :param check_in: The date of check-in in the format 'YYYY-MM-DD'
    :param check_out: The date of check-out in the format 'YYYY-MM-DD'
    :param adults: The number of adults (default 1)
    :param children: The number of children (default 0)
    :param rooms: The number of rooms (default 1)
    :param sort: The sort order (recommended, distance, price, rating)
    :return: The Kayak URL for the hotel search
    """
    request = HotelSearchRequest(
        destination=destination,
        check_in=check_in,
        check_out=check_out,
        adults=adults,
        children=children,
        rooms=rooms,
        sort=sort)

    logger.info(f"Request: {request}")

    logger.info(f"Generating Kayak URL for {destination} on {check_in} to {check_out}")
    URL = f"https://www.kayak.com/hotels/{destination}/{check_in}/{check_out}"
    URL += f"/{adults}adults"
    if children > 0:
        URL += f"/{children}children"

    if rooms > 1:
        URL += f"/{rooms}rooms"


    URL += "?currency=USD"
    if sort.lower() == "price":
        URL += "&sort=price_a"
    elif sort.lower() == "rating":
        URL += "&sort=userrating_b"
    elif sort.lower() == "distance":
        URL += "&sort=distance_a"
    logger.info(f"URL: {URL}")
    return URL
