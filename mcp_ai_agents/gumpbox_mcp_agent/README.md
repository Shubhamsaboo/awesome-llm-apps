# 📟 Gumpbox MCP Agent

> Turn any AI coding assistant (Claude Code, Codex, Cursor, Gemini, VSCode) into a Linux sysadmin that manages real servers over MCP.

Gumpbox is a native macOS/iOS app that manages remote Linux servers via SSH. It ships a built-in **global MCP server** that exposes your entire server fleet — SSH terminals, file transfers, tunnels, monitoring, workflows, and Docker sandboxes — as a single MCP endpoint. Any MCP-aware agent can connect and drive your infrastructure in natural language.

- **Native macOS app** (SwiftUI, not Electron) — local-first, runs on your Mac.
- **Local-first MCP** — credentials never leave your machine; the agent only sees what gumpbox exposes.
- **Single global endpoint** — one session URL bridges agents to every server you own.
- **17 built-in capabilities** — SSH, SFTP, tunnels, monitoring, cron, processes, sandboxes, workflows, skills.
- **Works with any MCP client** — Claude Code, Codex, Cursor, Windsurf, Continue, VSCode, Gemini.

## What the agent can do

Once connected, the agent gets access to these MCP resources:

| Resource | What it exposes |
|----------|-----------------|
| `servers` | List, add, connect, open terminals on configured SSH servers |
| `terminal_use` | Interactive PTY sessions — send commands, read screen, send input |
| `file_transfer` | Upload/download between your Mac and any server (SFTP) |
| `tunnels` | SSH local port-forwards — create, start, stop, open in browser |
| `sessions` | Per-server authorization sessions for terminal/file/memory ops |
| `sandbox` | Provision Docker + gVisor sandbox containers with SSH access |
| `workflows` | Build and run multi-step automation workflows |
| `memory` | Agent memory store — persist context across runs |
| `skills` | Custom skill library — reusable agent playbooks (CRUD via MCP) |
| `activities` | Full audit log of every MCP action the agent takes |
| `readme` | Self-documenting server orientation (call this first) |

## Setup

### 1. Install Gumpbox (macOS)

