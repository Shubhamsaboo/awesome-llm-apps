import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { MastraAgent } from "@ag-ui/mastra";
import { Agent } from "@mastra/core/agent";
import { MCPClient } from "@mastra/mcp";
import { createOpenAI } from "@ai-sdk/openai";
import { NextRequest } from "next/server";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { Observable } from "rxjs";
import crypto from "crypto";
import { z } from "zod";
import { E2BWorkspaceProvider } from "@/lib/workspace/e2b";
import { getDefaultMcpServers, type McpServerConfig } from "@/lib/mcp-defaults";

// Allow up to 5 minutes for long agent loops
export const maxDuration = 300;

const mastraVerbose = process.env.MASTRA_AGENT_DEBUG === "1";
function mastraLog(...args: unknown[]) {
  if (mastraVerbose) console.log(...args);
}

function readMcpServersFromHeader(req: NextRequest): McpServerConfig[] {
  try {
    const raw = req.headers.get("x-mcp-servers");
    if (raw == null) return getDefaultMcpServers();
    const parsed = JSON.parse(raw) as McpServerConfig[];
    if (!Array.isArray(parsed)) return getDefaultMcpServers();
    mastraLog(
      "[mastra-agent] MCP servers from header:",
      parsed.map((s) => s.url),
    );
    return parsed;
  } catch {
    console.warn(
      "[mastra-agent] Failed to parse x-mcp-servers header, using defaults",
    );
    return getDefaultMcpServers();
  }
}

// ── MCP UI tool metadata ─────────────────────────────────────────────────────

interface McpUIToolInfo {
  toolName: string;
  resourceUri: string;
  serverConfig: McpServerConfig;
  serverHash: string;
}

function getServerHash(cfg: McpServerConfig): string {
  const raw = JSON.stringify({ type: cfg.type, url: cfg.url });
  return crypto.createHash("md5").update(raw).digest("hex");
}

async function fetchUIToolMetadata(
  servers: McpServerConfig[],
): Promise<Map<string, McpUIToolInfo>> {
  const uiTools = new Map<string, McpUIToolInfo>();

  for (const server of servers) {
    try {
      const transport =
        server.type === "sse"
          ? new SSEClientTransport(new URL(server.url))
          : new StreamableHTTPClientTransport(new URL(server.url));

      const client = new Client(
        { name: "mastra-ui-metadata", version: "1.0.0" },
        { capabilities: {} },
      );

      await client.connect(transport);
      const { tools } = await client.listTools();
      await client.close();

      const serverId = server.serverId || new URL(server.url).hostname;

      for (const tool of tools) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const meta = tool._meta as Record<string, any> | undefined;
        const resourceUri = meta?.["ui/resourceUri"];
        if (typeof resourceUri === "string") {
          // Mastra MCPClient prefixes tool names with serverId
          const mastraToolName = `${serverId}_${tool.name}`;
          uiTools.set(mastraToolName, {
            toolName: mastraToolName,
            resourceUri,
            serverConfig: server,
            serverHash: getServerHash(server),
          });
        }
      }
    } catch (err) {
      console.warn(
        `[mastra-agent] Failed to fetch UI metadata from ${server.url}:`,
        err,
      );
    }
  }

  mastraLog("[mastra-agent] UI tools found:", [...uiTools.keys()]);
  return uiTools;
}

// ── Proxied MCP request handler ──────────────────────────────────────────────
// When CopilotKit v2's MCPAppsActivityRenderer needs to fetch HTML for a widget,
// it sends a proxied request through the agent. This handler executes it.

