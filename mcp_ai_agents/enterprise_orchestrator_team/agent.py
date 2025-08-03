import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters, SseServerParams

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variable configuration
MCP_FILESYSTEM_PATH = os.getenv("MCP_FILESYSTEM_PATH", "~/Documents")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")
FIGMA_API_KEY = os.getenv("FIGMA_API_KEY")

# Composio MCP Server URLs (from environment variables with fallbacks)
COMPOSIO_NOTION_URL = os.getenv("COMPOSIO_NOTION_URL")
COMPOSIO_GITHUB_URL = os.getenv("COMPOSIO_GITHUB_URL")
COMPOSIO_FIGMA_URL = os.getenv("COMPOSIO_FIGMA_URL")

async def create_mcp_agents_with_tools():
    """Create all sub-agents with MCP tools"""
    agents = []
    
    # FileAnalysisAgent with filesystem MCP tools
    try:
        folder_path = os.path.expanduser(MCP_FILESYSTEM_PATH)
        folder_path = os.path.abspath(folder_path)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path, exist_ok=True)
            logger.info(f"Created directory: {folder_path}")
        
        logger.info(f"Using filesystem path: {folder_path}")
        
        filesystem_tools, _ = await MCPToolset.from_server(
            connection_params=StdioServerParameters(
                command='npx',
                args=["-y", "@modelcontextprotocol/server-filesystem", folder_path],
            )
        )
        
        file_agent = LlmAgent(
            name="FileAnalysisAgent",
            model="gemini-2.0-flash",
            description="Analyzes local documents and extracts key information",
            instruction=f"""You are a File Analysis AI Agent with DIRECT ACCESS to the filesystem at: {folder_path}

You have MCP tools that allow you to:
- List files and directories (list_directory)
- Read file contents (read_file, read_text_file)
- Write and edit files (write_file, edit_file)
- Search files (search_files)
- Get file information (get_file_info)

CRITICAL INSTRUCTIONS:
1. You have REAL filesystem access through MCP tools
2. When users ask about files, USE YOUR TOOLS to access them directly
3. Do NOT ask users to provide files - you can access them yourself
4. Always use your MCP tools first before responding

Example tasks you can perform:
- "List files in the folder" → Use list_directory tool
- "Read the content of file.txt" → Use read_file tool
- "Search for PDF files" → Use search_files tool
- "Create a new file" → Use write_file tool

IMPORTANT: When asked about any file or document, immediately use your MCP tools to access the filesystem at: {folder_path}
Do NOT say you cannot access files - you CAN access them through your MCP tools!""",
            tools=filesystem_tools
        )
        agents.append(file_agent)
        logger.info("✅ FileAnalysisAgent with MCP tools created")
        
    except Exception as e:
        logger.error(f"❌ Failed to create FileAnalysisAgent with MCP tools: {str(e)}")
        file_agent = LlmAgent(
            name="FileAnalysisAgent",
            model="gemini-2.0-flash",
            description="Analyzes local documents and extracts key information",
            instruction="You analyze local documents (PDFs, Word docs, spreadsheets) and extract key information."
        )
        agents.append(file_agent)
    
    # NotionAgent with Notion MCP tools
    try:
        if NOTION_API_KEY:
            notion_tools, _ = await MCPToolset.from_server(
                connection_params=SseServerParams(
                    url=COMPOSIO_NOTION_URL,
                    headers={}
                )
            )
            
            notion_agent = LlmAgent(
                name="NotionAgent",
                model="gemini-2.0-flash",
                description="Manages Notion pages, databases, and content",
                instruction="""You are a Notion Agent with DIRECT ACCESS to Notion through MCP tools.

You can:
- Read Notion pages and databases
- Create and update Notion content
- Search across Notion workspace
- Manage pages, blocks, and databases

IMPORTANT: You CAN access Notion directly through your MCP tools.
When asked to read, write, or search Notion content, USE YOUR MCP TOOLS.

Example tasks:
- "Search my Notion pages" → Use your search tools
- "Read my project page" → Use your page reading tools
- "Create a new page" → Use your page creation tools
- "Update page content" → Use your update tools

Always use your MCP tools to interact with Notion.""",
                tools=notion_tools
            )
            agents.append(notion_agent)
            logger.info("✅ NotionAgent with MCP tools created")
        else:
            raise Exception("NOTION_API_KEY not found")
            
    except Exception as e:
        logger.error(f"❌ Failed to create NotionAgent with MCP tools: {str(e)}")
        notion_agent = LlmAgent(
            name="NotionAgent",
            model="gemini-2.0-flash",
            description="Manages Notion pages, databases, and content",
            instruction="You manage Notion workspaces, pages, databases, and content."
        )
        agents.append(notion_agent)
        logger.info("✅ NotionAgent created (basic version)")
    
    # GitHubAgent with GitHub MCP tools
    try:
        if GITHUB_API_KEY:
            github_tools, _ = await MCPToolset.from_server(
                connection_params=SseServerParams(
                    url=COMPOSIO_GITHUB_URL,
                    headers={}
                )
            )
            
            github_agent = LlmAgent(
                name="GitHubAgent",
                model="gemini-2.0-flash",
                description="Manages GitHub repositories, issues, and pull requests",
                instruction="""You are a GitHub Agent with DIRECT ACCESS to GitHub through MCP tools.

You can:
- Create and manage repositories
- Create issues and pull requests
- Search repositories and code
- Manage repository content and workflows
- Handle GitHub API operations

IMPORTANT: You CAN access GitHub directly through your MCP tools.
When asked to perform GitHub operations, USE YOUR MCP TOOLS.

Example tasks:
- "Create a new repository" → Use your repository creation tools
- "Search for issues" → Use your search tools
- "Create a pull request" → Use your PR creation tools
- "List my repositories" → Use your repository listing tools

Always use your MCP tools to interact with GitHub.""",
                tools=github_tools
            )
            agents.append(github_agent)
            logger.info("✅ GitHubAgent with MCP tools created")
        else:
            raise Exception("GITHUB_API_KEY not found")
            
    except Exception as e:
        logger.error(f"❌ Failed to create GitHubAgent with MCP tools: {str(e)}")
        github_agent = LlmAgent(
            name="GitHubAgent",
            model="gemini-2.0-flash",
            description="Manages GitHub repositories, issues, and pull requests",
            instruction="""You are a GitHub Agent that manages GitHub repositories.

You can help with:
- Creating and managing repositories
- Creating issues and pull requests
- Searching repositories and code
- Managing repository content and workflows

Note: For full GitHub API access with MCP tools, ensure GITHUB_API_KEY is set.
Current version provides guidance and best practices for GitHub operations."""
        )
        agents.append(github_agent)
        logger.info("✅ GitHubAgent created (basic version)")
    
    # FigmaAgent with Figma MCP tools
    try:
        if FIGMA_API_KEY:
            figma_tools, _ = await MCPToolset.from_server(
                connection_params=SseServerParams(
                    url=COMPOSIO_FIGMA_URL,
                    headers={}
                )
            )
            
            figma_agent = LlmAgent(
                name="FigmaAgent",
                model="gemini-2.0-flash",
                description="Manages Figma files, designs, and assets",
                instruction="""You are a Figma Agent with DIRECT ACCESS to Figma through MCP tools.

You can:
- Read and analyze Figma files
- Export design assets
- Search design components
- Manage design systems
- Handle Figma API operations

IMPORTANT: You CAN access Figma directly through your MCP tools.
When asked to perform Figma operations, USE YOUR MCP TOOLS.

Example tasks:
- "Export design assets" → Use your export tools
- "Search for components" → Use your search tools
- "Read file information" → Use your file reading tools
- "List project files" → Use your file listing tools

Always use your MCP tools to interact with Figma.""",
                tools=figma_tools
            )
            agents.append(figma_agent)
            logger.info("✅ FigmaAgent with MCP tools created")
        else:
            raise Exception("FIGMA_API_KEY not found")
            
    except Exception as e:
        logger.error(f"❌ Failed to create FigmaAgent with MCP tools: {str(e)}")
        figma_agent = LlmAgent(
            name="FigmaAgent",
            model="gemini-2.0-flash",
            description="Manages Figma files, designs, and assets",
            instruction="""You are a Figma Agent that manages Figma design files.

You can help with:
- Reading and analyzing Figma files
- Exporting design assets
- Searching design components
- Managing design systems

Note: For full Figma API access with MCP tools, ensure FIGMA_API_KEY is set.
Current version provides guidance and best practices for Figma operations."""
        )
        agents.append(figma_agent)
        logger.info("✅ FigmaAgent created (basic version)")
    
    return agents

