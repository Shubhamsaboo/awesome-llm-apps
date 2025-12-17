# 📁 Filesystem Agent - MCP Integration

This example demonstrates how to connect an ADK agent to a **filesystem MCP server** using the `MCPToolset`. The agent can perform file operations like reading, writing, and listing files through the Model Context Protocol.

## 🎯 What This Example Shows

- **MCP Server Connection**: Connect to `@modelcontextprotocol/server-filesystem`
- **File Operations**: Read, write, list files and directories
- **Stdio Communication**: Use standard input/output for local MCP server communication
- **Automatic Tool Discovery**: Let ADK discover and use available filesystem tools

## 🔧 How It Works

### MCP Server Setup
The agent connects to a filesystem MCP server that provides these tools:
- `list_directory`: List files and folders
- `read_file`: Read file contents
- `write_file`: Write content to files
- `create_directory`: Create new directories

### Connection Flow
```python
MCPToolset(
    connection_params=StdioServerParameters(
        command='npx',
        args=['-y', '@modelcontextprotocol/server-filesystem', '/path/to/folder']
    )
)
```

## 🚀 Getting Started

### Prerequisites
1. **Node.js and npm**: Required for the filesystem MCP server
2. **ADK Environment**: Set up with your Google AI API key
3. **Dependencies**: Install from `requirements.txt`

### Running the Agent

1. **Navigate to tutorials root**:
   ```bash
   cd ai_agent_framework_crash_course/google_adk_tutorials/
   ```

2. **Start ADK Web**:
   ```bash
   adk web
   ```

3. **Select Agent**: Choose `filesystem_mcp_agent` from the dropdown

4. **Test Commands**:
   - "List files in the current directory"
   - "Read the contents of sample.txt"
   - "Create a new file called hello.txt with the content Hello World!"
   - "Show me all text files in the directory"

## 📝 Example Conversations

### File Listing
```
User: List files in the current directory
Agent: I'll list the files in the current directory for you.
[Uses list_directory tool]
Found the following files:
- sample.txt
- hello.txt
```

### File Reading
```
User: Read the contents of sample.txt
Agent: I'll read the contents of sample.txt for you.
[Uses read_file tool]
The file contains:
This is a sample file for the MCP filesystem agent demonstration.
You can read, write, and list files using MCP tools.
```

### File Writing
```
User: Create a new file called notes.txt with the content "Meeting notes for today"
Agent: I'll create the file notes.txt with your specified content.
[Uses write_file tool]
Successfully created notes.txt with the content "Meeting notes for today".
```

## 🔧 Code Structure

### Agent Definition
```python
root_agent = LlmAgent(
    model='gemini-3-flash-preview',
    name='filesystem_mcp_agent',
    instruction="""
    You are a helpful filesystem assistant that can help users manage their files.
    You have access to filesystem tools through the Model Context Protocol (MCP).
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=['-y', '@modelcontextprotocol/server-filesystem', DEMO_FOLDER]
            )
        )
    ]
)
```

### Demo Environment
The agent uses the parent directory of the agent file for demonstration:
- **Location**: Parent directory of the filesystem_agent folder
- **Sample File**: `sample.txt` with demo content
- **Working Directory**: Accessible to the MCP server for safe operations

## 🛠️ Available Tools

The filesystem MCP server provides these tools automatically:

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_directory` | List files and folders | `path` (optional) |
| `read_file` | Read file contents | `path` (required) |
| `write_file` | Write content to file | `path`, `content` |
| `create_directory` | Create new directory | `path` |

## 🔍 Advanced Usage

### Tool Filtering
```python
MCPToolset(
    connection_params=StdioServerParameters(
        command='npx',
        args=['-y', '@modelcontextprotocol/server-filesystem', DEMO_FOLDER]
    ),
    tool_filter=['list_directory', 'read_file']  # Only expose specific tools
)
```

## 🚨 Important Notes

- **Security**: The MCP server only has access to the specified directory
- **Node.js Required**: The filesystem server runs via `npx`
- **Working Directory**: Uses parent directory for easy access to project files
- **Error Handling**: Agent handles file not found and permission errors gracefully

## 🔍 Troubleshooting

### Common Issues

1. **Node.js Not Found**:
   ```bash
   # Install Node.js
   # macOS: brew install node
   # Ubuntu: sudo apt install nodejs npm
   ```

2. **Permission Errors**:
   - Ensure the directory is writable
   - Check file permissions

3. **MCP Server Not Starting**:
   - Verify Node.js installation
   - Check if port is available
   - Review console logs

### Debug Commands
```bash
# Test MCP server directly
npx @modelcontextprotocol/server-filesystem /path/to/folder

# Run with debug logging
adk web --debug
```

## 🔗 Next Steps

After trying this example:
1. **Customize the Directory**: Change `DEMO_FOLDER` to your preferred location
2. **Add More Tools**: Explore other MCP servers
3. **Try Server Agent**: Learn to create custom MCP servers
4. **Integrate with Workflows**: Combine with other ADK features

## 📚 Related Documentation

- **[ADK MCP Tools](https://google.github.io/adk-docs/tools/mcp-tools/)** - Official documentation
- **[MCP Filesystem Server](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)** - Server details
- **[Model Context Protocol](https://modelcontextprotocol.io/)** - Protocol specification