# Agentlas OS Agent Operation Environment (AOE) Local MCP Agent

A self-contained Streamlit tutorial that runs a local Ollama model and gives it
the locally installed Agentlas OS MCP router as a tool. The app does not require
an API key, Agentlas account, or hosted Agentlas endpoint.

## Features

- Calls a real LLM through Ollama's local OpenAI-compatible API
- Spawns `hephaestus mcp serve` as a local stdio MCP server
- Forces the local model to call `hephaestus_route` before answering
- Routes against locally installed Agentlas agents and skills
- Returns the local MCP evidence alongside the model's recommendation
- Blocks external Hub access so the tutorial remains offline and reproducible

## Architecture

```text
Task entered in Streamlit
  -> local Ollama model receives the Agentlas MCP tool schema
  -> model calls hephaestus_route
  -> local Agentlas OS stdio MCP server routes against local inventory
  -> routing evidence returns to the local model
  -> model produces the final specialist or team recommendation
```

Both runtime connections are local. Ollama defaults to
`http://127.0.0.1:11434`, and Agentlas OS is launched from the installed
executable under `~/.agentlas/runtime/current/bin/hephaestus`. The MCP child
process points Hub traffic at a closed loopback port, so no hosted Agentlas
service is required or contacted.

The default project is `~/.agentlas/demo-project`. On its first run, Agentlas OS
creates private project metadata there before routing. You can select another
project directory in the sidebar when you want Agentlas to use that project's
local context.

## Setup

### Requirements

- Python 3.10+
- [Ollama](https://ollama.com/) with a tool-capable local model
- [Agentlas OS](https://github.com/agentlas-ai/Agentlas-OS) installed locally

### Installation

1. Install Agentlas OS from its public repository and verify the runtime:

   ```bash
   ~/.agentlas/runtime/current/bin/hephaestus doctor
   ```

2. Start Ollama and install a tool-capable model:

   ```bash
   ollama serve
   ollama pull qwen3:8b
   ```

3. Clone this repository and install the Python dependencies:

   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/agentlas_os_aoe_local_agent
   pip install -r requirements.txt
   ```

4. Start the app:

   ```bash
   streamlit run aoe_local_agent.py
   ```

5. Select a detected Ollama model, enter a task, and choose **Run local
   agent**.

## How It Works

The first local LLM turn receives the JSON schema for the installed
`hephaestus_route` MCP tool. Tool choice is forced so the model cannot answer
without consulting Agentlas OS. The app adds `allow_local_routing: true` and
passes the selected project directory to the tool.

Agentlas OS returns a deterministic routing receipt. Depending on the local
inventory, it may select a specialist, ask for clarification, or propose that a
new agent be built. The second local LLM turn interprets that evidence and
produces a concise execution recommendation. The raw MCP response remains
visible in the Streamlit interface.

## Learn More

- [Agentlas OS Agent Operation Environment (AOE)](https://github.com/agentlas-ai/Agentlas-OS)
- [Agentlas OS MCP adapter](https://github.com/agentlas-ai/Agentlas-OS/blob/main/agentlas_cloud/mcp_stdio.py)
- [Agentlas OS routing architecture](https://github.com/agentlas-ai/Agentlas-OS/blob/main/docs/hephaestus-network-2.0.md)
