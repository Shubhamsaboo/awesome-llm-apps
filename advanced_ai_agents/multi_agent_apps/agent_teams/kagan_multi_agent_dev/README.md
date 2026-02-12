# 🤖 Kagan — AI-Powered Kanban for Multi-Agent Autonomous Development

<p align="center">
  <img src="https://raw.githubusercontent.com/kagan-sh/kagan/main/.github/assets/logo-light.svg" alt="Kagan" width="400">
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/kagan-sh/kagan/main/.github/assets/demo.gif" alt="Kagan Demo" width="700">
</p>

A terminal Kanban board + MCP server for autonomous development. Manage tasks, pair-program with AI agents, launch IDE coding sessions, and orchestrate multiple coding agents — all from a TUI or programmatically via MCP.

## Overview

Kagan provides two interfaces into the same workflow:

**TUI (for developers)** — Interactive Kanban board where you create tasks, initiate AUTO (background) or PAIR (interactive) coding sessions, launch agents directly into tmux/VS Code/Cursor, review diffs, approve, and merge — without leaving the terminal.

**MCP Server (for AI CLIs)** — An admin-role MCP client connects to Kagan and uses it as a persistent orchestration layer — creating tasks, dispatching them to *different* AI coding agents, tracking progress with structured logs, and coordinating reviews. Claude Code can delegate a task to Gemini CLI, monitor it through Kagan, then assign the next task to Kimi CLI — all with persistent state, logging, and audit trail.

## Features

### Multi-Agent Orchestration
- **6 built-in AI coding agents**: Claude Code, OpenCode (SST), Codex (OpenAI), Gemini CLI (Google), Kimi CLI (Moonshot AI), GitHub Copilot
- **Cross-agent delegation**: An admin MCP client can delegate tasks to any supported agent through a single Kanban board
- Agents are discovered automatically if present in `PATH`

### Two Execution Modes

| Mode | Best for | How it works |
|------|----------|--------------|
| **AUTO** | Clear, bounded tasks | Agent runs in background; Kagan monitors progress and streams output |
| **PAIR** | Exploratory or interactive work | Opens a live terminal session in tmux, VS Code, or Cursor |

### Kanban Workflow
- Board columns: `BACKLOG` → `IN_PROGRESS` → `REVIEW` → `DONE`
- Built-in code review: inspect diffs, approve/reject, rebase, merge
- Git worktree isolation: each task gets its own branch and worktree — parallel work without conflicts
- Chat-driven planning: AI-powered task decomposition with approval flow

### MCP Server
- Full programmatic control over projects, tasks, agents, reviews, and merges
- 5 capability profiles: `viewer` → `planner` → `pair_worker` → `operator` → `maintainer`
- Two identity lanes: `kagan` (constrained) and `kagan_admin` (full access)
- Recovery policy: tools return structured hints for deterministic error handling

### Persistent State
- Every agent run is tracked with structured execution logs, scratchpad notes, and audit events
- SQLite database stores all projects, tasks, reviews, and runtime metadata
- State is shared across TUI and MCP — a task created from MCP appears in TUI and vice versa

## Architecture

```
Developer ──► TUI (Kanban Board)
                    │
                    ▼
              Core Daemon ◄── MCP Server ◄── External AI CLI (admin role)
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
     Claude Code  Gemini   Kimi CLI  ...
          │         │         │
          ▼         ▼         ▼
      Git worktree per task (isolated branches)
```

All interfaces (TUI, MCP, CLI) operate on the same core process and database.

## Installation

```bash
# Recommended
uv tool install kagan

# Or via pip
pip install kagan
```

### Requirements
- Python 3.12–3.13, Git, terminal 80×20+
- tmux (recommended for PAIR sessions on macOS/Linux)
- VS Code or Cursor (PAIR launchers, especially on Windows)
- At least one supported AI CLI installed (Claude Code, Codex, Gemini CLI, etc.)

## Usage

### Launch the TUI

```bash
cd /path/to/your-repo
kagan
```

### Quickstart Workflow

1. Open or create a project on the welcome screen
2. Press `n` to create a task — enter title, description, and pick `AUTO` or `PAIR`
3. Press `a` or `Enter` to start execution
4. Monitor progress in Task Output
5. Move task to `REVIEW`, inspect diff, approve, and merge

### Key Shortcuts

| Key | Action |
|-----|--------|
| `n` | New task |
| `Enter` | Open / confirm |
| `a` | Start agent (AUTO) |
| `s` | Stop agent |
| `v` | View task details |
| `e` | Edit task |
| `H` / `L` | Move task left/right |
| `p` | Plan mode |
| `?` | Help |
| `.` | Actions palette |
| `,` | Settings |

### MCP Server

Start the MCP server for external AI CLI integration:

```bash
# Read-only inspection
kagan mcp --readonly

# Full admin access for orchestration
kagan mcp --identity kagan_admin --capability maintainer
```

### Editor MCP Configuration

Add Kagan as an MCP server in your editor:

**Claude Code** (`~/.claude.json` or `.mcp.json`):
```json
{
  "mcpServers": {
    "kagan": {
      "command": "kagan",
      "args": ["mcp", "--capability", "pair_worker"]
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`):
```json
{
  "servers": {
    "kagan": {
      "command": "kagan",
      "args": ["mcp", "--capability", "pair_worker"]
    }
  }
}
```

**Cursor** (`.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "kagan": {
      "command": "kagan",
      "args": ["mcp", "--capability", "pair_worker"]
    }
  }
}
```

### Configuration

Kagan reads from `~/.config/kagan/config.toml`:

```toml
[general]
default_worker_agent = "claude"        # Default AI agent for AUTO tasks
default_pair_terminal_backend = "tmux" # tmux, vscode, or cursor
max_concurrent_agents = 3              # Parallel AUTO execution cap
auto_review = true                     # AI review on task completion
default_base_branch = "main"           # Default merge/diff base branch
```

### CLI Reference

```bash
kagan              # Launch TUI (default)
kagan core start   # Start core daemon in background
kagan core status  # Check core status
kagan core stop    # Stop core daemon
kagan mcp          # Run MCP server (stdio transport)
kagan list         # List all projects
kagan tools enhance "prompt"  # AI prompt enhancement
kagan update       # Check for updates
kagan reset        # Reset local state
```

## Resources

- **GitHub**: [github.com/kagan-sh/kagan](https://github.com/kagan-sh/kagan)
- **Documentation**: [docs.kagan.sh](https://docs.kagan.sh)
- **PyPI**: [pypi.org/project/kagan](https://pypi.org/project/kagan/)
- **Discord**: [discord.gg/dB5AgMwWMy](https://discord.gg/dB5AgMwWMy)

> For the latest and most detailed documentation, visit [docs.kagan.sh](https://docs.kagan.sh).
