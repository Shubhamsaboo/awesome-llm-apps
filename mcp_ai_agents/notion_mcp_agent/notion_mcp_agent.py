import asyncio
import json
import os
import sys
import uuid
from textwrap import dedent
from agno.agent import Agent 
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools 
from agno.memory.v2 import Memory
from mcp import StdioServerParameters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

async def main():
    print("\n========================================")
    print("      Notion MCP Terminal Agent")
    print("========================================\n")
    
    # Get configuration from environment or use defaults
    notion_token = NOTION_TOKEN
    openai_api_key = OPENAI_API_KEY
    
    # Prompt for page ID first
    if len(sys.argv) > 1:
        # Use command-line argument if provided
        page_id = sys.argv[1]
        print(f"Using provided page ID from command line: {page_id}")
    else:
        # Ask the user for the page ID
        print("Please enter your Notion page ID:")
        print("(You can find this in your page URL, e.g., https://www.notion.so/workspace/Your-Page-1f5b8a8ba283...)")
        print("The ID is the part after the last dash and before any query parameters")
        
        user_input = input("> ")
        
        # If user input is empty, use default
        if user_input.strip():
            page_id = user_input.strip()
            print(f"Using provided page ID: {page_id}")
        else:
            print(f"Using default page ID: {page_id}")
    
    # Generate unique user and session IDs for this terminal session
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")
    
    print("\nConnecting to Notion MCP server...\n")
    
    # Configure the MCP Tools
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@notionhq/notion-mcp-server"],
        env={
            "OPENAPI_MCP_HEADERS": json.dumps(
                {"Authorization": f"Bearer {notion_token}", "Notion-Version": "2022-06-28"}
            )
        }
    )
    
    # Start the MCP Tools session
    async with MCPTools(server_params=server_params) as mcp_tools:
        print("Connected to Notion MCP server successfully!")
        
        # Create the agent
        agent = Agent(
            name="NotionDocsAgent",
            model=OpenAIChat(id="gpt-4o", api_key=openai_api_key),
            tools=[mcp_tools],
            description="Agent to query and modify Notion docs via MCP",
            instructions=dedent(f"""
                You are an expert Notion assistant that helps users interact with their Notion pages.
                
                IMPORTANT INSTRUCTIONS:
                1. You have direct access to Notion documents through MCP tools - make full use of them.
                2. ALWAYS use the page ID: {page_id} for all operations unless the user explicitly provides another ID.
                3. When asked to update, read, or search pages, ALWAYS use the appropriate MCP tool calls.
                4. Be proactive in suggesting actions users can take with their Notion documents.
                5. When making changes, explain what you did and confirm the changes were made.
                6. If a tool call fails, explain the issue and suggest alternatives.
                
                Example tasks you can help with:
                - Reading page content
                - Searching for specific information
                - Adding new content or updating existing content
                - Creating lists, tables, and other Notion blocks
                - Explaining page structure
                - Adding comments to specific blocks
                
                The user's current page ID is: {page_id}
            """),
            markdown=True,
            show_tool_calls=True,
            retries=3,
            memory=Memory(),  # Use Memory v2 for better multi-session support
            add_history_to_messages=True,  # Include conversation history
            num_history_runs=5,  # Keep track of the last 5 interactions
        )
        
        print("\n\nNotion MCP Agent is ready! Start chatting with your Notion pages.\n")
        print("Type 'exit' or 'quit' to end the conversation.\n")
        
        # Start interactive CLI session with memory and proper session management
        await agent.acli_app(
            user_id=user_id,
            session_id=session_id,
            user="You",
            emoji="🤖",
            stream=True,
            markdown=True,
            exit_on=["exit", "quit", "bye", "goodbye"]
        )

if __name__ == "__main__":
    asyncio.run(main())