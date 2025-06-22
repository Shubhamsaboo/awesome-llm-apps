from pydantic import BaseModel, Field
from typing import List, Optional

class FlightResult(BaseModel):
    flight_number: str = Field(description="The flight number of the flight")
    price: str = Field(description="The price of the flight")
    airline: str = Field(description="The airline of the flight")
    departure_time: str = Field(description="The departure time of the flight")
    arrival_time: str = Field(description="The arrival time of the flight")
    duration: str = Field(description="The duration of the flight")
    stops: int = Field(description="The number of stops of the flight")

class FlightResults(BaseModel):
    flights: List[FlightResult] = Field(description="The list of flights")

class FlightSearchRequest(BaseModel):
    departure: str = Field(description="The departure airport")
    destination: str = Field(description="The destination airport")
    date: str = Field(description="The date of the flight")
    return_date: Optional[str] = Field(description="The return date of the flight")
    adults: int = Field(description="The number of adults")
    children: int = Field(description="The number of children")
    cabin_class: str = Field(description="The cabin class")
    sort: str = Field(description="The sort order")