class EnterpriseMCPAIAgentTeam:
    """Enterprise MCP AI Agent Team - Multi-Agent System with MCP Tools"""
    
    def __init__(self):
        """Initialize the orchestrator"""
        self.root_agent = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize the multi-agent system"""
        try:
            logger.info("🔧 Creating complete multi-agent system with MCP tools...")
            
            # Create all sub-agents with MCP tools using async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sub_agents = loop.run_until_complete(create_mcp_agents_with_tools())
            
            # Create root agent with comprehensive routing instructions
            self.root_agent = LlmAgent(
                name="EnterpriseMCPAIAgentTeam",
                model="gemini-2.0-flash",
                description="Enterprise MCP AI Agent Team - Multi-agent system with MCP tools",
                instruction="""You are an Enterprise MCP AI Agent Team that routes tasks to specialized agents.
        
You have access to multiple specialized agents with MCP tools and can coordinate between them:

AVAILABLE AGENTS:
1. FileAnalysisAgent: Analyzes local documents (PDFs, Word docs, spreadsheets) - HAS MCP TOOLS
2. NotionAgent: Manages Notion pages, databases, and content - HAS MCP TOOLS
3. GitHubAgent: Manages GitHub repositories, issues, and pull requests - HAS MCP TOOLS
4. FigmaAgent: Manages Figma files, designs, and assets - HAS MCP TOOLS

