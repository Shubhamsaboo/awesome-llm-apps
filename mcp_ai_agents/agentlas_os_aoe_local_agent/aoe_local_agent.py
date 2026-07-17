"""Run a local Ollama model with the local Agentlas OS MCP server."""

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import httpx
import streamlit as st
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import APIError, AsyncOpenAI


DEFAULT_TASK = (
    "Review a software repository for security risks and propose the specialist "
    "agent or team that should handle the work."
)
DEFAULT_AGENTLAS_BIN = str(
    Path.home() / ".agentlas" / "runtime" / "current" / "bin" / "hephaestus"
)


def normalize_ollama_host(value: str) -> str:
    host = value.strip().rstrip("/") or "http://127.0.0.1:11434"
    return host if host.startswith(("http://", "https://")) else f"http://{host}"


@st.cache_data(ttl=10)
def list_ollama_models(host: str) -> list[str]:
    response = httpx.get(f"{host}/api/tags", timeout=3)
    response.raise_for_status()
    return [item["name"] for item in response.json().get("models", [])]


def parse_tool_result(result: Any) -> tuple[dict[str, Any], str]:
    if isinstance(getattr(result, "structuredContent", None), dict):
        payload = result.structuredContent
        return payload, json.dumps(payload, ensure_ascii=False)

    text = "\n".join(
        block.text for block in result.content if hasattr(block, "text")
    )
    if not text:
        raise RuntimeError("The local Agentlas MCP server returned no result.")
    try:
        return json.loads(text), text
    except json.JSONDecodeError:
        return {"result": text}, text


async def run_local_agent(
    task: str,
    model: str,
    ollama_host: str,
    agentlas_bin: str,
    project_dir: str,
) -> tuple[str, dict[str, Any]]:
    """Let Ollama call a locally spawned Agentlas MCP routing tool."""
    project = Path(project_dir).expanduser().resolve()
    project.mkdir(parents=True, exist_ok=True)
    server_env = {
        **os.environ,
        "AGENTLAS_HUB_URL": "http://127.0.0.1:9",
        "AGENTLAS_MCP_PROJECT_BOOTSTRAP_AUTO": "1",
        "HEPHAESTUS_HUB_TIMEOUT_SECONDS": "1",
        "HEPHAESTUS_NETWORK_GUI_NO_OPEN": "1",
        "HEPHAESTUS_UPDATE_CHECK": "0",
    }
    server = StdioServerParameters(
        command=agentlas_bin,
        args=["mcp", "serve"],
        env=server_env,
        cwd=str(project),
    )

    async with stdio_client(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            available = await session.list_tools()
            route_tool = next(
                (tool for tool in available.tools if tool.name == "hephaestus_route"),
                None,
            )
            if route_tool is None:
                raise RuntimeError("The local Agentlas MCP route tool is unavailable.")

            client = AsyncOpenAI(
                base_url=f"{ollama_host}/v1",
                api_key="ollama",
                timeout=120,
            )
            messages: list[dict[str, Any]] = [
                {
                    "role": "system",
                    "content": (
                        "You are a local Agentlas OS planning agent. Always call "
                        "hephaestus_route before answering. Use the routing evidence "
                        "to recommend an existing local specialist or a new agent brief."
                    ),
                },
                {"role": "user", "content": task},
            ]
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": route_tool.name,
                        "description": route_tool.description,
                        "parameters": route_tool.inputSchema,
                    },
                }
            ]
            first = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice={
                    "type": "function",
                    "function": {"name": "hephaestus_route"},
                },
            )
            assistant_message = first.choices[0].message
            if not assistant_message.tool_calls:
                raise RuntimeError("The local model did not call the Agentlas MCP tool.")

            call = assistant_message.tool_calls[0]
            arguments = json.loads(call.function.arguments or "{}")
            arguments.update(
                {
                    "request": task,
                    "project_dir": str(project),
                    "allow_local_routing": True,
                    "hub_only": False,
                }
            )
            result = await session.call_tool("hephaestus_route", arguments)
            if result.isError:
                raise RuntimeError("The local Agentlas MCP tool returned an error.")
            route_payload, route_text = parse_tool_result(result)

            messages.append(assistant_message.model_dump(exclude_none=True))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": route_text,
                }
            )
            final = await client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return final.choices[0].message.content or "", route_payload


def render_app() -> None:
    st.set_page_config(
        page_title="Agentlas OS Agent Operation Environment (AOE) Local MCP Agent",
        layout="wide",
    )
    st.title("Agentlas OS Agent Operation Environment (AOE)")
    st.subheader("Local Ollama MCP Agent")
    st.caption("The model and Agentlas MCP server both run on this computer.")

    with st.sidebar:
        ollama_host = normalize_ollama_host(
            st.text_input(
                "Ollama host", value=os.getenv("OLLAMA_HOST", "127.0.0.1:11434")
            )
        )
        agentlas_bin = st.text_input(
            "Agentlas executable", value=DEFAULT_AGENTLAS_BIN
        )
        project_dir = st.text_input(
            "Project directory", value=str(Path.home() / ".agentlas" / "demo-project")
        )

    try:
        models = list_ollama_models(ollama_host)
    except (httpx.HTTPError, KeyError, TypeError) as exc:
        models = []
        st.error(f"Could not reach Ollama at {ollama_host}: {exc}")

    model = st.selectbox("Local model", options=models) if models else None
    task = st.text_area("Task", value=DEFAULT_TASK, height=140)

    if st.button("Run local agent", type="primary", use_container_width=True):
        if not model:
            st.error("Start Ollama and install a tool-capable local model first.")
        elif not Path(agentlas_bin).is_file():
            st.error("Install Agentlas OS or select its local executable.")
        elif not task.strip():
            st.error("Enter a task.")
        else:
            try:
                with st.spinner(f"Running {model} with local Agentlas MCP..."):
                    answer, route = asyncio.run(
                        run_local_agent(
                            task.strip(),
                            model,
                            ollama_host,
                            agentlas_bin,
                            project_dir,
                        )
                    )
            except (OSError, RuntimeError, ValueError, httpx.HTTPError, APIError) as exc:
                st.error(f"Local agent failed: {exc}")
            else:
                st.markdown("### Local model response")
                st.markdown(answer)
                with st.expander("Agentlas MCP routing evidence"):
                    st.json(route)


if __name__ == "__main__":
    render_app()
