import asyncio
import os
from dotenv import load_dotenv
from agno.agent import Agent 
from agno.team import Team
from agno.models.openai import OpenAIChat

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def create_simple_agents(llm):
    """Create simple agents without MCP tools for testing"""
    
    # File Analysis Agent (using simple file operations)
    file_analysis_agent = Agent(
        name="FileAnalysisAgent",
        model=llm,
        description="Expert in file system operations and document analysis",
        instructions="""
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
        """,
        tools=[],
        markdown=True,
        show_tool_calls=True
    )
    
    # Simple GitHub Agent (placeholder)
    github_agent = Agent(
        name="GitHubAgent",
        model=llm,
        description="Expert in GitHub repository management and code operations",
        instructions="""
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
            
            NOTE: This is a placeholder agent without MCP tools.
        """,
        tools=[],
        markdown=True,
        show_tool_calls=True
    )
    
    return file_analysis_agent, github_agent

def create_simple_team(llm):
    """Create a simple enterprise team for testing"""
    
    file_agent, github_agent = create_simple_agents(llm)
    
    return Team(
        name="🏢 Simple Enterprise Team",
        mode="route",
        model=llm,
        members=[file_agent, github_agent],
        instructions=[
            "You are a Simple Enterprise Team that routes tasks to specialized agents.",
            "",
            "🎯 TEAM MEMBERS & CAPABILITIES:",
            "1. FileAnalysisAgent: File system operations and document analysis",
            "2. GitHubAgent: Repository management and code operations (placeholder)",
            "",
            "🔄 ROUTING RULES:",
            "- File/folder/document operations → FileAnalysisAgent",
            "- GitHub repos/code/version control → GitHubAgent",
            "",
            "IMPORTANT: Route tasks intelligently and provide comprehensive solutions."
        ],
        show_members_responses=True,
        markdown=True,
        show_tool_calls=True,
    )

async def main():
    print("\n" + "="*60)
    print("           🧪 Simple Enterprise Team Test 🧪")
    print("="*60)
    print("💡 Testing basic team functionality without MCP tools")
    print("="*60 + "\n")
    
    # Validate required environment variables
    if not OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not found")
        print("Please check your .env file and ensure OPENAI_API_KEY is set.")
        return
    
    try:
        # Initialize LLM and team
        llm = OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY)
        simple_team = create_simple_team(llm)
        
        print("✅ Simple Enterprise Team initialized successfully!")
        
        # Display agent status
        print("\n🤖 Agent Status:")
        print("   📁 File Analysis Agent: ✅ Ready")
        print("   💻 GitHub Agent: ✅ Ready (placeholder)")
        
        print("\n" + "🎉 " + "="*40 + " 🎉")
        print("   Simple Test is READY!")
        print("🎉 " + "="*40 + " 🎉\n")
        
        print("💡 Try these example commands:")
        print("   • 'List files in my current directory'")
        print("   • 'What can you do with GitHub?'")
        print("   • 'Help me organize my files'")
        
        print("⚡ Type 'exit', 'quit', or 'bye' to end the session\n")
        
        # Simple terminal interface
        while True:
            try:
                # Get user input
                user_input = input("💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    print("\n👋 Goodbye! Thanks for testing!")
                    break
                
                if not user_input:
                    continue
                
                print("\n🤖 Simple Team: Processing your request...\n")
                
                # Get response from team
                response = simple_team.run(user_input)
                
                print(f"🤖 Simple Team: {response.content}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try again or type 'exit' to quit.\n")
        
    except Exception as e:
        print(f"❌ Error initializing Simple Team: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check your OpenAI API key in .env file")
        print("2. Ensure you have the required dependencies installed")
        print("3. Verify your internet connection")
        return

if __name__ == "__main__":
    asyncio.run(main()) 