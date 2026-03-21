import asyncio
import os
import uuid
from textwrap import dedent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MultiMCPTools
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def main():
    print("\n" + "=" * 60)
    print("      AI Agent Discovery Assistant (Global Chat MCP)")
    print("=" * 60)
    print("Search 100K+ AI agents across MCP, A2A, and agents.txt")
    print("Validate agents.txt files for compliance")
    print("=" * 60 + "\n")

    if not OPENAI_API_KEY:
        print("ERROR: Missing OPENAI_API_KEY environment variable.")
        print("Set it in your .env file or environment.")
        return

    user_id = f"user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    print(f"User ID: {user_id}")
    print(f"Session ID: {session_id}")

    print("\nConnecting to Global Chat MCP server...\n")

    # Global Chat MCP server — agent discovery and agents.txt validation
    # Uses the published npm package @global-chat/mcp-server
    mcp_servers = [
        "npx -y @global-chat/mcp-server",
    ]

    async with MultiMCPTools(mcp_servers) as mcp_tools:
        print("Connected to Global Chat MCP server!")

        agent = Agent(
            name="AgentDiscoveryAssistant",
            model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
            tools=[mcp_tools],
            description="AI assistant for discovering and validating AI agents across protocols",
            instructions=dedent(f"""
                You are an AI agent discovery assistant powered by Global Chat.
                You help users find AI agents across multiple protocols and registries.

                CAPABILITIES:
                1. SEARCH AGENTS - Search the Global Chat directory of 100K+ agents
                   across MCP, A2A, agents.txt, and other protocols.
                   Use the search_agents tool with a query string.

                2. LIST AGENTS - Browse all registered agents, optionally filtered by type.
                   Use the list_agents tool.

                3. VALIDATE AGENTS.TXT - Check if a domain's agents.txt file is compliant
                   with the agents.txt specification. Use validate_agents_txt with a URL
                   or raw content.

                4. REGISTER AGENTS - Register new agents in the directory.
                   Use register_agent with name, type, and wallet_address.

                INTERACTION STYLE:
                - Present search results in a clear, organized format
                - Highlight agent capabilities and protocols
                - Suggest related searches when appropriate
                - Explain agents.txt validation results clearly

                SESSION INFO:
                - User ID: {user_id}
                - Session ID: {session_id}
            """),
            markdown=True,
            retries=3,
        )

        print("\n" + "=" * 58)
        print("  Agent Discovery Assistant is READY!")
        print("=" * 58 + "\n")

        print("Try these example commands:")
        print("  - 'Search for DeFi trading agents'")
        print("  - 'List all available agents'")
        print("  - 'Validate agents.txt for example.com'")
        print("  - 'Find agents with data analysis capabilities'")

        print("\nType 'exit', 'quit', or 'bye' to end the session\n")

        await agent.acli_app(
            user_id=user_id,
            session_id=session_id,
            user="You",
            stream=True,
            markdown=True,
            exit_on=["exit", "quit", "bye", "goodbye"],
        )


if __name__ == "__main__":
    asyncio.run(main())
