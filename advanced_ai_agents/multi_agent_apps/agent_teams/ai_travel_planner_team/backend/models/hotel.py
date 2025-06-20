from pydantic import BaseModel, Field
from typing import List

class HotelResult(BaseModel):
    hotel_name: str = Field(description="The name of the hotel")
    price: str = Field(description="The price of the hotel")
    rating: str = Field(description="The rating of the hotel")
    address: str = Field(description="The address of the hotel")
    amenities: List[str] = Field(description="The amenities of the hotel")
    description: str = Field(description="The description of the hotel")
    url: str = Field(description="The url of the hotel")

class HotelResults(BaseModel):
    hotels: List[HotelResult] = Field(description="The list of hotels")

class HotelSearchRequest(BaseModel):
    destination: str = Field(description="The destination city or area")
    check_in: str = Field(description="The date of check-in in the format 'YYYY-MM-DD'")
    check_out: str = Field(description="The date of check-out in the format 'YYYY-MM-DD'")
    adults: int = Field(description="The number of adults")
    children: int = Field(description="The number of children")
    rooms: int = Field(description="The number of rooms")
    sort: str = Field(description="The sort order")