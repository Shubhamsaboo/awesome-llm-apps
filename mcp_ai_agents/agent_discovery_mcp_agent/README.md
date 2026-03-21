# AI Agent Discovery MCP Agent

An AI-powered assistant for discovering and validating AI agents across multiple protocols using the [Global Chat](https://global-chat.io) MCP server. Search 100K+ agents across MCP, A2A, agents.txt, and other agent discovery protocols through natural language.

## Features

- **Agent Search**: Search a directory of 100K+ AI agents across 15+ registries by name, description, or capabilities
- **Agent Listing**: Browse all registered agents with optional type filtering (DeFi, social, data, infra, trading, governance)
- **agents.txt Validation**: Validate any domain's agents.txt file for compliance with the [agents.txt specification](https://agentstext.org)
- **Agent Registration**: Register new AI agents in the Global Chat directory
- **Cross-Protocol Discovery**: Find agents regardless of which protocol they use (MCP, A2A, agents.txt, ACDP, and more)

## How to Run

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/mcp_ai_agents/agent_discovery_mcp_agent
   ```

2. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Node.js installation** (required for MCP servers):
   ```bash
   node --version
   npx --version
   ```
   If Node.js is not installed, download it from [nodejs.org](https://nodejs.org/)

4. **Set up your API keys**:
   Create a `.env` file in the project directory:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   ```
   Get an OpenAI API key from: https://platform.openai.com/api-keys

5. **Run the Agent Discovery Assistant**:
   ```bash
   python agent_discovery_mcp_agent.py
   ```

## Usage

### Example Commands

**Search for agents**:
- "Find AI agents for DeFi trading"
- "Search for data analysis agents"
- "Show me agents with social media capabilities"

**Browse agents**:
- "List all registered agents"
- "Show me all infra-type agents"

**Validate agents.txt**:
- "Validate the agents.txt file for example.com"
- "Check if this agents.txt content is valid: ..."

**Register an agent**:
- "Register a new trading agent called MyBot"

## Architecture

- **[Agno Framework](https://github.com/agno-agi/agno)**: Agent orchestration and tool management
- **OpenAI GPT-4o**: Core language model for natural language understanding
- **[Global Chat MCP Server](https://www.npmjs.com/package/@global-chat/mcp-server)**: Provides agent discovery, search, and validation tools via MCP
- **Async Architecture**: For efficient MCP server communication

## About Global Chat

[Global Chat](https://global-chat.io) is a cross-protocol AI agent discovery platform. It aggregates agents across MCP, A2A, agents.txt, ACDP, and 9+ other protocols into a single searchable directory. The MCP server (`@global-chat/mcp-server`) exposes this data programmatically so any AI agent can discover and interact with other agents.
