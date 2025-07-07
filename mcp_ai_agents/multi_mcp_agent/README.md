# 🚀 Multi-MCP Intelligent Assistant

The Multi-MCP Intelligent Assistant is a powerful productivity tool that integrates multiple Model Context Protocol (MCP) servers to provide seamless access to GitHub, Perplexity, Calendar, and Gmail services through natural language interactions. This advanced AI assistant is powered by Agno's AI Agent framework and designed to be a productivity multiplier across your digital workspace.

## Features

- **Multi-Agent System**
    - **GitHub Integration**: Complete repository management, issue tracking, and code analysis
    - **Perplexity Research**: Real-time web search and information gathering
    - **Calendar Management**: Event scheduling and meeting coordination
    - **Gmail Integration**: Email management and communication workflows

- **Core Capabilities**:
  - Repository management (create, clone, fork, search)
  - Issue & PR workflow (create, update, review, merge, comment)
  - Real-time web search and research
  - Event scheduling and availability management
  - Email organization and automated responses
  - Cross-platform workflow automation

- **Advanced Features**:
  - Interactive CLI with streaming responses
  - Conversation memory and context retention
  - Tool chaining for complex workflows
  - Session-specific user and session IDs
  - Markdown-formatted responses
  - Proactive workflow suggestions

- **Productivity Focus**:
  - Cross-platform automation (GitHub issues → Calendar events)
  - Research-driven development workflows
  - Project management integration
  - Documentation and knowledge sharing

## How to Run

Follow these steps to set up and run the application:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/multi_mcp_agent
   ```

2. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Verify Node.js installation** (required for MCP servers):
    ```bash
    node --version
    npm --version
    npx --version
    ```
    If Node.js is not installed, download it from [nodejs.org](https://nodejs.org/)

4. **Set up your API keys**:
    Create a `.env` file in the project directory with the following variables:
    ```env
    OPENAI_API_KEY=your-openai-api-key
    GITHUB_PERSONAL_ACCESS_TOKEN=your-github-token
    PERPLEXITY_API_KEY=your-perplexity-api-key
    ```

    - Get an OpenAI API key from: https://platform.openai.com/api-keys
    - Get a GitHub Personal Access Token from: https://github.com/settings/tokens (with `repo`, `user`, and `admin:org` scopes)
    - Get a Perplexity API key from: https://www.perplexity.ai/
    - Configure OpenAI MCP Headers according to your setup requirements

5. **Run the Multi-MCP Agent**:
    ```bash
    python multi_mcp_agent.py
    ```

6. **Start Interacting**:
    - The assistant will validate your environment variables
    - Generate unique user and session IDs
    - Initialize connections to all MCP servers
    - Start the interactive CLI interface

## Usage

1. **Environment Validation**: The assistant automatically checks for all required API keys and environment variables
2. **Session Management**: Each session gets unique user and session IDs for tracking and context
3. **Interactive Commands**: Use natural language to interact with integrated services:

### Example Commands

**GitHub Operations**:
- "Show my recent GitHub repositories"
- "Create a new issue in my project repo"
- "Search for Python code in my repositories"
- "Review the latest pull requests"

**Research & Information**:
- "Search for the latest AI developments"
- "What are the trending topics in machine learning?"
- "Find documentation for FastAPI"
- "Research best practices for microservices"

**Calendar Management**:
- "Schedule a meeting for next week"
- "Show my upcoming appointments"
- "Find available time slots for a 2-hour meeting"

**Cross-Platform Workflows**:
- "Create a GitHub issue and schedule a follow-up meeting"
- "Research a topic and create a summary document"
- "Find trending repositories and add them to my watchlist"

4. **Session Control**: Type 'exit', 'quit', or 'bye' to end the session

## Architecture

The Multi-MCP Agent leverages:
- **Agno Framework**: For agent orchestration and tool management
- **OpenAI GPT-4o**: As the core language model
- **MCP Servers**: For external service integrations
- **Async Architecture**: For efficient concurrent operations
- **Memory System**: For context retention and conversation history

## Note

The assistant connects to multiple MCP servers using Node.js packages. Ensure you have a stable internet connection and valid API keys for all services. The tool chaining capabilities allow for complex workflows that span multiple platforms, making it a powerful productivity multiplier for developers and professionals.