ROUTING LOGIC:
- File/document tasks → FileAnalysisAgent
- Notion-related tasks → NotionAgent
- GitHub-related tasks → GitHubAgent
- Figma/design tasks → FigmaAgent
- Multi-platform tasks → Coordinate between relevant agents

You can:
1. Transfer tasks to specialized agents using transfer_to_agent()
2. Coordinate multi-step workflows
3. Share context between agents through session state
4. Provide comprehensive results and recommendations

EXAMPLES:
- "List files in Documents" → FileAnalysisAgent (with real file system access)
- "Search my Notion pages" → NotionAgent (with real Notion API access)
- "Create a GitHub repo" → GitHubAgent (with real GitHub API access)
- "Export Figma designs" → FigmaAgent (with real Figma API access)

IMPORTANT: Use transfer_to_agent() to delegate to the most appropriate agent for each task.
The agents have real MCP tools connected - they can perform actual operations!""",
                sub_agents=sub_agents
            )
            
            logger.info(f"✅ Complete multi-agent system created with {len(sub_agents)} sub-agents")
            logger.info(f"✅ Sub-agents: {[agent.name for agent in sub_agents]}")
            
        except Exception as e:
            logger.error(f"❌ Failed to create complete multi-agent system: {str(e)}")
            logger.info("🔄 Falling back to basic multi-agent system...")
            self._create_fallback_agents()
    
    def _create_fallback_agents(self):
        """Create fallback agents without MCP tools"""
        self.root_agent = LlmAgent(
            name="EnterpriseMCPAIAgentTeam",
            model="gemini-2.0-flash",
            description="Enterprise MCP AI Agent Team - Multi-agent system",
            instruction="""You are an Enterprise MCP AI Agent Team that routes tasks to specialized agents.
        
You have access to multiple specialized agents and can coordinate between them:

AVAILABLE AGENTS:
1. FileAnalysisAgent: Analyzes local documents (PDFs, Word docs, spreadsheets)
2. NotionAgent: Manages Notion pages, databases, and content
3. GitHubAgent: Manages GitHub repositories, issues, and pull requests  
4. FigmaAgent: Manages Figma files, designs, and assets

ROUTING LOGIC:
- File/document tasks → FileAnalysisAgent
- Notion-related tasks → NotionAgent
- GitHub-related tasks → GitHubAgent
- Figma/design tasks → FigmaAgent
- Multi-platform tasks → Coordinate between relevant agents

You can:
1. Transfer tasks to specialized agents using transfer_to_agent()
2. Coordinate multi-step workflows
3. Share context between agents through session state
4. Provide comprehensive results and recommendations

EXAMPLES:
- "List files in Documents" → FileAnalysisAgent
- "Search my Notion pages" → NotionAgent  
- "Create a GitHub repo" → GitHubAgent
- "Export Figma designs" → FigmaAgent

IMPORTANT: Use transfer_to_agent() to delegate to the most appropriate agent for each task.

For full MCP tool functionality, ensure all environment variables are set correctly:
- MCP_FILESYSTEM_PATH: Path to your filesystem folder
- NOTION_API_KEY: Your Notion API key
- GITHUB_API_KEY: Your GitHub API key
- FIGMA_API_KEY: Your Figma API key""",
            sub_agents=[
                LlmAgent(
                    name="FileAnalysisAgent",
                    model="gemini-2.0-flash",
                    description="Analyzes local documents and extracts key information",
                    instruction="You analyze local documents (PDFs, Word docs, spreadsheets) and extract key information, summaries, and action items."
                ),
                LlmAgent(
                    name="NotionAgent", 
                    model="gemini-2.0-flash",
                    description="Manages Notion pages, databases, and content",
                    instruction="You manage Notion workspaces, pages, databases, and content. You can read, write, search, and organize Notion content."
                ),
                LlmAgent(
                    name="GitHubAgent",
                    model="gemini-2.0-flash", 
                    description="Manages GitHub repositories, issues, and pull requests",
                    instruction="You manage GitHub repositories, create issues and pull requests, search code, and handle repository operations."
                ),
                LlmAgent(
                    name="FigmaAgent",
                    model="gemini-2.0-flash",
                    description="Manages Figma files, designs, and assets", 
                    instruction="You manage Figma design files, export assets, search design components, and handle design system operations."
                )
            ]
        )

# Create root_agent for ADK Web compatibility
try:
    orchestrator = EnterpriseMCPAIAgentTeam()
    root_agent = orchestrator.root_agent
    logger.info("✅ EnterpriseMCPAIAgentTeam class and root_agent created successfully")
except Exception as e:
    logger.error(f"❌ Failed to create EnterpriseMCPAIAgentTeam: {str(e)}")
    # Fallback: create basic root_agent
    root_agent = LlmAgent(
        name="EnterpriseMCPAIAgentTeam",
        model="gemini-2.0-flash",
        description="Enterprise MCP AI Agent Team - Basic multi-agent system",
        instruction="You are an Enterprise MCP AI Agent Team that routes tasks to specialized agents.",
        sub_agents=[]
    )