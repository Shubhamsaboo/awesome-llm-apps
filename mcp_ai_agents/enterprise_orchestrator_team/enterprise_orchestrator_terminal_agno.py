import asyncio
import json
import os
import sys
import uuid
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('enterprise_orchestrator.log')
    ]
)
logger = logging.getLogger(__name__)

# API Keys
GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# COMPOSIO_NOTION_API_KEY = os.getenv("COMPOSIO_NOTION_API_KEY")
# COMPOSIO_FIGMA_API_KEY = os.getenv("COMPOSIO_FIGMA_API_KEY")

# MCP Server URLs (SSE)
COMPOSIO_GITHUB_MCP_URL = os.getenv("COMPOSIO_GITHUB_MCP_URL")
COMPOSIO_NOTION_MCP_URL = os.getenv("COMPOSIO_NOTION_MCP_URL")
COMPOSIO_FIGMA_MCP_URL = os.getenv("COMPOSIO_FIGMA_MCP_URL")

async def create_mcp_tools():
    """Create separate MCP tools for different services"""
    
    logger.info("🔄 Starting MCP tools creation...")
    mcp_tools = {}
    
    # GitHub MCP Tools
    if COMPOSIO_GITHUB_MCP_URL:
        logger.info(f"🔗 Attempting to connect GitHub MCP: {COMPOSIO_GITHUB_MCP_URL}")
        try:
            github_mcp = MCPTools(transport="streamable-http", url=COMPOSIO_GITHUB_MCP_URL)
            await github_mcp.__aenter__()  # Manually enter context for team usage
            mcp_tools["github"] = github_mcp
            logger.info("✅ GitHub MCP tools connected successfully")
            print("✅ GitHub MCP tools connected")
        except Exception as e:
            logger.error(f"❌ Failed to connect GitHub MCP: {e}")
            print(f"❌ Failed to connect GitHub MCP: {e}")
    else:
        logger.warning("⚠️ COMPOSIO_GITHUB_MCP_URL not found in environment")
    
    # Notion MCP Tools
    if COMPOSIO_NOTION_MCP_URL:
        logger.info(f"🔗 Attempting to connect Notion MCP: {COMPOSIO_NOTION_MCP_URL}")
        try:
            notion_mcp = MCPTools(transport="streamable-http", url=COMPOSIO_NOTION_MCP_URL)
            await notion_mcp.__aenter__()  # Manually enter context for team usage
            mcp_tools["notion"] = notion_mcp
            logger.info("✅ Notion MCP tools connected successfully")
            print("✅ Notion MCP tools connected")
        except Exception as e:
            logger.error(f"❌ Failed to connect Notion MCP: {e}")
            print(f"❌ Failed to connect Notion MCP: {e}")
    else:
        logger.warning("⚠️ COMPOSIO_NOTION_MCP_URL not found in environment")
    
    # Figma MCP Tools
    if COMPOSIO_FIGMA_MCP_URL:
        logger.info(f"🔗 Attempting to connect Figma MCP: {COMPOSIO_FIGMA_MCP_URL}")
        try:
            figma_mcp = MCPTools(transport="streamable-http", url=COMPOSIO_FIGMA_MCP_URL)
            await figma_mcp.__aenter__()  # Manually enter context for team usage
            mcp_tools["figma"] = figma_mcp
            logger.info("✅ Figma MCP tools connected successfully")
            print("✅ Figma MCP tools connected")
        except Exception as e:
            logger.error(f"❌ Failed to connect Figma MCP: {e}")
            print(f"❌ Failed to connect Figma MCP: {e}")
    else:
        logger.warning("⚠️ COMPOSIO_FIGMA_MCP_URL not found in environment")
    
    logger.info(f"📊 MCP tools summary: {list(mcp_tools.keys())}")
    return mcp_tools

