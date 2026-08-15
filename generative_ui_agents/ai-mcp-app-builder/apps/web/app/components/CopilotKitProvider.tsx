"use client";

import { CopilotKit } from "@copilotkit/react-core";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { DEFAULT_SERVERS, type McpServerEntry } from "../constants/mcpServers";
import { TOOL_CALL_RENDERERS } from "./ToolCallRenderer";

// ─── Shared context ───────────────────────────────────────────────────────────

type ServersUpdater =
  | McpServerEntry[]
  | ((prev: McpServerEntry[]) => McpServerEntry[]);

interface McpServersContextValue {
  servers: McpServerEntry[];
  setServers: (update: ServersUpdater) => void;
}

const McpServersContext = createContext<McpServersContextValue>({
  servers: DEFAULT_SERVERS,
  setServers: () => {},
});

/** Read and update the active MCP server list from anywhere inside the app. */
export function useMcpServers(): McpServersContextValue {
  return useContext(McpServersContext);
}

// ─── Provider ─────────────────────────────────────────────────────────────────

/**
 * Single source of truth for the MCP server list.
 *
 * - Initialized from DEFAULT_SERVERS (defined in constants/mcpServers.ts).
 * - State lives in React memory only — no localStorage.
 *   Add/remove servers through useMcpServers() from anywhere in the tree.
 * - Passes the list to CopilotKit as `x-mcp-servers` HTTP header so
 *   MCPAppsMiddleware always uses the up-to-date list.
 */
export function DynamicCopilotKitProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [servers, setServersState] =
    useState<McpServerEntry[]>(DEFAULT_SERVERS);

  const setServers = useCallback((update: ServersUpdater) => {
    setServersState((prev) => {
      const next = typeof update === "function" ? update(prev) : update;
      console.log(
        `[CopilotKitProvider] Server list updated — ${next.length} server(s):`,
        next.map((s) => s.endpoint),
      );
      return next;
    });
  }, []);

  const headers = useMemo(() => {
    const value = JSON.stringify(
      servers.map((s) => ({
        type: "http" as const,
        url: s.endpoint,
        ...(s.serverId ? { serverId: s.serverId } : {}),
      })),
    );
    console.log(
      `[CopilotKitProvider] x-mcp-servers header updated — ${servers.length} server(s):`,
      servers.map((s) => s.endpoint),
    );
    return { "x-mcp-servers": value };
  }, [servers]);

  return (
    <McpServersContext.Provider value={{ servers, setServers }}>
      <CopilotKit
        runtimeUrl="/api/mastra-agent"
        headers={headers}
        showDevConsole={false}
        renderToolCalls={TOOL_CALL_RENDERERS}
      >
        {children}
      </CopilotKit>
    </McpServersContext.Provider>
  );
}
