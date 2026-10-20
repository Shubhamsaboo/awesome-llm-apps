# 🧶 GitHub MCP Agent with Strands

A Streamlit app that explores a GitHub repository in plain English. An agent built with the [Strands Agents SDK](https://strandsagents.com) connects to the official [GitHub MCP Server](https://github.com/github/github-mcp-server) over HTTP, discovers the server's tools, and calls them to answer questions about issues, pull requests, and repository activity.

This example pairs the Strands MCP client with a real service MCP server, so the agent works against live GitHub data rather than a single SDK's documentation.

## Features

- **Natural language queries**: ask about a repository's issues, pull requests, and activity in plain English.
- **Official GitHub MCP server**: uses GitHub's hosted server over HTTP, so the tools come straight from GitHub with no local setup.
- **Strands MCP client**: the agent discovers the server's tools at runtime with `list_tools_sync()` and calls them inside the MCP client context.
- **Model choice**: run the agent on `gpt-4o-mini` or `gpt-4o`.

## How it works

1. The app connects to GitHub's official hosted MCP server over HTTP.
2. The Strands `MCPClient` connects and calls `list_tools_sync()` to discover the GitHub tools.
3. The discovered tools are passed to an `Agent` backed by an OpenAI model.
4. The agent decides which tools to call, reads the results, and answers with links back to GitHub.

## Setup

### Requirements

- Python 3.10+
- An OpenAI API key
- A GitHub personal access token with `repo` scope

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/strands_github_mcp_agent
   ```

2. Install the Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Get your keys:
   - **OpenAI API key**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - **GitHub token**: [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope

### Running the app

```bash
streamlit run strands_github_mcp_agent.py
```

In the app:

1. Enter your OpenAI API key and GitHub token in the sidebar.
2. Set the repository to analyze (format `owner/repo`).
3. Pick a query type or write your own question.
4. Select **Ask**.

## Example questions

**Issues**
- What issues are open and labeled bug?
- Which issues have the most discussion?

**Pull requests**
- Which pull requests are waiting for review?
- Show the pull requests merged in the last two weeks.

**Repository**
- Summarize the activity over the last month.
- Who are the most active contributors right now?

## Notes

- The token is sent only to the GitHub MCP server as an auth header and is not written to disk.
- The hosted server exposes the GitHub toolset documented in the [GitHub MCP Server README](https://github.com/github/github-mcp-server). To run the server yourself instead of using the hosted endpoint, that README covers the local and container options.