def create_specialist_agents(llm, mcp_tools):
    """Create specialized agents for different domains"""
    
    logger.info("🤖 Creating specialist agents...")
    logger.info(f"📦 Available MCP tools: {list(mcp_tools.keys())}")
    
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
    logger.info("✅ File Analysis Agent created (no MCP tools)")
    
    # GitHub Agent
    github_tools = [mcp_tools.get("github")] if mcp_tools.get("github") else []
    logger.info(f"🔧 GitHub Agent tools: {len(github_tools)} tools")
    
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
            If you have MCP tools available, use them to perform actual GitHub operations.
        """),
        tools=github_tools,
        markdown=True,
        show_tool_calls=True
    )
    logger.info(f"✅ GitHub Agent created with {len(github_tools)} tools")
    
    # Notion Agent
    notion_tools = [mcp_tools.get("notion")] if mcp_tools.get("notion") else []
    logger.info(f"📝 Notion Agent tools: {len(notion_tools)} tools")
    
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
            If you have MCP tools available, use them to perform actual Notion operations.
            If asked to write to a Notion page, use your MCP tools to actually create or update the page.
        """),
        tools=notion_tools,
        markdown=True,
        show_tool_calls=True
    )
    logger.info(f"✅ Notion Agent created with {len(notion_tools)} tools")
    
    # Figma Agent
    figma_tools = [mcp_tools.get("figma")] if mcp_tools.get("figma") else []
    logger.info(f"🎨 Figma Agent tools: {len(figma_tools)} tools")
    
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
            If you have MCP tools available, use them to perform actual Figma operations.
        """),
        tools=figma_tools,
        markdown=True,
        show_tool_calls=True
    )
    logger.info(f"✅ Figma Agent created with {len(figma_tools)} tools")
    
    return file_analysis_agent, github_agent, notion_agent, figma_agent

def create_enterprise_team(llm, mcp_tools):
    """Create the enterprise orchestrator team"""
    
    logger.info("🏢 Creating Enterprise Orchestrator Team...")
    
    file_agent, github_agent, notion_agent, figma_agent = create_specialist_agents(llm, mcp_tools)
    
    team = Team(
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
    
    logger.info("✅ Enterprise Orchestrator Team created successfully")
    return team

async def main():
    print("\n" + "="*70)
    print("           🏢 Enterprise Orchestrator - Agno Edition 🏢")
    print("="*70)
    print("🔗 Connected Services: GitHub • Notion • Figma • File System")
    print("💡 Powered by OpenAI GPT-4o with Agno Agents & SSE MCP Tools")
    print("="*70 + "\n")
    
    logger.info("🚀 Starting Enterprise Orchestrator...")
    
    # Generate unique user and session IDs for this terminal session
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    print(f"👤 User ID: {user_id}")
    print(f"🔑 Session ID: {session_id}")
    logger.info(f"👤 User ID: {user_id}, Session ID: {session_id}")
    
    print("\n🔌 Initializing SSE MCP server connections...\n")
    
    try:
        # Initialize LLM and MCP tools
        logger.info("🔧 Initializing LLM...")
        llm = OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY)
        logger.info("✅ LLM initialized")
        
        logger.info("🔧 Initializing MCP tools...")
        mcp_tools = await create_mcp_tools()
        
        # Create enterprise team
        logger.info("🔧 Creating enterprise team...")
        enterprise_team = create_enterprise_team(llm, mcp_tools)
        
        print("✅ Successfully connected to all MCP servers!")
        print("✅ Enterprise Orchestrator Team initialized successfully!")
        
        # Display agent status
        print("\n🤖 Agent Status:")
        print("   📁 File Analysis Agent: ✅ Ready (simple file operations)")
        
        if COMPOSIO_GITHUB_MCP_URL:
            print("   💻 GitHub Agent: ✅ Ready (SSE MCP tools)")
        else:
            print("   💻 GitHub Agent: ⚠️ Needs GitHub MCP URL")
            
        if COMPOSIO_NOTION_MCP_URL:
            print("   📝 Notion Agent: ✅ Ready (SSE MCP tools)")
        else:
            print("   📝 Notion Agent: ⚠️ Needs Notion MCP URL")
            
        if COMPOSIO_FIGMA_MCP_URL:
            print("   🎨 Figma Agent: ✅ Ready (SSE MCP tools)")
        else:
            print("   🎨 Figma Agent: ⚠️ Needs Figma MCP URL")
        
        print("\n" + "🎉 " + "="*54 + " 🎉")
        print("   Enterprise Orchestrator is READY! Let's get productive!")
        print("🎉 " + "="*54 + " 🎉\n")
        
        print("💡 Try these example commands:")
        print("   • 'List files in my current directory'")
        print("   • 'Show my recent GitHub repositories'")
        print("   • 'Create a Notion page for project planning'")
        print("   • 'Export Figma assets from my design file'")
        
        print("⚡ Type 'exit', 'quit', or 'bye' to end the session\n")
        
        # Simple terminal interface
        while True:
            try:
                # Get user input
                user_input = input("💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    print("\n👋 Goodbye! Thanks for using the Enterprise Orchestrator.")
                    break
                
                if not user_input:
                    continue
                
                logger.info(f"📝 User input: {user_input}")
                print("\n🤖 Enterprise Team: Processing your request...\n")
                
                # Get response from team
                logger.info("🔄 Calling enterprise team...")
                response = enterprise_team.run(user_input)
                logger.info(f"✅ Team response received: {len(response.content)} characters")
                
                print(f"🤖 Enterprise Team: {response.content}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                logger.error(f"❌ Error processing user input: {e}", exc_info=True)
                print(f"\n❌ Error: {str(e)}")
                print("Please try again or type 'exit' to quit.\n")
        
        # Close MCP connections
        print("\n🔌 Closing MCP connections...")
        for tool_name, tool in mcp_tools.items():
            try:
                await tool.__aexit__(None, None, None) # Use __aexit__ for async context manager
                logger.info(f"✅ {tool_name.capitalize()} MCP connection closed")
                print(f"✅ {tool_name.capitalize()} MCP connection closed")
            except Exception as e:
                logger.error(f"⚠️ Error closing {tool_name} MCP connection: {e}")
                print(f"⚠️ Error closing {tool_name} MCP connection: {e}")
        
    except Exception as e:
        logger.error(f"❌ Error initializing Enterprise Orchestrator: {e}", exc_info=True)
        print(f"❌ Error initializing Enterprise Orchestrator: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your API keys in .env file")
        print("2. Ensure you have the required dependencies installed")
        print("3. Verify your internet connection")
        print("4. Check your MCP server URLs")
        print("5. Check the log file: enterprise_orchestrator.log")
        return

if __name__ == "__main__":
    asyncio.run(main()) 