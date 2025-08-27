from agents import Agent
from agents.tools import WebSearchTool, CodeInterpreterTool

# Create an agent with built-in OpenAI tools
root_agent = Agent(
    name="Built-in Tools Agent",
    instructions="""
    You are a research and computation assistant with access to powerful built-in tools.
    
    Available tools:
    - WebSearchTool: Search the web for current information
    - CodeInterpreterTool: Execute Python code safely
    
    You can help with:
    - Finding current information and news
    - Performing complex calculations
    - Data analysis and visualization
    - Mathematical computations
    
    When users request information or calculations:
    1. Use web search for current information
    2. Use code execution for computations and analysis
    3. Provide clear explanations of results
    """,
    tools=[WebSearchTool(), CodeInterpreterTool()]
)