async function executeProxiedMcpRequest(
  serverConfig: McpServerConfig,
  method: string,
  params?: Record<string, unknown>,
): Promise<unknown> {
  const transport =
    serverConfig.type === "sse"
      ? new SSEClientTransport(new URL(serverConfig.url))
      : new StreamableHTTPClientTransport(new URL(serverConfig.url));

  const client = new Client(
    { name: "mastra-mcp-proxy", version: "1.0.0" },
    {
      capabilities: {
        extensions: {
          "io.modelcontextprotocol/ui": { mimeTypes: ["text/html+mcp"] },
        },
      },
    },
  );

  try {
    await client.connect(transport);
    switch (method) {
      case "tools/call":
        return await client.callTool(
          params as { name: string; arguments?: Record<string, unknown> },
        );
      case "resources/read": {
        const result = await client.readResource(params as { uri: string });
        // Fix widget HTML for CSP-safe rendering in sandboxed iframes:
        // 1. Extract internal origin from <base> tag (e.g. http://localhost:3109)
        // 2. Strip <base> tag — blocked by CSP base-uri 'self' and unnecessary
        //    when JS/CSS are inlined (--inline build) and images use __mcpPublicUrl
        // 3. Rewrite remaining internal origin refs to the external endpoint origin
        const serverOrigin = new URL(serverConfig.url).origin;
        if (Array.isArray(result.contents)) {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          result.contents = result.contents.map((c: any) => {
            if (typeof c.text === "string") {
              let html = c.text;
              const baseTagMatch = html.match(/<base\s+href="([^"]*)"[^>]*>/i);
              if (baseTagMatch) {
                try {
                  const internalOrigin = new URL(baseTagMatch[1]).origin;
                  html = html.replace(/<base\b[^>]*>/gi, "");
                  if (internalOrigin !== serverOrigin) {
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
        }
        return result;
      }
      case "notifications/message":
        await client.notification({
          method: "notifications/message",
          params: params as Record<string, unknown>,
        });
        return { success: true };
      case "ping":
        return await client.ping();
      default:
        throw new Error(`MCP method not allowed for UI proxy: ${method}`);
    }
  } finally {
    await client.close();
  }
}

// ── AG-UI function middleware: ACTIVITY_SNAPSHOT + proxied requests ───────────
// Operates at the AG-UI Observable layer (not SSE), so events properly flow
// through the CopilotKit v2 pipeline and trigger MCPAppsActivityRenderer.

function createMcpUIMiddleware(
  mcpServers: McpServerConfig[],
  uiTools: Map<string, McpUIToolInfo>,
) {
  // Build server lookup maps for proxied requests
  const serverById = new Map<string, McpServerConfig>();
  const serverByHash = new Map<string, McpServerConfig>();
  for (const s of mcpServers) {
    const hash = getServerHash(s);
    serverByHash.set(hash, s);
    if (s.serverId) serverById.set(s.serverId, s);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return (input: any, next: { run: (input: any) => Observable<any> }) => {
    // ── Handle proxied MCP requests (MCPAppsActivityRenderer fetching HTML) ──
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const proxiedReq = input.forwardedProps?.__proxiedMCPRequest as any;
    if (proxiedReq) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return new Observable<any>((subscriber) => {
        // Find the server config
        let server: McpServerConfig | undefined;
        if (proxiedReq.serverId) server = serverById.get(proxiedReq.serverId);
        if (!server && proxiedReq.serverHash)
          server = serverByHash.get(proxiedReq.serverHash);

        const runId = input.runId;

        subscriber.next({
          type: "RUN_STARTED",
          runId,
          threadId: input.threadId,
        });

        if (!server) {
          subscriber.next({
            type: "RUN_FINISHED",
            runId,
            threadId: input.threadId,
            result: {
              error: `Unknown MCP server: ${proxiedReq.serverId || proxiedReq.serverHash}`,
            },
          });
          subscriber.complete();
          return;
        }

        executeProxiedMcpRequest(server, proxiedReq.method, proxiedReq.params)
          .then((result) => {
            subscriber.next({
              type: "RUN_FINISHED",
              runId,
              threadId: input.threadId,
              result,
            });
            subscriber.complete();
          })
          .catch((err) => {
            subscriber.next({
              type: "RUN_FINISHED",
              runId,
              threadId: input.threadId,
              result: { error: String(err) },
            });
            subscriber.complete();
          });
      });
    }

    // ── Normal requests: run the agent, intercept tool results, emit ACTIVITY_SNAPSHOT ──
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return new Observable<any>((subscriber) => {
      const toolNameByCallId = new Map<string, string>();
      const toolArgsByCallId = new Map<string, string>();
      // FIX duplicate React keys (RCA):
      // Mastra reuses the same messageId for TOOL_CALL_START.parentMessageId and
      // all TEXT_MESSAGE_* events. CopilotKit creates messages from both: from
      // TEXT_MESSAGE_* (id = messageId) and from TOOL_CALL_START (id = parentMessageId).
      // If TEXT_MESSAGE_START with messageId X is emitted first, the runtime creates
      // message X. TOOL_CALL_START with parentMessageId X can then create a second
      // message with id X (reuse logic may not match), so the same id appears twice.
      // The UI keys messages (and "custom" blocks as id-custom-after) → duplicate key errors.
      //
      // Strategy:
      // 1) Track every id we've already emitted (as messageId or parentMessageId).
      // 2) Remap TEXT_MESSAGE_* messageId when it collides with a parentMessageId we've seen.
      // 3) Remap TOOL_CALL_START parentMessageId when that id was already emitted (so we
      //    never create a second message with the same id).
      const usedAsParentId = new Set<string>();
      const currentTextRemap = new Map<string, string>(); // original ID → current remap for this text msg
      const emittedMessageIds = new Set<string>(); // ids already sent (as messageId or parentMessageId)
      const parentRemap = new Map<string, string>(); // original parentMessageId → remapped (for TOOL_CALL_START)

      next.run(input).subscribe({
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        next: (event: any) => {
          // Track parentMessageIds from tool calls (for TEXT_MESSAGE remap)
          if (event.type === "TOOL_CALL_START" && event.parentMessageId) {
            usedAsParentId.add(event.parentMessageId);
          }

          // Remap messageId on text events that collide with a parentMessageId.
          if (event.messageId && usedAsParentId.has(event.messageId)) {
            if (event.type === "TEXT_MESSAGE_START") {
              currentTextRemap.set(event.messageId, crypto.randomUUID());
            }
            const remapped = currentTextRemap.get(event.messageId);
            if (remapped) {
              event = { ...event, messageId: remapped };
            }
          }

          // Remap TOOL_CALL_START parentMessageId when that id was already emitted
          // (avoids second message with same id → duplicate React keys).
          if (event.type === "TOOL_CALL_START" && event.parentMessageId) {
            const parentId = event.parentMessageId;
            if (emittedMessageIds.has(parentId)) {
              if (!parentRemap.has(parentId)) {
                parentRemap.set(parentId, crypto.randomUUID());
              }
              event = { ...event, parentMessageId: parentRemap.get(parentId) };
            }
          }

          // Pass through the (possibly remapped) event
          subscriber.next(event);

          // Record ids we've emitted so we can avoid reusing them
          if (event.messageId) emittedMessageIds.add(event.messageId);
          if (event.parentMessageId)
            emittedMessageIds.add(event.parentMessageId);

          // Track tool call names
          if (
            event.type === "TOOL_CALL_START" &&
            event.toolCallId &&
            event.toolCallName
          ) {
            toolNameByCallId.set(event.toolCallId, event.toolCallName);
          }

          // Accumulate tool call args
          if (
            event.type === "TOOL_CALL_ARGS" &&
            event.toolCallId &&
            event.delta
          ) {
            const prev = toolArgsByCallId.get(event.toolCallId) || "";
            toolArgsByCallId.set(event.toolCallId, prev + event.delta);
          }

          // When a tool result arrives for an MCP UI tool, emit ACTIVITY_SNAPSHOT
          if (event.type === "TOOL_CALL_RESULT" && event.toolCallId) {
            const toolName = toolNameByCallId.get(event.toolCallId);
            if (toolName && uiTools.has(toolName)) {
              const info = uiTools.get(toolName)!;

              let toolInput: Record<string, unknown> = {};
              try {
                toolInput = JSON.parse(
                  toolArgsByCallId.get(event.toolCallId) || "{}",
                );
              } catch {
                /* ignore parse errors */
              }

              // Wrap result to match MCPAppsActivityContentSchema:
              // { content?: [{type:"text", text:"..."}], structuredContent?: any, isError?: boolean }
              let rawResult: unknown;
              try {
                rawResult = JSON.parse(event.content || "{}");
              } catch {
                rawResult = event.content || "";
              }
              const resultText =
                typeof rawResult === "string"
                  ? rawResult
                  : JSON.stringify(rawResult);
              const result = {
                content: [{ type: "text" as const, text: resultText }],
                structuredContent: rawResult,
              };

              mastraLog(
                `[mastra-agent] Emitting ACTIVITY_SNAPSHOT for: ${toolName}`,
              );
              subscriber.next({
                type: "ACTIVITY_SNAPSHOT",
                messageId: crypto.randomUUID(),
                activityType: "mcp-apps",
                content: {
                  result,
                  resourceUri: info.resourceUri,
                  serverHash: info.serverHash,
                  serverId: info.serverConfig.serverId,
                  toolInput,
                },
                replace: true,
              });
            }
          }
        },
        error: (err: unknown) => subscriber.error(err),
        complete: () => subscriber.complete(),
      });
    });
  };
}

// ── E2B workspace provider (stateless — safe to reuse across requests) ──────

const workspaceProvider = new E2BWorkspaceProvider();

// ── Backend tools — run server-side inside the agent loop ────────────────────

const workspaceTools: Record<string, unknown> = {
  provision_workspace: {
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
    execute: async ({ name }: { name: string }) => {
      const info = await workspaceProvider.provision(name);

      // Auto-clean default template tool (product-search) so workspace starts fresh.
      // This avoids the agent having to know about template defaults and speeds up builds.
      try {
        const e2b = await import("e2b");
        const sandbox = await e2b.Sandbox.connect(info.workspaceId);
        const WS = "/home/user/workspace";
        let idx = await sandbox.files.read(`${WS}/index.ts`);
        const hadDefault = idx.includes("registerProductSearch");
        if (hadDefault) {
          idx = idx.replace(
            'import { register as registerProductSearch } from "./tools/product-search";\n',
            "",
          );
          idx = idx.replace("registerProductSearch(server);\n", "");
          await sandbox.files.write(`${WS}/index.ts`, idx);
          await sandbox.commands.run(
            "rm -rf resources/product-search-result tools/product-search.ts",
            { cwd: WS, timeoutMs: 5000 },
          );
          // Restart so the running server drops the old tools before mcp-introspect queries it
          await sandbox.commands.run(
            "kill $(ss -tlnp 'sport = :3109' | grep -oP 'pid=\\K[0-9]+' | head -1) 2>/dev/null; sleep 1",
            { cwd: WS, timeoutMs: 10000 },
          );
          await sandbox.commands.run("npm run dev > /tmp/dev.log 2>&1", {
            cwd: WS,
            timeoutMs: 5000,
            background: true,
          });
          mastraLog(
            "[provision_workspace] Cleaned up default template tool + restarted server",
          );
        }
      } catch (cleanupErr) {
        console.warn(
          "[provision_workspace] Template cleanup warning:",
          cleanupErr,
        );
      }

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
  },

  read_file: {
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
    execute: async ({
      workspaceId,
      path,
    }: {
      workspaceId: string;
      path: string;
    }) => {
      return await workspaceProvider.readFile(workspaceId, path);
    },
  },

  write_file: {
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
    execute: async ({
      workspaceId,
      path,
      content,
    }: {
      workspaceId: string;
      path: string;
      content: string;
    }) => {
      await workspaceProvider.writeFile(workspaceId, path, content);
      return `Wrote ${content.length} chars to "${path}"`;
    },
  },

  edit_file: {
    description:
      "Targeted search-and-replace in a workspace file. Supports multiple edits in one call. " +
      "Each search string must match exactly (including whitespace/newlines). " +
      "Edits are applied sequentially. Prefer this over write_file for small changes.",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
      path: z.string().describe("Relative file path"),
      edits: z
        .array(
          z.object({
            search: z.string().describe("Exact string to find in the file"),
            replace: z.string().describe("String to replace it with"),
          }),
        )
        .describe("Array of search/replace pairs to apply sequentially"),
    }),
    execute: async ({
      workspaceId,
      path,
      edits,
    }: {
      workspaceId: string;
      path: string;
      edits: Array<{ search: string; replace: string }>;
    }) => {
      const sandbox = await (await import("e2b")).Sandbox.connect(workspaceId);
      const fullPath = `/home/user/workspace/${path.replace(/^\//, "")}`;
      let content = await sandbox.files.read(fullPath);
      const results: string[] = [];
      for (const edit of edits) {
        if (!content.includes(edit.search)) {
          results.push(`SKIP: search string not found for one edit`);
          continue;
        }
        content = content.replace(edit.search, edit.replace);
        results.push(`OK`);
      }
      await sandbox.files.write(fullPath, content);
      return `Edited "${path}" — ${edits.length} edit(s): ${results.join(", ")}`;
    },
  },

  exec: {
    description:
      "Run a shell command in the workspace root of the active E2B sandbox. " +
      "Use background=true for long-running processes. " +
      "Note: fuser and lsof are NOT available — use ss for port lookups.",
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
    execute: async ({
      workspaceId,
      cmd,
      background,
      timeoutMs,
    }: {
      workspaceId: string;
      cmd: string;
      background?: boolean;
      timeoutMs?: number;
    }) => {
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
  },

  restart_server: {
    description:
      "Kill the running MCP server on port 3109, rebuild all widgets, restart, " +
      "and poll until healthy. Returns tools/list on success or build logs on failure. " +
      "Call this after writing/editing any tool or widget file.",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
    }),
    execute: async ({ workspaceId }: { workspaceId: string }) => {
      const e2b = await import("e2b");
      const sandbox = await e2b.Sandbox.connect(workspaceId);
      const WS = "/home/user/workspace";

      // 1. Kill old server via ss (fuser/lsof not available in E2B)
      await sandbox.commands.run(
        "kill $(ss -tlnp 'sport = :3109' | grep -oP 'pid=\\K[0-9]+' | head -1) 2>/dev/null; sleep 2",
        { cwd: WS, timeoutMs: 10000 },
      );

      // 2. Start npm run dev in background (builds widgets then starts server)
      await sandbox.commands.run("npm run dev > /tmp/dev.log 2>&1", {
        cwd: WS,
        timeoutMs: 5000,
        background: true,
      });

      // 3. Poll until server responds (up to 30s)
      for (let attempt = 0; attempt < 6; attempt++) {
        await new Promise((r) => setTimeout(r, 5000));

        const result = await sandbox.commands.run(
          "curl -sf http://localhost:3109/mcp -X POST " +
            "-H 'Content-Type: application/json' " +
            '-d \'{"jsonrpc":"2.0","method":"tools/list","id":1,"params":{}}\' 2>/dev/null | head -c 500',
          { cwd: WS, timeoutMs: 10000 },
        );

        if (result.stdout && result.stdout.includes("tools")) {
          return `Server restarted successfully.\n${result.stdout}`;
        }
      }

      // 4. Failed — return build logs for debugging
      const logs = await sandbox.commands.run("cat /tmp/dev.log | tail -40", {
        cwd: WS,
        timeoutMs: 5000,
      });
      return `Server failed to start after 30s. Build logs:\n${logs.stdout}\n${logs.stderr}`;
    },
  },

  get_workspace_info: {
    description: "Get current status and endpoint of the active E2B sandbox.",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
    }),
    execute: async ({ workspaceId }: { workspaceId: string }) => {
      const info = await workspaceProvider.getInfo(workspaceId);
      return JSON.stringify(info);
    },
  },

  download_workspace: {
    description:
      "Package the current workspace as a .tar.gz archive (excludes node_modules/dist) and return a signed download URL. " +
      "Present the URL to the user so they can download their MCP server.",
    parameters: z.object({
      workspaceId: z.string().describe("Sandbox ID"),
    }),
    execute: async ({ workspaceId }: { workspaceId: string }) => {
      const { downloadUrl } =
        await workspaceProvider.prepareDownload(workspaceId);
      return `Workspace packaged. Download URL (valid ~1 hour): ${downloadUrl}`;
    },
  },
};

// ── System prompt ─────────────────────────────────────────────────────────────

const AGENT_SYSTEM_PROMPT = `You are the MCP UI Studio coding agent. You BUILD MCP UI tools in E2B sandboxes and USE existing MCP tools.

RULES:
1. NEVER stop after a tool call — always continue to the next step or send a message.
2. Do NOT call read_file to "study" the template. All patterns are below.
3. Keep messages to 1 sentence max. Batch tool calls when possible.

REQUEST SHAPE (reliability):
- Prefer ONE tool + ONE widget: single screen, local state, vanilla React + template CSS in /home/user/workspace.
- Do NOT add npm dependencies or heavy client libraries unless the user clearly requires them and you can justify a minimal add—default is no new packages.
- Avoid flowcharts, node graphs, infinite canvases, or diagram editors (React Flow, Mermaid, D3, graphviz, etc.) unless the user insists; those blow scope in the sandbox. Offer a simpler bounded widget instead (game board, calculator, list + form).
- If the ask is vague, ask one short clarifying question instead of guessing a large architecture.

═══════════════════════════════════════════════════════════════
PATTERNS (use directly — do NOT read_file)
═══════════════════════════════════════════════════════════════

Workspace: /home/user/workspace — Server port: 3109

── Tool file: tools/<name>.ts ──
\`\`\`ts
import { MCPServer, text, widget } from "mcp-use/server";
import { z } from "zod";
export function register(server: MCPServer) {
  server.tool(
    { name: "tool-name", description: "What it does",
      schema: z.object({ param: z.string().describe("desc") }),
      widget: { name: "widget-folder-name", invoking: "Loading…", invoked: "Done" },
      _meta: {
        "ui/previewData": { param: "sample-value" },  // REQUIRED: sample data for MCP UI Studio sidebar preview
      } },
    async ({ param }) => widget({ props: { /* for React */ }, output: text("LLM summary") })
  );
}
\`\`\`
Always add _meta["ui/previewData"] to widget tools — object shape must match the props your widget receives. Without it the Studio has no demo preview.

── Widget: resources/<widget-folder-name>/widget.tsx ──
\`\`\`tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import React from "react";
import "../styles.css";
export const widgetMetadata: WidgetMetadata = { description: "What it shows", metadata: { prefersBorder: false } };
const W: React.FC = () => {
  const { props, isPending } = useWidget<{ param: string }>();
  if (isPending) return <McpUseProvider><div className="p-6 animate-pulse">Loading…</div></McpUseProvider>;
  return (<McpUseProvider><div className="rounded-2xl border border-default bg-surface-elevated p-6">{/* UI */}</div></McpUseProvider>);
};
export default W;
\`\`\`

── Register in index.ts (one edit_file call with multi-edit) ──
edit_file(path: "index.ts", edits: [
  { search: "// ADD NEW TOOL IMPORTS HERE", replace: 'import { register as registerX } from "./tools/x";\\n// ADD NEW TOOL IMPORTS HERE' },
  { search: "// ADD NEW TOOL REGISTRATIONS HERE", replace: 'registerX(server);\\n// ADD NEW TOOL REGISTRATIONS HERE' }
])

═══════════════════════════════════════════════════════════════
WORKFLOW A — BUILD NEW TOOL (no sandbox yet)
═══════════════════════════════════════════════════════════════
1. provision_workspace("<name>") → workspaceId + endpoint
2. add_mcp_server(endpoint, "<name>")
3. set_active_workspace(workspaceId, endpoint)
4. write_file: resources/<widget>/widget.tsx
5. write_file: tools/<name>.ts
6. edit_file(path: "index.ts", edits: [import edit, registration edit])
7. restart_server(workspaceId) — kills old server, rebuilds, polls until healthy. If error, fix code and retry.
8. refresh_mcp_tools()
9. show_mcp_test_prompts(prompts_json) — frontend action: pass a JSON array STRING like [{"label":"List tools","message":"List all tools available on the MCP server"},{"label":"…","message":"…"}] so the user gets clickable chips to test the server in the same chat thread.
10. Tell user it's live.

═══════════════════════════════════════════════════════════════
WORKFLOW B — EDIT / ADD TOOL (sandbox running)
═══════════════════════════════════════════════════════════════
Skip 1-3. Edit existing files or add new tool (steps 4-8).
After any change: restart_server → refresh_mcp_tools → show_mcp_test_prompts (optional, when new/changed tools should be tried).

═══════════════════════════════════════════════════════════════
WORKFLOW C — USE EXISTING MCP TOOL
═══════════════════════════════════════════════════════════════
Just call the tool. No sandbox work needed.`;

const openai = createOpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

/** OpenAI chat model for the Mastra agent (`@ai-sdk/openai` id), e.g. gpt-5.2, gpt-4.1, gpt-4o. */
const OPENAI_MODEL = process.env.OPENAI_MODEL?.trim() || "gpt-5.2";

// ── Request handler ──────────────────────────────────────────────────────────
// Architecture:
// - Mastra Agent executes MCP tools directly (via MCPClient — the LLM can see them)
// - A function middleware on the AG-UI Observable layer:
//   (a) Handles proxied MCP requests (MCPAppsActivityRenderer fetching widget HTML)
//   (b) Intercepts TOOL_CALL_RESULT for MCP UI tools → emits ACTIVITY_SNAPSHOT
// - CopilotKit v2's built-in MCPAppsActivityRenderer renders widget iframes

export const POST = async (req: NextRequest) => {
  const requestId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  let mcp: MCPClient | null = null;

  try {
    const mcpServers = readMcpServersFromHeader(req);
    mastraLog(
      "[mastra-agent] === NEW REQUEST ===",
      requestId,
      "model:",
      OPENAI_MODEL,
    );

    // 1. Fetch UI tool metadata (which tools have UI + their resource URIs)
    const uiTools = await fetchUIToolMetadata(mcpServers);

    // 2. Create Mastra MCP client for tool execution
    const mcpServerConfig: Record<string, { url: URL }> = {};
    for (const server of mcpServers) {
      const serverId = server.serverId || new URL(server.url).hostname;
      mcpServerConfig[serverId] = { url: new URL(server.url) };
    }

    mcp = new MCPClient({
      id: `mastra-agent-${requestId}`,
      servers: mcpServerConfig,
    });

    let mcpTools = {};
    try {
      mcpTools = await mcp.listTools();
      mastraLog("[mastra-agent] MCP tools loaded:", Object.keys(mcpTools));
    } catch (error) {
      console.error("[mastra-agent] Failed to load MCP tools:", error);
    }

    // 3. Create Mastra agent with MCP tools + workspace tools
    const mastraAgent = new Agent({
      id: "default",
      name: "MCP UI Builder",
      instructions: {
        role: "system",
        content: AGENT_SYSTEM_PROMPT,
        providerOptions: {
          openai: {
            reasoningEffort: "minimal", // Options: "minimal", "low", "medium", "high"
          },
        },
      },
      model: openai(OPENAI_MODEL),
      tools: {
        ...mcpTools,
        ...workspaceTools,
      } as Record<string, never>,
      defaultOptions: {
        maxSteps: 25, // Allow up to 25 tool call steps (default is 10)
      },
    });

    // 4. Wrap in AG-UI adapter
    const agentWrapper = new MastraAgent({
      agent: mastraAgent,
      resourceId: "anonymous",
    });

    // 5. Attach AG-UI middleware for ACTIVITY_SNAPSHOT + proxied requests
    //    This operates at the Observable layer (not SSE), so events flow
    //    through CopilotKit v2's pipeline and trigger MCPAppsActivityRenderer.
    // @ts-expect-error - rxjs version mismatch (7.8.1 vs 7.8.2) between @ag-ui packages
    agentWrapper.use(createMcpUIMiddleware(mcpServers, uiTools));

    // FIX: CopilotKit runtime calls `registeredAgent.clone()` before runAgent().
    // MastraAgent.clone() does `new MastraAgent(this.config)` which drops middlewares
    // added via .use(). Override clone() to re-attach our middleware on the clone.
    const mcpMiddleware = createMcpUIMiddleware(mcpServers, uiTools);
    const origClone = agentWrapper.clone.bind(agentWrapper);
    agentWrapper.clone = function () {
      const cloned = origClone();
      // @ts-expect-error - rxjs version mismatch
      cloned.use(mcpMiddleware);
      return cloned;
    };

    mastraLog(
      "[mastra-agent] Agent ready. UI tools:",
      uiTools.size,
      "MCP tools:",
      Object.keys(mcpTools).length,
    );

    // 6. CopilotKit runtime
    const serviceAdapter = new ExperimentalEmptyAdapter();

    const runtime = new CopilotRuntime({
      agents: {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        default: agentWrapper as any,
      },
    });

    const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
      runtime,
      serviceAdapter,
      endpoint: "/api/mastra-agent",
    });

    return handleRequest(req);
  } catch (error) {
    console.error("[mastra-agent] Error:", error);
    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Internal server error",
      }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      },
    );
  } finally {
    if (mcp) {
      try {
        await mcp.disconnect();
      } catch {
        /* ignore */
      }
    }
  }
};
