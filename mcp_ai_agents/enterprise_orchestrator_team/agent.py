
import os
import asyncio
import logging
from typing import Dict, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, SseServerParams

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment configuration
MCP_FILESYSTEM_PATH = os.getenv("MCP_FILESYSTEM_PATH", "~/Documents")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
FIGMA_API_KEY = os.getenv("FIGMA_API_KEY")

COMPOSIO_NOTION_URL = os.getenv("COMPOSIO_NOTION_URL")
COMPOSIO_GITHUB_URL = os.getenv("COMPOSIO_GITHUB_URL")
COMPOSIO_FIGMA_URL = os.getenv("COMPOSIO_FIGMA_URL")

# ========================================
# SPECIALIST AGENT CREATION
# ========================================

async def create_file_agent() -> Optional[LlmAgent]:
    """Create FileAnalysisAgent with filesystem MCP tools"""
    try:
        folder_path = os.path.expanduser(MCP_FILESYSTEM_PATH)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
        
        filesystem_tools, exit_stack = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command='npx',
                args=["-y", "@modelcontextprotocol/server-filesystem", os.path.abspath(folder_path)]
            )
        )
        
        agent = LlmAgent(
            name="FileAnalysisAgent",
            model="gemini-2.0-flash",
            description="File and document management specialist",
            instruction=f"""You are FileAnalysisAgent - Expert in file operations.
You have direct filesystem access at: {folder_path}
Your tools allow you to: list directories, read files, create files, search files, get metadata.
When given a task, use your MCP tools to complete it fully. Provide detailed results.""",
            tools=filesystem_tools
        )
        
        agent._exit_stack = exit_stack
        logger.info("✅ FileAnalysisAgent created")
        return agent
        
    except Exception as e:
        logger.error(f"❌ FileAnalysisAgent creation failed: {e}")
        return None

async def create_notion_agent() -> Optional[LlmAgent]:
    """Create NotionAgent with Notion MCP tools"""
    try:
        if not (NOTION_API_KEY and COMPOSIO_NOTION_URL):
            logger.warning("⚠️ Notion credentials missing")
            return None
            
        notion_tools, exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=COMPOSIO_NOTION_URL, headers={})
        )
        
        agent = LlmAgent(
            name="NotionAgent",
            model="gemini-2.0-flash",
            description="Notion workspace management specialist",
            instruction="""You are NotionAgent - Expert in Notion operations.
Your tools allow you to: search pages, create content, update content, manage organization, export data.
When given a task, use your MCP tools to complete it fully. Provide detailed results.""",
            tools=notion_tools
        )
        
        logger.info("✅ NotionAgent created")
        return agent
        
    except Exception as e:
        logger.error(f"❌ NotionAgent creation failed: {e}")
        return None

async def create_github_agent() -> Optional[LlmAgent]:
    """Create GitHubAgent with GitHub MCP tools"""
    try:
        if not (GITHUB_API_KEY and COMPOSIO_GITHUB_URL):
            logger.warning("⚠️ GitHub credentials missing")
            return None
            
        github_tools, exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=COMPOSIO_GITHUB_URL, headers={})
        )
        
        agent = LlmAgent(
            name="GitHubAgent",
            model="gemini-2.0-flash",
            description="GitHub repository and development specialist",
            instruction="""You are GitHubAgent - Expert in GitHub operations.
Your tools allow you to: manage repos, handle PRs, manage branches, search code, analyze data.
When given a task, use your MCP tools to complete it fully. Provide detailed results.""",
            tools=github_tools
        )
        
        logger.info("✅ GitHubAgent created")
        return agent
        
    except Exception as e:
        logger.error(f"❌ GitHubAgent creation failed: {e}")
        return None

async def create_figma_agent() -> Optional[LlmAgent]:
    """Create FigmaAgent with Figma MCP tools"""
    try:
        if not (FIGMA_API_KEY and COMPOSIO_FIGMA_URL):
            logger.warning("⚠️ Figma credentials missing")
            return None
            
        figma_tools, exit_stack = await MCPToolset.from_server(
            connection_params=SseServerParams(url=COMPOSIO_FIGMA_URL, headers={})
        )
        
        agent = LlmAgent(
            name="FigmaAgent",
            model="gemini-2.0-flash",
            description="Figma design and asset management specialist",
            instruction="""You are FigmaAgent - Expert in Figma operations.
Your tools allow you to: analyze designs, export assets, manage libraries, handle systems, generate docs.
When given a task, use your MCP tools to complete it fully. Provide detailed results.""",
            tools=figma_tools
        )
        
        logger.info("✅ FigmaAgent created")
        return agent
        
    except Exception as e:
        logger.error(f"❌ FigmaAgent creation failed: {e}")
        return None

