import asyncio
import json
import uuid
from datetime import timedelta
from typing import Any

import streamlit as st
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


PARALLEL_SEARCH_MCP_URL = "https://search.parallel.ai/mcp"
CURSOR_INSTALL_URL = (
    "https://cursor.com/en/install-mcp?"
    "name=Parallel%20Search%20MCP&"
    "config=eyJ1cmwiOiJodHRwczovL3NlYXJjaC5wYXJhbGxlbC5haS9tY3AifQ=="
)
VSCODE_INSTALL_URL = (
    "https://insiders.vscode.dev/redirect/mcp/install?"
    "name=Parallel%20Search%20MCP&"
    "config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fsearch.parallel.ai%2Fmcp%22%7D"
)
REQUEST_TIMEOUT_SECONDS = 120
MAX_DISPLAY_EXCERPTS = 3
SAMPLE_AGENT_PROMPT = "Which AI products shipped this week? Give me a short list with sources."

CLIENT_INSTALL_OPTIONS = {
    "Claude Code": {
        "install_title": "Run this command in your terminal",
        "install_note": "This adds Parallel Search as a remote MCP server.",
        "verify": "In Claude Code, run `/mcp` to see `parallel-search` in your connected servers.",
        "language": "bash",
        "snippet": "claude mcp add --transport http parallel-search https://search.parallel.ai/mcp",
    },
    "Codex": {
        "install_title": "Run this command in your terminal",
        "install_note": "This adds Parallel Search as a remote MCP server.",
        "verify": "Run `codex mcp list` to confirm `parallel-search` is registered, then restart Codex.",
        "language": "bash",
        "snippet": "codex mcp add parallel-search --url https://search.parallel.ai/mcp",
    },
    "Cursor": {
        "install_title": "Add Parallel Search to Cursor",
        "install_note": "One click installs Parallel Search as a remote MCP server in Cursor.",
        "action_label": "Add to Cursor",
        "action_url": CURSOR_INSTALL_URL,
        "verify": "Confirm the install when Cursor opens, then check Settings > MCP to see `Parallel Search MCP` enabled.",
        "language": "json",
        "snippet": json.dumps(
            {
                "mcpServers": {
                    "Parallel Search MCP": {
                        "url": PARALLEL_SEARCH_MCP_URL,
                    }
                }
            },
            indent=2,
        ),
    },
    "VS Code": {
        "install_title": "Add Parallel Search to VS Code",
        "install_note": "One click installs Parallel Search as a remote MCP server in VS Code.",
        "action_label": "Add to VS Code",
        "action_url": VSCODE_INSTALL_URL,
        "verify": "Confirm the install when VS Code opens. The server then appears under MCP Servers in your settings.",
        "language": "json",
        "snippet": json.dumps(
            {
                "servers": {
                    "Parallel Search MCP": {
                        "type": "http",
                        "url": PARALLEL_SEARCH_MCP_URL,
                    }
                }
            },
            indent=2,
        ),
    },
}

AGENT_INSTALL_PROMPT = """Please add Parallel Search MCP to this agent so you can search the live web.

- Server URL: https://search.parallel.ai/mcp
- Transport: Streamable HTTP
- Authentication: no auth by default; the server is free to use without an API key

First, identify which MCP client you are running inside: Claude Code, Codex, Cursor, VS Code, or another MCP-compatible client. Then add the server to that client's MCP config using the mechanism it expects.

After the config is in place, tell me whether the client needs to be restarted. Then confirm the server connects, lists `web_search` and `web_fetch`, and can answer this test prompt:

Which AI products shipped this week? Give me a short list with sources."""


def parse_lines(value: str) -> list[str]:
    return [item.strip() for item in value.replace(",", "\n").splitlines() if item.strip()]


def extract_tool_text(result: object) -> str:
    parts = []
    for item in getattr(result, "content", []) or []:
        text = getattr(item, "text", None)
        if text:
            parts.append(text)
    return "\n\n".join(parts)


async def call_parallel_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    async with streamablehttp_client(
        PARALLEL_SEARCH_MCP_URL,
        timeout=timedelta(seconds=REQUEST_TIMEOUT_SECONDS),
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)

    text = extract_tool_text(result)
    if getattr(result, "isError", False):
        raise RuntimeError(text or f"Parallel Search MCP returned an error from {tool_name}.")

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Parallel Search MCP returned non-JSON output: {text[:500]}") from exc


