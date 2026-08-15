export interface McpServerEntry {
  endpoint: string;
  serverId?: string;
}

/** Initial sidebar list. No defaults (localhost not available in production). Set NEXT_PUBLIC_DEFAULT_MCP_SERVERS to pre-fill hosted MCP(s). */
function getDefaultServersFromEnv(): McpServerEntry[] | null {
  const raw = process.env.NEXT_PUBLIC_DEFAULT_MCP_SERVERS;
  if (typeof raw !== "string" || !raw) return null;
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return null;
    return parsed.filter(
      (s): s is McpServerEntry =>
        s != null &&
        typeof s === "object" &&
        typeof (s as McpServerEntry).endpoint === "string",
    );
  } catch {
    return null;
  }
}

const envDefaults = getDefaultServersFromEnv();

/** Built-in default: Excalidraw MCP server (public, no auth). Override with NEXT_PUBLIC_DEFAULT_MCP_SERVERS. */
const BUILTIN_DEFAULTS: McpServerEntry[] = [
  { endpoint: "https://mcp.excalidraw.com", serverId: "excalidraw" },
];

export const DEFAULT_SERVERS: McpServerEntry[] =
  envDefaults ?? BUILTIN_DEFAULTS;
