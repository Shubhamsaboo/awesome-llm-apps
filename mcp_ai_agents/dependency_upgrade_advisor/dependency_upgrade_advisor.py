"""Dependency Upgrade Advisor: paste a requirements.txt or package.json, get an upgrade report.

For each package you pick, one agent reads two public MCP servers and writes a short report:
what breaks between your current version and the target, what to change, and how to check it.

    Context7  -> up-to-date library documentation and code examples (resolve-library-id, query-docs)
    DeepWiki  -> questions answered from a GitHub repository's code and docs (ask_wiki_question)

Neither server needs an account or a token. The agent is a plain Strands `Agent`; the model
provider is your choice (see `build_model`).

The agent code is at the top and the Streamlit app is in `main()`, so you can import
`parse_dependencies` and `build_agent` from another script without starting the UI.

SPDX-License-Identifier: Apache-2.0
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any

import streamlit as st
from strands import Agent
from strands.hooks import AfterToolCallEvent
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient

DEFAULT_MODEL = "gpt-5.4-mini"

SAMPLE_REQUIREMENTS = """\
pydantic==1.10.13
requests==2.25.1
sqlalchemy==1.4.49
"""

SYSTEM_PROMPT = """\
You are a careful release engineer. You are given one package, the version a project uses today
and the version it wants to move to. Find out what breaks between the two and what the project
has to change.

Tools:
- Context7 (resolve-library-id, then query-docs): the library's documentation, migration guides
  and code examples. Resolve the library id first, and ask for a specific version when the
  resolve result lists one.
- DeepWiki (ask_wiki_question): answers about the library's GitHub repository, for example its
  release notes, deprecations and migration steps. Use owner/repo as the repository name.

Rules:
- Every breaking change, rename and removal you report must come from a tool result. Never add
  details from memory, even if you are sure of them.
- If the target is "latest", use the newest stable version that the tools list, and say which
  version that is. If you cannot find it, say so instead of guessing.
- If you cannot find notes for part of the version range, say which part is not covered.
- Name the source of each point (the Context7 library id or the GitHub repository).
- Do not use any other tool, and do not run or edit code.

