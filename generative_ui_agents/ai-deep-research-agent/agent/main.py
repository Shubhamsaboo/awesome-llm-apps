"""
Deep Research Assistant - FastAPI Server

Serves the Deep Research Agent via AG-UI protocol for CopilotKit integration.
The agent uses Tavily for web research and Deep Agents for planning and filesystem operations.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent
from copilotkit.langgraph import copilotkit_customize_config

from agent import build_agent

load_dotenv()

app = FastAPI(
    title="Deep Research Assistant",
    description="A research assistant powered by Deep Agents and CopilotKit",
    version="1.0.0",
)

# Enable CORS for frontend communication
# Using "*" for demo purposes - allows any origin including localhost and Railway deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Health check endpoint for monitoring and Railway deployments"""
    return {"status": "ok", "service": "deep-research-agent", "version": "1.0.0"}


# Build and register the Deep Research Agent
try:
    agent_graph = build_agent()

    # Configure which tool calls to emit to the frontend
    # Only emit main agent tools - suppress internal tools (internet_search from research subagent)
    # This prevents subagent tool calls from appearing as JSON noise in the chat
    agui_config = copilotkit_customize_config(
        emit_tool_calls=[
            "research",
            "write_todos",
            "write_file",
            "read_file",
            "edit_file",
        ]
    )

    # Add recursion limit for complex research tasks (6+ research calls + file operations)
    agui_config["recursion_limit"] = 100

    # Add AG-UI endpoint at root path for CopilotKit frontend
    add_langgraph_fastapi_endpoint(
        app=app,
        agent=LangGraphAGUIAgent(
            name="research_assistant",
            description="A deep research assistant that plans, searches, and synthesizes research reports",
            graph=agent_graph,
            config=agui_config,
        ),
        path="/",
    )

    print("[SERVER] Deep Research Agent registered at /")
except Exception as e:
    print(f"[ERROR] Failed to build agent: {e}")
    raise


def main():
    """Run the server with uvicorn"""
    import uvicorn

    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", "8123"))

    print(f"[SERVER] Starting on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
