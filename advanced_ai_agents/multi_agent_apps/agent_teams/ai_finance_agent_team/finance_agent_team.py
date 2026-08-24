from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.server import Server

# Setup database for storage
db = SqliteDb(db_file="agents.db")

web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    db=db,
    add_history_to_context=True,
    markdown=True,
)

finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools(include_tools=["get_current_stock_price", "get_analyst_recommendations", "get_company_info", "get_company_news"])],
    instructions=["Always use tables to display data"],
    db=db,
    add_history_to_context=True,
    markdown=True,
)

agent_team = Team(
    name="Agent Team (Web+Finance)",
    model=OpenAIChat(id="gpt-4o"),
    members=[web_agent, finance_agent],
    debug_mode=True,
    markdown=True,
)

# agent_os = AgentOS(teams=[agent_team])
# app = agent_os.get_app()

if __name__ == "__main__":
    Server.serve(app_name="finance_agent_team:app", agents=[agent_team], reload=True)
