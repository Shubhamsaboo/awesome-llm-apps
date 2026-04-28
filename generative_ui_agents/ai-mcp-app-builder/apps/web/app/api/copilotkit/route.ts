import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { BuiltInAgent, defineTool } from "@copilotkit/runtime/v2";
import { z } from "zod";
import { NextRequest } from "next/server";
import { MCPAppsMiddleware, getServerHash } from "@ag-ui/mcp-apps-middleware";
import { map } from "rxjs/operators";
import { E2BWorkspaceProvider } from "@/lib/workspace/e2b";
import { getDefaultMcpServers, type McpServerConfig } from "@/lib/mcp-defaults";

// Allow up to 5 minutes for long agent loops
export const maxDuration = 300;

/**
 * Fallback used only when no x-mcp-servers header is present
 * (e.g. direct API calls, curl tests).
 * In normal frontend usage the header is always sent by DynamicCopilotKitProvider.
 */
function readMcpServersFromHeader(req: NextRequest): McpServerConfig[] {
  try {
    const raw = req.headers.get("x-mcp-servers");
    if (raw == null) return getDefaultMcpServers();
    const parsed = JSON.parse(raw) as McpServerConfig[];
    if (!Array.isArray(parsed)) return getDefaultMcpServers();
    console.log(
      "[copilotkit] MCP servers from header:",
      parsed.map((s) => s.url),
    );
    return parsed;
  } catch {
    console.warn(
      "[copilotkit] Failed to parse x-mcp-servers header, using defaults",
    );
    return getDefaultMcpServers();
  }
}

/**
 * Subclass that fixes widget HTML for CSP-safe rendering:
 * 1. Strips <base> tags (blocked by CSP base-uri 'self' in SANDBOX_HTML)
 * 2. Rewrites internal origin refs to the external server origin
 *    (for window.__mcpPublicUrl, window.__getFile, etc.)
 *
 * With --inline builds, all JS/CSS is inlined into the HTML, so no external
 * script/style loads are needed. Only image/fetch URLs need rewriting.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
class MCPAppsMiddlewareFixBase extends MCPAppsMiddleware {
  private _mcpServers: McpServerConfig[];

  constructor(opts: { mcpServers: McpServerConfig[] }) {
    super(opts);
    this._mcpServers = opts.mcpServers || [];
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  run(input: any, next: any) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const source = super.run(input, next) as any;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const proxiedReq = (input as any).forwardedProps?.__proxiedMCPRequest;
    const isResourceRead = proxiedReq?.method === "resources/read";
    if (!isResourceRead) return source;

    // Find the server config to get the correct external origin URL
    let serverOrigin: string | null = null;
    if (proxiedReq) {
      const cfg = this._mcpServers.find((s) => {
        if (proxiedReq.serverId && s.serverId)
          return s.serverId === proxiedReq.serverId;
        if (proxiedReq.serverHash)
          return (
            getServerHash({ type: s.type, url: s.url } as Parameters<
              typeof getServerHash
            >[0]) === proxiedReq.serverHash
          );
        return false;
      });
      if (cfg) {
        try {
          serverOrigin = new URL(cfg.url).origin;
        } catch {
          /* ignore */
        }
      }
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return source.pipe(
      map((event: any) => {
        if (
          event.type === "RUN_FINISHED" &&
          Array.isArray(event.result?.contents)
        ) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const contents = event.result.contents.map((c: any) => {
            if (typeof c.text === "string") {
              let html = c.text;
              const baseTagMatch = html.match(/<base\s+href="([^"]*)"[^>]*>/i);
              if (baseTagMatch) {
                try {
                  const internalOrigin = new URL(baseTagMatch[1]).origin;
                  // Strip <base> tag (violates CSP base-uri 'self')
                  html = html.replace(/<base\b[^>]*>/gi, "");
                  // Rewrite all remaining internal origin references
                  if (serverOrigin && internalOrigin !== serverOrigin) {
                    html = html.replaceAll(internalOrigin, serverOrigin);
                  }
                } catch {
                  /* ignore */
                }
              }
              return { ...c, text: html };
            }
            return c;
          });
          return { ...event, result: { ...event.result, contents } };
        }
        return event;
      }),
    );
  }
}

// ── E2B workspace provider (stateless — safe to reuse across requests) ──────

const workspaceProvider = new E2BWorkspaceProvider();

// ── Backend tools — run server-side inside the agent loop ────────────────────

