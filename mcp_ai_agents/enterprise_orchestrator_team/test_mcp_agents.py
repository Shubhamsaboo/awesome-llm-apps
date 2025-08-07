import asyncio
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from dotenv import load_dotenv
import os
load_dotenv()

SERVER_URL = os.getenv("COMPOSIO_GITHUB_MCP_URL")

async def run_mcp_agent():
    print("\n" + "="*60)
    print("           🧪 GitHub MCP Agent Test 🧪")
    print("="*60)
    print("💡 Test GitHub MCP tools with interactive chat")
    print("="*60 + "\n")
    
    if not SERVER_URL:
        print("❌ ERROR: COMPOSIO_GITHUB_MCP_URL not found in environment")
        return
    
    print(f"🔗 Connecting to GitHub MCP: {SERVER_URL}")
    
    async with MCPTools(url=SERVER_URL, transport="streamable-http") as mcp_tools:
        print("✅ GitHub MCP connected successfully!")
        
        # Initialize the Agent
        agent = Agent(
            model=OpenAIChat(id="gpt-4o"), 
            description="You are a helpful assistant that can do github related tasks using the mcp tools available to you",
            tools=[mcp_tools],
            markdown=True
        )
        
        print("🤖 GitHub Agent ready! You can now chat with it.")
        print("💡 Try asking about repositories, users, or GitHub operations")
        print("⚡ Type 'exit', 'quit', or 'bye' to end the session\n")
        
        # Interactive chat loop
        while True:
            try:
                # Get user input
                user_input = input("💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                    print("\n👋 Goodbye! Thanks for testing the GitHub MCP Agent.")
                    break
                
                if not user_input:
                    continue
                
                print("\n🤖 GitHub Agent: Processing your request...\n")
                
                # Get response from agent
                await agent.aprint_response(user_input, stream=True)
                print()  # Add spacing after response
                
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try again or type 'exit' to quit.\n")

if __name__ == "__main__":
    asyncio.run(run_mcp_agent())