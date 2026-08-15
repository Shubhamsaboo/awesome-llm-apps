# Agent Skills

This directory contains AI coding assistant skills for building MCP servers with the `mcp-use` framework.

## Installation

Skills are installed via the `mcp-use` CLI:

```bash
npx skills install mcp-use/mcp-use --skill mcp-app-builder
```

## Available Skills

- **mcp-apps-builder** — Primary skill for creating and modifying MCP servers (tools, resources, prompts, widgets).
- **mcp-builder** — Deprecated, replaced by `mcp-apps-builder`.
- **chatgpt-app-builder** — Deprecated, replaced by `mcp-apps-builder`.

## IDE Support

These skills are also mirrored to `.claude/skills/` and `.cursor/skills/` for use in Claude Code and Cursor respectively.