Answer in Markdown, under 250 words, with exactly these sections:
**Verdict:** one of Safe / Needs changes / Risky, then one sentence why. Name the exact
versions you compared, for example "1.10.13 to 2.14.1".
**What breaks:** a bullet list. Each bullet is the old thing, the new thing and the source.
**What to change:** a bullet list with a short code snippet when the sources have one.
**How to check:** one or two concrete checks (a test, a command or a warning to look for).
"""


# --------------------------------------------------------------------------------------
# Reading a dependency file
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Dependency:
    name: str
    version: str  # "" when the file does not pin one
    ecosystem: str  # "PyPI" or "npm"


_REQ_LINE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*(?:(?:===|==|~=|>=|<=|!=|>|<)\s*([^\s,;#]+))?")


def parse_dependencies(text: str) -> list[Dependency]:
    """Read a requirements.txt or a package.json (dependencies and devDependencies).

    Lines such as comments, `-r other.txt`, `-e .` and URLs are skipped. A range such as
    `>=1.0,<2` keeps its first version number, because that is the lower bound in use.
    """
    text = text.strip()
    if not text:
        return []

    if text.startswith("{"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"This looks like package.json but is not valid JSON: {exc}") from exc
        found: dict[str, str] = {}
        for section in ("dependencies", "devDependencies"):
            for name, spec in (data.get(section) or {}).items():
                found[name] = str(spec)
        # Keep only real version numbers; specs such as "workspace:*" or "latest" count as unpinned.
        versions = {n: re.sub(r"^[\^~<>=\s]+", "", s) for n, s in found.items()}
        return [Dependency(n, v if v[:1].isdigit() else "", "npm") for n, v in versions.items()]

    deps: list[Dependency] = []
    for raw in text.splitlines():
        line = raw.split(" #")[0].strip()
        if not line or line.startswith(("#", "-", "git+", "http")):
            continue
        match = _REQ_LINE.match(line)
        if match:
            deps.append(Dependency(match.group(1), match.group(2) or "", "PyPI"))
    return deps


# --------------------------------------------------------------------------------------
# The agent
# --------------------------------------------------------------------------------------


def context7_client() -> MCPClient:
    # Hosted, works without an API key (Context7 applies a rate limit to anonymous use).
    return MCPClient(
        url="https://mcp.context7.com/mcp",
        tool_filters={"allowed": ["resolve-library-id", "query-docs"]},
    )


def deepwiki_client() -> MCPClient:
    # Hosted, no account needed, public repositories only.
    return MCPClient(
        url="https://mcp.deepwiki.com/mcp",
        tool_filters={"allowed": ["ask_wiki_question"]},
    )


def build_model(model_id: str = DEFAULT_MODEL, api_key: str | None = None) -> OpenAIModel:
    """The one place that picks the model provider.

    To use another provider, return a different Strands model here, for example
    `AnthropicModel(model_id=...)` from `strands.models.anthropic`, and install the
    matching extra (`strands-agents[anthropic]`).
    """
    return OpenAIModel(client_args={"api_key": api_key or os.environ.get("OPENAI_API_KEY")}, model_id=model_id)


@dataclass
class ToolTrail:
    """Which MCP tools the agent used while answering one package."""

    calls: list[str] = field(default_factory=list)

    def record(self, event: AfterToolCallEvent) -> None:
        self.calls.append(event.tool_use["name"])


def build_agent(model: Any) -> tuple[Agent, ToolTrail]:
    """A plain Strands Agent holding both MCP clients. Call `agent.cleanup()` when done."""
    trail = ToolTrail()
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[context7_client(), deepwiki_client()],
        callback_handler=None,  # the UI does the streaming
    )
    agent.add_hook(trail.record, AfterToolCallEvent)
    return agent, trail


def question_for(dep: Dependency, target: str) -> str:
    current = dep.version or "an unpinned (unknown) version"
    return f"Package: {dep.name} ({dep.ecosystem})\nCurrent version: {current}\nTarget version: {target or 'latest'}"


# --------------------------------------------------------------------------------------
# Streamlit app
# --------------------------------------------------------------------------------------


async def advise(agent: Agent, trail: ToolTrail, dep: Dependency, target: str, status, box) -> str:
    """Stream the report for one package into the page."""
    agent.messages.clear()  # every package starts from a clean conversation
    trail.calls.clear()
    text = ""
    async for event in agent.stream_async(question_for(dep, target)):
        tool = event.get("current_tool_use")
        if tool and tool.get("name"):
            status.update(label=f"{dep.name}: using {tool['name']}...")
        if "data" in event:
            text += event["data"]
            box.markdown(text)
    return text


def main() -> None:
    st.set_page_config(page_title="Dependency Upgrade Advisor", page_icon="📦", layout="wide")
    st.title("📦 Dependency Upgrade Advisor")
    st.caption(
        "Paste a requirements.txt or package.json, pick what to upgrade, and get a report per package "
        "from two public MCP servers: Context7 (library docs) and DeepWiki (GitHub repositories)."
    )

    with st.sidebar:
        st.header("⚙ Settings")
        api_key = st.text_input("OpenAI API key", type="password", help="Or export OPENAI_API_KEY before starting.")
        model_id = st.text_input("Model", value=DEFAULT_MODEL)
        st.caption("To use another provider, change `build_model()`. See the README.")

    text = st.text_area("Your dependency file", value=SAMPLE_REQUIREMENTS, height=180)
    try:
        deps = parse_dependencies(text)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    if not deps:
        st.info("No dependencies found. Paste the contents of a requirements.txt or package.json.")
        st.stop()

    st.subheader("What do you want to upgrade?")
    table = st.data_editor(
        [
            {"Upgrade": i < 3, "Package": d.name, "Current": d.version or "(unpinned)", "Target": "latest"}
            for i, d in enumerate(deps)
        ],
        disabled=["Package", "Current"],
        hide_index=True,
        key=f"table_{hash(text)}",  # a new file gives a fresh table
    )
    st.caption(
        "Tick the packages and edit **Target** (a version number, or `latest`). Keep it to a few packages per run."
    )

    if not st.button("Check upgrades", type="primary"):
        return

    chosen = [(deps[i], (row["Target"] or "").strip() or "latest") for i, row in enumerate(table) if row["Upgrade"]]
    if not chosen:
        st.warning("Tick at least one package.")
        return
    if not (api_key or os.environ.get("OPENAI_API_KEY")):
        st.error("Enter your OpenAI API key in the sidebar.")
        return

    agent = None
    try:
        agent, trail = build_agent(build_model(model_id, api_key))
        for dep, target in chosen:
            with st.expander(f"{dep.name}  {dep.version or '?'} → {target}", expanded=True):
                status = st.status(f"{dep.name}: starting...", expanded=False)
                box = st.empty()
                asyncio.run(advise(agent, trail, dep, target, status, box))
                status.update(
                    label=f"{dep.name}: done (tools used: {', '.join(trail.calls) or 'none'})", state="complete"
                )
    except Exception as exc:  # show setup problems (key, model name, network) instead of a stack trace
        st.error(f"{type(exc).__name__}: {exc}")
    finally:
        if agent is not None:
            agent.cleanup()  # closes the MCP connections


if __name__ == "__main__":
    main()
