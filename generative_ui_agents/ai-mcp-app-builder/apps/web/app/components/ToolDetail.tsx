"use client";

import { useState, useEffect, useCallback } from "react";
import { McpAppPreview } from "./McpAppPreview";
import type { MergedToolConfig } from "../hooks/useToolConfigStore";

type DetailTab = "preview" | "parameters" | "data" | "json" | "ui" | "schema";

/**
 * Tabbed tool inspector — used inside {@link ToolDetailModal}.
 * Preview tab first: live widget + summary; other tabs for power users.
 */
export function ToolDetailContent({
  tool,
  onTryPrompt,
  onPreviewDataChange,
}: {
  tool: MergedToolConfig;
  onTryPrompt: (prompt: string) => void;
  onPreviewDataChange: (data: Record<string, unknown>) => void;
}) {
  const [tab, setTab] = useState<DetailTab>("preview");
  const [previewJson, setPreviewJson] = useState(
    JSON.stringify(tool.previewData, null, 2),
  );
  const [previewJsonError, setPreviewJsonError] = useState<string | null>(null);

  useEffect(() => {
    setPreviewJson(JSON.stringify(tool.previewData, null, 2));
    setPreviewJsonError(null);
  }, [tool.toolName, tool.previewData]);

  useEffect(() => {
    if (!tool.htmlSource && tab === "ui") setTab("preview");
  }, [tool.htmlSource, tab]);

  const savePreviewData = useCallback(() => {
    try {
      const parsed = JSON.parse(previewJson);
      onPreviewDataChange(parsed);
      setPreviewJsonError(null);
    } catch (e) {
      setPreviewJsonError((e as Error).message);
    }
  }, [previewJson, onPreviewDataChange]);

  const params = Object.entries(
    ((tool.inputSchema as Record<string, unknown>)?.properties as Record<
      string,
      { type?: string; description?: string }
    >) ?? {},
  );
  const required =
    ((tool.inputSchema as Record<string, unknown>)?.required as string[]) ?? [];
  const paramKeys = params.map(([k]) => k);
  const tryPrompts =
    paramKeys.length > 0
      ? paramKeys
          .slice(0, 2)
          .map((k) => `Use ${tool.toolName} with ${k}: "example"`)
      : [`Use the ${tool.toolName} tool`];

  const toolJson = JSON.stringify(
    {
      name: tool.toolName,
      description: tool.description,
      inputSchema: tool.inputSchema,
      _meta: tool._meta,
    },
    null,
    2,
  );

  const tabs: { key: DetailTab; label: string }[] = [
    { key: "preview", label: "Preview" },
    { key: "parameters", label: "Parameters" },
    { key: "data", label: "Preview data" },
    { key: "json", label: "JSON" },
    ...(tool.htmlSource ? [{ key: "ui" as const, label: "Source" }] : []),
    { key: "schema", label: "Schema" },
  ];

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <nav
        className="-mx-1 flex gap-1 overflow-x-auto overscroll-x-contain px-1 pb-1 [scrollbar-width:thin]"
        aria-label="Tool detail sections"
      >
        {tabs.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={
              tab === t.key
                ? "shrink-0 rounded-lg bg-slate-900 px-2.5 py-1.5 text-[11px] font-semibold text-white sm:text-xs"
                : "shrink-0 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-[11px] font-medium text-slate-600 hover:border-slate-300 hover:text-slate-900 sm:text-xs"
            }
          >
            {t.label}
          </button>
        ))}
      </nav>

      <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden pr-0.5">
        {tab === "preview" && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-1.5">
              <h3 className="truncate text-sm font-semibold text-slate-900">
                {tool.toolName}
              </h3>
              {tool.hasUI && (
                <span className="rounded-full border border-emerald-200 bg-emerald-50 px-1.5 py-0.5 text-[9px] font-semibold text-emerald-700">
                  UI
                </span>
              )}
              {tool.source === "local" && (
                <span className="rounded-full border border-blue-200 bg-blue-50 px-1.5 py-0.5 text-[9px] font-semibold text-blue-700">
                  Local
                </span>
              )}
              {tool.isModified && (
                <span className="rounded-full border border-amber-200 bg-amber-50 px-1.5 py-0.5 text-[9px] font-semibold text-amber-700">
                  Modified
                </span>
              )}
            </div>
            <p className="text-xs leading-relaxed text-slate-600 sm:text-[13px]">
              {tool.description}
            </p>

            {params.length > 0 && (
              <div className="rounded-xl border border-slate-100 bg-slate-50/90 p-2.5">
                <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                  Inputs
                </p>
                <ul className="space-y-1">
                  {params.slice(0, 6).map(([name, meta]) => (
                    <li
                      key={name}
                      className="flex flex-wrap items-baseline gap-1.5 text-[11px]"
                    >
                      <code className="font-semibold text-slate-800">
                        {name}
                      </code>
                      {required.includes(name) && (
                        <span className="text-[9px] font-medium text-amber-700">
                          required
                        </span>
                      )}
                      <span className="text-slate-500">
                        {meta?.type ?? "any"}
                      </span>
                    </li>
                  ))}
                  {params.length > 6 && (
                    <li className="text-[10px] text-slate-400">
                      +{params.length - 6} more in Parameters
                    </li>
                  )}
                </ul>
              </div>
            )}

            {tool.hasUI && (
              <div className="min-h-[180px] w-full overflow-hidden rounded-xl border border-slate-200 bg-white">
                <McpAppPreview
                  toolName={tool.toolName}
                  toolDescription={tool.description}
                  inputSchema={tool.inputSchema}
                  htmlSource={tool.htmlSource}
                  hasUI={tool.hasUI}
                  previewData={tool.previewData}
                  height="min(42dvh, 340px)"
                />
              </div>
            )}

            {tool.hasUI && tool.uiResourceUri && (
              <div className="rounded-lg border border-slate-100 bg-slate-50/80 px-2.5 py-2">
                <p className="mb-0.5 text-[9px] font-semibold uppercase tracking-wide text-slate-400">
                  UI resource
                </p>
                <code className="break-all text-[10px] text-slate-600">
                  {tool.uiResourceUri}
                </code>
                {tool.htmlSource && (
                  <span className="mt-1 block text-[10px] text-slate-400">
                    {(tool.htmlSource.length / 1024).toFixed(1)} KB widget
                    bundle
                  </span>
                )}
              </div>
            )}

            <div className="flex flex-col gap-1.5">
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-400">
                Try in chat
              </p>
              <div className="flex flex-col gap-1 sm:flex-row sm:flex-wrap">
                {tryPrompts.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => onTryPrompt(p)}
                    className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-left text-[11px] text-slate-600 transition hover:border-slate-300 hover:bg-slate-50 hover:text-slate-900 sm:min-w-0 sm:flex-1"
                  >
                    ▶ {p}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === "parameters" && (
          <div className="space-y-2 rounded-xl border border-slate-100 bg-slate-50/80 p-3">
            {params.length > 0 ? (
              params.map(([name, meta]) => (
                <div key={name} className="flex flex-wrap items-start gap-1.5">
                  <code className="text-[11px] font-semibold text-slate-800">
                    {name}
                  </code>
                  {required.includes(name) && (
                    <span className="rounded bg-amber-100 px-1 py-0.5 text-[9px] font-semibold text-amber-700">
                      required
                    </span>
                  )}
                  <span className="rounded bg-slate-200/70 px-1 py-0.5 text-[9px] font-medium text-slate-500">
                    {meta?.type ?? "any"}
                  </span>
                  {meta?.description && (
                    <span className="w-full text-[10px] leading-snug text-slate-500">
                      {meta.description}
                    </span>
                  )}
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400">No parameters</p>
            )}
          </div>
        )}

        {tab === "data" && (
          <div className="flex flex-col gap-1.5">
            {previewJsonError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-2 py-1 text-[10px] text-red-700">
                {previewJsonError}
              </div>
            )}
            <textarea
              value={previewJson}
              onChange={(e) => setPreviewJson(e.target.value)}
              className="min-h-[12rem] w-full resize-y rounded-lg bg-slate-950 p-2.5 font-mono text-[10px] leading-relaxed text-slate-100 focus:outline-none focus:ring-1 focus:ring-slate-600 sm:min-h-[14rem] sm:text-[11px]"
              spellCheck={false}
            />
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => onPreviewDataChange({})}
                className="rounded-lg border border-slate-200 px-2 py-1 text-[10px] font-medium text-slate-500 hover:border-slate-300"
              >
                Clear
              </button>
              <button
                type="button"
                onClick={savePreviewData}
                className="rounded-lg bg-slate-900 px-2.5 py-1 text-[10px] font-semibold text-white hover:bg-slate-800"
              >
                Save
              </button>
            </div>
          </div>
        )}

        {(tab === "json" || tab === "ui" || tab === "schema") && (
          <div className="max-h-[min(50dvh,28rem)] overflow-auto rounded-xl bg-slate-950 p-2.5 sm:max-h-[min(55dvh,32rem)]">
            <pre className="whitespace-pre-wrap break-words text-[10px] leading-relaxed text-slate-100 sm:text-[11px]">
              {tab === "json" && toolJson}
              {tab === "ui" && (tool.htmlSource ?? "No UI source")}
              {tab === "schema" && JSON.stringify(tool.inputSchema, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Full-screen overlay on small viewports, centered dialog on md+.
 * Closes on Escape and backdrop click.
 */
export function ToolDetailModal({
  tool,
  open,
  onClose,
  onTryPrompt,
  onPreviewDataChange,
}: {
  tool: MergedToolConfig | null;
  open: boolean;
  onClose: () => void;
  onTryPrompt: (prompt: string) => void;
  onPreviewDataChange: (data: Record<string, unknown>) => void;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open || !tool) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center sm:items-center sm:p-4"
      role="presentation"
    >
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-[2px] transition-opacity"
        aria-label="Close dialog"
        onClick={onClose}
      />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="tool-detail-modal-title"
        className="relative flex h-[min(88dvh,820px)] w-full max-w-[min(100vw,44rem)] flex-col rounded-t-2xl border border-slate-200 bg-white shadow-2xl sm:rounded-2xl"
      >
        <header className="flex shrink-0 items-start justify-between gap-3 border-b border-slate-200 px-4 py-3 sm:px-5">
          <div className="min-w-0 flex-1">
            <h2
              id="tool-detail-modal-title"
              className="truncate text-base font-semibold text-slate-900 sm:text-lg"
            >
              {tool.toolName}
            </h2>
            <p className="line-clamp-2 text-[11px] text-slate-500 sm:text-xs">
              {tool.description}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-lg border border-slate-200 bg-white p-2 text-slate-500 hover:bg-slate-50 hover:text-slate-900"
            aria-label="Close"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </header>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-4 pb-4 pt-3 sm:px-5 sm:pb-5 sm:pt-4">
          <ToolDetailContent
            tool={tool}
            onTryPrompt={(p) => {
              onTryPrompt(p);
              onClose();
            }}
            onPreviewDataChange={onPreviewDataChange}
          />
        </div>
      </div>
    </div>
  );
}
