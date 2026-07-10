"""Bridge remote MCP tools into a raw OpenAI function-calling loop."""

import argparse
import asyncio
import builtins
import json
import os
import re
from datetime import timedelta
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import AsyncOpenAI


DEFAULT_MCP_SERVER_URL = "https://search.parallel.ai/mcp"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_MAX_TOOL_CALLS = 6
READ_TIMEOUT_SECONDS = 120
MAX_TOOL_RESULT_CHARS = 12_000
MAX_TRACE_CHARS = 500
OPENAI_FUNCTION_NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def limit_text(text: str, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
    """Bound text before it enters model context or the terminal trace."""
    if len(text) <= max_chars:
        return text
    omitted = len(text) - max_chars
    return f"{text[:max_chars]}\n[truncated {omitted} characters]"


def explain_error(exc: BaseException) -> str:
    """Flatten nested task-group errors into a readable message."""
    group_type = getattr(builtins, "BaseExceptionGroup", None)
    if group_type and isinstance(exc, group_type):
        messages = [explain_error(child) for child in exc.exceptions]
        return "; ".join(message for message in messages if message)
    return str(exc) or exc.__class__.__name__


async def list_all_tools(session: ClientSession) -> list[Any]:
    """Collect every page returned by MCP tool discovery."""
    tools: list[Any] = []
    cursor = None
    while True:
        page = await session.list_tools(cursor=cursor)
        tools.extend(page.tools)
        cursor = getattr(page, "nextCursor", None)
        if not cursor:
            return tools


def mcp_tool_to_openai(tool: Any) -> dict[str, Any]:
    """Convert one compatible MCP tool definition to OpenAI's format."""
    name = getattr(tool, "name", "")
    if not OPENAI_FUNCTION_NAME.fullmatch(name):
        raise ValueError(
            f"MCP tool name {name!r} is not a valid OpenAI function name "
            "(use 1-64 letters, numbers, underscores, or hyphens)."
        )

    input_schema = getattr(tool, "inputSchema", None)
    if input_schema is None:
        input_schema = {}
    if not isinstance(input_schema, dict) or input_schema.get("type", "object") != "object":
        raise ValueError(f"MCP tool {name!r} must have an object input schema.")

    parameters = dict(input_schema)
    parameters.setdefault("type", "object")
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": getattr(tool, "description", "") or "",
            "parameters": parameters,
        },
    }


def tool_result_text(result: Any) -> str:
    """Extract bounded model-safe text without copying binary payloads."""
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return limit_text(json.dumps(structured, ensure_ascii=False, default=str))

    parts: list[str] = []
    for block in getattr(result, "content", None) or []:
        block_type = getattr(block, "type", block.__class__.__name__)
        text = getattr(block, "text", None)
        if block_type == "text" and isinstance(text, str):
            parts.append(text)
        else:
            parts.append(f"[{block_type} content omitted]")
    return limit_text("\n\n".join(parts) or "(no text result)")


def select_tools(tools: list[Any], selected_names: list[str] | None) -> list[Any]:
    """Return all discovered tools or a validated caller-selected subset."""
    if not selected_names:
        return tools
    if len(selected_names) != len(set(selected_names)):
        raise ValueError("--tools contains duplicate names.")

    by_name = {tool.name: tool for tool in tools}
    missing = [name for name in selected_names if name not in by_name]
    if missing:
        raise ValueError("Unknown MCP tool(s): " + ", ".join(missing))
    return [by_name[name] for name in selected_names]


