# 🌐 MCP Tools Integration

Welcome to the **Model Context Protocol (MCP)** integration guide! This example demonstrates how to connect your ADK agents with external data sources and tools through the standardized MCP protocol.

## 🎯 What You'll Learn

- **MCP Fundamentals**: Understanding the Model Context Protocol
- **ADK ↔ MCP Integration**: Using `MCPToolset` to connect to MCP servers
- **External Tool Access**: Leveraging tools from MCP servers
- **Server Communication**: Working with both local and remote MCP servers
- **Real-world Applications**: Practical examples with filesystem and Wikipedia

## 🧠 Core Concept: Model Context Protocol

The **Model Context Protocol (MCP)** is an open standard that enables AI agents to:
- Access external data sources consistently
- Use tools from remote servers
- Communicate with various applications
- Maintain context across interactions

### How MCP Works with ADK

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  ADK Agent  │◄──►│ MCPToolset  │◄──►│ MCP Server  │
│             │    │             │    │             │
│   Gemini    │    │   Bridge    │    │   Tools     │
└─────────────┘    └─────────────┘    └─────────────┘
```

**MCPToolset** acts as a bridge that:
- Connects to MCP servers (local or remote)
- Discovers available tools automatically
- Translates MCP tools into ADK-compatible format
- Manages connection lifecycle

## 🔧 Integration Patterns

### 1. **Using External MCP Servers**
Connect to existing MCP servers:
- **Filesystem Server**: File operations
- **Wikipedia Server**: Knowledge retrieval
- **Database Server**: Data access
- **API Server**: External service integration

### 2. **Communication Protocols**
- **Server-Sent Events (SSE)**: Real-time communication for remote servers
- **Standard I/O**: Local process communication for MCP servers

## 🚀 Examples in This Tutorial

### 📍 **Example 1: Filesystem Agent**
**Location**: `./filesystem_agent/`
- Connect to filesystem MCP server
- Perform file operations (read, write, list)
- Handle local file system interactions
- Use Standard I/O communication

### 🔥 **Example 2: Firecrawl Agent**
**Location**: `./firecrawl_agent/`
- Connect to Firecrawl MCP server for advanced web scraping
- Perform single page scraping, batch processing, and website crawling
- Extract structured data with AI-powered analysis
- Conduct deep web research with multi-source synthesis
- Use Standard I/O communication with cloud API integration


## 📁 Project Structure

```
4_4_mcp_tools/
├── README.md                    # This file - MCP integration guide
├── requirements.txt             # MCP dependencies
├── filesystem_agent/            # Filesystem MCP integration
│   ├── __init__.py             # Package initialization
│   ├── agent.py                # Main agent implementation
│   └── README.md               # Filesystem agent guide
├── firecrawl_agent/             # Firecrawl web scraping integration
│   ├── __init__.py             # Package initialization
│   ├── agent.py                # Main agent implementation
│   └── README.md               # Firecrawl agent guide
```

## 🎯 Key Features

- **Seamless Integration**: `MCPToolset` handles all MCP protocol details
- **Automatic Discovery**: Tools are discovered and made available automatically
- **Multiple Protocols**: Supports both stdio and SSE communication
- **Error Handling**: Robust error management for network and server issues
- **Resource Management**: Proper cleanup of connections and resources

## 📋 Prerequisites

Before running these examples:

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment**:
   ```bash
   # From the root tutorials directory
   cp env.example .env
   # Edit .env and add your Google AI API key
   ```

3. **Node.js for MCP Servers** (for community servers):
   ```bash
   # Install Node.js if not already installed
   # Required for npm/npx based MCP servers
   ```

## 🔄 How It Works

### Connection Flow
1. **Initialize MCPToolset** with connection parameters
2. **Establish Connection** to MCP server
3. **Discover Tools** via MCP protocol
4. **Adapt Tools** to ADK format
5. **Use Tools** in agent conversations
6. **Cleanup** connections on completion

### Code Example
```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Create MCP toolset for external server
toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command='npx',
        args=['-y', '@modelcontextprotocol/server-filesystem', '/path/to/folder']
    )
)

# Create agent with MCP tools
agent = LlmAgent(
    model='gemini-3-flash-preview',
    name='mcp_agent',
    instruction='Use MCP tools to help users',
    tools=[toolset]
)
```

## 🚀 Getting Started

### Quick Start
1. **Choose an example** to explore:
   - **Filesystem Agent**: For file operations
   - **Firecrawl Agent**: For advanced web scraping and research

2. **Follow the guide** in each example directory

3. **Run with ADK Web**:
   ```bash
   # From the root tutorials directory
   adk web
   ```

## 🔗 Example Walkthrough

### Filesystem Agent Example
```python
# Connect to filesystem MCP server
toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command='npx',
        args=['-y', '@modelcontextprotocol/server-filesystem', '/path/to/folder']
    )
)

# Ask agent to use filesystem tools
# "List files in the current directory"
# "Read the contents of sample.txt"
```

### Firecrawl Agent Example
```python
# Connect to Firecrawl MCP server
toolset = MCPToolset(
    connection_params=StdioServerParameters(
        command='npx',
        args=['-y', 'firecrawl-mcp'],
        env={'FIRECRAWL_API_KEY': 'your_api_key'}
    )
)

# Ask agent to use web scraping tools
# "Scrape the homepage of https://example.com"
# "Find all blog post URLs on https://blog.example.com"
# "Search for recent AI research papers and extract summaries"
# "Extract product details from this e-commerce page: [URL]"
```



## 💡 Best Practices

- **Connection Management**: Always handle connection lifecycle properly
- **Error Handling**: Implement robust error handling for network issues
- **Resource Cleanup**: Use proper cleanup patterns for connections
- **Security**: Validate inputs and handle authentication appropriately
- **Performance**: Consider connection pooling for high-throughput scenarios

## 🔍 Troubleshooting

### Common Issues
- **Connection Errors**: Check server URL and network connectivity
- **Tool Not Found**: Verify server is running and tools are exposed
- **Authentication**: Ensure proper API keys and credentials
- **Version Compatibility**: Check MCP protocol version compatibility

### Debug Commands
```bash
# Test MCP server connection
npx @modelcontextprotocol/inspector

# Check ADK agent logs
adk web --debug
```

## 🔗 Next Steps

After completing this tutorial:
- **[Tutorial 4: Memory Agent](../../5_memory_agent/README.md)** - Add memory capabilities
- **[Tutorial 5: Workflow Agent](../../7_plugins/README.md)** - Multi-step processes
- **[Tutorial 6: Multi-agent System](../../8_simple_multi_agent/README.md)** - Agent collaboration

## 📚 Additional Resources

- **[MCP Specification](https://modelcontextprotocol.io/docs/spec)** - Protocol details
- **[ADK MCP Documentation](https://google.github.io/adk-docs/tools/mcp-tools/)** - Integration guide
- **[Community MCP Servers](https://github.com/modelcontextprotocol/servers)** - Ready-to-use servers

## 🎯 Real-World Applications

MCP tools enable:
- **Knowledge Retrieval**: Access Wikipedia, databases, documents
- **File Operations**: Read, write, manage files and directories
- **API Integration**: Connect to external services and APIs
- **Data Processing**: Transform and analyze data from various sources
- **Custom Tools**: Create and share specialized tools across agents