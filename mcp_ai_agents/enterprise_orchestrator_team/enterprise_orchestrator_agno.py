import asyncio
import json
import os
import sys
import uuid
import streamlit as st
from typing import List, Optional, Dict
from textwrap import dedent
from agno.agent import Agent 
from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from agno.memory.v2 import Memory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
COMPOSIO_OPENAI_API_KEY = os.getenv("COMPOSIO_OPENAI_API_KEY")
COMPOSIO_NOTION_API_KEY = os.getenv("COMPOSIO_NOTION_API_KEY")
COMPOSIO_FIGMA_API_KEY = os.getenv("COMPOSIO_FIGMA_API_KEY")

# MCP Server URLs (SSE)
COMPOSIO_GITHUB_MCP_URL = os.getenv("COMPOSIO_GITHUB_MCP_URL")
COMPOSIO_NOTION_MCP_URL = os.getenv("COMPOSIO_NOTION_MCP_URL")
COMPOSIO_FIGMA_MCP_URL = os.getenv("COMPOSIO_FIGMA_MCP_URL")

async def create_mcp_tools():
    """Create separate MCP tools for different services"""
    
    mcp_tools = {}
    
    # GitHub MCP Tools
    if COMPOSIO_GITHUB_MCP_URL:
        try:
            github_mcp = MCPTools(transport="sse", url=COMPOSIO_GITHUB_MCP_URL)
            await github_mcp.connect()
            mcp_tools["github"] = github_mcp
            print("✅ GitHub MCP tools connected")
        except Exception as e:
            print(f"❌ Failed to connect GitHub MCP: {e}")
    
    # Notion MCP Tools
    if COMPOSIO_NOTION_MCP_URL:
        try:
            notion_mcp = MCPTools(transport="sse", url=COMPOSIO_NOTION_MCP_URL)
            await notion_mcp.connect()
            mcp_tools["notion"] = notion_mcp
            print("✅ Notion MCP tools connected")
        except Exception as e:
            print(f"❌ Failed to connect Notion MCP: {e}")
    
    # Figma MCP Tools
    if COMPOSIO_FIGMA_MCP_URL:
        try:
            figma_mcp = MCPTools(transport="sse", url=COMPOSIO_FIGMA_MCP_URL)
            await figma_mcp.connect()
            mcp_tools["figma"] = figma_mcp
            print("✅ Figma MCP tools connected")
        except Exception as e:
            print(f"❌ Failed to connect Figma MCP: {e}")
    
    return mcp_tools

def create_specialist_agents(llm, mcp_tools):
    """Create specialized agents for different domains"""
    
    # File Analysis Agent (using simple file operations)
    file_analysis_agent = Agent(
        name="FileAnalysisAgent",
        model=llm,
        description="Expert in file system operations and document analysis",
        instructions=dedent("""
            You are a File Analysis Expert. Your capabilities:
            
            📁 FILE OPERATIONS:
            - List files and directories
            - Read and analyze file contents
            - Create, modify, and delete files
            - Search for specific files and patterns
            - Get file metadata and properties
            
            🎯 YOUR ROLE:
            - Handle all file system related queries
            - Provide detailed file analysis
            - Organize and structure file information
            - Help with file management tasks
            
            IMPORTANT: Use simple file operations and provide clear, actionable responses.
            Always explain what you're doing and provide helpful context.
        """),
        tools=[],  # Will use simple file operations
        markdown=True,
        show_tool_calls=True
    )
    
    # GitHub Agent
    github_agent = Agent(
        name="GitHubAgent",
        model=llm,
        description="Expert in GitHub repository management and code operations",
        instructions=dedent("""
            You are a GitHub Expert. Your capabilities:
            
            🔧 REPOSITORY MANAGEMENT:
            - Create, clone, fork, and manage repositories
            - Handle issues, pull requests, and code reviews
            - Manage branches, releases, and deployments
            - Search code across repositories
            
            💻 CODE OPERATIONS:
            - Analyze code and suggest improvements
            - Handle version control workflows
            - Manage collaboration and team workflows
            - Code review and quality assurance
            
            🎯 YOUR ROLE:
            - Handle all GitHub related queries
            - Provide detailed repository analysis
            - Help with code management and collaboration
            - Suggest best practices and workflows
            
            IMPORTANT: Use GitHub MCP tools for all operations. Be proactive in suggesting improvements.
        """),
        tools=[mcp_tools.get("github")] if mcp_tools.get("github") else [],
        markdown=True,
        show_tool_calls=True
    )
    
    # Notion Agent
    notion_agent = Agent(
        name="NotionAgent",
        model=llm,
        description="Expert in Notion workspace management and content organization",
        instructions=dedent("""
            You are a Notion Expert. Your capabilities:
            
            📝 CONTENT MANAGEMENT:
            - Create and manage pages, databases, and workspaces
            - Organize content and knowledge bases
            - Handle project management and task tracking
            - Manage team collaboration and workflows
            
            🗂️ WORKSPACE ORGANIZATION:
            - Structure information effectively
            - Create templates and workflows
            - Manage permissions and access
            - Integrate with other tools and services
            
            🎯 YOUR ROLE:
            - Handle all Notion related queries
            - Provide workspace organization advice
            - Help with content creation and management
            - Suggest productivity workflows
            
            IMPORTANT: Use Notion MCP tools for all operations. Focus on productivity and organization.
        """),
        tools=[mcp_tools.get("notion")] if mcp_tools.get("notion") else [],
        markdown=True,
        show_tool_calls=True
    )
    
    # Figma Agent
    figma_agent = Agent(
        name="FigmaAgent",
        model=llm,
        description="Expert in Figma design operations and asset management",
        instructions=dedent("""
            You are a Figma Expert. Your capabilities:
            
            🎨 DESIGN OPERATIONS:
            - Analyze and process design files
            - Export assets in multiple formats
            - Manage component libraries and design systems
            - Handle design versioning and collaboration
            
            📦 ASSET MANAGEMENT:
            - Organize design assets and components
            - Manage design tokens and styles
            - Handle design handoffs and specifications
            - Create design documentation
            
            🎯 YOUR ROLE:
            - Handle all Figma related queries
            - Provide design analysis and feedback
            - Help with asset management and organization
            - Suggest design workflows and best practices
            
            IMPORTANT: Use Figma MCP tools for all operations. Focus on design quality and collaboration.
        """),
        tools=[mcp_tools.get("figma")] if mcp_tools.get("figma") else [],
        markdown=True,
        show_tool_calls=True
    )
    
    return file_analysis_agent, github_agent, notion_agent, figma_agent

