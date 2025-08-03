# Enterprise Knowledge Orchestrator

A production-grade multi-agent system built with Google ADK that orchestrates knowledge management across local files and SaaS platforms using MCP (Model Context Protocol).

## Overview

This system combines:
- **Local Filesystem MCP Server** - for accessing and analyzing local documents
- **Notion MCP Server** - for managing Notion workspaces and content
- **Composio MCP Server** - for GitHub and Figma integration
- **Intelligent Router/Orchestrator** - context-aware task delegation with state management
- **4 Specialized Agents** - each handling specific platform capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Router/Orchestrator Agent                    │
│              (Coordinator/Dispatcher Pattern)               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ File Analysis   │  │ Notion Agent    │  │ GitHub Agent │ │
│  │ Agent           │  │ (Optional)      │  │ (Optional)   │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│           │                     │                    │       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Filesystem MCP  │  │ Notion MCP      │  │ Composio MCP │ │
│  │ Server          │  │ Server          │  │ Server       │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│           │                     │                    │       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Local Documents │  │ Notion Pages &  │  │ GitHub Repos │ │
│  │ (PDF, DOC, XLS) │  │ Databases       │  │ & Issues     │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ Figma Agent     │  │ Composio MCP    │                   │
│  │ (Optional)      │  │ Server          │                   │
│  └─────────────────┘  └─────────────────┘                   │
│           │                     │                           │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ Figma Files &   │  │ Figma Designs & │                   │
│  │ Designs         │  │ Assets          │                   │
│  └─────────────────┘  └─────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### **Routing Patterns:**

1. **Coordinator/Dispatcher Pattern**: Intelligent routing based on query analysis
2. **LLM-Driven Delegation**: Automatic agent selection using `transfer_to_agent()`
3. **Explicit Invocation**: Direct agent calls using `AgentTool`
4. **Graceful Degradation**: System works with any combination of available agents

## Features

### 🔍 File Analysis Agent
- Analyzes local documents (PDFs, Word docs, spreadsheets)
- Extracts key topics, summaries, and action items
- Categorizes documents by type and content
- Identifies information for knowledge base sync

### 📝 Notion Agent
- Reads, writes, and updates Notion pages and databases
- Searches for content across Notion workspace
- Creates structured knowledge bases and documentation
- Syncs content from other sources to Notion

### 🐙 GitHub Agent
- Creates and manages GitHub issues and pull requests
- Searches repositories and code
- Manages repository content and documentation
- Sets up automated workflows and actions

### 🎨 Figma Agent
- Reads and analyzes Figma files and designs
- Exports design assets and components
- Searches for design elements and styles
- Manages design system components

### 🎯 Router/Orchestrator Agent
- Analyzes user requests and determines which agents should handle them
- Routes tasks to appropriate specialized agents based on capabilities
- Coordinates multi-step workflows that require multiple agents
- Shares context and results between agents through session state
- Provides comprehensive results and recommendations

### 🛡️ Error Handling & Graceful Degradation
- **MCP Server Failures**: Graceful fallback when servers are unavailable
- **Missing Environment Variables**: System works with available APIs only
- **Agent Creation Failures**: Continues with available agents
- **Validation**: Ensures at least one agent is available before operation
- **Comprehensive Logging**: Detailed logs for troubleshooting

## Prerequisites

1. **Python 3.9+** and **Node.js** (for MCP servers)
2. **Google ADK** installed and configured
3. **Notion API Key** for Notion integration
4. **Required API Keys** in environment variables

## Setup

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key_here

# Required: API Keys for MCP Tools
NOTION_API_KEY=your_notion_api_key_here
GITHUB_API_KEY=your_github_api_key_here
FIGMA_API_KEY=your_figma_api_key_here

# Optional: Custom filesystem path (defaults to ~/Documents)
MCP_FILESYSTEM_PATH=/Users/madhushantan/Downloads

```

### 2. Notion Setup

#### Creating a Notion Integration
1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Name your integration (e.g., "Enterprise Knowledge Orchestrator")
4. Select the capabilities needed (Read & Write content)
5. Submit and copy your "Internal Integration Token"

#### Sharing Your Notion Page with the Integration
1. Open your Notion page
2. Click the three dots (⋮) in the top-right corner
3. Select "Add connections" from the dropdown
4. Search for your integration name
5. Click on your integration to add it to the page
6. Confirm by clicking "Confirm"

#### Finding Your Notion Page ID
1. Open your Notion page in a browser
2. Copy the URL: `https://www.notion.so/workspace/Your-Page-1f5b8a8ba283...`
3. The ID is the part after the last dash: `1f5b8a8ba283`

