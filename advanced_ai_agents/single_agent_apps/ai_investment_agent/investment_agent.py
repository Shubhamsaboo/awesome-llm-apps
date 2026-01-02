# import necessary python libraries
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.yfinance import YFinanceTools
from agno.os import AgentOS

# create the AI investment agent
agent = Agent(
    name="AI Investment Agent",
    model=OpenAIChat(id="gpt-5.2-2025-12-11"),
    tools=[YFinanceTools()],
    description="You are an investment analyst that researches stock prices, analyst recommendations, and stock fundamentals.",
    instructions=[
        "Format your response using markdown and use tables to display data where possible.",
        "When comparing stocks, provide detailed analysis including price trends, fundamentals, and analyst recommendations.",
        "Always provide actionable insights for investors."
    ],
    debug_mode=True,
    markdown=True,
)

# UI for investment agent using AgentOS
agent_os = AgentOS(agents=[agent])
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="investment_agent:app", reload=True)
