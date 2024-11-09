# import necessary python libraries
from phi.agent import Agent
from phi.model.xai import xAI
from phi.tools.yfinance import YFinanceTools
from phi.tools.duckduckgo import DuckDuckGo
from phi.playground import Playground, serve_playground_app

# create the AI finance agent
agent = Agent(
    name="xAI Finance Agent",
    model = xAI(id="grok-beta"),
    tools=[DuckDuckGo(), YFinanceTools(stock_price=True, analyst_recommendations=True, stock_fundamentals=True)],
    instructions = ["Always use tables to display financial/numerical data. For text data use bullet points and small paragrpahs."],
    show_tool_calls = True,
    markdown = True,
    )

# UI for finance agent
app = Playground(agents=[agent]).get_app()

if __name__ == "__main__":
    serve_playground_app("xai_finance_agent:app", reload=True)