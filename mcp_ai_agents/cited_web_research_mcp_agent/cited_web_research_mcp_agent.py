import asyncio
import builtins
import json
import os
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from textwrap import dedent
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from openai import AsyncOpenAI


DEFAULT_MCP_SERVER_URL = "https://search.parallel.ai/mcp"
DEFAULT_MODEL = "gpt-4o-mini"
REQUEST_TIMEOUT_SECONDS = 120
MAX_TOOL_CALLS = 8
MAX_TOOL_RESULT_CHARS = 12000
REQUIRED_MCP_TOOLS = ("web_search", "web_fetch")


@dataclass
class ToolEvent:
    name: str
    arguments: dict[str, Any]
    preview: str
    is_error: bool = False


@dataclass
class ResearchResult:
    answer: str
    events: list[ToolEvent]
    available_tools: list[str]


def limit_text(value: str, max_chars: int = MAX_TOOL_RESULT_CHARS) -> str:
    if len(value) <= max_chars:
        return value
    return f"{value[:max_chars]}\n\n[truncated {len(value) - max_chars} characters]"


def extract_tool_text(result: object) -> str:
    parts = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            parts.append(text)
        else:
            parts.append(str(item))
    return "\n\n".join(parts)


def result_is_error(result: object) -> bool:
    return bool(getattr(result, "isError", False) or getattr(result, "is_error", False))


def explain_error(exc: BaseException) -> str:
    exception_group_type = getattr(builtins, "BaseExceptionGroup", None)
    if exception_group_type and isinstance(exc, exception_group_type):
        messages = [explain_error(child) for child in exc.exceptions]
        return "; ".join(message for message in messages if message) or str(exc)
    return str(exc) or exc.__class__.__name__


def mcp_tool_to_openai(tool: object) -> dict[str, Any]:
    input_schema = getattr(tool, "inputSchema", None) or {
        "type": "object",
        "properties": {},
    }
    if not isinstance(input_schema, dict):
        input_schema = {"type": "object", "properties": {}}
    if "type" not in input_schema:
        input_schema = {"type": "object", **input_schema}

    return {
        "type": "function",
        "function": {
            "name": getattr(tool, "name"),
            "description": getattr(tool, "description", "") or "",
            "parameters": input_schema,
        },
    }


def parse_tool_arguments(raw_arguments: str | None) -> dict[str, Any]:
    if not raw_arguments:
        return {}
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {"raw_arguments": raw_arguments}
    return parsed if isinstance(parsed, dict) else {"value": parsed}


def build_system_prompt() -> str:
    return dedent(
        """\
        You are a cited web research agent.

        Use the MCP web tools to answer questions that need current or sourced evidence.
        For every user question, call web_search at least once before final synthesis.
        Start by planning what evidence is needed, then call web_search with a clear
        objective and two to four targeted queries. Use web_fetch on the most relevant
        URLs before final synthesis when source pages are needed.

        Final answers must be grounded in tool results. Do not invent citations.
        Prefer primary sources when available. Separate facts from uncertainty.

        Start with a concise answer, then use these sections:
        - Evidence
        - Limitations
        - Sources
        """
    )


