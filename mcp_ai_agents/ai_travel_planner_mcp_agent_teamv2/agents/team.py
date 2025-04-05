from agents.booking import BookingAgent
from agents.reviews import ReviewsAgent
from agents.calendar_agent import CalendarAgent
from agents.weather import WeatherAgent
from agents.maps import MapsAgent

from agno.agent import Agent
from agno.team import Team

class TravelTeam(Team):
    def __init__(self):
        super().__init__(
            members=[
                MapsAgent(),
                WeatherAgent(),
                BookingAgent(),
                ReviewsAgent(),
                CalendarAgent()
            ],
            name="TravelTeam",
            description="A team that handles travel-related queries using Maps and Weather agents.",
        )

    def on_agent_selected(self, agent: Agent, user_input: str):
        print(f"\n🧠 [INFO] Agent selected for this query: {agent.__class__.__name__}")