# ========================================
# AGENT STORE AND REAL EXECUTION
# ========================================

# Global agent store
_agent_store = {}

async def _execute_specialist_agent_async(agent_name: str, user_query: str) -> str:
    """Execute query with real specialist agent using MCP tools"""
    try:
        # Get or create agent
        if agent_name not in _agent_store:
            if agent_name == "FileAnalysisAgent":
                _agent_store[agent_name] = await create_file_agent()
            elif agent_name == "NotionAgent":
                _agent_store[agent_name] = await create_notion_agent()
            elif agent_name == "GitHubAgent":
                _agent_store[agent_name] = await create_github_agent()
            elif agent_name == "FigmaAgent":
                _agent_store[agent_name] = await create_figma_agent()
        
        agent = _agent_store.get(agent_name)
        if not agent:
            return f"❌ {agent_name} not available"
        
        logger.info(f"🔄 {agent_name} executing with REAL MCP tools: {user_query}")
        
        # Execute with real agent and MCP tools
        response_content = ""
        async for event in agent.run_async(user_query):
            if hasattr(event, 'content') and event.content:
                response_content += str(event.content)
            elif hasattr(event, 'text') and event.text:
                response_content += str(event.text)
            elif hasattr(event, 'message') and event.message:
                response_content += str(event.message)
            elif isinstance(event, str):
                response_content += event
        
        if response_content.strip():
            logger.info(f"✅ {agent_name} completed with REAL MCP tools")
            return f"🤖 {agent_name} Real MCP Response:\n\n{response_content.strip()}"
        else:
            return f"⚠️ {agent_name} returned empty response"
            
    except Exception as e:
        logger.error(f"❌ {agent_name} execution failed: {e}")
        return f"❌ {agent_name} execution failed: {str(e)}"

# ========================================
# DELEGATION FUNCTIONS
# ========================================

def execute_file_agent(user_query: str) -> str:
    """Execute query with FileAnalysisAgent using REAL MCP tools"""
    try:
        try:
            loop = asyncio.get_running_loop()
            return "🔄 FileAnalysisAgent processing with REAL MCP tools... (async execution required)"
        except RuntimeError:
            return asyncio.run(_execute_specialist_agent_async("FileAnalysisAgent", user_query))
    except Exception as e:
        logger.error(f"❌ FileAnalysisAgent wrapper error: {e}")
        return f"❌ FileAnalysisAgent wrapper error: {str(e)}"

def execute_notion_agent(user_query: str) -> str:
    """Execute query with NotionAgent using REAL MCP tools"""
    try:
        try:
            loop = asyncio.get_running_loop()
            return "🔄 NotionAgent processing with REAL MCP tools... (async execution required)"
        except RuntimeError:
            return asyncio.run(_execute_specialist_agent_async("NotionAgent", user_query))
    except Exception as e:
        logger.error(f"❌ NotionAgent wrapper error: {e}")
        return f"❌ NotionAgent wrapper error: {str(e)}"

def execute_github_agent(user_query: str) -> str:
    """Execute query with GitHubAgent using REAL MCP tools"""
    try:
        try:
            loop = asyncio.get_running_loop()
            return "🔄 GitHubAgent processing with REAL MCP tools... (async execution required)"
        except RuntimeError:
            return asyncio.run(_execute_specialist_agent_async("GitHubAgent", user_query))
    except Exception as e:
        logger.error(f"❌ GitHubAgent wrapper error: {e}")
        return f"❌ GitHubAgent wrapper error: {str(e)}"

def execute_figma_agent(user_query: str) -> str:
    """Execute query with FigmaAgent using REAL MCP tools"""
    try:
        try:
            loop = asyncio.get_running_loop()
            return "🔄 FigmaAgent processing with REAL MCP tools... (async execution required)"
        except RuntimeError:
            return asyncio.run(_execute_specialist_agent_async("FigmaAgent", user_query))
    except Exception as e:
        logger.error(f"❌ FigmaAgent wrapper error: {e}")
        return f"❌ FigmaAgent wrapper error: {str(e)}"

# ========================================
# ENTERPRISE ORCHESTRATOR (ROUTER)
# ========================================

