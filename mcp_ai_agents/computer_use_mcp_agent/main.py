# Computer Use MCP Agent
# Terminal agent that drives the screen-control MCP server with an
# OpenAI-compatible tool-calling loop.
#
# Usage:
#   python main.py --list-tools
#   python main.py "Open Notepad, type hello, read it back with OCR"
#   python main.py --api-base https://api.groq.com/openai/v1 --model llama-3.3-70b-versatile "..."

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import sys

from openai import OpenAI

try:
    from mcp import ClientSession
    # mcp >= 2.0 renamed streamablehttp_client -> streamable_http_client and
    # moved custom headers into a pre-built http client.
    from mcp.client.streamable_http import streamable_http_client as _http_client
    from mcp.shared._httpx_utils import create_mcp_http_client

    def _connect(url: str, headers: dict[str, str]):
        client = create_mcp_http_client(headers=headers)
        return _http_client(url, http_client=client)
except ImportError:  # mcp 1.x
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client as _http_client

    def _connect(url: str, headers: dict[str, str]):
        return _http_client(url, headers=headers)

SYSTEM_PROMPT = (
    "You control a real Windows desktop through tools. Use screenshot or "
    "ocr_screen to see the screen, list_windows to find targets, and "
    "mouse/keyboard/window_post to act. Prefer read-only tools first and "
    "verify the result of each action with a screenshot before the next "
    "step. Coordinates come from screenshots or window geometry, never "
    "guesswork. Stop as soon as the task is done and report what you did."
)


def resolve_token(args: argparse.Namespace) -> str:
    if args.token:
        return args.token
    if args.token_file and os.path.isfile(args.token_file):
        with open(args.token_file, "r", encoding="utf-8") as fh:
            return fh.read().strip()
    env = os.environ.get("SCREEN_CONTROL_TOKEN")
    if env:
        return env
    print(
        "No session token. Copy the screen-control .token file into this "
        "directory, or pass --token-file /path/to/screen-control/.token"
    )
    sys.exit(1)


def to_openai_schema(tool) -> dict:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.inputSchema or {"type": "object", "properties": {}},
        },
    }


def result_to_content(result, tool_name: str) -> tuple[str, list[dict]]:
    """Split an MCP result into (text, image_parts) for the chat history."""
    texts, images = [], []
    for item in result.content:
        kind = getattr(item, "type", None)
        if kind == "text":
            texts.append(item.text)
        elif kind == "image":
            uri = "data:{};base64,{}".format(item.mimeType, item.data)
            images.append({"type": "image_url",
                           "image_url": {"url": uri}})
    prefix = "ERROR: " if getattr(result, "is_error", getattr(result, "isError", False)) else ""
    text = prefix + ("\n".join(texts) if texts else "(no output)")
    if images:
        images.insert(0, {"type": "text", "text": "Result of {}: {}".format(tool_name, text)})
    return text, images


def print_tools(tools) -> None:
    print("{} tools available:\n".format(len(tools)))
    for t in tools:
        desc = (t.description or "").strip().splitlines()[0]
        print("  {:<20} {}".format(t.name, desc))


async def run_task(session: ClientSession, tools, client: OpenAI,
                   model: str, task: str, max_steps: int) -> None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    for step in range(1, max_steps + 1):
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=tools)
        msg = resp.choices[0].message
        if not msg.tool_calls:
            print("\nAgent: {}".format(msg.content))
            return
        messages.append(msg.model_dump(exclude_none=True))
        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            print("  [step {:>2}] {} {}".format(step, call.function.name, args))
            result = await session.call_tool(call.function.name, args)
            text, images = result_to_content(result, call.function.name)
            messages.append({"role": "tool",
                             "tool_call_id": call.id,
                             "content": text})
            if images:
                messages.append({"role": "user", "content": images})
    print("\nStopped after {} steps without a final answer.".format(max_steps))


async def amain(args: argparse.Namespace) -> None:
    url = args.base_url.rstrip("/") + args.mcp_path
    token = resolve_token(args)
    headers = {"X-Auth-Token": token}

    async with _connect(url, headers) as streams:
        r, w = streams[0], streams[1]  # mcp 1.x yields (r, w, session_id)
        async with ClientSession(r, w) as session:
            await session.initialize()
            listed = await session.list_tools()
            tools = listed.tools
            if args.list_tools:
                print_tools(tools)
                return

            schemas = [to_openai_schema(t) for t in tools]
            client = OpenAI(
                api_key=args.api_key or os.environ.get("OPENAI_API_KEY", "sk-none"),
                base_url=args.api_base,
            )
            tasks = args.task or [line.strip() for line in sys.stdin if line.strip()]
            for task in tasks:
                print("\nTask: {}\n".format(task))
                await run_task(session, schemas, client, args.model, task,
                               args.max_steps)


def main() -> None:
    ap = argparse.ArgumentParser(description="Computer Use MCP Agent")
    ap.add_argument("task", nargs="*", help="natural-language task(s)")
    ap.add_argument("--list-tools", action="store_true",
                    help="print the server's tools and exit")
    ap.add_argument("--api-base", default=os.environ.get("OPENAI_API_BASE",
                    "https://api.openai.com/v1"))
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--api-key", default=None,
                    help="defaults to OPENAI_API_KEY")
    ap.add_argument("--base-url", default="http://127.0.0.1:8751",
                    help="screen-control MCP endpoint base")
    ap.add_argument("--mcp-path", default="/mcp")
    ap.add_argument("--token", default=None, help="session token")
    ap.add_argument("--token-file", default=".token",
                    help="file holding the session token (default: .token)")
    ap.add_argument("--max-steps", type=int, default=12)
    args = ap.parse_args()

    try:
        asyncio.run(amain(args))
    except Exception as exc:
        print("Failed: {}".format(exc))
        print("Is the server running? From the screen-control checkout:\n"
              "  python server.py\n"
              "  python mcp_server.py --http --port 8751")
        sys.exit(1)


if __name__ == "__main__":
    main()