Download from [gumpbox.com](https://gumpbox.com) — summer sale $3.99, free trial available.

Gumpbox runs entirely on your Mac. Add your SSH servers via the UI (credentials stored in macOS Keychain, never on disk in plaintext).

### 2. Enable the Global MCP server

Open Gumpbox → **Settings → Global MCP** → enable. Copy the session URL (looks like `http://127.0.0.1:7777/global/mcp/<token>`). The token is scoped to your machine.

### 3. Connect your AI client

Pick your editor below. Each installer writes the right MCP config and prompts for the session URL.

#### Claude Code

```bash
npx @gumpbox/cli install claude-code
```

Writes `~/.claude/mcp-servers/gumpbox.json`. Restart Claude Code.

#### Codex (OpenAI)

```bash
npx @gumpbox/cli install codex
```

Appends `[mcp_servers.gumpbox]` to `~/.codex/config.toml`. Restart Codex.

#### Gemini

```bash
npx @gumpbox/cli install gemini
```

Writes `mcpServers.gumpbox` to `~/.gemini/settings.json`. Restart Gemini CLI.

#### VSCode / Cursor / Windsurf / Continue

Install the **Gumpbox MCP** extension from the VSCode Marketplace or OpenVSX (covers Cursor + Windsurf automatically). Then run `Gumpbox: Set Session URL` from the command palette.

### 4. Seed starter skills (optional but recommended)

```bash
npx @gumpbox/cli seed-skills
```

Pushes 6 starter skills into Gumpbox (`connect-server`, `run-command`, `tunnel-setup`, `sandbox-quickstart`, `file-transfer`, `skill-management`). The agent will discover and use these automatically.

### 5. Talk to your agent

Open your AI client and ask:

> "Use the gumpbox MCP to list my servers, then SSH into the first one and check disk usage."

The agent will:
1. Call `list_resources` → see the gumpbox MCP surface
2. Call `readme.get` → orient itself on the server version + capabilities
3. Call `servers.list` → enumerate your fleet
4. Call `terminal_use.create_session` → open a PTY on the chosen server
5. Call `terminal_use.send_command` → run `df -h`
6. Call `terminal_use.read_terminal` → read the output back to you

Every command runs inside a `systemd-run` sandbox wrapper. Dangerous operations surface an approval dialog in the Gumpbox app before they execute.

## How it works

```
┌─────────────────┐    stdio JSON-RPC    ┌──────────────┐    HTTP loopback    ┌─────────────────┐
│  AI editor      │  ──────────────────► │  @gumpbox    │  ────────────────► │  Gumpbox app    │
│  (Claude Code,  │                      │  /cli proxy  │                     │  GlobalMCPServer│
│  Codex, Cursor, │  ◄────────────────── │              │  ◄──────────────── │  :7777          │
│  Gemini, VSCode)│                      │              │                     │                 │
└─────────────────┘                      └──────────────┘                     └─────────────────┘
                                                                                       │
                                                                                       ▼
                                                                              Your SSH servers
                                                                              (Docker, tunnels,
                                                                               files, terminals)
```

- The **`@gumpbox/cli`** npm package provides a single `gumpbox` bin with a `proxy` subcommand. Host editors spawn `gumpbox proxy` as a stdio MCP server.
- The proxy reads `~/.gumpbox/session.json` (perms `0600`) for the session URL, forwards every JSON-RPC call over HTTP loopback to the Gumpbox app.
- Gumpbox's existing `GlobalMCPServer` (Hummingbird + SwiftNIO) handles the request, fans out to per-server labeled SSH connections, and returns the result.
- Zero new server code in Gumpbox — the bridge reuses the production MCP endpoint that ships with the app.

## Session URL contract

- Source: Gumpbox UI → Global MCP panel → "Copy session URL".
- Shape: `http://127.0.0.1:7777/global/mcp/<token>` (loopback only, token in URL path).
- Stored at `~/.gumpbox/session.json` with `0600` perms on POSIX, `%USERPROFILE%\.gumpbox\session.json` on Windows.
- Never stored in env vars or in client MCP config files (those reference only the `gumpbox proxy` binary path).
- Proxy re-reads on every request — change the URL via `npx @gumpbox/cli set-url` and it takes effect without restarting your editor.

## Example agent sessions

**Deploy a side project to a sandbox:**
> "Use gumpbox to provision a sandbox on the khoa-agent server, install Node 20, clone my repo, and start the app on port 3000."

**Investigate a flapping service:**
> "SSH into omniroute and tell me why nginx keeps restarting. Show me the last 50 lines of the error log."

**Set up a tunnel for local dev:**
> "Create a tunnel from local port 5432 to the production Postgres on omniroute so I can inspect it from my Mac."

**Onboard a new server:**
> "I have a fresh Ubuntu box at 164.152.167.164. Add it to gumpbox, connect, install Docker, and harden SSH (disable root login, set up ufw)."

Each of these flows through the same MCP surface — the agent picks the right resource/action by reading `list_resources` + `list_resource_actions` + `get_resource_action_schema` first.

## Security model

- **Loopback only** — Gumpbox's MCP server binds to `127.0.0.1`. No remote exposure.
- **Per-machine session token** — copied from the app, stored in `~/.gumpbox/session.json` with `0600` perms, never in env vars or git.
- **Keychain-backed credentials** — SSH passwords/keys live in macOS Keychain. The agent never sees them; it only invokes gumpbox actions that use them internally.
- **`systemd-run` sandboxing** — every command the agent runs on a server is wrapped in a `systemd-run` sandbox with configurable security presets (minimal / write / trusted).
- **Approval flows for dangerous ops** — adding servers, provisioning credentials, accessing paths outside `$HOME`, and other sensitive mutations surface a native approval dialog in the Gumpbox app before they execute.
- **Full audit log** — every MCP action is recorded in the `activities` resource with timestamp, params, and result.

## Links

- **Gumpbox app**: [gumpbox.com](https://gumpbox.com)
- **CLI + installers (npm)**: [`@gumpbox/cli`](https://www.npmjs.com/package/@gumpbox/cli)
- **Source (extensions repo)**: [github.com/0xtrou/gumpbox-extensions](https://github.com/0xtrou/gumpbox-extensions)
- **MCP protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)

## License

The `@gumpbox/cli` bridge and installers are MIT-licensed. The Gumpbox app itself is commercial ($3.99 summer sale, free trial available).

---

<p align="center">
  <sub>Built by <a href="https://github.com/0xtrou">0xtrou</a> · Gumpbox = AI-first Linux server management for macOS + iOS</sub>
</p>
