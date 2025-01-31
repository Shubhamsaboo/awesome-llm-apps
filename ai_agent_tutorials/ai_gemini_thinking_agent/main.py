from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
import os
from dotenv import load_dotenv
load_dotenv()

thinking_agent = Agent(
    name="Thinking Agent",
    role="Think about the problem",
    model=Gemini(id="gemini-2.0-flash-thinking-exp-1219", api_key=os.getenv("GOOGLE_API_KEY")),
    instructions="Given the problem, think about it and provide a detailed explanation",
    show_tool_calls=True,
    markdown=True,
)


thinking_agent.print_response("Explain Deep Q Networks from first principles", stream=True)