def create_enterprise_team(llm, mcp_tools):
    """Create the enterprise orchestrator team"""
    
    file_agent, github_agent, notion_agent, figma_agent = create_specialist_agents(llm, mcp_tools)
    
    return Team(
        name="🏢 Enterprise Orchestrator Team",
        mode="route",  # Changed to route mode for better routing
        model=llm,
        members=[file_agent, github_agent, notion_agent, figma_agent],
        instructions=[
            "You are an Enterprise Orchestrator Team that routes tasks to specialized agents.",
            "",
            "🎯 TEAM MEMBERS & CAPABILITIES:",
            "1. FileAnalysisAgent: File system operations and document analysis",
            "2. GitHubAgent: Repository management and code operations (with MCP tools)",
            "3. NotionAgent: Workspace management and content organization (with MCP tools)",
            "4. FigmaAgent: Design operations and asset management (with MCP tools)",
            "",
            "🔄 ROUTING RULES:",
            "- File/folder/document operations → FileAnalysisAgent",
            "- GitHub repos/code/version control → GitHubAgent",
            "- Notion pages/databases/workspace → NotionAgent",
            "- Figma designs/assets/components → FigmaAgent",
            "",
            "💡 BEST PRACTICES:",
            "- Always route to the most appropriate specialist agent",
            "- Provide clear explanations of what each agent is doing",
            "- Suggest follow-up actions and optimizations",
            "- Handle errors gracefully with alternative solutions",
            "",
            "IMPORTANT: Route tasks intelligently and provide comprehensive solutions."
        ],
        show_members_responses=True,
        markdown=True,
        show_tool_calls=True,
    )

