# AI MCP App Builder

Describe an MCP app in chat and get a live, sandboxed instance back. Built with [CopilotKit](https://github.com/CopilotKit/CopilotKit), [AG-UI](https://github.com/ag-ui-protocol/ag-ui), [Mastra](https://mastra.ai/), and [E2B](https://e2b.dev/) sandboxes.

**Gen UI concept — agent-generated apps.** Most generative UI picks from a fixed catalogue of components. This goes a step further: the agent authors a brand-new MCP app at runtime, the builder provisions an E2B sandbox to host it, and the app renders inline with full bidirectional tool access. The "component" the agent emits *is a whole app*.

**Production go-live:** [`docs/TRACKER.md`](docs/TRACKER.md) · **Stakeholder / product handoff** (shipped scope, CopilotKit open questions): [`docs/HANDOFF.md`](docs/HANDOFF.md)

This monorepo wires up the **MCP App builder** web UI (`apps/web`) to a **Mastra** agent (`/api/mastra-agent`) that provisions **E2B** sandboxes running the **`mcp-use-server`** template (`apps/mcp-use-server`). An optional local sample is the [Three.js MCP example](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/threejs-server) in **`apps/threejs-server`** (used for sidebar defaults when running everything locally).

https://github.com/user-attachments/assets/4bb35806-5e42-43c0-a8fe-01c0d1e5b8b3

## Prerequisites

- Node.js 20+
- [pnpm](https://pnpm.io/installation) (required for the workspace)
- OpenAI API key (`OPENAI_API_KEY`); optional **`OPENAI_MODEL`** for `/api/mastra-agent` (default **`gpt-5.5`**)

> **Lockfile:** **`pnpm-lock.yaml` is committed** and should stay in version control so installs are reproducible (`--frozen-lockfile`). This repo’s `.gitignore` only excludes `package-lock.json`, `yarn.lock`, and `bun.lockb` — not pnpm’s lockfile.

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

## Scripts reference

### Root (`package.json`)

| Script                      | Description                                                                     |
| --------------------------- | ------------------------------------------------------------------------------- |
| `pnpm dev`                  | Turbo: all packages’ `dev` scripts                                              |
| `pnpm build`                | Turbo: all packages’ `build` (for `web`, runs **`prebuild`** first — see below) |
| `pnpm lint`                 | Turbo lint                                                                      |
| `pnpm clean` / `pnpm fresh` | Remove installs / lockfile helpers (see script definitions)                     |

### `apps/web`

| Script                       | Description                                                                                                                                                |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pnpm dev`                   | Next.js dev (Turbopack)                                                                                                                                    |
| `pnpm build`                 | Runs **`prebuild`** → **`pack-download-kit`** (writes **`.download-kit/base.tar.gz`** for [full app kit](docs/HANDOFF.md) download), then **`next build`** |
| `pnpm pack-download-kit`     | Regenerate **`.download-kit/base.tar.gz`** without a full Next build                                                                                       |
| `pnpm start`                 | Production Next server                                                                                                                                     |
| `pnpm lint`                  | ESLint                                                                                                                                                     |
| `pnpm run test:download-kit` | Integration test: Next + E2B + **`POST /api/workspace/download`** (see **`apps/web/test/`)**                                                               |
| `pnpm run test:e2b-download` | Smoke test: E2B tarball only                                                                                                                               |
| `pnpm run dev:mcp`           | Starts the **Three.js** sample MCP from **`apps/threejs-server`** (for local MCP alongside web)                                                            |

Manual scripts under **`apps/web/test/`**: run from **`apps/web`** as `node test/<file>.mjs` (paths and env documented in each file).

### E2B sandbox template (`apps/mcp-use-server`)

The agent provisions sandboxes from an E2B **template** defined in **`template.ts`**. Rebuild the image when you change dependencies, tools, or widgets there.

| Script                                  | When to use                    | Command (from repo root)                                                |
| --------------------------------------- | ------------------------------ | ----------------------------------------------------------------------- |
| **Dev template** (`mcp-use-server-dev`) | Day-to-day iteration           | `cd apps/mcp-use-server && npx tsx --env-file=../../.env build.dev.ts`  |
| **Prod template** (`mcp-use-server`)    | Stable snapshot for production | `cd apps/mcp-use-server && npx tsx --env-file=../../.env build.prod.ts` |

Requirements: **`E2B_API_KEY`** in `.env` (or environment). The CLI prints a **`BuildInfo`** object; set **`E2B_TEMPLATE`** to **`templateId`** from that output (and the same in your hosting dashboard). Template **name** (e.g. `mcp-use-server-dev`) is not the same as **`templateId`**.

## Agent and UI

The app title is **MCP App builder** (subtitle **Powered by CopilotKit**), logo **`apps/web/app/image.png`**, agent route **`/api/mastra-agent`**. Header CTAs use **`NEXT_PUBLIC_HEADER_*`** (and **`NEXT_PUBLIC_GITHUB_REPO_URL`** for the secondary link; code default points at **this demo repo**). Chat starters: **`NEXT_PUBLIC_CHAT_STARTER_PROMPTS`** (JSON) or **three** built-in bounded demos — tic tac toe, tip calculator, dice roller (**[`docs/HANDOFF.md`](docs/HANDOFF.md)**). Reference CopilotKit route: **`apps/web/app/api/copilotkit/route.ts`**.

**Starter prompts** use **`useCopilotChatSuggestions`** (`ChatSuggestions.tsx`) with v2 **`CopilotChat`**.

**Post-provision test chips:** frontend action **`show_mcp_test_prompts`** (`McpTestPromptsAction.tsx`) — JSON string of `{ label, message }[]` for clickable chips (**`appendMessage`**).

**Download:** **`restart_server`** / sidebar download can return a **full app kit** (`.tar.gz`): E2B workspace merged into **`mcp-apps-starter/`** when **`apps/web/.download-kit/base.tar.gz`** exists (created by **`pnpm build`** / **`prebuild`** in `apps/web`). Otherwise download is **MCP-only**. Details: **`docs/HANDOFF.md`**.

**Debug agent traffic:** set **`MASTRA_AGENT_DEBUG=1`** in `.env` for verbose **`/api/mastra-agent`** logs (see `.env.example`).

### Duplicate React keys (Mastra agent) — RCA and fix

Mastra can reuse the same `messageId` for tool-call parents and text events; CopilotKit then collides keys. **`mastra-agent/route.ts`** remaps ids when collisions are detected — see **`docs/HANDOFF.md`** / inline comments.

## Dynamic MCP UI (sidebar)

- **MCP servers:** add/remove by URL (+ optional `serverId`); list is sent as **`x-mcp-servers`**. Built-in default: **Excalidraw** (`https://mcp.excalidraw.com`). Override via **`NEXT_PUBLIC_DEFAULT_MCP_SERVERS`** / **`DEFAULT_MCP_SERVERS`**.
- **Tools:** compact list; open a tool for **detail + preview** in a **modal** (not a third mobile tab).
- **Chat:** CopilotKit v2 chat with suggestions.

More: **[`docs/DYNAMIC_MCP.md`](docs/DYNAMIC_MCP.md)**.

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

## Hosting on Render

1. Push this repo to GitHub/GitLab.
2. In the Render dashboard, go to **Blueprints** and select your repo — Render auto-detects `render.yaml`.
3. Set secret env vars in the dashboard: at least **`OPENAI_API_KEY`**; for sandboxes add **`E2B_API_KEY`** + **`E2B_TEMPLATE`**.
4. Deploy. The Blueprint configures build/start commands, `NODE_VERSION`, and `HOSTNAME` automatically.

Render runs a long-lived Node.js process (not serverless), so there are no per-function timeout limits. See **[`docs/DEPLOY-RENDER.md`](docs/DEPLOY-RENDER.md)** for full setup, env var tables, and troubleshooting.

### Agent tool pattern (sidebar preview)

Widget tools should include **`_meta["ui/previewData"]`** for offline sidebar preview (example: **`apps/mcp-use-server/tools/product-search.ts`**).

## Documentation

**In this repo**

- **[`docs/TRACKER.md`](docs/TRACKER.md)** — **production go-live checklist**
- **[`docs/HANDOFF.md`](docs/HANDOFF.md)** — shipped scope, CopilotKit open questions
- **[`docs/DEPLOY-RENDER.md`](docs/DEPLOY-RENDER.md)** — Render deployment guide
- **[`docs/DYNAMIC_MCP.md`](docs/DYNAMIC_MCP.md)** — dynamic MCP patterns
- **[`docs/PLAN.md`](docs/PLAN.md)** / **[`docs/E2B-IMPLEMENTATION.md`](docs/E2B-IMPLEMENTATION.md)** — roadmap and E2B design

**UI entry:** `apps/web/app/page.tsx` (theme, layout, CopilotKit wiring).

**External**

- [CopilotKit](https://docs.copilotkit.ai)
- [Next.js](https://nextjs.org/docs)
- [MCP Apps / UI](https://mcpui.dev/guide/introduction)

## Contributing

Issues and PRs welcome.

## License

MIT — see **LICENSE**.
