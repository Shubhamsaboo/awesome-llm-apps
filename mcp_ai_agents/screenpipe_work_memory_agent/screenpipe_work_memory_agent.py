import argparse
import asyncio
import json
import os
import shutil
import sys
from textwrap import dedent
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from dotenv import load_dotenv


load_dotenv()

HEALTH_URL = os.getenv("SCREENPIPE_HEALTH_URL", "http://localhost:3030/health")
MCP_COMMAND = os.getenv("SCREENPIPE_MCP_COMMAND", "npx -y screenpipe-mcp")
MODEL_ID = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def screenpipe_health(timeout: float = 3.0) -> tuple[bool, str]:
    request = Request(HEALTH_URL, headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except HTTPError as error:
        return False, f"screenpipe health check returned HTTP {error.code}"
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        return False, f"cannot reach screenpipe at {HEALTH_URL}: {error}"

    status = payload.get("status", "unknown")
    version = payload.get("version", "unknown")
    if response.status != 200:
        return False, f"screenpipe reported HTTP {response.status} ({status})"
    return True, f"screenpipe {version} is reachable ({status})"


def environment_errors(require_model: bool = True) -> list[str]:
    errors = []
    if shutil.which("npx") is None:
        errors.append("Node.js and npx are required to launch screenpipe-mcp")
    if require_model and not os.getenv("OPENAI_API_KEY"):
        errors.append(
            "OPENAI_API_KEY is required; for a local OpenAI-compatible server, "
            "set it to any non-empty value"
        )

    healthy, message = screenpipe_health()
    if not healthy:
        errors.append(message)
    return errors


def build_model() -> OpenAIChat:
    options = {
        "id": MODEL_ID,
        "api_key": os.environ["OPENAI_API_KEY"],
    }
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        options["base_url"] = base_url
    return OpenAIChat(**options)


def build_agent(mcp_tools: MCPTools) -> Agent:
    return Agent(
        name="ScreenpipeWorkMemoryAgent",
        model=build_model(),
        tools=[mcp_tools],
        description=(
            "An evidence-first work memory agent backed by the user's local "
            "screenpipe history."
        ),
        instructions=dedent(
            """
            You answer questions about the user's real computer activity using
            the screenpipe MCP tools.

            Rules:
            - Use screenpipe tools before answering questions about past work.
            - Treat tool results as evidence. Do not invent missing activity.
            - State the time range you searched and mention relevant apps,
              meetings, or speakers when the evidence includes them.
            - Prefer compact activity summaries before broad raw searches.
            - Narrow searches by time, app, window, speaker, or content type.
            - When asked for an SOP, reconstruct ordered steps and clearly mark
              any step that is inferred rather than directly observed.
            - When asked what to automate, identify repeated actions and cite
              the observed pattern before proposing an automation.
            - Avoid exposing unrelated sensitive content from tool results.
            """
        ),
        markdown=True,
        add_history_to_context=True,
        num_history_runs=5,
        retries=2,
    )


async def run_agent(query: str | None) -> None:
    env = os.environ.copy()
    async with MCPTools(command=MCP_COMMAND, env=env) as mcp_tools:
        agent = build_agent(mcp_tools)
        if query:
            response = await agent.arun(query)
            print(response.content)
            return

        await agent.acli_app(
            user="You",
            stream=True,
            markdown=True,
            exit_on=["exit", "quit", "bye"],
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask an AI agent about your local screenpipe work history."
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Run one question and exit. Omit it to start an interactive session.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check local prerequisites without starting the agent.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors = environment_errors(require_model=not args.check)
    if errors:
        print("Setup check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    healthy, message = screenpipe_health()
    print(message)
    if args.check:
        print("npx is available; setup is ready for an LLM key")
        return 0

    try:
        asyncio.run(run_agent(args.query))
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
