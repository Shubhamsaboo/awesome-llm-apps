from pydantic import BaseModel, Field
from typing import List
from models.hotel import HotelResult


class TravelDates(BaseModel):
    start: str = ""
    end: str = ""


class TravelPlanRequest(BaseModel):
    name: str = ""
    destination: str = ""
    starting_location: str = ""
    travel_dates: TravelDates = TravelDates()
    date_input_type: str = "picker"
    duration: int = 0
    traveling_with: str = ""
    adults: int = 1
    children: int = 0
    age_groups: List[str] = []
    budget: int = 75000
    budget_currency: str = "INR"
    travel_style: str = ""
    budget_flexible: bool = False
    vibes: List[str] = []
    priorities: List[str] = []
    interests: str = ""
    rooms: int = 1
    pace: List[int] = [3]
    been_there_before: str = ""
    loved_places: str = ""
    additional_info: str = ""


class TravelPlanAgentRequest(BaseModel):
    trip_plan_id: str
    travel_plan: TravelPlanRequest


class TravelPlanResponse(BaseModel):
    success: bool
    message: str
    trip_plan_id: str


class DayByDayPlan(BaseModel):
    day: int = Field(
        default=0, description="The day number in the itinerary, starting from 0"
    )
    date: str = Field(
        default="", description="The date for this day in YYYY-MM-DD format"
    )
    morning: str = Field(
        default="", description="Description of morning activities and plans"
    )
    afternoon: str = Field(
        default="", description="Description of afternoon activities and plans"
    )
    evening: str = Field(
        default="", description="Description of evening activities and plans"
    )
    notes: str = Field(
        default="",
        description="Additional tips, reminders or important information for the day",
    )


class Attraction(BaseModel):
    name: str = Field(default="", description="Name of the attraction")
    description: str = Field(
        default="", description="Detailed description of the attraction"
    )


class FlightResult(BaseModel):
    duration: str = Field(default="", description="Duration of the flight")
    price: str = Field(
        default="", description="Price of the flight in the local currency"
    )
    departure_time: str = Field(default="", description="Departure time of the flight")
    arrival_time: str = Field(default="", description="Arrival time of the flight")
    airline: str = Field(default="", description="Airline of the flight")
    flight_number: str = Field(default="", description="Flight number of the flight")
    url: str = Field(default="", description="Website or booking URL for the flight")
    stops: int = Field(default=0, description="Number of stops in the flight")


class RestaurantResult(BaseModel):
    name: str = Field(default="", description="Name of the restaurant")
    description: str = Field(default="", description="Description of the restaurant")
    location: str = Field(default="", description="Location of the restaurant")
    url: str = Field(
        default="", description="Website or booking URL for the restaurant"
    )


class TravelPlanTeamResponse(BaseModel):
    day_by_day_plan: List[DayByDayPlan] = Field(
        description="A list of day-by-day plans for the trip"
    )
    hotels: List[HotelResult] = Field(description="A list of hotels for the trip")
    attractions: List[Attraction] = Field(
        description="A list of recommended attractions for the trip"
    )
    flights: List[FlightResult] = Field(description="A list of flights for the trip")
    restaurants: List[RestaurantResult] = Field(
        description="A list of recommended restaurants for the trip"
    )
    budget_insights: List[str] = Field(
        description="A list of budget insights for the trip"
    )
    tips: List[str] = Field(
        description="A list of tips or recommendations for the trip"
    )
