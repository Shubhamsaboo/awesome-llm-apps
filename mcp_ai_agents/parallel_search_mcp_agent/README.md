# 🔎 Free Web Search MCP Starter

A no-key Streamlit starter for trying Parallel's free Search MCP endpoint before adding it to an agent.

The app connects directly to `https://search.parallel.ai/mcp` and calls the two tools exposed by Parallel Search MCP:

- `web_search` searches the current web.
- `web_fetch` fetches focused content from public URLs.

No OpenAI API key, Parallel API key, local MCP server, or agent framework is required to run this example.

## What It Shows

- Connecting to a remote MCP server over Streamable HTTP
- Calling `web_search` with an objective and keyword queries
- Calling `web_fetch` with one or more URLs
- Copying the same MCP endpoint into an MCP-compatible agent or client

## Setup

### Requirements

- Python 3.10+
- No API keys required

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/parallel_search_mcp_agent
   ```

2. Check your Python version:
   ```bash
   python3 --version
   ```

   The version must be 3.10 or newer. If it prints 3.9 or older, create the environment with a newer Python interpreter before installing dependencies.

3. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

Start the Streamlit app:

```bash
streamlit run parallel_search_agent.py
```

In the app:

- Use **Search** to call `web_search`.
- Use **Fetch URL** to call `web_fetch`.
- Use **Add To Agent** to copy the MCP endpoint into your agent or client.

## Parallel Search MCP Endpoint

The app connects to the free Parallel Search MCP endpoint:

```text
https://search.parallel.ai/mcp
```

No Parallel API key or Parallel account is required for this example. The same endpoint works with other MCP-compatible clients and agent frameworks.

## Add To An Agent

Add live web search to the coding agent or editor you already use. Each option points to the same free remote MCP endpoint:

```text
https://search.parallel.ai/mcp
```

Once connected, your agent gets two tools:

- `web_search` for fresh web results with LLM-ready excerpts.
- `web_fetch` for reading focused content from public URLs.

### Claude Code

Run this command in your terminal:

```bash
claude mcp add --transport http parallel-search https://search.parallel.ai/mcp
```

Then run `/mcp` inside Claude Code to see `parallel-search` in your connected servers.

### Codex

Run this command in your terminal:

```bash
codex mcp add parallel-search --url https://search.parallel.ai/mcp
```

Then run `codex mcp list` to confirm `parallel-search` is registered, and restart Codex.

### Cursor

[Add to Cursor](https://cursor.com/en/install-mcp?name=Parallel%20Search%20MCP&config=eyJ1cmwiOiJodHRwczovL3NlYXJjaC5wYXJhbGxlbC5haS9tY3AifQ==)

Confirm the install when Cursor opens, then check Settings > MCP to see `Parallel Search MCP` enabled.

Manual config for `~/.cursor/mcp.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "Parallel Search MCP": {
      "url": "https://search.parallel.ai/mcp"
    }
  }
}
```

### VS Code

[Add to VS Code](https://insiders.vscode.dev/redirect/mcp/install?name=Parallel%20Search%20MCP&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fsearch.parallel.ai%2Fmcp%22%7D)

Confirm the install when VS Code opens. The server then appears under MCP Servers in your settings.

Manual config for `.vscode/mcp.json` or VS Code's MCP user configuration:

```json
{
  "servers": {
    "Parallel Search MCP": {
      "type": "http",
      "url": "https://search.parallel.ai/mcp"
    }
  }
}
```

### Agent Install Prompt

If you already have a coding agent open, paste this and let the agent pick the right client setup:

```text
Please add Parallel Search MCP to this agent so you can search the live web.

- Server URL: https://search.parallel.ai/mcp
- Transport: Streamable HTTP
- Authentication: no auth by default; the server is free to use without an API key

First, identify which MCP client you are running inside: Claude Code, Codex, Cursor, VS Code, or another MCP-compatible client. Then add the server to that client's MCP config using the mechanism it expects.

After the config is in place, tell me whether the client needs to be restarted. Then confirm the server connects, lists `web_search` and `web_fetch`, and can answer this test prompt:

Which AI products shipped this week? Give me a short list with sources.
```

Try that same prompt after you install the MCP server. You should get cited, LLM-ready excerpts from the live web.

## Example Inputs

Search:

- Objective: "Find current information about Parallel Search MCP."
- Queries:
  ```text
  Parallel Search MCP
  free web search MCP
  ```

Fetch:

- URL: `https://parallel.ai/blog/free-web-search-mcp`
- Objective: "Summarize the setup steps for adding the free Search MCP endpoint to an agent."

## Troubleshooting

### Dependency installation fails

Check that `python3 --version` is 3.10 or newer. If your system Python is older, create the environment with a newer Python interpreter before installing dependencies.

### MCP connection or rate-limit error

Retry once if the free endpoint is temporarily rate-limited. If the issue persists, check that you can reach the MCP endpoint from your network.

### Network restrictions

The app must be able to reach `https://search.parallel.ai/mcp`. If you are on a restricted network, try another network or configure your proxy settings before starting Streamlit.

## Project Structure

```text
parallel_search_agent.py  # Streamlit app using the Parallel Search MCP tools
requirements.txt          # Python dependencies
README.md                 # Setup and usage guide
```