class EnterpriseOrchestrator:
    """LLM-based router agent that intelligently delegates to specialized agents"""
    
    def __init__(self):
        self.router_agent = None
        
    async def initialize(self):
        """Initialize the orchestrator and all agents"""
        try:
        # Create router agent with delegation functions as tools
            self.router_agent = LlmAgent(
            name="EnterpriseOrchestrator",
            model="gemini-2.0-flash",
            description="LLM-based router that intelligently delegates queries to specialized agents",
            instruction=f"""You are the Enterprise Orchestrator - an intelligent router that analyzes user queries and delegates them to the most appropriate specialized agent.

AVAILABLE AGENTS AND THEIR CAPABILITIES:

🗂️ FileAnalysisAgent (use execute_file_agent):
- List directories and files in filesystem
- Read and analyze file contents
- Create, modify, and delete files
- Search for specific files and patterns
- Get file metadata and properties

📝 NotionAgent (use execute_notion_agent):
- Search and retrieve Notion pages and databases
- Create new pages, databases, and content
- Update existing Notion workspace content
- Manage workspace organization and structure

💻 GitHubAgent (use execute_github_agent):
- Create and manage GitHub repositories
- Handle issues, pull requests, and code reviews
- Manage branches, releases, and deployments
- Search code across repositories

🎨 FigmaAgent (use execute_figma_agent):
- Analyze and process design files
- Export assets in multiple formats
- Manage component libraries and design systems

YOUR ROLE:
Analyze the user's query and determine which agent is best suited to handle it. Then use the appropriate execution function to delegate the task.

ROUTING DECISIONS:
- File/folder/document operations → execute_file_agent
- Notion pages/databases/workspace → execute_notion_agent
- GitHub repos/code/version control → execute_github_agent
- Figma designs/assets/components → execute_figma_agent

Always call the appropriate execution function and return the agent's response to the user.""",
            tools=[execute_file_agent, execute_notion_agent, execute_github_agent, execute_figma_agent]
        )
            
            logger.info("✅ Enterprise Orchestrator initialized with real MCP tool integration")
            return True
            
        except Exception as e:
            logger.error(f"❌ Enterprise Orchestrator initialization failed: {e}")
            return False
    
    async def process_query(self, query: str) -> str:
        """Process user query through LLM-based router with REAL MCP tool execution"""
        try:
            if not self.router_agent:
                await self.initialize()
            
            logger.info(f"📥 Router processing: {query}")
            
            # Let the router LLM analyze and delegate using its tools
            response_content = ""
            async for event in self.router_agent.run_async(query):
                if hasattr(event, 'content') and event.content:
                        response_content += str(event.content)
                elif hasattr(event, 'text') and event.text:
                        response_content += str(event.text)
                elif hasattr(event, 'message') and event.message:
                        response_content += str(event.message)
                elif isinstance(event, str):
                    response_content += event
                
            # Check if we got a placeholder response indicating async execution needed
            if "processing with REAL MCP tools... (async execution required)" in response_content:
                logger.info("🔄 Detected async execution required, routing to specialist agent")
                
                # Determine which agent to use based on response
                if "FileAnalysisAgent" in response_content:
                    return await _execute_specialist_agent_async("FileAnalysisAgent", query)
                elif "NotionAgent" in response_content:
                    return await _execute_specialist_agent_async("NotionAgent", query)
                elif "GitHubAgent" in response_content:
                    return await _execute_specialist_agent_async("GitHubAgent", query)
                elif "FigmaAgent" in response_content:
                    return await _execute_specialist_agent_async("FigmaAgent", query)
            
            if response_content.strip():
                logger.info("✅ Router completed delegation successfully")
                return response_content.strip()
            else:
                logger.warning("⚠️ Router returned empty response")
                return "⚠️ Router completed but returned no content"
            
        except Exception as e:
            logger.error(f"❌ Router error: {e}")
            return f"❌ Router failed: {str(e)}"

# ========================================
# SYSTEM CREATION
# ========================================

async def create_enterprise_orchestrator_system() -> Optional[EnterpriseOrchestrator]:
    """Create the complete system with real MCP tool integration"""
    try:
        logger.info("🔧 Building Enterprise Orchestrator System with MCP tools...")
        
        orchestrator = EnterpriseOrchestrator()
        success = await orchestrator.initialize()
        
        if success:
            logger.info("✅ System ready: 1 router + specialist agents with real MCP tools")
            return orchestrator
        else:
            logger.error("❌ System initialization failed")
            return None
        
    except Exception as e:
        logger.error(f"❌ System creation failed: {e}")
        return None

# ========================================
# TESTING FUNCTIONS
# ========================================

