import asyncio
import os
import streamlit as st
from textwrap import dedent
from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Page config
st.set_page_config(page_title="🐙 GitHub MCP Agent", page_icon="🐙", layout="wide")

# Title and description
st.markdown("<h1 class='main-header'>🐙 GitHub MCP Agent</h1>", unsafe_allow_html=True)
st.markdown("Explore GitHub repositories with natural language using the Model Context Protocol")

# Setup sidebar for API key
with st.sidebar:
    st.header("🔑 Authentication")
    github_token = st.text_input("GitHub Token", type="password", 
                                help="Create a token with repo scope at github.com/settings/tokens")
    
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token
    
    st.markdown("---")
    st.markdown("### Example Queries")
    
    st.markdown("**Issues**")
    st.markdown("- Show me issues by label")
    st.markdown("- What issues are being actively discussed?")
    
    st.markdown("**Pull Requests**")
    st.markdown("- What PRs need review?")
    st.markdown("- Show me recent merged PRs")
    
    st.markdown("**Repository**")
    st.markdown("- Show repository health metrics")
    st.markdown("- Show repository activity patterns")
    
    st.markdown("---")
    st.caption("Note: Always specify the repository in your query if not already selected in the main input.")

# Query input
col1, col2 = st.columns([3, 1])
with col1:
    repo = st.text_input("Repository", value="Shubhamsaboo/awesome-llm-apps", help="Format: owner/repo")
with col2:
    query_type = st.selectbox("Query Type", [
        "Issues", "Pull Requests", "Repository Activity", "Custom"
    ])

# Create predefined queries based on type
if query_type == "Issues":
    query_template = f"Find issues labeled as bugs in {repo}"
elif query_type == "Pull Requests":
    query_template = f"Show me recent merged PRs in {repo}"
elif query_type == "Repository Activity":
    query_template = f"Analyze code quality trends in {repo}"
else:
    query_template = ""

query = st.text_area("Your Query", value=query_template, 
                     placeholder="What would you like to know about this repository?")

# Main function to run agent
async def run_github_agent(message):
    if not os.getenv("GITHUB_TOKEN"):
        return "Error: GitHub token not provided"
    
    try:
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
        )
        
        # Create client session
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize MCP toolkit
                mcp_tools = MCPTools(session=session)
                await mcp_tools.initialize()
                
                # Create agent
                agent = Agent(
                    tools=[mcp_tools],
                    instructions=dedent("""\
                        You are a GitHub assistant. Help users explore repositories and their activity.
                        - Provide organized, concise insights about the repository
                        - Focus on facts and data from the GitHub API
                        - Use markdown formatting for better readability
                        - Present numerical data in tables when appropriate
                        - Include links to relevant GitHub pages when helpful
                    """),
                    markdown=True,
                    show_tool_calls=True,
                )
                
                # Run agent
                response = await agent.arun(message)
                return response.content
    except Exception as e:
        return f"Error: {str(e)}"

# Run button
if st.button("🚀 Run Query", type="primary", use_container_width=True):
    if not github_token:
        st.error("Please enter your GitHub token in the sidebar")
    elif not query:
        st.error("Please enter a query")
    else:
        with st.spinner("Analyzing GitHub repository..."):
            # Ensure the repository is explicitly mentioned in the query
            if repo and repo not in query:
                full_query = f"{query} in {repo}"
            else:
                full_query = query
                
            result = asyncio.run(run_github_agent(full_query))
        
        # Display results in a nice container
        st.markdown("### Results")
        st.markdown(result)

# Display help text for first-time users
if 'result' not in locals():
    st.markdown(
        """<div class='info-box'>
        <h4>How to use this app:</h4>
        <ol>
            <li>Enter your GitHub token in the sidebar</li>
            <li>Specify a repository (e.g., Shubhamsaboo/awesome-llm-apps)</li>
            <li>Select a query type or write your own</li>
            <li>Click 'Run Query' to see results</li>
        </ol>
        <p><strong>Important Notes:</strong></p>
        <ul>
            <li>The Model Context Protocol (MCP) provides real-time access to GitHub repositories</li>
            <li>Queries work best when they focus on specific aspects like issues, PRs, or repository info</li>
            <li>More specific queries yield better results</li>
            <li>This app requires Node.js to be installed (for the npx command)</li>
        </ul>
        </div>""", 
        unsafe_allow_html=True
    )

# Footer
st.markdown("---")
st.write("Built with Streamlit, Agno, and Model Context Protocol ❤️")