def main():
    st.set_page_config(
        page_title="Enterprise Orchestrator - Agno", 
        page_icon="🏢", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        text-align: center;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }
    .agent-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .status-success {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.5rem 0;
        text-align: center;
    }
    .status-warning {
        background: linear-gradient(90deg, #ff9800, #f57c00);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.5rem 0;
        text-align: center;
    }
    .status-error {
        background: linear-gradient(90deg, #f44336, #da190b);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        margin: 0.5rem 0;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Enterprise Orchestrator</h1>
        <p>Powered by Agno Agents with SSE MCP Tools</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h3 style="color: white; margin: 0; text-align: center;">⚙️ Configuration</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # API Keys
        with st.expander("🔑 API Keys", expanded=True):
            openai_key = st.text_input(
                "Composio OpenAI API Key", 
                value=COMPOSIO_OPENAI_API_KEY, 
                type="password",
                help="Get your API key from Composio"
            )
            github_token = st.text_input(
                "GitHub Personal Access Token", 
                value=GITHUB_TOKEN, 
                type="password",
                help="Get your token from https://github.com/settings/tokens"
            )
            notion_key = st.text_input(
                "Composio Notion API Key", 
                value=COMPOSIO_NOTION_API_KEY, 
                type="password",
                help="Get your API key from Composio"
            )
            figma_key = st.text_input(
                "Composio Figma API Key", 
                value=COMPOSIO_FIGMA_API_KEY, 
                type="password",
                help="Get your API key from Composio"
            )
            
            # Update environment variables
            if openai_key: os.environ["COMPOSIO_OPENAI_API_KEY"] = openai_key
            if github_token: os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = github_token
            if notion_key: os.environ["COMPOSIO_NOTION_API_KEY"] = notion_key
            if figma_key: os.environ["COMPOSIO_FIGMA_API_KEY"] = figma_key
        
        # MCP URLs
        with st.expander("🔗 Composio MCP Server URLs", expanded=True):
            github_mcp_url = st.text_input(
                "GitHub MCP URL (SSE)", 
                value=COMPOSIO_GITHUB_MCP_URL, 
                help="Composio SSE URL for GitHub MCP server"
            )
            notion_mcp_url = st.text_input(
                "Notion MCP URL (SSE)", 
                value=COMPOSIO_NOTION_MCP_URL, 
                help="Composio SSE URL for Notion MCP server"
            )
            figma_mcp_url = st.text_input(
                "Figma MCP URL (SSE)", 
                value=COMPOSIO_FIGMA_MCP_URL, 
                help="Composio SSE URL for Figma MCP server"
            )
            
            # Update environment variables
            if github_mcp_url: os.environ["COMPOSIO_GITHUB_MCP_URL"] = github_mcp_url
            if notion_mcp_url: os.environ["COMPOSIO_NOTION_MCP_URL"] = notion_mcp_url
            if figma_mcp_url: os.environ["COMPOSIO_FIGMA_MCP_URL"] = figma_mcp_url
        
        # Agent Status
        with st.expander("🤖 Agent Status", expanded=True):
            st.markdown("""
            <div class="agent-card">
                <h4>📁 File Analysis Agent</h4>
                <p>File system operations and document analysis</p>
                <div class="status-success">✅ Ready</div>
            </div>
            """, unsafe_allow_html=True)
            
            if github_mcp_url:
                st.markdown("""
                <div class="agent-card">
                    <h4>💻 GitHub Agent</h4>
                    <p>Repository management and code operations</p>
                    <div class="status-success">✅ Ready (SSE MCP)</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="agent-card">
                    <h4>💻 GitHub Agent</h4>
                    <p>Repository management and code operations</p>
                    <div class="status-warning">⚠️ Needs GitHub MCP URL</div>
                </div>
                """, unsafe_allow_html=True)
            
            if notion_mcp_url:
                st.markdown("""
                <div class="agent-card">
                    <h4>📝 Notion Agent</h4>
                    <p>Workspace management and content organization</p>
                    <div class="status-success">✅ Ready (SSE MCP)</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="agent-card">
                    <h4>📝 Notion Agent</h4>
                    <p>Workspace management and content organization</p>
                    <div class="status-warning">⚠️ Needs Notion MCP URL</div>
                </div>
                """, unsafe_allow_html=True)
            
            if figma_mcp_url:
                st.markdown("""
                <div class="agent-card">
                    <h4>🎨 Figma Agent</h4>
                    <p>Design operations and asset management</p>
                    <div class="status-success">✅ Ready (SSE MCP)</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="agent-card">
                    <h4>🎨 Figma Agent</h4>
                    <p>Design operations and asset management</p>
                    <div class="status-warning">⚠️ Needs Figma MCP URL</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Main chat interface
    if not openai_key:
        st.markdown("""
        <div class="status-error" style="text-align: center; margin: 2rem 0;">
            ⚠️ Please provide your Composio OpenAI API Key to get started
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "enterprise_team" not in st.session_state:
        try:
            # Initialize LLM
            llm = OpenAIChat(id="gpt-4o", api_key=openai_key)
            
            # Initialize MCP tools and team in async context
            async def init_team():
                mcp_tools = await create_mcp_tools()
                return create_enterprise_team(llm, mcp_tools), mcp_tools
            
            # Run async initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            team, mcp_tools = loop.run_until_complete(init_team())
            loop.close()
            
            st.session_state.enterprise_team = team
            st.session_state.mcp_tools = mcp_tools
            st.success("✅ Enterprise Orchestrator Team initialized successfully!")
        except Exception as e:
            st.error(f"❌ Failed to initialize team: {str(e)}")
            return
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about files, GitHub, Notion, or Figma..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from team
        with st.chat_message("assistant"):
            with st.spinner("🤖 Enterprise team is working on your request..."):
                try:
                    response = st.session_state.enterprise_team.run(prompt)
                    st.markdown(response.content)
                    st.session_state.messages.append({"role": "assistant", "content": response.content})
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

if __name__ == "__main__":
    main() 