async def run_bridge(
    task: str | None,
    api_key: str | None,
    model: str,
    server_url: str,
    selected_names: list[str] | None,
    max_tool_calls: int,
) -> str | None:
    """Own the remote MCP lifecycle and OpenAI-to-MCP dispatch loop."""
    print(f"[connect] {server_url}")
    async with streamable_http_client(server_url) as (read_stream, write_stream, _):
        async with ClientSession(
            read_stream,
            write_stream,
            read_timeout_seconds=timedelta(seconds=READ_TIMEOUT_SECONDS),
        ) as session:
            await session.initialize()
            discovered = await list_all_tools(session)
            print(f"[discover] {len(discovered)} tool(s)")

            if task is None:
                for tool in discovered:
                    description = (tool.description or "No description").splitlines()[0]
                    print(f"- {tool.name}: {description}")
                return None

            exposed = select_tools(discovered, selected_names)
            openai_tools = [mcp_tool_to_openai(tool) for tool in exposed]
            if not openai_tools:
                raise ValueError("The MCP server did not expose any selected tools.")

            tool_names = {tool.name for tool in exposed}
            print("[tools] " + ", ".join(sorted(tool_names)))
            print("[convert] MCP inputSchema -> OpenAI function parameters")
            messages: list[dict[str, Any]] = [
                {
                    "role": "system",
                    "content": (
                        "Use the available tools when needed to complete the task. "
                        "Ground factual claims in tool results and never invent tool output."
                    ),
                },
                {"role": "user", "content": task},
            ]
            requested_calls = 0

            async with AsyncOpenAI(api_key=api_key) as client:
                while True:
                    request: dict[str, Any] = {"model": model, "messages": messages}
                    if requested_calls < max_tool_calls:
                        request.update(
                            tools=openai_tools,
                            tool_choice="auto",
                            parallel_tool_calls=False,
                        )
                    response = await client.chat.completions.create(**request)
                    message = response.choices[0].message
                    messages.append(message.model_dump(exclude_none=True))
                    tool_calls = message.tool_calls or []
                    if not tool_calls:
                        answer = message.content or "No final answer was returned."
                        print(f"[final] {answer}")
                        return answer

                    for tool_call in tool_calls:
                        requested_calls += 1
                        name = tool_call.function.name
                        raw_arguments = tool_call.function.arguments or "{}"
                        print(
                            f"[openai -> mcp] {name} {limit_text(raw_arguments, MAX_TRACE_CHARS)}"
                        )

                        if requested_calls > max_tool_calls:
                            result_text = "Skipped: the MCP tool-call budget is exhausted."
                        elif name not in tool_names:
                            result_text = f"Error: unknown MCP tool {name!r}."
                        else:
                            try:
                                arguments = json.loads(raw_arguments)
                                if not isinstance(arguments, dict):
                                    raise ValueError("tool arguments must be a JSON object")
                            except (json.JSONDecodeError, ValueError) as exc:
                                result_text = f"Error: invalid tool arguments: {exc}"
                            else:
                                try:
                                    result = await session.call_tool(name, arguments)
                                    result_text = tool_result_text(result)
                                    if getattr(result, "isError", False) or getattr(
                                        result, "is_error", False
                                    ):
                                        result_text = "MCP tool error: " + result_text
                                except Exception as exc:
                                    result_text = f"Error calling MCP tool: {explain_error(exc)}"

                        print(f"[mcp -> openai] {limit_text(result_text, MAX_TRACE_CHARS)}")
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": result_text,
                            }
                        )

                    if requested_calls >= max_tool_calls:
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "The tool-call budget is exhausted. Answer using only "
                                    "the results already returned."
                                ),
                            }
                        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bridge a trusted remote MCP server into raw OpenAI tool calling."
    )
    parser.add_argument("task", nargs="?", help="Task for the model; omit with --list-tools")
    parser.add_argument("--list-tools", action="store_true", help="Discover tools without OpenAI")
    parser.add_argument("--server-url", default=os.getenv("MCP_SERVER_URL", DEFAULT_MCP_SERVER_URL))
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--tools", help="Optional comma-separated discovered tool names")
    parser.add_argument("--max-tool-calls", type=int, default=DEFAULT_MAX_TOOL_CALLS)
    args = parser.parse_args()
    if args.list_tools:
        args.task = None
    elif not args.task:
        parser.error("provide a task or use --list-tools")
    if args.max_tool_calls < 1:
        parser.error("--max-tool-calls must be at least 1")

    api_key = os.getenv("OPENAI_API_KEY")
    if args.task and not api_key:
        raise SystemExit("OPENAI_API_KEY is required when running a task.")
    selected_names = [name.strip() for name in args.tools.split(",")] if args.tools else None
    if selected_names and any(not name for name in selected_names):
        raise SystemExit("--tools must be a comma-separated list of non-empty names.")

    try:
        asyncio.run(
            run_bridge(
                args.task,
                api_key,
                args.model,
                args.server_url,
                selected_names,
                args.max_tool_calls,
            )
        )
    except Exception as exc:
        raise SystemExit(f"Bridge failed: {explain_error(exc)}") from None


if __name__ == "__main__":
    main()