def apply_page_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            max-width: 920px;
            padding-top: 5rem;
            padding-bottom: 4rem;
        }

        .stTextArea textarea {
            min-height: 108px;
        }

        .stButton > button {
            min-width: 180px;
        }

        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li {
            line-height: 1.65;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


async def run_research_agent(
    question: str,
    openai_api_key: str,
    model: str,
    mcp_server_url: str,
    max_tool_calls: int = MAX_TOOL_CALLS,
) -> ResearchResult:
    client = AsyncOpenAI(api_key=openai_api_key)
    events: list[ToolEvent] = []

    async with streamablehttp_client(
        mcp_server_url,
        timeout=timedelta(seconds=REQUEST_TIMEOUT_SECONDS),
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed_tools = await session.list_tools()
            mcp_tools = {tool.name: tool for tool in listed_tools.tools}
            missing_tools = [name for name in REQUIRED_MCP_TOOLS if name not in mcp_tools]
            if missing_tools:
                raise RuntimeError(
                    "MCP server is missing required tools: " + ", ".join(missing_tools)
                )

            openai_tools = [
                mcp_tool_to_openai(mcp_tools[name]) for name in REQUIRED_MCP_TOOLS
            ]
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": question},
            ]
            tool_call_count = 0

            while True:
                if tool_call_count >= max_tool_calls:
                    response = await client.chat.completions.create(
                        model=model,
                        messages=[
                            *messages,
                            {
                                "role": "user",
                                "content": (
                                    "You have reached the MCP tool-call budget. "
                                    "Write the final answer using only the evidence "
                                    "already gathered."
                                ),
                            },
                        ],
                    )
                    answer = response.choices[0].message.content
                    return ResearchResult(
                        answer=answer or "No final answer was returned.",
                        events=events,
                        available_tools=sorted(mcp_tools),
                    )

                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto",
                )
                message = response.choices[0].message
                messages.append(message.model_dump(exclude_none=True))

                tool_calls = message.tool_calls or []
                if not tool_calls:
                    answer = message.content or "No final answer was returned."
                    return ResearchResult(
                        answer=answer,
                        events=events,
                        available_tools=sorted(mcp_tools),
                    )

                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    arguments = parse_tool_arguments(tool_call.function.arguments)

                    if tool_call_count >= max_tool_calls:
                        limit_text_message = (
                            "Skipped this tool call because the MCP tool-call budget "
                            "has already been reached."
                        )
                        events.append(
                            ToolEvent(tool_name, arguments, limit_text_message, True)
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": limit_text_message,
                            }
                        )
                        continue

                    tool_call_count += 1

                    if tool_name not in mcp_tools:
                        error_text = f"Unknown MCP tool requested: {tool_name}"
                        events.append(ToolEvent(tool_name, arguments, error_text, True))
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": error_text,
                            }
                        )
                        continue

                    try:
                        tool_result = await session.call_tool(tool_name, arguments)
                        tool_text = extract_tool_text(tool_result)
                        is_error = result_is_error(tool_result)
                        if is_error and not tool_text:
                            tool_text = f"{tool_name} returned an error."
                    except Exception as exc:
                        tool_text = f"Error calling {tool_name}: {exc}"
                        is_error = True

                    clipped_text = limit_text(tool_text)
                    events.append(
                        ToolEvent(
                            name=tool_name,
                            arguments=arguments,
                            preview=limit_text(tool_text, 1500),
                            is_error=is_error,
                        )
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": clipped_text,
                        }
                    )


def run_research_agent_sync(
    question: str,
    openai_api_key: str,
    model: str,
    mcp_server_url: str,
    max_tool_calls: int,
) -> ResearchResult:
    return asyncio.run(
        run_research_agent(
            question=question,
            openai_api_key=openai_api_key,
            model=model,
            mcp_server_url=mcp_server_url,
            max_tool_calls=max_tool_calls,
        )
    )


def render_tool_trace(events: list[ToolEvent]) -> None:
    if not events:
        st.info("No MCP tools were called.")
        return

    for index, event in enumerate(events, start=1):
        status = "error" if event.is_error else "ok"
        with st.expander(f"{index}. {event.name} ({status})"):
            st.markdown("Arguments")
            st.json(event.arguments)
            st.markdown("Result preview")
            st.code(event.preview or "(empty result)", language="text")


def main() -> None:
    load_dotenv(Path(__file__).with_name(".env"))

    st.set_page_config(
        page_title="Cited Web Research MCP Agent",
        layout="centered",
    )
    apply_page_styles()

    st.title("Cited Web Research MCP Agent")
    st.caption(
        "Ask a research question. The model plans searches, calls MCP web tools, "
        "fetches sources, and writes a cited answer."
    )

    with st.sidebar:
        st.header("Configuration")
        openai_api_key = st.text_input(
            "OpenAI API Key",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password",
        )
        model = st.text_input("OpenAI model", value=os.getenv("OPENAI_MODEL", DEFAULT_MODEL))
        mcp_server_url = st.text_input(
            "MCP server URL",
            value=os.getenv("MCP_SERVER_URL", DEFAULT_MCP_SERVER_URL),
        )
        max_tool_calls = st.slider(
            "Maximum MCP tool calls",
            min_value=2,
            max_value=12,
            value=MAX_TOOL_CALLS,
        )
        st.caption("The server must expose web_search and web_fetch.")

    default_question = (
        "What are the most important recent changes in Python packaging standards? "
        "Give me a concise answer with citations."
    )
    question = st.text_area(
        "Research question",
        value=default_question,
        height=108,
    )

    if st.button("Run cited research", type="primary"):
        if not openai_api_key.strip():
            st.error("Please enter an OpenAI API key.")
        elif not question.strip():
            st.error("Please enter a research question.")
        elif not mcp_server_url.strip():
            st.error("Please enter an MCP server URL.")
        else:
            with st.spinner("Planning searches, reading sources, and synthesizing..."):
                try:
                    result = run_research_agent_sync(
                        question=question.strip(),
                        openai_api_key=openai_api_key.strip(),
                        model=model.strip() or DEFAULT_MODEL,
                        mcp_server_url=mcp_server_url.strip(),
                        max_tool_calls=max_tool_calls,
                    )
                except Exception as exc:
                    st.error(f"Research failed: {explain_error(exc)}")
                    return

            st.markdown(result.answer)

            st.divider()
            with st.expander("MCP tool trace", expanded=False):
                st.caption("Available tools: " + ", ".join(result.available_tools))
                render_tool_trace(result.events)


if __name__ == "__main__":
    main()