const workspaceTools = [
  defineTool({
    name: "provision_workspace",
    description:
      "Create an E2B sandbox from the pre-built mcp-use-server template. " +
      "With a template this takes ~3 s (deps + server are baked in). " +
      "Returns workspaceId and endpoint. " +
      "After success, ALWAYS call add_mcp_server(endpoint, serverId) " +
      "and set_active_workspace(workspaceId, endpoint) so the UI updates.",
    parameters: z.object({
      name: z
        .string()
        .describe("Short identifier for this workspace, e.g. 'weather-widget'"),
    }),
    execute: async ({ name }) => {
      const info = await workspaceProvider.provision(name);
      return JSON.stringify({
        workspaceId: info.workspaceId,
        endpoint: info.endpoint,
        status: info.status,
        nextSteps: [
          `Call add_mcp_server("${info.endpoint}", "${name}") to connect the sandbox to the UI`,
          `Call set_active_workspace("${info.workspaceId}", "${info.endpoint}") to show the status badge`,
        ],
      });
    },
  }),

  defineTool({
    name: "read_file",
    description:
      "Read a file from the active E2B workspace. Path is relative to workspace root " +
      "(/home/user/workspace). Use this to inspect existing code before editing.",
    parameters: z.object({
      workspaceId: z
        .string()
        .describe("Sandbox ID returned by provision_workspace"),
      path: z
        .string()
        .describe("Relative file path, e.g. 'index.ts' or 'tools/my-tool.ts'"),
    }),
    execute: async ({ workspaceId, path }) => {
      return await workspaceProvider.readFile(workspaceId, path);
    },
  }),

  defineTool({
    name: "write_file",
    description:
      "Write (create or overwrite) a file in the active E2B workspace. " +
      "Parent directories are created automatically. Path is relative to workspace root.",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
      path: z
        .string()
        .describe(
          "Relative file path, e.g. 'resources/price-chart/widget.tsx'",
        ),
      content: z.string().describe("Full file content to write"),
    }),
    execute: async ({ workspaceId, path, content }) => {
      await workspaceProvider.writeFile(workspaceId, path, content);
      return `Wrote ${content.length} chars to "${path}"`;
    },
  }),

  defineTool({
    name: "edit_file",
    description:
      "Targeted search-and-replace in a workspace file. " +
      "The search string must match exactly (including whitespace/newlines). " +
      "Prefer this over write_file for small changes.",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
      path: z.string().describe("Relative file path"),
      search: z.string().describe("Exact string to find in the file"),
      replace: z.string().describe("String to replace it with"),
    }),
    execute: async ({ workspaceId, path, search, replace }) => {
      await workspaceProvider.editFile(workspaceId, path, search, replace);
      return `Edited "${path}" — replaced the target string.`;
    },
  }),

  defineTool({
    name: "exec",
    description:
      "Run a shell command in the workspace root of the active E2B sandbox. " +
      "Use background=true for long-running processes (e.g. starting the dev server). " +
      "Rebuild sequence after edits: " +
      "1) exec(\"ss -tlnp 'sport = :3109' | grep -oP 'pid=\\\\K[0-9]+' | head -1 | xargs -r kill; sleep 1\") " +
      "2) exec('npm run dev', background=true).",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
      cmd: z.string().describe("Shell command to run"),
      background: z
        .boolean()
        .optional()
        .describe(
          "Run in background and return immediately (for servers). Default: false.",
        ),
      timeoutMs: z
        .number()
        .optional()
        .describe(
          "Timeout in milliseconds for foreground commands. Default: 60000.",
        ),
    }),
    execute: async ({ workspaceId, cmd, background, timeoutMs }) => {
      const result = await workspaceProvider.exec(workspaceId, cmd, {
        background,
        timeoutMs,
      });
      if (result.background) return `Started in background: ${cmd}`;
      const parts: string[] = [];
      if (result.stdout) parts.push(`stdout:\n${result.stdout}`);
      if (result.stderr) parts.push(`stderr:\n${result.stderr}`);
      parts.push(`exit code: ${result.exitCode}`);
      return parts.join("\n");
    },
  }),

  defineTool({
    name: "get_workspace_info",
    description: "Get current status and endpoint of the active E2B sandbox.",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
    }),
    execute: async ({ workspaceId }) => {
      const info = await workspaceProvider.getInfo(workspaceId);
      return JSON.stringify(info);
    },
  }),

  defineTool({
    name: "download_workspace",
    description:
      "Package the current workspace as a .tar.gz archive (excludes node_modules/dist) and return a signed download URL. " +
      "Present the URL to the user so they can download their MCP server.",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
    }),
    execute: async ({ workspaceId }) => {
      const { downloadUrl } =
        await workspaceProvider.prepareDownload(workspaceId);
      return `Workspace packaged. Download URL (valid ~1 hour): ${downloadUrl}`;
    },
  }),
];

