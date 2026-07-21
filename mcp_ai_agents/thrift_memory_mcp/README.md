# Thrift Memory — Cost-First MCP Memory for an Agent Fleet

**Cost-first, budgeted memory for AI agents.** Thrift Memory is an open-source (Apache-2.0) MCP memory server for coding agents that stop reloading large `MEMORY.md` / `AGENTS.md` / project-context files every session. It recalls only task-relevant memory under a **hard token budget** and returns a **savings receipt** on every recall — `baselineTokens` vs `injectedTokens` vs `savedTokens` — so you can *see* the tokens you didn't pay for.

```text
savedTokens = baselineTokens − injectedTokens
```

Unlike knowledge-graph memory layers (Mem0 / Zep / Graphiti) that optimize how *smart* recall is, Thrift Memory optimizes **cost visibility**: it's the memory server that *proves* the saving.

---

## What this example shows

A coding-agent fleet where every agent reloads the same big context file at session start is paying that token bill again and again. This template wires Thrift Memory in as the memory layer and shows the **functional outcome**: a per-session savings receipt instead of a silent, repeated reload cost.

## Quick start

**1. Audit your current reload bill (nothing installed, 10 seconds):**

```bash
npx -y thrift-memory audit
```

This prints how many tokens your agents re-pay to reload context each session.

**2. Wire Thrift Memory into any MCP client** (Claude Code, Cursor, Windsurf) with the one-block config in [`mcp_config.json`](./mcp_config.json):

```json
{
  "mcpServers": {
    "thrift-memory": { "command": "npx", "args": ["-y", "thrift-memory"] }
  }
}
```

**3. Use the three memory tools from your agent:**

| Tool | Purpose |
| --- | --- |
| `remember` | Store a memory |
| `recall` | Recall only task-relevant memory **under a hard token budget** → returns the savings receipt |
| `search_memory` | Search stored memory |

Every `recall` returns `baselineTokens` (everything that would have loaded), `injectedTokens` (what was actually returned), and `savedTokens` — so the token saving is measured, not assumed.

## The functional outcome

```text
recall("wire the lead form")  →
  baselineTokens: 8,120   injectedTokens: 690   savedTokens: 7,430
```

Across a fleet, those receipts add up to a real, provable token bill you stopped paying. A local dashboard (`thrift-panel`) aggregates fleet savings across runs.

## Links

- Repo: <https://github.com/YohadH/thrift-memory>
- npm: <https://www.npmjs.com/package/thrift-memory>
- Landing: <https://yohadh.github.io/thrift-memory/>
- License: Apache-2.0 · MCP tools: `remember`, `recall`, `search_memory`
