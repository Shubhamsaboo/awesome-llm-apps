/**
 * Server-side default MCP servers when no x-mcp-servers header is present.
 * Unset = no defaults. Set DEFAULT_MCP_SERVERS (JSON array) to pre-fill.
 */

export type McpServerConfig = {
  type: "http" | "sse";
  url: string;
  serverId?: string;
};

/** Built-in default: Excalidraw MCP server (public, no auth). Override with DEFAULT_MCP_SERVERS env. */
const BUILTIN_DEFAULTS: McpServerConfig[] = [
  { type: "http", url: "https://mcp.excalidraw.com", serverId: "excalidraw" },
];

function parseDefaultMcpServers(): McpServerConfig[] {
  const raw = process.env.DEFAULT_MCP_SERVERS;
  if (raw == null || raw === "") return BUILTIN_DEFAULTS;
  try {
    const parsed = JSON.parse(raw) as McpServerConfig[];
    if (!Array.isArray(parsed)) return BUILTIN_DEFAULTS;
    const filtered = parsed.filter(
      (s): s is McpServerConfig =>
        s != null &&
        typeof s.url === "string" &&
        (s.type === "http" || s.type === "sse"),
    );
    return filtered.length > 0 ? filtered : BUILTIN_DEFAULTS;
  } catch {
    return BUILTIN_DEFAULTS;
  }
}

let cached: McpServerConfig[] | null = null;

/** Default MCP server configs for API routes when header is absent. */
export function getDefaultMcpServers(): McpServerConfig[] {
  if (cached === null) cached = parseDefaultMcpServers();
  return cached;
}
