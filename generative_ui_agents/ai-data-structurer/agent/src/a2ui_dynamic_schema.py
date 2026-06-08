"""
Dynamic A2UI tool: LLM-generated UI from conversation context.

A secondary LLM generates v0.9 A2UI components via a structured tool call.
The generate_a2ui tool wraps the output as a2ui_operations, which the
middleware detects in the TOOL_CALL_RESULT and renders automatically.
"""

from __future__ import annotations

import json
from typing import Any

from langchain.tools import tool, ToolRuntime
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from copilotkit import a2ui

CUSTOM_CATALOG_ID = "copilotkit://app-dashboard-catalog"


@tool
def render_a2ui(
    surfaceId: str,
    catalogId: str,
    components: list[dict],
    data: dict | None = None,
) -> str:
    """Render a dynamic A2UI v0.9 surface.

    Args:
        surfaceId: Unique surface identifier.
        catalogId: The catalog ID (use "copilotkit://app-dashboard-catalog").
        components: A2UI v0.9 component array (flat format). The root
            component must have id "root".
        data: Optional initial data model for the surface (e.g. form values,
            list items for data-bound components).
    """
    return "rendered"


@tool
def generate_a2ui(runtime: ToolRuntime) -> str:
    """Generate dynamic A2UI components based on the conversation.

    A secondary LLM designs the UI schema and data. The result is
    returned as an a2ui_operations container for the middleware to detect.
    """
    messages = runtime.state["messages"][:-1]

    context_entries = runtime.state.get("copilotkit", {}).get("context", [])
    context_text = "\n\n".join(
        entry.get("value", "") for entry in context_entries
        if isinstance(entry, dict) and entry.get("value")
    )

    prompt = context_text

    import os
    model = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5.5"))
    model_with_tool = model.bind_tools(
        [render_a2ui],
        tool_choice="render_a2ui",
    )

    response = model_with_tool.invoke(
        [SystemMessage(content=prompt), *messages],
    )

    if not response.tool_calls:
        return json.dumps({"error": "LLM did not call render_a2ui"})

    tool_call = response.tool_calls[0]
    args = tool_call["args"]

    surface_id = args.get("surfaceId", "dynamic-surface")
    catalog_id = args.get("catalogId", CUSTOM_CATALOG_ID)
    components = args.get("components", [])
    data = args.get("data", {})

    ops = [
        a2ui.create_surface(surface_id, catalog_id=catalog_id),
        a2ui.update_components(surface_id, components),
    ]
    if data:
        ops.append(a2ui.update_data_model(surface_id, data))

    return a2ui.render(operations=ops)
