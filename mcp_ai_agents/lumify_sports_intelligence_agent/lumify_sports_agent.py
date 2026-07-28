import asyncio
import os
import sys
import uuid
from textwrap import dedent

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools, StreamableHTTPClientParams
from dotenv import load_dotenv

load_dotenv()

LUMIFY_API_KEY = os.getenv("LUMIFY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LUMIFY_MCP_URL = os.getenv("LUMIFY_MCP_URL", "https://lumify.ai/mcp")


async def main():
    print("\n========================================")
    print(" Lumify Sports Intelligence Agent")
    print("========================================\n")

    if not LUMIFY_API_KEY:
        print("No LUMIFY_API_KEY set - grab a free instant key (no signup) at")
        print("https://lumify.ai/docs/ai, or a persistent one at https://lumify.ai/api-keys")
        print("Continuing without auth: discovery works, but tool calls will fail.\n")

    user_id = f"user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    print("Connecting to the Lumify MCP server...\n")

    server_params = StreamableHTTPClientParams(
        url=LUMIFY_MCP_URL,
        headers={"Authorization": f"Bearer {LUMIFY_API_KEY}"} if LUMIFY_API_KEY else {},
    )

    async with MCPTools(server_params=server_params, transport="streamable-http") as mcp_tools:
        print("Connected! Lumify's sports intelligence tools are ready.\n")
        db = SqliteDb(db_file="agno.db")

        agent = Agent(
            name="LumifySportsAgent",
            model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
            tools=[mcp_tools],
            description="Agent that answers sports schedule, odds, and bet-confidence questions via the Lumify MCP server",
            instructions=dedent("""
                You are a sports intelligence assistant backed by the Lumify API
                (schedules, live scores, odds, line movement, public betting splits,
                and explainable AI bet confidence across MLB, NFL, NCAAF, NCAAB, NBA,
                NHL, tennis, and soccer).

                IMPORTANT INSTRUCTIONS:
                1. Use the Lumify MCP tools directly - don't guess at scores, odds, or
                   schedules.
                2. Every `tools/call` other than `estimate_cost` costs Lumify credits.
                   If a user asks "how much would this cost", call `estimate_cost`
                   first - it is always free.
                3. Calls for odds/intelligence/splits on a match that isn't priced yet
                   return `available: false` at no charge - explain that plainly
                   instead of treating it as an error.
                4. `get_splits` only has data for MLB, NBA, NHL, and NFL.
                5. When asked for "the best bet" or similar judgment calls, use
                   `get_intelligence` and explain the confidence/reasoning it returns
                   rather than inventing your own pick.
                6. Be concise. Cite the sport, teams, and timeframe you actually
                   queried so answers are easy to verify.
            """),
            markdown=True,
            retries=3,
            db=db,
            add_history_to_context=True,
            num_history_runs=5,
        )

        print("Lumify Sports Intelligence Agent is ready! Ask about schedules, odds,")
        print("live scores, or bet confidence for any supported sport.\n")
        print("Type 'exit', 'quit', or 'bye' to end the conversation.\n")

        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
            await agent.aprint_response(input=query, stream=True, markdown=True)
            return

        await agent.acli_app(
            user_id=user_id,
            session_id=session_id,
            user="You",
            emoji="🏆",
            stream=True,
            markdown=True,
            exit_on=["exit", "quit", "bye", "goodbye"],
        )


if __name__ == "__main__":
    asyncio.run(main())
