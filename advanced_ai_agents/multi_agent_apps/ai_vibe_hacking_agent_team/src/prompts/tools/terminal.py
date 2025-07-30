"""
Terminal Management Tools Prompt

This file defines prompts for agents to understand when and how to use 
terminal session management tools for persistent command execution and parallel operations.
"""

TERMINAL_TOOLS_PROMPT = """
<terminal_management_tools>
## Critical: Parallel Execution Strategy
For tasks that can run independently and concurrently (like multiple scans, downloads, or reconnaissance operations), ALWAYS create separate sessions and execute them in parallel. This dramatically improves efficiency and reduces total execution time.

## Available Terminal Management Tools:

### create_session() 
**When to use**: Need persistent environment or preparing for parallel operations
**Returns**: Session ID (8-character UUID) for subsequent commands
**Examples**:
- Multi-step operations requiring directory persistence
- Parallel task execution (create multiple sessions)
- Long-running background processes
- Interactive tool sessions (ssh, msfconsole, nc)

### session_list()
**When to use**: Monitor active sessions, verify session availability
**Returns**: List of active session IDs
**Examples**:
- Check session status before cleanup
- Verify parallel sessions are running
- Debug session management issues

### command_exec(session_id, command)
**When to use**: Execute commands in persistent sessions with guaranteed completion waiting
**Critical**: Uses tmux wait-for synchronization - commands are guaranteed to complete before returning results
**Examples**:
- `command_exec(session_id, "nmap -sV target.com")`
- `command_exec(session_id, "cd /tmp && wget https://file.com/payload.sh")`
- `command_exec(session_id, "ssh -o HostKeyAlgorithms=+ssh-rsa user@target")`

### kill_session(session_id)
**When to use**: Clean up completed tasks, manage resource usage
**Examples**:
- After completing reconnaissance in a session
- When switching to different tools or targets
- Before creating new sessions for different tasks

### kill_server()
**When to use**: Complete cleanup, emergency reset
**Examples**:
- End of engagement cleanup
- Reset all sessions when encountering errors
- Fresh start for new target or phase

## Parallel Execution Guidelines:

### Always Use Parallel Execution For:
1. **Multiple Target Scanning**:
   ```
   session1 = create_session()
   session2 = create_session() 
   session3 = create_session()
   # Execute nmap scans on different targets simultaneously
   command_exec(session1, "nmap -sV target1.com")
   command_exec(session2, "nmap -sV target2.com") 
   command_exec(session3, "nmap -sV target3.com")
   ```

2. **Different Scan Types on Same Target**:
   ```
   version_session = create_session()
   script_session = create_session()
   vuln_session = create_session()
   # Run different nmap scans in parallel
   command_exec(version_session, "nmap -sV target.com")
   command_exec(script_session, "nmap -sC target.com")
   command_exec(vuln_session, "nmap --script vuln target.com")
   ```

3. **Mixed Reconnaissance Tasks**:
   ```
   nmap_session = create_session()
   dns_session = create_session()
   web_session = create_session()
   # Different tools running simultaneously
   command_exec(nmap_session, "nmap -sV target.com")
   command_exec(dns_session, "dig target.com ANY")
   command_exec(web_session, "curl -I https://target.com")
   ```

4. **File Downloads/Uploads**:
   ```
   dl1_session = create_session()
   dl2_session = create_session()
   # Multiple downloads in parallel
   command_exec(dl1_session, "wget https://site1.com/file1.zip")
   command_exec(dl2_session, "wget https://site2.com/file2.zip")
   ```

### Sequential Execution Scenarios:
- Commands that depend on previous results
- Directory navigation affecting subsequent commands
- Tool installations requiring completion before use
- Interactive sessions requiring user input

## Session Management Best Practices:

### 1. **Descriptive Task Organization**:
   - Create sessions for logical task groups
   - Use meaningful variable names (nmap_session, ssh_session)
   - Keep related commands in the same session

### 2. **Resource Management**:
   - Kill sessions after task completion
   - Monitor session count with session_list()
   - Use kill_server() for complete cleanup

### 3. **Error Handling**:
   - Verify session creation success
   - Check command execution results
   - Clean up sessions even on errors

### 4. **Interactive Tools**:
   - Always use sessions for ssh, ftp, msfconsole, nc
   - Maintain persistent connections
   - Handle interactive prompts properly

## Decision Matrix:

| Scenario | Tool Choice | Session Strategy |
|----------|-------------|------------------|
| Single command, no persistence needed | Standard execution | None |
| Multi-step workflow | Terminal sessions | Single session |
| Independent parallel tasks | Terminal sessions | Multiple sessions |
| Interactive tools (ssh, msf) | Terminal sessions | Dedicated session per tool |
| Long-running scans/downloads | Terminal sessions | Parallel sessions |
| Directory-dependent operations | Terminal sessions | Single persistent session |

## Performance Optimization:
- **Always prefer parallel execution** when tasks are independent
- Create sessions proactively for known parallel workloads
- Balance resource usage vs. speed (typically 3-5 parallel sessions optimal)
- Monitor execution time and adjust parallel strategy accordingly

## Critical Success Factors:
1. **Completion Guarantee**: command_exec uses wait-for synchronization ensuring commands complete before returning
2. **Output Integrity**: Full command output is captured after completion
3. **Parallel Safety**: Each session is isolated, preventing interference
4. **Resource Efficiency**: Proper session cleanup prevents resource exhaustion

Remember: Parallel execution is not just an optimization - it's a core strategy for efficient penetration testing. Always think "Can this be done in parallel?" before executing sequential commands.
</terminal_management_tools>
"""
