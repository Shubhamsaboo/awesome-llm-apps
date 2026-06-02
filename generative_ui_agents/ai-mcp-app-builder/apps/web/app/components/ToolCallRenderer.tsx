"use client";

import { useState, useEffect, type ReactNode } from "react";
import { defineToolCallRenderer } from "@copilotkit/react-core/v2";
import { z } from "zod";
import { triggerBlobDownload } from "@/lib/open-download";

// ── Download link for restart_server ─────────────────────────────────────────

function DownloadServerCodeLink({ workspaceId }: { workspaceId: string }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/workspace/download", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ workspaceId, stream: true, fullKit: true }),
      });
      if (!res.ok) {
        const data = (await res.json().catch(() => ({}))) as { error?: string };
        throw new Error(data.error || `Download failed (${res.status})`);
      }
      const blob = await res.blob();
      const safeId =
        workspaceId.replace(/[^\w-]/g, "").slice(0, 16) || "workspace";
      const cd = res.headers.get("Content-Disposition");
      const m = cd?.match(/filename="([^"]+)"/);
      const filename = m?.[1] ?? `workspace-${safeId}.tar.gz`;
      triggerBlobDownload(blob, filename);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Download failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="px-3.5 py-3 border-t border-slate-200/70">
      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        Local starter kit
      </p>
      <button
        type="button"
        onClick={handleDownload}
        disabled={loading}
        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[11px] font-medium text-slate-700 hover:bg-slate-50 hover:border-slate-300 disabled:opacity-50"
      >
        {loading ? (
          <>
            <span className="h-3 w-3 rounded-full border-2 border-slate-400 border-t-transparent animate-spin" />
            Preparing…
          </>
        ) : (
          <>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-3.5 w-3.5"
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
            Download full app kit
          </>
        )}
      </button>
      {error && <p className="mt-1.5 text-[10px] text-red-600">{error}</p>}
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function safeFormat(val: unknown, maxLen = 800): string {
  if (val === null || val === undefined) return "";
  let s: string;
  try {
    s = typeof val === "string" ? val : JSON.stringify(val, null, 2);
  } catch {
    s = String(val);
  }
  return s.length > maxLen ? s.slice(0, maxLen) + "\n…(truncated)" : s;
}

// ── Card component ────────────────────────────────────────────────────────────

function ToolCallCard({
  name,
  args,
  status,
  result,
  footer,
}: {
  name: string;
  args: unknown;
  status: string;
  result: string | undefined;
  footer?: ReactNode;
}) {
  const done = status === "complete";

  // Start expanded while running; auto-collapse when done.
  // User can click the header to toggle at any time.
  const [expanded, setExpanded] = useState(true);
  useEffect(() => {
    if (done) setExpanded(false);
  }, [done]);

  // Build a human-readable args string
  const argsEntries =
    args && typeof args === "object" && !Array.isArray(args)
      ? Object.entries(args as Record<string, unknown>)
      : null;
  const hasArgs = argsEntries ? argsEntries.length > 0 : args != null;
  const argsDisplay = argsEntries
    ? argsEntries.map(([k, v]) => `${k}: ${safeFormat(v, 300)}`).join("\n")
    : safeFormat(args, 600);

  const resultDisplay = result !== undefined ? safeFormat(result, 800) : null;

  return (
    <div className="mx-1 mt-1.5 mb-4 rounded-xl border border-slate-200 bg-slate-50/80 text-[12px] overflow-hidden shadow-sm">
      {/* ── Header (always visible, clickable) ── */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-center gap-2 px-3.5 py-2 bg-slate-100/70 hover:bg-slate-100 transition-colors text-left"
      >
        {done ? (
          <span className="shrink-0 font-bold text-emerald-600 text-[13px] leading-none">
            ✓
          </span>
        ) : (
          <span className="h-3 w-3 shrink-0 rounded-full border-2 border-slate-400 border-t-transparent animate-spin" />
        )}
        <code className="font-semibold text-slate-700">{name}</code>
        <span className="ml-auto flex items-center gap-2 text-[10px] font-semibold uppercase tracking-wide">
          {done ? (
            <span className="text-emerald-600">Done</span>
          ) : (
            <span className="text-amber-500">Running…</span>
          )}
          <span className="text-slate-400 text-[10px]">
            {expanded ? "▲" : "▼"}
          </span>
        </span>
      </button>

      {/* ── Expandable body ── */}
      {expanded && (
        <div className="border-t border-slate-200/70">
          {/* Arguments */}
          {hasArgs && (
            <div className="px-3.5 py-3">
              <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Arguments
              </p>
              <pre className="rounded-lg bg-white border border-slate-100 px-3 py-2 font-mono text-[11px] leading-relaxed text-slate-800 whitespace-pre-wrap break-all overflow-x-auto max-h-40 overflow-y-auto">
                {argsDisplay}
              </pre>
            </div>
          )}

          {/* Result */}
          {resultDisplay !== null && (
            <div
              className={`px-3.5 py-3 ${hasArgs ? "border-t border-slate-200/70" : ""}`}
            >
              <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-emerald-600">
                Result
              </p>
              <pre className="rounded-lg bg-white border border-slate-100 px-3 py-2 font-mono text-[11px] leading-relaxed text-slate-800 whitespace-pre-wrap break-all overflow-x-auto max-h-48 overflow-y-auto">
                {resultDisplay}
              </pre>
            </div>
          )}
        </div>
      )}
      {footer}
    </div>
  );
}

// ── restart_server: same card + download MCP server code link ──────────────────

function RestartServerCard({
  name,
  args,
  status,
  result,
}: {
  name: string;
  args: unknown;
  status: string;
  result: string | undefined;
}) {
  const workspaceId =
    args &&
    typeof args === "object" &&
    !Array.isArray(args) &&
    "workspaceId" in args
      ? String((args as Record<string, unknown>).workspaceId)
      : null;

  return (
    <ToolCallCard
      name={name}
      args={args}
      status={status}
      result={result}
      footer={
        workspaceId ? (
          <DownloadServerCodeLink workspaceId={workspaceId} />
        ) : null
      }
    />
  );
}

// ── Wildcard renderer — catches all tool calls with no specific renderer ──────
// Module-level constant so it's stable across renders (no new array each time).

export const TOOL_CALL_RENDERERS = [
  defineToolCallRenderer({
    name: "restart_server",
    args: z.object({ workspaceId: z.string() }),
    render: ({ name, args, status, result }) => (
      <RestartServerCard
        name={name}
        args={args}
        status={status}
        result={result}
      />
    ),
  }),
  defineToolCallRenderer({
    name: "*",
    render: ({ name, args, status, result }) => (
      <ToolCallCard name={name} args={args} status={status} result={result} />
    ),
  }),
];