### 3. Notion Implementation

The system uses SSE (Composio) for Notion integration:

```python
# Notion MCP Server (SSE - Composio)
url="https://mcp.composio.dev/composio/server/61e41019-d05f-44d0-973e-2aef7777063a/sse?useComposioHelperActions=true"
```

**Features:**
- **SSE Connection**: Uses Server-Sent Events for real-time communication
- **Composio Managed**: No local dependencies required
- **Full Tool Access**: All available Notion tools are accessible
- **Authentication**: Handled by Composio service

**Note**: The Notion integration requires a valid `NOTION_API_KEY` and `NOTION_PAGE_ID` to function properly.

### 4. GitHub & Figma Implementation

The system uses separate SSE (Composio) servers for GitHub and Figma:

```python
# GitHub MCP Server (SSE - Composio)
url="https://mcp.composio.dev/composio/server/11fbff47-fa12-432f-8c3a-18ed4e9f66f8/sse?useComposioHelperActions=true"

# Figma MCP Server (SSE - Composio)  
url="https://mcp.composio.dev/composio/server/f05e7129-7997-4c17-a654-f935278c0dfe/sse?useComposioHelperActions=true"
```

**Features:**
- **Separate Servers**: Each service has its own dedicated Composio server
- **Full Tool Access**: All available GitHub and Figma tools are accessible
- **No Local Dependencies**: Managed by Composio service

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Verify MCP Server Installation

```bash
# Verify npx is available
which npx

# Test filesystem MCP server
npx -y @modelcontextprotocol/server-filesystem --help

# Test Notion MCP server
npx -y @notionhq/notion-mcp-server --help
```

## Usage

### Basic Usage

```python
import asyncio
from agent import EnterpriseKnowledgeOrchestrator

async def main():
    # Create orchestrator
    orchestrator = EnterpriseKnowledgeOrchestrator()
    
    try:
        # Process knowledge request
        results = await orchestrator.process_knowledge_request(
            "Analyze all PDF documents in my Documents folder and create GitHub issues for action items"
        )
        
        # Access results
        print(f"Files analyzed: {len(results['file_analysis'])}")
        print(f"Notion operations: {len(results['notion_operations'])}")
        print(f"GitHub operations: {len(results['github_operations'])}")
        print(f"Figma operations: {len(results['figma_operations'])}")
        
    finally:
        await orchestrator.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Example Requests

```python
# Document analysis
"Analyze all PDF documents in my Documents folder and create a summary"

# Multi-platform operations
"Search for design components in my Figma files and create a GitHub repository for the design system"

# Notion and GitHub integration
"Read my Notion project page and create GitHub issues for all action items"

# Figma asset management
"Export design assets from Figma and organize them in a structured folder"

# Complex workflows
"Analyze quarterly reports, extract key metrics, create Notion dashboard, and set up GitHub issues for follow-ups"
```

## Agent Routing Logic

The Router/Orchestrator agent intelligently routes tasks based on query analysis:

- **File-related tasks** → FileAnalysisAgent
- **Notion-related tasks** → NotionAgent  
- **GitHub-related tasks** → GitHubAgent
- **Figma-related tasks** → FigmaAgent
- **Multi-platform tasks** → Coordinate between relevant agents

## Configuration

### MCP Server URLs

The system uses these MCP servers:

```python
# Filesystem MCP Server (local)
command='npx'
args=["-y", "@modelcontextprotocol/server-filesystem", "~/Documents"]

# Notion MCP Server (SSE - Composio)
url="https://mcp.composio.dev/composio/server/61e41019-d05f-44d0-973e-2aef7777063a/sse?useComposioHelperActions=true"

# GitHub MCP Server (SSE - Composio)
url="https://mcp.composio.dev/composio/server/11fbff47-fa12-432f-8c3a-18ed4e9f66f8/sse?useComposioHelperActions=true"

# Figma MCP Server (SSE - Composio)
url="https://mcp.composio.dev/composio/server/f05e7129-7997-4c17-a654-f935278c0dfe/sse?useComposioHelperActions=true"
# No tool filtering - all available tools are accessible
```

### Custom Filesystem Path

The system now supports configurable filesystem paths through environment variables:

```bash
# Set in .env file or export in terminal
export MCP_FILESYSTEM_PATH="/path/to/your/folder"

