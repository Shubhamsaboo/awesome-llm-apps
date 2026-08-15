"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";

/** Mirrors the shape returned by /api/mcp-introspect */
export interface IntrospectedTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  hasUI: boolean;
  uiResourceUri: string | null;
  uiHtml: string | null;
  uiPreviewData: Record<string, unknown> | null;
  _meta: Record<string, unknown> | null;
}

export interface McpResource {
  uri: string;
  name: string;
  mimeType?: string;
}

export interface ServerIntrospection {
  endpoint: string;
  serverId?: string;
  tools: IntrospectedTool[];
  resources: McpResource[];
  error: string | null;
  loading: boolean;
}

/**
 * Fetches tool & resource data from all connected MCP servers via the
 * `/api/mcp-introspect` proxy route.
 *
 * Re-fetches automatically whenever `servers` changes.
 */
export function useMcpIntrospect(
  servers: { endpoint: string; serverId?: string }[],
) {
  const [data, setData] = useState<ServerIntrospection[]>([]);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    // Abort any in-flight requests
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    if (servers.length === 0) {
      console.log("[useMcpIntrospect] No servers configured, skipping");
      setData([]);
      setLoading(false);
      return;
    }

    console.log(
      "[useMcpIntrospect] Fetching from",
      servers.length,
      "server(s):",
      servers.map((s) => s.endpoint),
    );
    setLoading(true);

    const results = await Promise.all(
      servers.map(async (server) => {
        const entry: ServerIntrospection = {
          endpoint: server.endpoint,
          serverId: server.serverId,
          tools: [],
          resources: [],
          error: null,
          loading: true,
        };

        try {
          console.log(`[useMcpIntrospect] Fetching ${server.endpoint}...`);
          const res = await fetch("/api/mcp-introspect", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ endpoint: server.endpoint }),
            signal: controller.signal,
          });

          console.log(
            `[useMcpIntrospect] Response from ${server.endpoint}: ${res.status}`,
          );

          if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            entry.error =
              (body as Record<string, string>).error ?? `HTTP ${res.status}`;
            console.error(
              `[useMcpIntrospect] Error for ${server.endpoint}:`,
              entry.error,
            );
          } else {
            const body = await res.json();
            entry.tools = body.tools ?? [];
            entry.resources = body.resources ?? [];
            console.log(
              `[useMcpIntrospect] Got ${entry.tools.length} tools, ${entry.resources.length} resources from ${server.endpoint}`,
            );
          }
        } catch (err) {
          if ((err as Error).name !== "AbortError") {
            entry.error = (err as Error).message ?? String(err);
            console.error(
              `[useMcpIntrospect] Fetch failed for ${server.endpoint}:`,
              entry.error,
            );
          }
        }

        entry.loading = false;
        return entry;
      }),
    );

    if (!controller.signal.aborted) {
      setData(results);
      setLoading(false);
    }
  }, [servers]);

  // Auto-fetch on server list change
  useEffect(() => {
    refresh();
    return () => abortRef.current?.abort();
  }, [refresh]);

  // Stable reference — flatMap always creates a new array, so memoize by
  // serializing tool names to avoid triggering downstream useEffects on every render.
  const allTools = useMemo(
    () => data.flatMap((s) => s.tools),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data],
  );

  return { data, allTools, loading, refresh };
}
