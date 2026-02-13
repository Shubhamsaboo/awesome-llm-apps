import asyncio
import os
from pathlib import Path
from textwrap import dedent

import streamlit as st
from agno.agent import Agent
from agno.run.agent import RunOutput
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="🧠 MemoV Coding History Agent",
    page_icon="🧠",
    layout="wide",
)

st.markdown("# 🧠 Chat with Your Coding History")
st.markdown("Query your local coding history via **MemoV MCP Server** using natural language.")

with st.sidebar:
    st.header("🔑 Configuration")

    openai_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Required for the AI agent to interpret queries"
    )
    if openai_key:
        os.environ["OPENAI_API_KEY"] = openai_key

    project_path = st.text_input(
        "Project Path",
        value=str(Path.cwd()),
        help="Path to your Git repository with MemoV initialized"
    )

    st.markdown("---")
    st.markdown("### Example Queries")
    st.markdown("**History**")
    st.markdown("- Show me the last 10 snapshots")
    st.markdown("- What files did I modify recently?")

    st.markdown("**Search**")
    st.markdown("- Find authentication patterns")
    st.markdown("- Search for database migrations")

    st.markdown("**Specific**")
    st.markdown("- Show details for commit abc123")
    st.markdown("- What changed in the last week?")

query_type = st.selectbox(
    "Quick Actions",
    ["Custom Query", "Browse History", "Semantic Search", "Recent Changes"]
)

if query_type == "Browse History":
    query_template = "Show me the last 10 coding snapshots with details"
elif query_type == "Semantic Search":
    query_template = "Search for: [describe what you're looking for]"
elif query_type == "Recent Changes":
    query_template = "What files were changed recently?"
else:
    query_template = ""

query = st.text_area(
    "Your Query",
    value=query_template,
    placeholder="Ask about your coding history...",
    height=120
)


async def run_memov_agent(message: str, proj_path: str) -> str:
    """Run MemoV agent using real MCP server via stdio from remote Git repo"""

    if not os.getenv("OPENAI_API_KEY"):
        return "❌ Error: OpenAI API key not provided"

    if not Path(proj_path).exists():
        return f"❌ Error: Project path does not exist: {proj_path}"

    if not (Path(proj_path) / ".git").exists():
        return f"❌ Error: Not a Git repository: {proj_path}"

    try:
        # Reference: https://github.com/memovai/memov
        server_params = StdioServerParameters(
            command="uvx",
            args=[
                "--from",
                "git+https://github.com/memovai/memov.git",
                "mem-mcp-launcher",
                "stdio",
                proj_path,
            ],
            env=os.environ.copy()
        )

        st.info("🚀 Starting MemoV MCP server from GitHub (first run may take a moment to install)...")

        async with MCPTools(server_params=server_params, timeout_seconds=120) as mcp_tools:
            st.success("✅ Connected to MemoV MCP server!")

            agent = Agent(
                name="MemoV Coding History Agent",
                model="openai:gpt-4o-mini",
                tools=[mcp_tools],
                instructions=dedent(f"""\
                    You are a developer assistant that queries coding history using MemoV MCP tools.

                    Project: {proj_path}

                    Available MCP tools:
                    - mem_history(limit, commit_hash): View memov history with prompts and file changes
                    - vibe_search(query, limit): Semantic search through code (requires ChromaDB)
                    - snap(...): Record interactions (for internal use)

                    CRITICAL INSTRUCTIONS:
                    1. ALWAYS use mem_history or vibe_search to answer - DO NOT make up data
                    2. When asked for history/snapshots, IMMEDIATELY call mem_history(limit=...)
                    3. When asked to search code, call vibe_search(query=..., limit=...)
                    4. Display the EXACT data returned by tools without modification
                    5. Format output clearly with markdown
                    6. If a tool returns an error, show it to the user

                    These tools connect to REAL Git data. Never fabricate commits or changes.
                """),
                markdown=True,
                debug_mode=True,
            )

            st.info("🤖 Running agent query...")

            response: RunOutput = await asyncio.wait_for(
                agent.arun(message),
                timeout=120.0
            )

            return response.content

    except asyncio.TimeoutError:
        return "❌ Error: Request timed out after 120 seconds"
    except FileNotFoundError as e:
        return dedent(f"""\
            ❌ Error: Could not find uvx

            Please install uv first:
            ```bash
            # macOS/Linux
            curl -LsSf https://astral.sh/uv/install.sh | sh

            # Or with pip
            pip install uv
            ```

            Details: {str(e)}
        """)
    except Exception as e:
        import traceback
        error_msg = str(e)

        # Check for common errors
        if "Memov not initialized" in error_msg or "mem init" in error_msg:
            return dedent(f"""\
                ❌ Error: MemoV not initialized in this project

                Please initialize MemoV first:
                ```bash
                cd {proj_path}

                # Install memov CLI (if not already installed)
                pip install git+https://github.com/memovai/memov.git

                # Initialize MemoV
                mem init

                # Track files
                mem track .
                ```

                Then try again!
            """)

        return dedent(f"""\
            ❌ Error: {error_msg}

            **Troubleshooting:**
            1. Ensure MemoV is initialized: `cd {proj_path} && mem init`
            2. Check that uvx is available: `uvx --version`
            3. Verify project has Git history: `git log`
            4. First run may take longer (installing from GitHub)

            **Technical details:**
            ```
            {traceback.format_exc()}
            ```
        """)


if st.button("🚀 Run Query", type="primary", use_container_width=True):
    if not openai_key:
        st.error("Please enter your OpenAI API key in the sidebar")
    elif not query:
        st.error("Please enter a query")
    else:
        with st.spinner("Querying your coding history via MCP..."):
            result = asyncio.run(run_memov_agent(query, project_path))

        st.markdown("### 📊 Results")
        st.markdown(result)

if 'result' not in locals():
    # Use Streamlit's native components instead of raw HTML
    with st.container():
        st.info("👋 **Welcome to MemoV Coding History Agent**")

        st.markdown("### 🎯 How to use:")
        st.markdown("""
1. Enter your **OpenAI API key** in the sidebar
2. Specify your **project path** (Git repo with MemoV initialized)
3. Select a quick action or write your custom query
4. Click '**Run Query**' to explore your coding history
        """)

        st.markdown("### 🚀 How it works:")
        st.markdown("""
- **Remote MCP Server**: Uses uvx to install and run memov from GitHub
- **MCP Protocol**: Agent calls actual MCP tools via stdio
- **Real Git Data**: All data comes from your actual repository
- **No Local Install Needed**: Server is fetched from `git+https://github.com/memovai/memov.git`
        """)

        st.markdown("### 📦 First Time Setup:")
        st.markdown("Install MemoV CLI and initialize in your project:")
        st.code("""# Install memov
pip install git+https://github.com/memovai/memov.git

# Initialize in your project
cd /path/to/your/project
mem init
mem track .""", language="bash")

        st.warning("**Note:** First run may take longer as the MCP server is installed from GitHub.")
