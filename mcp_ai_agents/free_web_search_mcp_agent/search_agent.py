import asyncio
import os
import streamlit as st
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

st.set_page_config(page_title="🔍 Free Web Search MCP Agent", page_icon="🔍", layout="wide")
st.markdown("<h1 class='main-header'>🔍 Free Web Search MCP Agent</h1>", unsafe_allow_html=True)
st.markdown("A Search-First LLM Agent that uses DuckDuckGo for free, real-time web searches via Model Context Protocol.")

with st.sidebar:
    st.header("🔑 Authentication")
    
    openai_key = st.text_input("OpenAI API Key", type="password",
                              help="Required for the AI agent to interpret queries and format results. The search itself is 100% free.")
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key
    
    st.markdown("---")
    st.markdown("### How it works")
    st.markdown(
        "This agent uses the **Search-First Paradigm**: it is explicitly instructed to "
        "*always* search the web before answering, rather than relying on its internal training data."
    )
    st.markdown(
        "It uses the `free-web-search-mcp` server which provides two tools:\n"
        "1. `search_web`: Queries DuckDuckGo\n"
        "2. `visit_page`: Extracts markdown from URLs"
    )
    
    st.markdown("---")
    st.markdown("### Example Queries")
    st.markdown("- What are the latest developments in AI this week?")
    st.markdown("- What is the current stock price of Apple?")
    st.markdown("- Summarize the latest news about SpaceX")

query = st.text_area("What would you like to know?", 
                    value="What are the latest developments in AI this week?",
                    help="Ask any question that requires up-to-date knowledge")

async def run_search_agent(query: str):
    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please enter your OpenAI API Key in the sidebar.")
        return

    with st.spinner("Connecting to Free Web Search MCP server..."):
        try:
            # Initialize MCP Tools with the free-web-search-mcp server
            mcp_tools = MCPTools(
                server_parameters=StdioServerParameters(
                    command="free-web-search-mcp",
                    args=[]
                )
            )
            
            # Create the Agent with Search-First instructions
            agent = Agent(
                model=OpenAIChat(id="gpt-4o"),
                tools=[mcp_tools],
                show_tool_calls=True,
                instructions=dedent("""\
                    You are a Search-First AI Assistant. You MUST follow these rules:
                    
                    1. BEHAVIORAL OVERRIDE: You must NEVER rely solely on your internal training data for factual, real-world, or time-sensitive questions.
                    2. ALWAYS search the web first using the 'search_web' tool before formulating an answer.
                    3. If the search results contain interesting URLs, use the 'visit_page' tool to read the full content.
                    4. Synthesize the information gathered from the web to provide a comprehensive, accurate, and up-to-date answer.
                    5. ALWAYS cite your sources by including the URLs you visited or found in the search results.
                """)
            )
            
            st.success("Connected to MCP server successfully!")
            
            with st.spinner("Agent is searching and thinking..."):
                # Run the agent and get the response
                response = agent.run(query)
                return response.content
                
        except Exception as e:
            st.error(f"Error running agent: {str(e)}")
            st.info("Make sure you have installed the server: `pip install free-web-search-ultimate`")
            return None

if st.button("Search & Answer", type="primary"):
    if query:
        # Run the async function using asyncio
        result = asyncio.run(run_search_agent(query))
        
        if result:
            st.markdown("### Result")
            st.markdown(result)
    else:
        st.warning("Please enter a query.")
