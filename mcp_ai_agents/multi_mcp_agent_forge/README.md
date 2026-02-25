# Multi-MCP Agent Forge

A Streamlit app that demonstrates the **multi-agent + MCP** pattern: specialized AI agents that each connect to different MCP servers to handle domain-specific tasks.

Instead of one agent with all tools, Agent Forge routes your request to a **specialist** — a code reviewer, security auditor, researcher, or BIM engineer — each with access to only the MCP tools they need.

## Features

- **4 Specialized Agents**: Code Reviewer, Security Auditor, Researcher, and BIM Engineer
- **MCP Tool Routing**: Each agent connects to different MCP servers (GitHub, filesystem, fetch, etc.)
- **Agent Selection**: Automatic routing based on query type, or manual agent selection
- **Streaming Responses**: Real-time output from Claude via the Anthropic API
- **Conversation Memory**: Per-agent conversation history within a session

## Architecture

```
User Query
    |
    v
[Router] --> Classifies intent
    |
    +-- Code Review  --> GitHub MCP + Filesystem MCP
    +-- Security     --> GitHub MCP + Fetch MCP  
    +-- Research     --> Fetch MCP + Filesystem MCP
    +-- BIM/Revit    --> Custom MCP (named pipes)
```

## Setup

### Requirements

- Python 3.10+
- Anthropic API Key
- MCP servers (optional — the app works with or without them)

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd mcp_ai_agents/multi_mcp_agent_forge
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   streamlit run agent_forge.py
   ```

4. Enter your Anthropic API key in the sidebar and start asking questions.

## How It Works

1. **Agent Definitions**: Each agent has a name, system prompt, and list of MCP server configs
2. **Router**: Classifies the user's query and selects the best agent
3. **MCP Connection**: The selected agent connects to its assigned MCP servers
4. **Execution**: Claude processes the query with access to the agent's specific tools
5. **Response**: Results stream back to the Streamlit UI

## Extending

Add new agents by defining them in the `AGENTS` dictionary:

```python
AGENTS["my_agent"] = Agent(
    name="My Agent",
    description="Handles X tasks",
    system_prompt="You are an expert in X...",
    mcp_servers=[{"command": "npx", "args": ["-y", "@some/mcp-server"]}]
)
```

## Credits

Inspired by [cadre-ai/Agent Forge](https://github.com/WeberG619/cadre-ai) — a production multi-agent framework for Claude Code with 17 specialized agents, persistent memory, and desktop automation.
