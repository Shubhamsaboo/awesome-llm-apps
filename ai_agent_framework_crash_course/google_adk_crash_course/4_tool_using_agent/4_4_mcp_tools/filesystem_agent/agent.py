"""
Filesystem Agent - MCP Tools Integration Example

This example demonstrates how to connect an ADK agent to a filesystem MCP server
using the MCPToolset. The agent can perform file operations like reading, writing,
and listing files through the MCP protocol.
"""

import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Create a temporary directory for demonstration
# In a real application, you would use a specific folder path
DEMO_FOLDER = os.path.join(os.path.dirname(__file__), "..")

# Ensure the demo folder exists
os.makedirs(DEMO_FOLDER, exist_ok=True)

# Create a sample file for demonstration
sample_file_path = os.path.join(DEMO_FOLDER, "sample.txt")
with open(sample_file_path, "w") as f:
    f.write("This is a sample file for the MCP filesystem agent demonstration.\n")
    f.write("You can read, write, and list files using MCP tools.\n")

# Create the ADK agent with MCP filesystem tools
root_agent = LlmAgent(
    model='gemini-3-flash-preview',
    name='filesystem_mcp_agent',
    instruction=f"""
    You are a helpful filesystem assistant that can help users manage their files.
    
    You have access to filesystem tools through the Model Context Protocol (MCP).
    You can:
    - List files and directories
    - Read file contents
    - Write to files
    - Create directories
    
    The current working directory is: {DEMO_FOLDER}
    
    Always be helpful and explain what you're doing when performing file operations.
    If a user asks about files, use the available tools to check the filesystem.
    """,
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=[
                    "-y",  # Auto-confirm npm package installation
                    "@modelcontextprotocol/server-filesystem",
                    DEMO_FOLDER,  # The directory path the MCP server can access
                ],
            ),
            # Optional: Filter which tools from the MCP server to expose
            # tool_filter=['list_directory', 'read_file', 'write_file']
        )
    ],
)

# Export the agent for use with ADK web
__all__ = ['root_agent']

# Example usage in a script
if __name__ == "__main__":
    print(f"Filesystem MCP Agent initialized!")
    print(f"Demo folder: {DEMO_FOLDER}")
    print(f"Sample file created at: {sample_file_path}")
    print("\nTo use this agent:")
    print("1. Run 'adk web' from the tutorials root directory")
    print("2. Select 'filesystem_mcp_agent' from the dropdown")
    print("3. Try commands like:")
    print("   - 'List files in the current directory'")
    print("   - 'Read the contents of sample.txt'")
    print("   - 'Create a new file called hello.txt with the content Hello World!'")
    print("   - 'Show me all text files in the directory'") 