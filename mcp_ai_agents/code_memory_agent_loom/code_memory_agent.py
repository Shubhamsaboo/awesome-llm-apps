"""Code Memory Agent: ask about your codebase, and teach it lessons that stay with the code.

One agent talks to a self-hosted ClickHouse Loom server over MCP:

    code tools   -> where a symbol is defined, who calls it, what a change touches, search by meaning
    memory tools -> save a lesson about the code; read the lessons saved about a file

A lesson is saved in the repository's code namespace with the files it is about. Loom links
it to the definitions it names and keeps the link up to date as the code moves or changes,
so a later question about that file, in any session, gets the lesson back. The agent is a
plain Strands `Agent`; the model provider is your choice (see `build_model`).

The agent code is at the top and the Streamlit app is in `main()`, so you can import
`build_agent` from another script without starting the UI.

SPDX-License-Identifier: Apache-2.0
"""

import asyncio
import os
from dataclasses import dataclass, field
from typing import Any

import streamlit as st
from strands import Agent
from strands.hooks import AfterToolCallEvent
from strands.models.anthropic import AnthropicModel
from strands.tools.mcp import MCPClient

DEFAULT_MODEL = "claude-sonnet-5-5"
DEFAULT_LOOM_URL = "http://localhost:7777"

# The tools this app lets the agent use; Loom serves more on the same connection.
LOOM_TOOLS = [
    "loom_code_search",
    "loom_code_symbol",
    "loom_code_callers",
    "loom_code_impact",
    "loom_memory_set",
    "loom_op",  # runs one named op; the prompt uses it only for memory.for_file
]

SYSTEM_PROMPT = """\
You answer questions about one code repository and keep the team's lessons about it.

The repository is indexed in Loom under the code namespace `{namespace}`, and its lessons
are saved there too. Pass `namespace="{namespace}"` on every loom_code_* and
loom_memory_set call.

Tools:
- loom_code_symbol: a definition by name, with its signature. Use it first for
  "where is X / what is X".
- loom_code_callers, loom_code_impact: who calls a symbol, and what a change to it touches.
- loom_code_search: find where a behaviour lives when there is no name to look up.
- loom_op with `op="memory.for_file"` and
  `arguments={{"namespace": "{namespace}", "path": "<file>"}}`: the lessons saved about
  that file. Call it for the main file of every answer, before you answer.
- loom_memory_set: save a lesson the user states (a rule, a decision, a gotcha about the code).
  Use a key like `lesson/<short-slug>`, put the lesson in `value` as one plain sentence
  without surrounding quotes that names the symbols in backticks, add the tag `lesson`, and
  list the files it is about in `files`.

Rules:
- Every file path, line, symbol and caller you report must come from a tool result.
- Cite file:line for each code fact, and quote each lesson that applies with its key.
- Save a lesson only when the user states one; say which key you saved it under.
- If the tools find nothing, say so instead of guessing.
"""


def loom_client(loom_url: str, token: str) -> MCPClient:
    """Loom's MCP endpoint with the coding toolset, authenticated with a Loom token."""
    headers = {"Authorization": f"Bearer {token}"} if token else None
    return MCPClient(
        url=f"{loom_url.rstrip('/')}/mcp?toolset=coding",
        headers=headers,
        tool_filters={"allowed": LOOM_TOOLS},
    )


def build_model(model_id: str = DEFAULT_MODEL, api_key: str | None = None) -> AnthropicModel:
    """The one place that picks the model provider.

    To use another provider, return a different Strands model here, for example
    `OpenAIModel(model_id=...)` from `strands.models.openai`, and install the matching
    extra (`strands-agents[openai]`).
    """
    return AnthropicModel(
        client_args={"api_key": api_key or os.environ.get("ANTHROPIC_API_KEY")},
        model_id=model_id,
        max_tokens=4096,
    )


@dataclass
class ToolTrail:
    """Which Loom tools the agent used while answering one message."""

    calls: list[str] = field(default_factory=list)

    def record(self, event: AfterToolCallEvent) -> None:
        self.calls.append(event.tool_use["name"])


def build_agent(model: Any, loom_url: str, token: str, namespace: str) -> tuple[Agent, ToolTrail]:
    """A plain Strands Agent holding the Loom MCP client. Call `agent.cleanup()` when done."""
    trail = ToolTrail()
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT.format(namespace=namespace),
        tools=[loom_client(loom_url, token)],
        callback_handler=None,  # the UI does the streaming
    )
    agent.add_hook(trail.record, AfterToolCallEvent)
    return agent, trail


async def answer(agent: Agent, trail: ToolTrail, question: str, status, box) -> str:
    """Stream one answer into the page; the agent keeps the conversation between messages."""
    trail.calls.clear()
    text = ""
    async for event in agent.stream_async(question):
        tool = event.get("current_tool_use")
        if tool and tool.get("name"):
            status.update(label=f"using {tool['name']}...")
        if "data" in event:
            text += event["data"]
            box.markdown(text)
    return text


def main() -> None:
    st.set_page_config(page_title="Code Memory Agent", page_icon="🧵", layout="wide")
    st.title("🧵 Code Memory Agent")
    st.caption(
        "Ask about your codebase and teach the agent lessons about it. A self-hosted ClickHouse Loom "
        "server answers the code questions and keeps the lessons linked to the code they describe."
    )

    with st.sidebar:
        st.header("⚙ Settings")
        api_key = st.text_input("Anthropic API key", type="password", help="Or export ANTHROPIC_API_KEY.")
        model_id = st.text_input("Model", value=DEFAULT_MODEL)
        loom_url = st.text_input("Loom server", value=os.environ.get("LOOM_URL", DEFAULT_LOOM_URL))
        token = st.text_input("Loom token", type="password", value=os.environ.get("LOOM_API_KEY", ""))
        namespace = st.text_input("Code namespace", value=os.environ.get("LOOM_CODE_NAMESPACE", ""))
        st.caption("The code namespace is the one your repository is indexed in, e.g. `code-myrepo`.")

    if "history" not in st.session_state:
        st.session_state.history = []
    for role, text in st.session_state.history:
        st.chat_message(role).markdown(text)

    question = st.chat_input("Where is X defined? Who calls Y? Remember that Z must run first...")
    if not question:
        return
    if not (api_key or os.environ.get("ANTHROPIC_API_KEY")) or not namespace:
        st.error("Enter your Anthropic API key and the code namespace in the sidebar.")
        return

    st.chat_message("user").markdown(question)
    st.session_state.history.append(("user", question))
    key = (model_id, loom_url, token, namespace)
    if st.session_state.get("agent_key") != key:
        if st.session_state.get("agent"):
            st.session_state.agent.cleanup()
        st.session_state.agent, st.session_state.trail = build_agent(
            build_model(model_id, api_key), loom_url, token, namespace
        )
        st.session_state.agent_key = key

    with st.chat_message("assistant"):
        status = st.status("thinking...", expanded=False)
        box = st.empty()
        try:
            text = asyncio.run(answer(st.session_state.agent, st.session_state.trail, question, status, box))
            used = ", ".join(st.session_state.trail.calls) or "none"
            status.update(label=f"done (tools used: {used})", state="complete")
            st.session_state.history.append(("assistant", text))
        except Exception as exc:  # show setup problems (key, URL, token, namespace) instead of a stack trace
            status.update(label="failed", state="error")
            st.error(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
