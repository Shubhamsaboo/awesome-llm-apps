from typing import Any
from agno.agent import Agent
from mcp.server.fastmcp import FastMCP
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from rich.console import Console

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("calendar")

# Rich console for styled output
console = Console()

# Get service account file path from environment
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
SCOPES = ["https://www.googleapis.com/auth/calendar"]

if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
    console.print("[bold red]❌ GOOGLE_CREDENTIALS_FILE not set or file not found. Please check your .env file.[/bold red]")
    exit(1)

# Initialize Google Calendar service
def get_calendar_service():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds)

class CalendarAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Calendar Agent",
            description="Manages travel schedules and blocks time using Google Calendar.",
            tools=[mcp],
            system_message="""
                You are CalendarAgent. Your job is to manage travel time and block schedules on Google Calendar.
                You will be given a summary, start time, end time, and timezone to create an event.

                Respond ONLY in the following format:

                ### 📅 Calendar Update:

                Event Summary: <summary>  
                Start Time: <start_time>  
                End Time: <end_time>  
                Timezone: <timezone>  
                Status: ✅ Event created or ❌ Failed

                Do not add any extra commentary.
            """
        )

    def run(self, query: str, **kwargs):
        console.rule(f"[bold green]📆 Running: {self.__class__.__name__}")
        return super().run(query, **kwargs)

@mcp.tool(name="Block Time on Calendar", description="Block a specific time on user's Google Calendar.")
def block_time_on_calendar(summary: str, start_time: str, end_time: str, timezone: str = "UTC") -> str:
    """Block time on Google Calendar."""
    try:
        service = get_calendar_service()
        event = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": timezone},
            "end": {"dateTime": end_time, "timeZone": timezone},
        }
        event_result = service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ Event created: {event_result.get('htmlLink')}"
    except Exception as e:
        return f"❌ Failed to create event: {str(e)}"

if __name__ == "__main__":
    import sys
    if "--server" in sys.argv:
        mcp.run(transport='stdio')
    else:
        console.print("[bold yellow]⚠️ To run the MCP server, use: python calendar_agent.py --server")
