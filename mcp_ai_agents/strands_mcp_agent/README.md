# 🧵 Strands MCP Agent

A Streamlit app that answers questions about the Strands Agents SDK using a Strands agent connected to an MCP server. The agent connects to the Strands documentation MCP server over stdio, discovers its tools, and calls them to find answers, so you can explore the SDK in plain English.

This app shows how Strands works as an MCP client: point it at a server, list the tools, and hand them to the agent.

## Features

- **Natural language interface**: Ask about Strands concepts and get answers grounded in the docs
- **MCP over stdio**: Launches the Strands documentation MCP server locally with `uvx`
- **Tool discovery**: The Strands `MCPClient` lists the server tools and passes them to the agent
- **Cited answers**: The agent uses `search_docs` and `fetch_doc` and points to the pages it used
- **Model choice**: Runs on OpenAI `gpt-4o-mini` by default, with `gpt-4o` available

## How it works

1. The app starts the `strands-agents-mcp-server` as a local subprocess with `uvx`.
2. The Strands `MCPClient` connects over stdio and calls `list_tools_sync()` to discover the server tools.
3. Those tools are passed to a Strands `Agent` backed by an OpenAI model.
4. The agent decides when to call `search_docs` and `fetch_doc`, then writes an answer with citations.

## Setup

### Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed, so `uvx` can launch the MCP server
- OpenAI API key

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/strands_mcp_agent
   ```

2. Install the Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Confirm `uvx` is available:
   ```bash
   uvx --version
   ```

### Running the app

1. Start the Streamlit app:
   ```bash
   streamlit run strands_mcp_agent.py
   ```

2. In the app:
   - Enter your OpenAI API key in the sidebar
   - Pick a model
   - Type a question and click Ask

## Example questions

- How do I connect a Strands agent to an MCP server over stdio?
- What transports does the Strands MCP client support?
- How do I use the OpenAI model provider in Strands?

## References

- [Strands Agents documentation](https://strandsagents.com)
- [Using MCP Tools in Strands](https://strandsagents.com/docs/user-guide/concepts/tools/mcp-tools/)
- [Model Context Protocol](https://modelcontextprotocol.io)
