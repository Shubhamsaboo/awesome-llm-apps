"""
Interactive Shell Execution Tools Prompt

This file defines prompts for agents to understand when and how to use 
interactive shell execution tools for persistent terminal session management.
"""

INTERACTIVE_EXEC_TOOLS_PROMPT = """
<terminal_tools>
## important
If interactive shell commands such as ssh, ftp, nc or msfconsole are required to be executed, the commands should be executed using the following tools.
Use the `-o HostKeyAlgoriths=+ssh-rsa` option when connecting to the ssh

## Persistent Session Management Tools:
### create_session()
**When to use**: Need persistent environment for multi-step operations
**Returns**: Session ID for subsequent commands

### session_list
session list

### command_exec(command, session_id)
**When to use**: Execute commands that require state persistence
**Examples**: Directory navigation, environment setup, background processes

### kill_session(session_id)
**When to use**: Clean up when session no longer needed

## Decision Guide:
**Use Interactive Sessions For**:
- Directory changes affecting subsequent commands
- Environment variable setup
- Tool installation and configuration  
- Background process management
- Multi-command workflows requiring state

**Use Standard Execution For**:
- Simple information gathering
- One-time status checks
- Independent file operations

Use interactive sessions when commands build upon each other. Use standard execution for simple, independent operations.
</interactive_shell_tools>
"""