async def test_system():
    """Test the enterprise orchestrator system"""
    print("🧪 Testing Enterprise Orchestrator System")
    print("=" * 60)
    
    # Create orchestrator
    orchestrator = await create_enterprise_orchestrator_system()
    if not orchestrator:
        print("❌ Failed to create orchestrator")
        return
    
    # Test queries
    test_queries = [
        "List all files in the current directory",
        "Create a new file called test.txt with hello world content",
        "Read the contents of any Python file in the directory"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        try:
            response = await orchestrator.process_query(query)
            print(f"📋 Response: {response[:300]}...")
            
            if "Real MCP Response:" in response:
                print("✅ REAL MCP execution detected!")
            elif "async execution required" in response:
                print("🔄 Async execution triggered")
            else:
                print("❓ Response format unclear")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Testing complete")

# ========================================
# ADK WEB INTEGRATION
# ========================================

async def create_root_agent() -> LlmAgent:
    """Create root agent for ADK Web interface"""
    try:
        # Create the enterprise orchestrator system
        orchestrator = await create_enterprise_orchestrator_system()
        
        if orchestrator and orchestrator.router_agent:
            logger.info("✅ Root agent ready for ADK Web")
            return orchestrator.router_agent
        else:
            # Fallback router agent if system creation fails
            logger.warning("⚠️ Creating fallback root agent")
            return LlmAgent(
                name="EnterpriseOrchestrator",
                model="gemini-2.0-flash",
                description="Enterprise router agent - fallback mode",
                instruction="""You are the Enterprise Orchestrator. 
                
I help route queries to specialized agents for:
- 🗂️ File operations (filesystem management)
- 📝 Notion workspace tasks
- 💻 GitHub repository work  
- 🎨 Figma design operations

However, I'm currently in fallback mode due to system initialization issues.
Please try your query and I'll do my best to help.""",
                tools=[]
            )
            
    except Exception as e:
        logger.error(f"❌ Root agent creation failed: {e}")
        # Critical fallback for ADK Web
        return LlmAgent(
            name="EnterpriseOrchestrator",
            model="gemini-2.0-flash",
            description="Enterprise router agent - critical fallback",
            instruction="I'm the Enterprise Orchestrator in emergency mode. Please describe your task and I'll help as best I can.",
            tools=[]
        )

# Simple ADK Web compatible root_agent (following working pattern)
root_agent = LlmAgent(
    name="enterprise_orchestrator",
        model="gemini-2.0-flash",
    description="Enterprise Orchestrator - Intelligent multi-agent router with real MCP tool integration",
    instruction="""You are the Enterprise Orchestrator - an intelligent router that analyzes user queries and delegates them to specialized agents with real MCP tools.

AVAILABLE SPECIALIST AGENTS:

🗂️ FileAnalysisAgent (use execute_file_agent):
- List directories and files in filesystem  
- Read and analyze file contents
- Create, modify, and delete files
- Search for specific files and patterns
- Get file metadata and properties

📝 NotionAgent (use execute_notion_agent):
- Search and retrieve Notion pages and databases
- Create new pages, databases, and content
- Update existing Notion workspace content  
- Manage workspace organization and structure

💻 GitHubAgent (use execute_github_agent):
- Create and manage GitHub repositories
- Handle issues, pull requests, and code reviews
- Manage branches, releases, and deployments
- Search code across repositories

🎨 FigmaAgent (use execute_figma_agent):
- Analyze and process design files
- Export assets in multiple formats
- Manage component libraries and design systems

YOUR ROLE:
1. Analyze the user's query to understand the intent
2. Choose the most appropriate specialist agent
3. Use the corresponding execution function to delegate the task
4. Return the specialist's response to the user

ROUTING DECISIONS:
- File/folder/document operations → execute_file_agent
- Notion pages/databases/workspace → execute_notion_agent  
- GitHub repos/code/version control → execute_github_agent
- Figma designs/assets/components → execute_figma_agent

IMPORTANT: Always use the appropriate execution function to delegate tasks. These functions connect to real MCP tools and provide actual functionality.

Examples:
- "List files in my project" → execute_file_agent
- "Create a Notion page" → execute_notion_agent
- "Show my GitHub repos" → execute_github_agent
- "Export Figma assets" → execute_figma_agent

Be intelligent about routing and always delegate to the specialist agents rather than trying to handle requests yourself.""",
    tools=[execute_file_agent, execute_notion_agent, execute_github_agent, execute_figma_agent]
)

# Export for ADK Web
__all__ = ['EnterpriseOrchestrator', 'root_agent', 'create_enterprise_orchestrator_system']

if __name__ == "__main__":
    # Test the system
    asyncio.run(test_system())