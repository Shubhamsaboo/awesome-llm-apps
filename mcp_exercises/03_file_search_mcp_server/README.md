# File Search MCP Server

An MCP server for searching and reading files on the local filesystem with path safety restrictions.

## Features

**Tools:**
- `search_files` - Search for files by glob pattern (e.g., `*.py`, `**/*.md`)
- `read_file` - Read file contents with line limit control
- `search_in_files` - Search for text within file contents (grep-like)
- `get_file_info` - Get detailed metadata about files/directories
- `list_directory` - List directory contents with optional hidden file display

**Resources:**
- `filesystem://info` - Information about the configured base directory

**Prompts:**
- `analyze_codebase` - Analyze project structure for a given language
- `find_in_project` - Search for a term across the entire project

## Concepts Demonstrated

- File I/O operations with path safety validation
- Configurable base directory via environment variables
- Glob pattern matching for file discovery
- Text search across multiple files
- Human-readable file size formatting
- Security: all paths are resolved and validated against the base directory

## Setup

```bash
pip install -r requirements.txt

# Run with default base directory (current working directory)
python server.py

# Or set a custom base directory
MCP_BASE_DIR=/path/to/project python server.py
```

## Configuration

Set the `MCP_BASE_DIR` environment variable to control which directory the server can access. By default, it uses the current working directory.

```json
{
  "mcpServers": {
    "file-search": {
      "command": "python",
      "args": ["/path/to/03_file_search_mcp_server/server.py"],
      "env": {
        "MCP_BASE_DIR": "/path/to/your/project"
      }
    }
  }
}
```

## Example Tool Calls

```
search_files(pattern="**/*.py")
read_file(path="src/main.py", max_lines=50)
search_in_files(query="import", pattern="*.py")
list_directory(path="src", show_hidden=false)
```
