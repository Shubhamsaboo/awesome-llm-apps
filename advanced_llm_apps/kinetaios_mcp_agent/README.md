# KinetAios MCP Agent Example

Run a **self-contained Python client** that drives [KinetAios](https://github.com/phinn/KinetAios) — a local-first, multi-engine AI agent workstation (macOS & Windows) — through its built-in **MCP server**.

KinetAios exposes an `run_agent` MCP tool: point this example at a machine running KinetAios and it will spawn a full autonomous agent (shell / read_file / write_file / web_fetch, ReAct loop, SQLite-backed long-term memory) and return the final answer. No LLM API key is needed in this repo — the KinetAios instance brings its own provider.

## Why this is interesting

- **The agent runtime is remote**: this script is ~100 lines of pure `requests` — MCP JSON-RPC over HTTP, no SDK, no API key. All reasoning, tool use and memory live inside the KinetAios workstation.
- **Multi-engine**: the KinetAios side can run the task on its built-in ReAct engines or delegate to Claude Code / Codex CLIs — this example is engine-agnostic.
- **Cross-machine handoff**: sessions can be exported/imported between machines via `export_session` / `import_session` MCP tools.

## Prerequisites

1. Install & launch [KinetAios](https://github.com/phinn/KinetAios/releases) (v4.2.0+, macOS or Windows).
2. In KinetAios: **Settings → MCP Server → enable**, set a port (default `18109`) and an access token.
3. Configure an LLM provider in KinetAios (e.g. DeepSeek, GLM, OpenAI-compatible endpoint) so `run_agent` has a brain.

## Run

```bash
pip install requests
python kinetaios_agent.py --task "Summarize the top 3 items in /tmp and write a note to /tmp/summary.md"
```

Options: `--host 127.0.0.1 --port 18109 --token <token> --task "<any natural language task>"`

## What happens

```
kinetaios_agent.py            KinetAios (macOS / Windows)
      │  initialize                 │
      │────────────────────────────▶│  MCP handshake
      │  tools/list                  │
      │────────────────────────────▶│  discovers run_agent
      │  tools/call run_agent        │
      │────────────────────────────▶│  spawns full autonomous agent
      │                              │  ├─ ReAct loop (reason → act → observe)
      │                              │  ├─ shell / files / web tools
      │                              │  └─ long-term memory (SQLite/FTS5)
      │◀────────────────────────────│  final answer text
```

## Files

- `kinetaios_agent.py` — the whole client (~100 lines, pure stdlib + requests)
- `.env.example` — copy to `.env` if you prefer env config over CLI flags

## License

MIT (example code). KinetAios itself is GPL-3.0.
