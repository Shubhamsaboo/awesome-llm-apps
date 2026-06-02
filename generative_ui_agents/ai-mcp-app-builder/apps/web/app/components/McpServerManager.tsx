"use client";

import { useState, useEffect, useCallback } from "react";
import { useCopilotChat } from "@copilotkit/react-core";
import { useMcpServers } from "./CopilotKitProvider";
import type { McpServerEntry } from "../constants/mcpServers";
import { triggerBlobDownload } from "@/lib/open-download";
import type { WorkspaceInfo } from "@/lib/workspace/types";
import type { ServerIntrospection } from "../hooks/useMcpIntrospect";

export type { McpServerEntry };
export { DEFAULT_SERVERS } from "../constants/mcpServers";

function AddServerForm({
  onAdd,
  onCancel,
}: {
  onAdd: (entry: McpServerEntry) => void;
  onCancel: () => void;
}) {
  const [endpoint, setEndpoint] = useState("");
  const [serverId, setServerId] = useState("");

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const url = endpoint.trim();
    if (!url) return;
    onAdd({ endpoint: url, serverId: serverId.trim() || undefined });
    setEndpoint("");
    setServerId("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3"
    >
      <input
        type="url"
        value={endpoint}
        onChange={(e) => setEndpoint(e.target.value)}
        placeholder="MCP endpoint URL (e.g. http://localhost:3108/mcp)"
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
        required
      />
      <input
        type="text"
        value={serverId}
        onChange={(e) => setServerId(e.target.value)}
        placeholder="Server ID (optional, e.g. threejs)"
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
      />
      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded-lg bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
        >
          Add server
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

export function McpServerManager({
  activeWorkspace,
  serverStatuses = [],
  onReconnect,
  globalLoading = false,
}: {
  activeWorkspace?: WorkspaceInfo | null;
  /** Per-server introspection state (error, loading) from useMcpIntrospect */
  serverStatuses?: ServerIntrospection[];
  /** Called when user clicks Reconnect for a failed server */
  onReconnect?: () => void;
  /** True when a full refresh is in progress */
  globalLoading?: boolean;
}) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  // Single source of truth: React context owned by DynamicCopilotKitProvider
  const { servers, setServers } = useMcpServers();
  const [showAddForm, setShowAddForm] = useState(false);
  const { setMcpServers } = useCopilotChat();

  // Keep CopilotKit's runtime in sync whenever the list changes
  const syncToRuntime = useCallback(
    (list: McpServerEntry[]) => {
      console.log(
        "[McpServerManager] syncToRuntime called with",
        list.length,
        "server(s):",
        list.map((s) => s.endpoint),
      );
      if (typeof setMcpServers === "function") {
        setMcpServers(
          list.map((s) => ({
            endpoint: s.endpoint,
            ...(s.serverId ? { serverId: s.serverId } : {}),
          })),
        );
        console.log(
          "[McpServerManager] setMcpServers called — agent server list updated",
        );
      } else {
        console.warn(
          "[McpServerManager] setMcpServers is not available (not inside CopilotKit context?)",
        );
      }
    },
    [setMcpServers],
  );

  useEffect(() => {
    syncToRuntime(servers);
  }, [servers, syncToRuntime]);

  const addServer = (entry: McpServerEntry) => {
    setServers([...servers, entry]);
    setShowAddForm(false);
  };

  const removeServer = (index: number) => {
    setServers(servers.filter((_, i) => i !== index));
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-800">MCP servers</h2>
        <button
          type="button"
          onClick={() => setShowAddForm((v: boolean) => !v)}
          className="rounded-lg border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-100"
        >
          {showAddForm ? "Cancel" : "+ Add"}
        </button>
      </div>

      {showAddForm && (
        <AddServerForm
          onAdd={addServer}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      {downloadError && (
        <p className="rounded-lg border border-red-200 bg-red-50 px-2 py-1.5 text-xs text-red-700">
          {downloadError}
        </p>
      )}

      <ul className="space-y-1.5">
        {servers.map((s, i) => {
          const isWorkspace = activeWorkspace?.endpoint === s.endpoint;
          const isProvisioning =
            isWorkspace && activeWorkspace?.status === "provisioning";
          const isRunning =
            isWorkspace && activeWorkspace?.status === "running";
          const status = serverStatuses.find(
            (st) => st.endpoint === s.endpoint,
          );
          const hasError = Boolean(status?.error);
          const isConnecting = Boolean(status?.loading);

          const handleDownload = async () => {
            if (!activeWorkspace) return;
            setDownloadError(null);
            setDownloading(true);
            const wid = activeWorkspace.workspaceId;
            try {
              const res = await fetch("/api/workspace/download", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  workspaceId: wid,
                  stream: true,
                  fullKit: true,
                }),
              });
              if (!res.ok) {
                const body = (await res.json().catch(() => ({}))) as {
                  error?: string;
                };
                setDownloadError(
                  body.error || `Download failed (${res.status})`,
                );
                return;
              }
              const blob = await res.blob();
              const safeId =
                wid.replace(/[^\w-]/g, "").slice(0, 16) || "workspace";
              const cd = res.headers.get("Content-Disposition");
              const m = cd?.match(/filename="([^"]+)"/);
              const filename = m?.[1] ?? `workspace-${safeId}.tar.gz`;
              triggerBlobDownload(blob, filename);
            } catch (e) {
              setDownloadError(
                e instanceof Error ? e.message : "Download failed",
              );
            } finally {
              setDownloading(false);
            }
          };

          return (
            <li
              key={`${s.endpoint}-${i}`}
              className={`flex flex-col gap-1.5 rounded-xl border py-2 pl-3 pr-2 ${
                hasError
                  ? "border-red-200 bg-red-50/50"
                  : isWorkspace
                    ? "border-emerald-200 bg-emerald-50/50"
                    : "border-slate-200 bg-white"
              }`}
            >
              <div className="flex min-w-0 flex-1 items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`truncate text-sm font-medium ${hasError ? "text-red-800" : "text-slate-800"}`}
                    >
                      {s.serverId || `Server ${i + 1}`}
                    </span>
                    {isProvisioning && (
                      <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-700">
                        <svg
                          className="h-2.5 w-2.5 animate-spin"
                          viewBox="0 0 24 24"
                          fill="none"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"
                          />
                        </svg>
                        Setting up…
                      </span>
                    )}
                    {isConnecting && !hasError && (
                      <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
                        <svg
                          className="h-2.5 w-2.5 animate-spin"
                          viewBox="0 0 24 24"
                          fill="none"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"
                          />
                        </svg>
                        Connecting…
                      </span>
                    )}
                    {isRunning && !hasError && (
                      <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                        Running
                      </span>
                    )}
                    {hasError && (
                      <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-medium text-red-700">
                        Error
                      </span>
                    )}
                  </div>
                  <div
                    className={`truncate text-xs ${hasError ? "text-red-600" : "text-slate-500"}`}
                  >
                    {s.endpoint}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-0.5">
                  {hasError && onReconnect && (
                    <button
                      type="button"
                      onClick={onReconnect}
                      disabled={globalLoading}
                      className="rounded-lg border border-red-200 bg-white px-2 py-1 text-[10px] font-medium text-red-700 hover:bg-red-50 disabled:opacity-50"
                      title="Reconnect to this server"
                    >
                      {globalLoading ? "…" : "Reconnect"}
                    </button>
                  )}
                  {isRunning && (
                    <button
                      type="button"
                      onClick={handleDownload}
                      disabled={downloading}
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-emerald-100 hover:text-emerald-700 disabled:opacity-50"
                      aria-label="Download workspace"
                      title="Download full app kit (.tar.gz) — monorepo + your MCP server, or MCP-only if base kit missing"
                    >
                      {downloading ? (
                        <svg
                          className="h-4 w-4 animate-spin"
                          viewBox="0 0 24 24"
                          fill="none"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"
                          />
                        </svg>
                      ) : (
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                          />
                        </svg>
                      )}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => removeServer(i)}
                    className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                    aria-label="Remove server"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-4 w-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              </div>
              {hasError && status?.error && (
                <p className="text-[11px] text-red-700" title={status.error}>
                  {status.error.length > 80
                    ? `${status.error.slice(0, 80)}…`
                    : status.error}
                </p>
              )}
            </li>
          );
        })}
      </ul>
      {servers.length === 0 && (
        <p className="text-xs text-slate-500">
          No servers. Add one to let the assistant use MCP tools.
        </p>
      )}
    </div>
  );
}
