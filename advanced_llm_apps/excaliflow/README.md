# ✏️ Excaliflow

**Hand-drawn diagrams with live animated flows.** Sketch out AI agents, RAG pipelines, or system architectures just like in Excalidraw, and watch data flow through your arrows in real time. Connect shapes, customize colors and sketch styles, and export a crisp 2x PNG or a 60fps video loop. Runs in a single HTML file with zero dependencies.

## Features

- **Hand-drawn look and feel.** Draw boxes, circles, decision diamonds, freehand sketches, and sticky notes using Excalidraw's hand-drawn fonts (`Excalifont`, `Virgil`, `Cascadia`) and sketch fills.
- **Live animated arrows.** Connect any two shapes and watch comets, pulses, neon streaks, or dashed streams travel along your arrows in order from start to finish.
- **Easy arrow editing.** Drag any arrow endpoint around the edge of a shape, pull the middle of an arrow to curve it, or double-click an arrow to straighten it.
- **Fast diagram building.** Press `Tab` or click a `+` port on any selected shape to add and connect the next step automatically, or drop a shape onto an existing arrow to split it in two.
- **Multi-agent MCP collaboration & live agent cursors.** Connect **Claude Code**, **Antigravity**, **Codex**, **Grok Bot**, or **ChatGPT** concurrently via the built-in zero-dependency Model Context Protocol (MCP) server (`stdio` and `HTTP`). Watch each agent's named cursor glide across the canvas at 60fps, branch nodes without overlapping, stamp author attribution badges (`[Claude Code]`, `[Antigravity]`), respond to `@Agent` task stickies, or click **⚡ Agent Jam** to watch 4 agents co-architect live.
- **Multi-canvas tabs & auto-save.** Work across multiple canvas tabs in the bottom tab dock or top-left canvas switcher—create new tabs (`+ New` / `+ Canvas`), fork/duplicate a diagram (`⧉`) to compare architectures side-by-side, step between tabs (`‹` / `›`), double-click to rename, and have every tab auto-saved to your browser.
- **Ready-made starter templates.** Load built-in diagrams for **AI Agent Swarm**, **RAG Pipeline**, **How Browsers Work**, and **Microservices** in one click.
- **Light & dark canvas + instant export.** Switch between a clean white canvas and a pitch-black neon canvas, then export a cropped 2x PNG, copy to clipboard, record a `.webm` video loop, or save and load `.excaliflow` / `.excalidraw` JSON files.

## How to Get Started

Requires **Node.js 18+** (or open `index.html` directly in any modern browser). Excaliflow has no external npm dependencies, so no install step is needed.

```sh
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/excaliflow
npm start
```

Open **http://localhost:3000** in your browser.

## Multi-Agent MCP Server (Claude Code, Antigravity, Codex, Grok)

`server.js` includes a zero-dependency **Model Context Protocol (MCP) JSON-RPC 2.0 server** (both `stdio` and `HTTP /mcp`) plus a real-time Server-Sent Events (`/api/events`) bridge so multiple CLI/IDE agents can collaborate on the same live browser canvas simultaneously.

```sh
# Add Excaliflow as an MCP server in Claude Code:
claude mcp add excaliflow -- node /path/to/awesome-llm-apps/advanced_llm_apps/excaliflow/server.js --mcp-stdio --agent "Claude Code"

# Or spawn for Antigravity / Codex / Grok:
node server.js --mcp-stdio --agent "Antigravity"
```

### Exposed MCP Tools
| MCP Tool | Description |
| --- | --- |
| `get_workspace_state` | Read all canvas tabs, nodes, arrows, active agents, and `@Agent` sticky mentions |
| `move_agent_cursor` | Glide an agent's named cursor (`agentName`, `x`, `y`, `statusText`) across the live canvas |
| `draw_node` | Sketch a shape or sticky with automatic collision avoidance and author attribution badge |
| `branch_from` | Semantically branch a new connected node (`right`, `bottom`, `left`, `top`) from an existing node |
| `connect_nodes` | Wire an animated causal flow arrow (`curved`, `elbow`, `straight`) between two nodes |
| `insert_between` | Split an existing arrow between two nodes and insert an intermediary node mid-stream |
| `add_critique_sticky` | Attach an architectural review sticky note next to a target node and fire a pulse burst |
| `trigger_flow_pulse` | Fire a burst of 60fps data packets along outgoing arrows from a node |
| `manage_canvas_tab` | Create, fork/duplicate, switch, or rename canvas tabs for parallel agent proposals |

## Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `V` or `1` | Select, move, resize shapes, or bend arrows |
| `H` or `Space + Drag` | Pan around the canvas |
| `R` or `2` | Rectangle |
| `D` or `3` | Diamond / Decision |
| `O` or `4` | Circle / Ellipse |
| `A` or `5` | Animated Arrow |
| `P` or `7` | Freehand Pen |
| `T` or `8` | Text |
| `N` or `9` | Sticky Note |
| `K` | Laser Pointer |
| `E` or `0` | Eraser |
| `Q` | Keep selected tool active (Tool Lock) |
| `Tab` | Add and connect the next shape |
| `Double-click` | Add a node on empty canvas, edit text, or straighten an arrow |
| `Alt / Option + Drag` | Duplicate selection while dragging |
| `⌥T` (`Alt + T`) | Create a new blank canvas tab |
| `⌥[` / `⌥]` (`Alt + [` / `]`) | Step to previous / next canvas tab |
| `⌥1` – `⌥9` (`Alt + 1..9`) | Switch directly to canvas tab 1–9 |
| `⌘Z` / `⇧⌘Z` | Undo / Redo |
| `⌘D` | Duplicate selection |
| `⌘\` | Show or hide the left style panel |

## Project Structure

```text
excaliflow/
|-- index.html            Complete single-file app (UI, sketch renderer, and animation loop)
|-- server.js             Zero-dependency local static server (http://localhost:3000)
|-- verify.js             Automated test suite for geometry, arrows, and interactions
|-- package.json          Start and test scripts
`-- README.md
```

## Development

Run the automated verification checks:

```sh
npm test
```

Licensed under the repository's [Apache-2.0 license](../../LICENSE).
