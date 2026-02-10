# 🧠 MemoV Coding History Agent

**Query your Git coding history using natural language** - Powered by MemoV MCP Server

## ✨ Features

- 🔍 **Natural Language Queries**: Ask about your code history like talking to a colleague
- 📊 **Real MCP Tools**: Uses actual Model Context Protocol tools (mem_history, vibe_search)
- 🚀 **No Local Install**: MCP server is fetched from GitHub automatically
- ✅ **Zero Hallucination**: All data comes from real Git commits
- 🐛 **Debug Mode**: See exactly which tools are called and what they return

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd awesome-llm-apps/mcp_ai_agents/memov_coding_history_agent
pip install -r requirements.txt
```

### 2. Initialize MemoV in Your Project

```bash
# Install memov CLI
pip install git+https://github.com/memovai/memov.git

# Go to your Git repository
cd /path/to/your/git/repo

# Initialize MemoV
mem init

# Track files
mem track .
```

### 3. Run the Agent

```bash
# Set your OpenAI API key
export OPENAI_API_KEY='sk-your-key-here'

# Run Streamlit app
streamlit run memov_agent.py
```

### 4. Query Your History

In the browser:
- Enter your OpenAI API key (or it will use the environment variable)
- Specify your project path
- Ask questions like:
  - "Show me the last 10 snapshots"
  - "What files did I modify yesterday?"
  - "Find authentication patterns in my code"

## 📋 Example Queries

### History Browsing
```
- Show me the last 10 coding snapshots
- What changed in the last week?
- Display recent commits with diffs
```

### Semantic Search
```
- Find authentication code
- Search for database migrations
- Show error handling patterns
```

### Specific Analysis
```
- What files were modified in commit abc123?
- Show details for the latest snapshot
- Search for API endpoints
```

## 🔧 How It Works

```
User Query
    ↓
Streamlit UI
    ↓
Agent (GPT-4o-mini)
    ↓
MCPTools (agno)
    ↓
stdio transport
    ↓
uvx --from git+https://github.com/memovai/memov.git mem-mcp-launcher
    ↓
MemMCPTools (FastMCP Server)
    ↓
MCP Tools: mem_history(), vibe_search(), snap()
    ↓
Real Git Data from Your Repository
```

### Key Components

1. **uvx**: Runs Python packages without local installation
2. **MCP Protocol**: Model Context Protocol for tool calling
3. **stdio transport**: Standard input/output communication
4. **FastMCP Server**: Exposes MemoV tools as MCP endpoints
5. **Debug Mode**: Shows all tool calls in terminal logs

## 🛠️ MCP Tools

### mem_history(limit, commit_hash)

View MemoV history with prompts and file changes.

**Parameters**:
- `limit` (int): Number of snapshots to return (max 50)
- `commit_hash` (str): Optional specific commit to view

**Returns**: Formatted history with commits, prompts, files, timestamps

**Example**:
```python
# Agent will call:
mem_history(limit=10)

# Returns:
======================================================================
MEMOV HISTORY (10 snapshots)
======================================================================
  **314d0ee** [None]
  Operation: snap
  Prompt: test
  Files: .memignore, README.md, ...
  Time: 2026-01-27T18:49:28+08:00
...
```

### vibe_search(query, limit)

Semantic search through code (requires ChromaDB).

**Parameters**:
- `query` (str): Search query
- `limit` (int): Max results to return

**Returns**: Relevant code snippets with context

**Example**:
```python
# Agent will call:
vibe_search(query="authentication", limit=5)
```

**Note**: Requires ChromaDB: `pip install 'git+https://github.com/memovai/memov.git[rag]'`

## ✅ Verifying Real Tool Calls

When you run the agent, watch the **terminal output** for these indicators:

### Success ✅

```
DEBUG tool_calls: [ToolCall(id='...', function=Function(name='mem_history', arguments='{"limit":10}'))]
DEBUG ===================================================================== tool ========================================================================
DEBUG mem_history result:
======================================================================
MEMOV HISTORY (10 snapshots)
  **314d0ee** - Real commit hash!
```

**Key signs**:
- ✅ `tool_calls: [ToolCall(..., name='mem_history'` - Tool is being called
- ✅ `mem_history result:` - Tool returned data
- ✅ Real commit hashes (8-char hex like `314d0ee`)
- ✅ Can verify with `git log`

### Failure ❌

If you DON'T see `tool_calls` in the debug output, the agent is hallucinating.

## 📦 Requirements

- **Python**: 3.10+
- **uv**: For running packages from Git
- **OpenAI API Key**: For the AI agent
- **Git Repository**: With MemoV initialized
- **MemoV CLI**: Installed in the project

## 🐛 Troubleshooting

### "Could not find uvx"

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Verify
uvx --version
```

### "Memov not initialized"

```bash
cd /your/project

# Install memov CLI if needed
pip install git+https://github.com/memovai/memov.git

# Initialize
mem init

# Track files
mem track .
```

### "First run is slow"

The first time you run, uvx downloads and installs the MCP server from GitHub. This is normal and only happens once.

### "No tool_calls in debug output"

This means the agent isn't calling tools. Check:
1. Is `debug_mode=True` set?
2. Did MCPTools connect successfully?
3. Are there any connection errors in the logs?

### "vibe_search not available"

```bash
# Install with RAG dependencies
pip install 'git+https://github.com/memovai/memov.git[rag]'
```

## 🎯 Architecture

### Why This Works (No Hallucination)

1. **Real MCP Server**: Actual FastMCP server from memov codebase
2. **MCP Protocol**: Agent knows tools are available and callable
3. **stdio Transport**: Direct process communication
4. **Debug Logging**: Can see every tool call
5. **Type Safety**: MCP enforces tool signatures

### vs. Previous Approaches

❌ **Direct Python import**: Tools not recognized by Agent
❌ **HTTP wrappers**: Custom code, not real MCP
✅ **MCP via stdio**: Industry standard, used by Claude Desktop

## 📁 Project Structure

```
memov_coding_history_agent/
├── memov_agent.py              # Main Streamlit app
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── FINAL_IMPLEMENTATION.md     # Technical details
└── MCP_REAL_TOOLS.md          # MCP tools documentation
```

## 🔗 Links

- **MemoV GitHub**: https://github.com/memovai/memov
- **MCP Protocol**: https://modelcontextprotocol.io/
- **agno Framework**: https://github.com/agno-agi/agno
- **awesome-llm-apps**: https://github.com/Shubhamsaboo/awesome-llm-apps

## 🤝 Contributing

This agent is part of the awesome-llm-apps repository. Contributions welcome!

## 📄 License

Follows the license of the awesome-llm-apps repository.

---

**Status**: ✅ Production Ready
**Last Updated**: February 11, 2026
**MemoV Source**: git+https://github.com/memovai/memov.git

**No local installation needed - just run and query!** 🚀
