# import necessary python libraries
from agno.agent import Agent
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.os import AgentOS

# create the AI finance agent
agent = Agent(
    name="xAI Finance Agent",
    model = xAI(id="grok-4-1-fast"),
    tools=[DuckDuckGoTools(), YFinanceTools()],
    instructions = ["Always use tables to display financial/numerical data. For text data use bullet points and small paragrpahs."],
    debug_mode = True,
    markdown = True,
    )

# UI for finance agent
agent_os = AgentOS(agents=[agent])
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="xai_finance_agent:app", reload=True)