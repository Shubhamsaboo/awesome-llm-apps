from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
import os
from dotenv import load_dotenv
load_dotenv()

vision_agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp", api_key=os.getenv("GEMINI_API_KEY")),
    markdown=True,
)

coding_agent = Agent(
    model=OpenAIChat(id="o3-mini", api_key=os.getenv("OPENAI_API_KEY")),
    markdown=True
)

# Print the response in the terminal
coding_agent.print_response("Share a 2 sentence horror story.")

