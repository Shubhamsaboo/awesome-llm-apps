import os
from dotenv import load_dotenv
from agents.maps import MapsAgent
from rich.console import Console
from rich.markdown import Markdown
from agents.team import TravelTeam

# Load environment variables from .env
load_dotenv()

console = Console()

def main():
    console.rule("[bold blue]🌍 AI Travel Planner is Running")
    maps_agent = MapsAgent()
    team = TravelTeam()

    while True:
        user_query = input("\n📝 Enter your travel query (or type 'exit' to quit): ")
        if user_query.lower() == "exit":
            console.print("[bold red]👋 Exiting Travel Planner. Safe travels!")
            break
        
        response = team.run(user_query)
        console.rule("[bold green] Travel Info")
        console.print(Markdown(response.content))
        console.rule()

if __name__ == "__main__":
    main()