# Examples:
export MCP_FILESYSTEM_PATH="/Users/username/Projects"
export MCP_FILESYSTEM_PATH="/home/user/documents"
export MCP_FILESYSTEM_PATH="~/Desktop/Work"
```

**Features:**
- **Flexible Paths**: Use absolute or relative paths
- **Auto-Expansion**: Tilde (~) expansion for home directory
- **Auto-Creation**: Directory created if it doesn't exist
- **Fallback**: Defaults to `~/Documents` if not specified

## Output Schemas

The system uses structured Pydantic models for consistent outputs:

### FileAnalysis
```python
{
    "file_name": "quarterly_report.pdf",
    "file_type": "PDF",
    "summary": "Q3 financial performance analysis...",
    "key_topics": ["revenue", "expenses", "growth"],
    "action_items": ["Review budget allocation", "Update projections"]
}
```

### NotionOperation
```python
{
    "operation_type": "read",
    "page_id": "1f5b8a8ba283...",
    "content_summary": "Project documentation read from Notion",
    "status": "completed",
    "results": {"content": "...", "blocks": [...]}
}
```

### GitHubOperation
```python
{
    "operation_type": "create_issue",
    "repository": "my-project",
    "content_summary": "Created issue for design system documentation",
    "status": "completed",
    "results": {"issue_id": 123, "url": "..."}
}
```

### FigmaOperation
```python
{
    "operation_type": "export",
    "file_id": "figma_file_id",
    "content_summary": "Exported design assets from Figma",
    "status": "completed",
    "results": {"assets": [...], "urls": [...]}
}
```

## Context Sharing

The system implements intelligent context sharing between agents:

```python
# Session state includes shared context
"shared_context": {
    "current_task": user_request,
    "agent_results": {},
    "dependencies": []
}

# Agents can access and update shared context
updated_session.state["shared_context"]["agent_results"]["file_analysis"] = file_results
```

## Error Handling

The system includes comprehensive error handling:

- **MCP Connection Failures**: Graceful fallback when servers are unavailable
- **API Rate Limits**: Automatic retry logic with exponential backoff
- **Invalid Data**: Validation and sanitization of inputs
- **Session Management**: Proper cleanup of resources

## Monitoring and Logging

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.INFO)

# Monitor agent activities
logger.info("File analysis completed: 5 documents processed")
logger.warning("Notion API key not found, Notion integration disabled")
logger.error("Failed to create GitHub issue: rate limit exceeded")
```

## Production Deployment

### Environment Setup
```bash
# Production environment variables
export GOOGLE_API_KEY="your_production_key"
export NOTION_API_KEY="your_production_key"
export LOG_LEVEL="INFO"
```

### Resource Management
```python
# Proper cleanup in production
async with EnterpriseKnowledgeOrchestrator() as orchestrator:
    results = await orchestrator.process_knowledge_request(request)
```

### Scaling Considerations
- Use connection pooling for MCP servers
- Implement caching for frequently accessed documents
- Consider async processing for large document sets
- Monitor memory usage with large file operations

## Troubleshooting

### Common Issues

1. **MCP Server Connection Failed**
   ```bash
   # Verify Node.js and npx installation
   node --version
   npx --version
   
   # Test filesystem MCP server manually
   npx -y @modelcontextprotocol/server-filesystem /path/to/documents
   
   # Test Notion MCP server manually
   npx -y @notionhq/notion-mcp-server
   ```

2. **Notion Integration Not Working**
   ```bash
   # Verify environment variables
   echo $NOTION_API_KEY
   
   # Test Notion connection
   curl -H "Authorization: Bearer $NOTION_API_KEY" \
        -H "Notion-Version: 2022-06-28" \
        https://api.notion.com/v1/users/me
   ```

3. **Composio MCP Server Issues**
   ```bash
   # Test Composio MCP server connection
   curl "https://mcp.composio.dev/composio/server/f05e7129-7997-4c17-a654-f935278c0dfe/sse?useComposioHelperActions=true"
   ```

4. **Permission Denied for Documents**
   ```bash
   # Check file permissions
   ls -la ~/Documents
   
   # Update permissions if needed
   chmod 755 ~/Documents
   ```

### Debug Mode

```python
# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Add debug information to agent
orchestrator = EnterpriseKnowledgeOrchestrator()
print(f"Platforms available: {orchestrator.session_service.get_session(...).state['platforms_available']}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [MCP Tools Guide](https://google.github.io/adk-docs/tools/mcp-tools/)
- [Notion MCP Server](https://github.com/notionhq/notion-mcp-server)
- [Composio MCP Server](https://mcp.composio.dev/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
