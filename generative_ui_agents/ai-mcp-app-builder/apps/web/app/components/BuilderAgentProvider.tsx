"use client";

import { useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import type { MergedToolConfig } from "../hooks/useToolConfigStore";
import type { WorkspaceInfo } from "@/lib/workspace/types";
import { RegisterMcpTestPromptsAction } from "./McpTestPromptsAction";

// ---------------------------------------------------------------------------
// BuilderAgentProvider
//
// Registers FRONTEND-ONLY CopilotKit actions — these update React / UI state.
// All heavy async work (E2B provision, file I/O, exec) lives as backend tools
// on BuiltInAgent in app/api/copilotkit/route.ts.
// ---------------------------------------------------------------------------

interface BuilderAgentProviderProps {
  activeTool: MergedToolConfig | null;
  allToolNames: string[];
  onAddServer: (endpoint: string, serverId?: string) => void;
  onRefreshServers: () => void;
  connectedServers: string[];
  activeWorkspace: WorkspaceInfo | null;
  onWorkspaceChange: (ws: WorkspaceInfo | null) => void;
  children: React.ReactNode;
}

export function BuilderAgentProvider({
  activeTool,
  allToolNames,
  onAddServer,
  onRefreshServers,
  connectedServers,
  activeWorkspace,
  onWorkspaceChange,
  children,
}: BuilderAgentProviderProps) {
  // ── Context readables ────────────────────────────────────────────────────
  // Injected into every agent request as live context for the LLM.

  useCopilotReadable({
    description:
      "Active E2B workspace. null = no sandbox provisioned yet — call the backend provision_workspace tool first.",
    value: activeWorkspace ?? {
      status: "not-provisioned",
      message:
        "Call provision_workspace(name) backend tool to create an E2B sandbox.",
    },
  });

  useCopilotReadable({
    description: "Currently selected tool in the builder",
    value: activeTool
      ? {
          toolName: activeTool.toolName,
          source: activeTool.source,
          description: activeTool.description,
          inputSchema: activeTool.inputSchema,
          previewData: activeTool.previewData,
          hasUI: activeTool.hasUI,
          htmlSourceLength: activeTool.htmlSource?.length ?? 0,
          htmlSourcePreview: activeTool.htmlSource?.slice(0, 500) ?? null,
          isModified: activeTool.isModified,
        }
      : { toolName: null, message: "No tool selected" },
  });

  useCopilotReadable({
    description: "All available tool names in the builder",
    value: allToolNames,
  });

  useCopilotReadable({
    description:
      "MCP servers currently connected to the studio. Each entry is an endpoint URL.",
    value: connectedServers,
  });

  // ── UI-state frontend actions ─────────────────────────────────────────────
  // These actions only update React state — no async I/O.
  // The agent calls them after backend tools complete.

  useCopilotAction({
    name: "add_mcp_server",
    description:
      "Connect a new MCP server to the studio sidebar. " +
      "Call this after provision_workspace returns the sandbox endpoint.",
    parameters: [
      {
        name: "endpoint",
        type: "string",
        description:
          "Full MCP endpoint URL, e.g. https://sandbox-abc.e2b.app/mcp",
        required: true,
      },
      {
        name: "serverId",
        type: "string",
        description: "Short identifier, e.g. 'weather-widget'",
        required: false,
      },
    ],
    handler: async ({ endpoint, serverId }) => {
      if (connectedServers.includes(endpoint as string)) {
        return `Server "${endpoint}" is already connected.`;
      }
      onAddServer(endpoint as string, serverId as string | undefined);
      // Persist serverId for session restoration
      try {
        const saved = JSON.parse(
          localStorage.getItem("mcp_active_workspace") ?? "{}",
        );
        localStorage.setItem(
          "mcp_active_workspace",
          JSON.stringify({ ...saved, serverId: serverId ?? "workspace" }),
        );
      } catch {}
      return `Connected MCP server at "${endpoint}"${serverId ? ` (${serverId})` : ""}.`;
    },
  });

  useCopilotAction({
    name: "set_active_workspace",
    description:
      "Register the provisioned workspace in the UI — shows the status badge on the server entry. " +
      "Call right after provision_workspace completes.",
    parameters: [
      {
        name: "workspaceId",
        type: "string",
        description: "Sandbox ID returned by provision_workspace",
        required: true,
      },
      {
        name: "endpoint",
        type: "string",
        description: "MCP endpoint URL of the sandbox",
        required: true,
      },
    ],
    handler: async ({ workspaceId, endpoint }) => {
      onWorkspaceChange({
        workspaceId: workspaceId as string,
        endpoint: endpoint as string,
        status: "running",
        path: "/home/user/workspace",
      });
      // Persist for session restoration — next page load reconnects instead of re-provisioning
      try {
        const saved = JSON.parse(
          localStorage.getItem("mcp_active_workspace") ?? "{}",
        );
        localStorage.setItem(
          "mcp_active_workspace",
          JSON.stringify({
            ...saved,
            workspaceId: workspaceId as string,
            endpoint: endpoint as string,
          }),
        );
      } catch {}
      return `Workspace registered in UI (sandboxId: ${workspaceId}).`;
    },
  });

  useCopilotAction({
    name: "refresh_mcp_tools",
    description:
      "Re-introspect all connected MCP servers so newly created tools appear in the sidebar. " +
      "Call after rebuilding the dev server and waiting ~3-5 seconds.",
    parameters: [],
    handler: async () => {
      onRefreshServers();
      return "Refreshing MCP tools from all connected servers. New tools will appear shortly.";
    },
  });

  return (
    <>
      <RegisterMcpTestPromptsAction />
      {children}
    </>
  );
}
