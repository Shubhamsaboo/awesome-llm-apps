# 🐙 GitHub MCP Agent

A Streamlit application that allows you to explore and analyze GitHub repositories using natural language queries through the Model Context Protocol (MCP).

## Features

- **Natural Language Interface**: Ask questions about repositories in plain English
- **Comprehensive Analysis**: Explore issues, pull requests, repository activity, and code statistics
- **Interactive UI**: User-friendly interface with example queries and custom input
- **MCP Integration**: Leverages the Model Context Protocol to interact with GitHub's API
- **Real-time Results**: Get immediate insights on repository activity and health

## Setup

### Requirements

- Python 3.8+
- Node.js and npm (for MCP GitHub server)
  - This is a critical requirement! The app uses `npx` to run the MCP GitHub server
  - Download and install from [nodejs.org](https://nodejs.org/)
- GitHub Personal Access Token with appropriate permissions
- OpenAI API Key

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

3. Verify Node.js and npm are installed:
   ```bash
   node --version
   npm --version
   npx --version
   ```
   All of these commands should return version numbers. If they don't, please install Node.js.

4. Set up your API keys:
   - Set OpenAI API Key as an environment variable:
     ```bash
     export OPENAI_API_KEY=your-openai-api-key
     ```
   - GitHub token will be entered directly in the app interface

5. Create a GitHub Personal Access Token:
   - Visit https://github.com/settings/tokens
   - Create a new token with `repo` and `user` scopes
   - Save the token somewhere secure

### Running the App

1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```

2. In the app interface:
   - Enter your GitHub token in the sidebar
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
