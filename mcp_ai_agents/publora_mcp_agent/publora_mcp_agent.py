"""Terminal agent that drafts and schedules social posts through the Publora MCP server.

Publora is a remote MCP server, so there is nothing to install locally: the agent
connects over streamable HTTP and authenticates with an API key.
"""

import asyncio
import os
import uuid
from textwrap import dedent

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools, StreamableHTTPClientParams
from dotenv import load_dotenv

load_dotenv()

PUBLORA_MCP_URL = "https://mcp.publora.com/mcp"
PUBLORA_API_KEY = os.getenv("PUBLORA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

INSTRUCTIONS = dedent(
    """\
    You publish and schedule social media posts through Publora.

    Read the connections first. Call `list_connections` before anything else and
    copy each target's `platformId` verbatim into the next call. Never invent or
    shorten an id — a guessed id is the usual reason a post silently goes nowhere.
    If the network the user asked for is not connected, say so and stop.

    Default to a draft. `create_post` without `scheduledTime` stores a draft;
    with `scheduledTime` it queues the post. Schedule only when the user gave a
    time, and use ISO 8601 in UTC. A draft that should have been a post costs one
    click; a post that should have been a draft cannot be recalled.

    Show the text and the target accounts before anything goes out, and wait for
    a yes. Repeat the stored time back from the response rather than the time you
    were asked for — the server may adjust it.

    Respect the platform rules. Instagram, TikTok and YouTube reject a text-only
    post; attach media with `mediaUrls` or leave those networks out. When one post
    goes to several networks, the strictest caption limit applies.

    To test without publishing, send a post to the reserved `publora-playground`
    target. It is acknowledged and discarded, and it must be the only entry in
    `platforms`.
    """
)

EXAMPLES = [
    "Which social accounts do I have connected?",
    "Draft a LinkedIn post about our new changelog page and keep it as a draft.",
    "Schedule that draft for tomorrow at 9:00 UTC.",
    "What do I have scheduled this week?",
]


async def main() -> None:
    if not PUBLORA_API_KEY:
        print("PUBLORA_API_KEY is not set. Get one at publora.com -> Settings -> API.")
        return
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY is not set.")
        return

    print("\n=======================================")
    print("     Publora MCP Terminal Agent")
    print("=======================================\n")

    server_params = StreamableHTTPClientParams(
        url=PUBLORA_MCP_URL,
        headers={"Authorization": f"Bearer {PUBLORA_API_KEY}"},
    )
    mcp_tools = MCPTools(server_params=server_params, transport="streamable-http")

    print(f"Connecting to {PUBLORA_MCP_URL} ...\n")
    await mcp_tools.connect()

    agent = Agent(
        model=OpenAIChat(id="gpt-4o", api_key=OPENAI_API_KEY),
        tools=[mcp_tools],
        instructions=INSTRUCTIONS,
        db=SqliteDb(db_file="publora_agent.db"),
        session_id=f"session_{uuid.uuid4().hex[:8]}",
        add_history_to_context=True,
        markdown=True,
    )

    print("Connected. Try one of these, or type your own:\n")
    for example in EXAMPLES:
        print(f"  - {example}")
    print("\nType 'exit' to quit.\n")

    try:
        while True:
            message = input("> ").strip()
            if message.lower() in {"exit", "quit"}:
                break
            if not message:
                continue
            print()
            await agent.aprint_response(message, stream=True)
            print()
    finally:
        await mcp_tools.close()
        print("\nDisconnected.")


if __name__ == "__main__":
    asyncio.run(main())
