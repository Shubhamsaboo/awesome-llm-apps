# 🐙 GitHub MCP Agent

A Streamlit application that allows you to explore and analyze GitHub repositories using natural language queries through the Model Context Protocol (MCP).

**✨ Now using the official [GitHub MCP Server](https://github.com/github/github-mcp-server) from GitHub!**

## Features

- **Natural Language Interface**: Ask questions about repositories in plain English
- **Comprehensive Analysis**: Explore issues, pull requests, repository activity, and code statistics
- **Interactive UI**: User-friendly interface with example queries and custom input
- **MCP Integration**: Leverages the Model Context Protocol to interact with GitHub's API
- **Real-time Results**: Get immediate insights on repository activity and health

## Setup

### Requirements

- Python 3.8+
- Docker (for official GitHub MCP server)
  - Download and install from [docker.com](https://www.docker.com/get-started)
  - Make sure Docker is running before starting the app
- OpenAI API Key
- GitHub Personal Access Token

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd mcp-github-agent
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify Docker is installed and running:
   ```bash
   docker --version
   docker ps
   ```

4. Get your API keys:
   - **OpenAI API Key**: Get from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - **GitHub Token**: Create at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope

### Running the App

1. Start the Streamlit app:
   ```bash
   streamlit run github_agent.py
   ```

2. In the app interface:
   - Enter your OpenAI API key
   - Enter your GitHub token
   - Specify a repository to analyze
   - Select a query type or write your own
   - Click "Run Query"

### Example Queries

#### Issues
- "Show me issues by label"
- "What issues are being actively discussed?"
- "Find issues labeled as bugs"

#### Pull Requests
- "What PRs need review?"
- "Show me recent merged PRs"
- "Find PRs with conflicts"

#### Repository
- "Show repository health metrics"
- "Show repository activity patterns"
- "Analyze code quality trends"