// ── System prompt ─────────────────────────────────────────────────────────────

const AGENT_SYSTEM_PROMPT = `You are the MCP UI Studio coding agent. You can USE existing MCP tools and BUILD new ones in live E2B sandboxes.

CRITICAL — DO NOT STOP AFTER A TOOL CALL:
After every tool result you MUST continue in the same run. Either:
  (a) Call the next tool in your plan, or
  (b) Send a short text message to the user (e.g. "Done. Next I'll…" or "That succeeded. …").
Never end your turn immediately after a tool returns without doing (a) or (b). The user sees nothing if you stop without a message. Keep going until the workflow is complete, then send a final summary.

COMMUNICATION — follow these rules on every turn:
- Before calling any tool, send a short message explaining what you are about to do.
- After each tool returns, send a brief update: what succeeded and what comes next (or call the next tool).
- When the task is done, send a plain-text summary to the user.
- Keep messages concise (1–2 sentences). No filler phrases.

═══════════════════════════════════════════════════════════════
TEMPLATE KNOWLEDGE — mcp-use-server
═══════════════════════════════════════════════════════════════
The E2B sandbox runs a pre-built mcp-use-server template.
Deps and build artifacts are baked in — provisioning takes ~3 s.
The dev server starts automatically on port 3109.

Key files in the workspace (/home/user/workspace):
  index.ts                          — Entry point. Has TWO marker comments:
                                        // ADD NEW TOOL IMPORTS HERE
                                        // ADD NEW TOOL REGISTRATIONS HERE
  tools/<name>.ts                   — Tool backend: exports register(server).
  resources/<widget-name>/widget.tsx — Widget UI: React component rendered in an iframe.
  resources/<widget-name>/types.ts  — Prop types: zod schema + TS type for the widget props.(Only needed for complex widgets)
  resources/styles.css              — Shared Tailwind styles (already exists, import in widgets).(Only needed for complex widgets)
  package.json                      — Uses mcp-use framework + React + Tailwind.

Every MCP UI tool has TWO parts that you MUST create:
  1. A tool file   (tools/<name>.ts)           — backend logic + widget binding
  2. A widget folder (resources/<name>/)        — React component the user sees

── TOOL FILE PATTERN (tools/<name>.ts) ─────────────────────────

\`\`\`ts
import { MCPServer, text, widget } from "mcp-use/server";
import { z } from "zod";

export function register(server: MCPServer) {
  server.tool(
    {
      name: "get-weather",
      description: "Fetch weather for a city and display it in a widget",
      schema: z.object({
        city: z.string().describe("City name"),
      }),
      widget: {
        name: "weather-widget",       // must match the folder name under resources/
        invoking: "Fetching weather…",
        invoked: "Weather loaded",
      },
      _meta: {
        // REQUIRED for MCP UI Studio: preview shown in sidebar before any live call
        "ui/previewData": {
          city: "London",
          temperature: 22,
          conditions: "Sunny",
        },
      },
    },
    async ({ city }) => {
      const temp = Math.round(15 + Math.random() * 20);
      const conditions = ["Sunny", "Cloudy", "Rainy", "Windy"][Math.floor(Math.random() * 4)];
      return widget({
        props: { city, temperature: temp, conditions },
        output: text(\`Weather in \${city}: \${temp}°C, \${conditions}\`),
      });
    }
  );
}
\`\`\`

Key points:
  • widget.name in the tool config MUST match the resources/ folder name.
  • For every widget tool you MUST add _meta["ui/previewData"] with sample data matching
    the widget props shape. This powers the MCP UI Studio sidebar preview (demo before any live call).
    Example: _meta: { "ui/previewData": { city: "London", temperature: 22, conditions: "Sunny" } }
  • The handler returns widget({ props, output }) — props go to the React component,
    output is the text summary the LLM sees.
  • For tools without UI, skip the widget config and _meta, and return text(...) instead.

── WIDGET FILE PATTERN (resources/<name>/types.ts) ─────────────

\`\`\`ts
import { z } from "zod";

export const propSchema = z.object({
  city: z.string(),
  temperature: z.number(),
  conditions: z.string(),
});

export type WeatherWidgetProps = z.infer<typeof propSchema>;
\`\`\`

── WIDGET FILE PATTERN (resources/<name>/widget.tsx) ───────────

\`\`\`tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import React from "react";
import "../styles.css";
import { propSchema } from "./types";
import type { WeatherWidgetProps } from "./types";

export const widgetMetadata: WidgetMetadata = {
  description: "Displays weather information for a city",
  props: propSchema,
  metadata: { prefersBorder: false },
};

const WeatherWidget: React.FC = () => {
  const { props, isPending } = useWidget<WeatherWidgetProps>();

  if (isPending) {
    return (
      <McpUseProvider>
        <div className="p-6 animate-pulse">Loading weather…</div>
      </McpUseProvider>
    );
  }

  const { city, temperature, conditions } = props;

  return (
    <McpUseProvider>
      <div className="rounded-2xl border border-default bg-surface-elevated p-6">
        <h2 className="text-xl font-bold">{city}</h2>
        <p className="text-4xl font-light mt-2">{temperature}°C</p>
        <p className="text-secondary mt-1">{conditions}</p>
      </div>
    </McpUseProvider>
  );
};

export default WeatherWidget;
\`\`\`

Key points:
  • MUST export widgetMetadata (with props: propSchema) and a default React component.
  • Wrap the entire component tree in <McpUseProvider>.
  • useWidget<Props>() gives you { props, isPending } — show a loading state when isPending.
  • Import "../styles.css" for Tailwind classes.
  • The widget renders inside an iframe — it must be self-contained.

── REGISTERING IN index.ts ─────────────────────────────────────

Use edit_file with these exact marker strings:
  1. Add import BEFORE the marker:
     search: "// ADD NEW TOOL IMPORTS HERE"
     replace: 'import { register as registerMyTool } from "./tools/my-tool";\\n// ADD NEW TOOL IMPORTS HERE'
  2. Add registration BEFORE the marker:
     search: "// ADD NEW TOOL REGISTRATIONS HERE"
     replace: "registerMyTool(server);\\n// ADD NEW TOOL REGISTRATIONS HERE"

═══════════════════════════════════════════════════════════════
WORKFLOWS
═══════════════════════════════════════════════════════════════

You handle three kinds of requests. Pick the right workflow.

── A. BUILD A NEW MCP UI TOOL (user has no sandbox yet) ───────

Goal: spin up a sandbox, create the tool + widget, and make it live.

1. Spin up the sandbox.
   provision_workspace("weather-app") → gives you workspaceId + endpoint.

2. Wire the sandbox into the UI so the user sees it.
   add_mcp_server(endpoint, "weather-app")
   set_active_workspace(workspaceId, endpoint)

3. Study the template so you understand the patterns.
   read_file(workspaceId, "index.ts")
   read_file(workspaceId, "tools/product-search.ts")
   read_file(workspaceId, "resources/product-search-result/widget.tsx")
   read_file(workspaceId, "resources/product-search-result/types.ts")

4. Create the widget (the UI the user will see).
   write_file(workspaceId, "resources/weather-widget/types.ts", <prop schema + type>)
   write_file(workspaceId, "resources/weather-widget/widget.tsx", <React component>)
   The folder name ("weather-widget") becomes the widget name you reference in the tool.

5. Create the tool (the backend that powers the widget).
   write_file(workspaceId, "tools/weather.ts", <tool code>)
   Make sure the tool config has widget: { name: "weather-widget" } matching the folder.

6. Register the tool in index.ts so the server knows about it.
   edit_file — add import at "// ADD NEW TOOL IMPORTS HERE"
   edit_file — add registration at "// ADD NEW TOOL REGISTRATIONS HERE"
   Skipping this step means the tool won't load.

7. Restart the dev server to pick up all changes.
   "npm run dev" first runs "mcp-use build" (compiles widget React code into
   the iframe bundle), then starts the server. Both steps must succeed.
   exec(workspaceId, "kill $(lsof -t -i:3109) 2>/dev/null; sleep 1")
   exec(workspaceId, "npm run dev", background=true)

8. Verify everything works.
   exec(workspaceId, "sleep 8") — give the build + server startup time to finish.
   refresh_mcp_tools()
   If the new tool does NOT appear, check for build errors:
     exec(workspaceId, "cat /tmp/dev.log") or re-run npm run dev in foreground
     to see the error output, fix the code, and restart again.
   Once confirmed, tell the user it's live.

── B. ADD / EDIT A TOOL (sandbox already running) ─────────────

The sandbox and UI are already connected — skip steps 1–2.

  • To edit an existing tool → read_file the tool and/or widget, then edit_file.
  • To add a new tool → create the widget folder (types.ts + widget.tsx),
    create the tool file, register in index.ts (same as A.4–A.6).
  • After any change → restart the server (A.7) and verify (A.8).
    Remember: "npm run dev" rebuilds widgets before starting, so widget
    changes only take effect after a restart.

── C. USE AN EXISTING MCP TOOL ────────────────────────────────

The user wants to call a tool already registered on a connected server.
No sandbox work — the tool is available to you via the middleware. Just call it.

═══════════════════════════════════════════════════════════════
EXAMPLE — "Build me a crypto price widget"
═══════════════════════════════════════════════════════════════

User: "Build a crypto price widget"

→ You say: "I'll spin up a sandbox and build that for you."
→ provision_workspace("crypto-price")
→ add_mcp_server(endpoint, "crypto-price")
→ set_active_workspace(workspaceId, endpoint)

→ You say: "Sandbox is ready. Let me study the template first."
→ read_file(workspaceId, "index.ts")
→ read_file(workspaceId, "tools/product-search.ts")
→ read_file(workspaceId, "resources/product-search-result/widget.tsx")
→ read_file(workspaceId, "resources/product-search-result/types.ts")

→ You say: "Got it. I'll create the widget UI first, then the tool."
→ write_file(workspaceId, "resources/crypto-price/types.ts",
    <zod schema: symbol, price, change24h, marketCap>)
→ write_file(workspaceId, "resources/crypto-price/widget.tsx",
    <React component: shows coin name, price in large text, 24h change with
     green/red coloring, market cap, loading skeleton when isPending>)

→ You say: "Widget created. Now writing the tool that fetches prices."
→ write_file(workspaceId, "tools/crypto-price.ts",
    <tool: name "get-crypto-price", schema { symbol: z.string() },
     widget: { name: "crypto-price" }, handler fetches mock/real price data
     and returns widget({ props, output: text(...) })>)

→ You say: "Registering the tool in index.ts."
→ edit_file(workspaceId, "index.ts", ...) — add import
→ edit_file(workspaceId, "index.ts", ...) — add registration

→ You say: "All files written. Restarting the server — this will rebuild the widget and start fresh."
→ exec(workspaceId, "kill $(lsof -t -i:3109) 2>/dev/null; sleep 1")
→ exec(workspaceId, "npm run dev", background=true)
→ exec(workspaceId, "sleep 8")
→ refresh_mcp_tools()

→ You say: "Your crypto price widget is live! You should see get-crypto-price in the sidebar. Try asking me to look up the price of Bitcoin."

═══════════════════════════════════════════════════════════════
AVAILABLE TOOLS
═══════════════════════════════════════════════════════════════
BACKEND (run inside the E2B sandbox):
  provision_workspace  — create a new sandbox (~3 s with template)
  read_file            — read any file in the workspace
  write_file           — create or overwrite a file
  edit_file            — search-and-replace inside a file
  exec                 — run a shell command (use background=true for servers)
  get_workspace_info   — check sandbox status
  download_workspace   — archive the workspace and get a download URL

FRONTEND ACTIONS (update UI state — no server-side effect):
  add_mcp_server(endpoint, serverId)          — connect sandbox to the sidebar
  set_active_workspace(workspaceId, endpoint) — show the "Running" badge
  refresh_mcp_tools()                         — re-introspect servers after a restart

Always pass the workspaceId from provision_workspace to every subsequent backend tool call.`;

// ── Request handler ────────────────────────────────────────────────────────────
// Note: If the agent stops after one or two tool calls with no final message, the
// LLM is likely ending the turn after tool results. The system prompt instructs it
// to always continue (next tool or a user message). If it persists, see CopilotKit
// issues e.g. #2416 (tool result / RunError handling) and runtime agent-loop options.

export const POST = async (req: NextRequest) => {
  const mcpServers = readMcpServersFromHeader(req);

  const middleware = new MCPAppsMiddlewareFixBase({ mcpServers });

  const agent = new BuiltInAgent({
    model: "openai/gpt-4o",
    prompt: AGENT_SYSTEM_PROMPT,
    // Cast: defineTool() returns specific Zod types; BuiltInAgent expects ToolDefinition<ZodTypeAny>[]
    tools: workspaceTools as unknown as ConstructorParameters<
      typeof BuiltInAgent
    >[0]["tools"],
  });

  agent.use(middleware);

  const serviceAdapter = new ExperimentalEmptyAdapter();

  const runtime = new CopilotRuntime({
    agents: {
      default: agent,
    },
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
