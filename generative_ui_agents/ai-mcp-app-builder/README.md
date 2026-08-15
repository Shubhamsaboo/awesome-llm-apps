# AI MCP App Builder

Describe an MCP app in chat and get a live, sandboxed instance back. Built with [CopilotKit](https://github.com/CopilotKit/CopilotKit), [AG-UI](https://github.com/ag-ui-protocol/ag-ui), [Mastra](https://mastra.ai/), and [E2B](https://e2b.dev/) sandboxes.

**Gen UI concept — agent-generated apps.** Most generative UI picks from a fixed catalogue of components. This goes a step further: the agent authors a brand-new MCP app at runtime, the builder provisions an E2B sandbox to host it, and the app renders inline with full bidirectional tool access. The "component" the agent emits *is a whole app*.

This monorepo wires up the **MCP App builder** web UI (`apps/web`) to a **Mastra** agent (`/api/mastra-agent`) that provisions **E2B** sandboxes running the **`mcp-use-server`** template (`apps/mcp-use-server`). An optional local sample is the [Three.js MCP example](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/threejs-server) in **`apps/threejs-server`** (used for sidebar defaults when running everything locally).

https://github.com/user-attachments/assets/4bb35806-5e42-43c0-a8fe-01c0d1e5b8b3

## Prerequisites

- Node.js 20+
- [pnpm](https://pnpm.io/installation) (required for the workspace)
- OpenAI API key (`OPENAI_API_KEY`); optional **`OPENAI_MODEL`** for `/api/mastra-agent` (default **`gpt-5.5`**)

## Getting started

From the project root (`generative_ui_agents/ai-mcp-app-builder`):

```powershell
pnpm i
Copy-Item .env.example .env
# Edit .env: set OPENAI_API_KEY=sk-proj-... at minimum; add E2B_* for sandbox provisioning (see below)
pnpm dev
```

**`pnpm dev`** runs **Turbo** and starts workspace **`dev`** tasks (the Next.js app and other configured apps — see root `package.json` / `turbo.json`).

**Run pieces individually**

| Goal                                            | Command                                                               |
| ----------------------------------------------- | --------------------------------------------------------------------- |
| Web app only                                    | `pnpm --filter web dev` (from repo root) or `cd apps/web && pnpm dev` |
| Three.js MCP sample (local sidebar default)     | `cd apps/threejs-server && pnpm dev`                                  |
| `mcp-use-server` (local MCP, not the E2B image) | `cd apps/mcp-use-server && pnpm dev`                                  |

Open the URL shown by Next (usually `http://localhost:3000`).

## Dynamic MCP UI (sidebar)

- **MCP servers:** add/remove by URL (+ optional `serverId`); list is sent as **`x-mcp-servers`**. Built-in default: **Excalidraw** (`https://mcp.excalidraw.com`). Override via **`NEXT_PUBLIC_DEFAULT_MCP_SERVERS`** / **`DEFAULT_MCP_SERVERS`**.
- **Tools:** compact list; open a tool for **detail + preview** in a **modal** (not a third mobile tab).
- **Chat:** CopilotKit v2 chat with suggestions.

### Mobile layout

- **Tabs:** **Chat** and **Tools** (servers + tool list). Tool **preview / detail** opens in a **modal**.
- **Desktop:** sidebar + chat column (**`md+`**).
- **Chat UX:** spacing and bottom padding so the composer does not cover the latest messages.

## Environment variables (E2B)

| Variable       | Description                                                                                                                                     |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `E2B_API_KEY`  | From [e2b.dev/dashboard](https://e2b.dev/dashboard)                                                                                             |
| `E2B_TEMPLATE` | **`templateId`** from `Template.build` output after **`build.dev.ts`** / **`build.prod.ts`**                                                    |
| `E2B_REPO_URL` | Used when **`E2B_TEMPLATE`** is empty — clones repo into sandbox (slower cold start). Default in code: **`mcp-use-server-template`** GitHub URL |

## Documentation

**UI entry:** `apps/web/app/page.tsx` (theme, layout, CopilotKit wiring).

**External**

- [CopilotKit](https://docs.copilotkit.ai)
- [Next.js](https://nextjs.org/docs)
- [MCP Apps / UI](https://mcpui.dev/guide/introduction)