def call_parallel_tool_sync(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(call_parallel_tool(tool_name, arguments))


def run_web_search(objective: str, search_queries: list[str], session_id: str) -> dict[str, Any]:
    return call_parallel_tool_sync(
        "web_search",
        {
            "objective": objective,
            "search_queries": search_queries,
            "session_id": session_id,
        },
    )


def run_web_fetch(urls: list[str], objective: str, session_id: str) -> dict[str, Any]:
    arguments: dict[str, Any] = {
        "urls": urls,
        "session_id": session_id,
    }
    if objective:
        arguments["objective"] = objective

    return call_parallel_tool_sync("web_fetch", arguments)


def render_results(payload: dict[str, Any]) -> None:
    results = payload.get("results", [])
    if not results:
        st.info("No results returned.")
        return

    for result in results:
        title = result.get("title") or result.get("url", "Untitled result")
        url = result.get("url", "")
        publish_date = result.get("publish_date")

        if url:
            st.markdown(f"#### [{title}]({url})")
        else:
            st.markdown(f"#### {title}")

        if publish_date:
            st.caption(f"Published: {publish_date}")

        excerpts = result.get("excerpts") or []
        for excerpt in excerpts[:MAX_DISPLAY_EXCERPTS]:
            st.markdown(excerpt)

        if len(excerpts) > MAX_DISPLAY_EXCERPTS:
            with st.expander(f"Show {len(excerpts) - MAX_DISPLAY_EXCERPTS} more excerpts"):
                for excerpt in excerpts[MAX_DISPLAY_EXCERPTS:]:
                    st.markdown(excerpt)

        st.divider()


def main() -> None:
    st.set_page_config(page_title="Free Web Search MCP Starter", page_icon="🔎", layout="wide")

    if "parallel_mcp_session_id" not in st.session_state:
        st.session_state.parallel_mcp_session_id = uuid.uuid4().hex

    st.title("🔎 Free Web Search MCP Starter")
    st.caption("Try Parallel Search MCP with no API keys, then add the same endpoint to your agent.")

    with st.sidebar:
        st.header("MCP Endpoint")
        st.code(PARALLEL_SEARCH_MCP_URL, language="text")
        st.caption("Tools: web_search, web_fetch")

    search_tab, fetch_tab, agent_tab = st.tabs(["Search", "Fetch URL", "Add To Agent"])

    with search_tab:
        objective = st.text_area(
            "Objective",
            value="Find current information about Parallel Search MCP.",
            height=100,
        )
        search_queries_text = st.text_area(
            "Search Queries",
            value="Parallel Search MCP\nfree web search MCP",
            height=100,
            help="One query per line, or comma-separated.",
        )

        if st.button("🔎 Run Web Search", type="primary", use_container_width=True):
            search_queries = parse_lines(search_queries_text)
            if not objective.strip():
                st.warning("Please enter a search objective.")
            elif not search_queries:
                st.warning("Please enter at least one search query.")
            else:
                with st.spinner("Calling Parallel Search MCP web_search..."):
                    try:
                        payload = run_web_search(
                            objective.strip(),
                            search_queries,
                            st.session_state.parallel_mcp_session_id,
                        )
                        render_results(payload)
                    except Exception as exc:
                        st.error(f"Error: {exc}")

    with fetch_tab:
        urls_text = st.text_area(
            "URLs",
            value="https://parallel.ai/blog/free-web-search-mcp",
            height=100,
            help="One URL per line, or comma-separated.",
        )
        fetch_objective = st.text_input(
            "Objective",
            value="Summarize the setup steps for adding the free Search MCP endpoint to an agent.",
        )

        if st.button("📄 Fetch URLs", type="primary", use_container_width=True):
            urls = parse_lines(urls_text)
            if not urls:
                st.warning("Please enter at least one URL.")
            else:
                with st.spinner("Calling Parallel Search MCP web_fetch..."):
                    try:
                        payload = run_web_fetch(
                            urls,
                            fetch_objective.strip(),
                            st.session_state.parallel_mcp_session_id,
                        )
                        render_results(payload)
                    except Exception as exc:
                        st.error(f"Error: {exc}")

    with agent_tab:
        st.subheader("Add Free Web Search To Your Agent")
        st.markdown(
            "Give any MCP-compatible agent live web search and URL fetching by pointing it at "
            "the same free endpoint this app uses."
        )

        benefit_cols = st.columns(3)
        with benefit_cols[0]:
            st.markdown("#### No key to start")
            st.caption("No Parallel account, API key, or local MCP server is needed for light use.")
        with benefit_cols[1]:
            st.markdown("#### One remote endpoint")
            st.caption("Use the Streamable HTTP server at `https://search.parallel.ai/mcp`.")
        with benefit_cols[2]:
            st.markdown("#### Agent-ready tools")
            st.caption("Adds `web_search` for fresh answers and `web_fetch` for reading URLs.")

        st.markdown("### 1. Choose Your Client")

        selected_client = st.radio(
            "Choose your client",
            list(CLIENT_INSTALL_OPTIONS.keys()),
            horizontal=True,
            label_visibility="collapsed",
        )
        option = CLIENT_INSTALL_OPTIONS[selected_client]

        st.markdown(f"### 2. {option['install_title']}")
        st.caption(option["install_note"])
        if option.get("action_url"):
            st.link_button(
                option["action_label"],
                option["action_url"],
                use_container_width=True,
            )
            with st.expander("Manual config"):
                st.code(option["snippet"], language=option["language"])
        else:
            st.code(option["snippet"], language=option["language"])

        st.markdown("### 3. Verify And Search")
        st.caption(option["verify"])
        st.code(SAMPLE_AGENT_PROMPT, language="text")
        st.caption("You should get cited, LLM-ready excerpts from the live web.")

        with st.expander("Let your coding agent install it"):
            st.markdown("Paste this into the agent you are already using.")
            st.code(AGENT_INSTALL_PROMPT, language="markdown")

        st.markdown("### Endpoint")
        st.code(PARALLEL_SEARCH_MCP_URL, language="text")


if __name__ == "__main__":
    main()
