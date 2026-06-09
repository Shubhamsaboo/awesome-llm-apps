"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { useAgent } from "@copilotkit/react-core/v2";
import { useCopilotReadable } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-core/v2";
import { useDataEditorUI } from "@/hooks/use-data-editor-ui";
import { useSuggestions } from "@/hooks/use-suggestions";
import { useDataEditorContext } from "@/hooks/use-agent-context";
import { useDataEditorTools } from "@/hooks/use-frontend-tools";
import { Database, Loader2, Upload, X } from "lucide-react";
import { CanvasDashboard } from "@/components/canvas-dashboard";
import { CanvasMutationPreview } from "@/components/canvas-mutation-preview";

function parseCSV(text: string): {
  columns: string[];
  rows: Record<string, unknown>[];
} {
  const trimmed = text.trim();

  // Detect JSON arrays or objects
  if (trimmed.startsWith("[") || trimmed.startsWith("{")) {
    try {
      let parsed = JSON.parse(trimmed);
      if (!Array.isArray(parsed)) parsed = [parsed];
      if (parsed.length === 0) return { columns: [], rows: [] };
      const columns = Object.keys(parsed[0]);
      return { columns, rows: parsed };
    } catch (e) {
      console.warn("JSON parse failed, falling through to CSV parser:", e);
    }
  }

  const lines = trimmed.split("\n").filter((l) => l.trim());
  if (lines.length < 2) return { columns: [], rows: [] };

  const sep = lines[0].includes("\t") ? "\t" : ",";
  const columns = lines[0]
    .split(sep)
    .map((c) => c.trim().replace(/^"|"$/g, ""));
  const rows = lines.slice(1).map((line) => {
    const values = line.split(sep).map((v) => v.trim().replace(/^"|"$/g, ""));
    const row: Record<string, unknown> = {};
    columns.forEach((col, i) => {
      const val = values[i] ?? "";
      const num = Number(val);
      row[col] = val !== "" && !isNaN(num) ? num : val;
    });
    return row;
  });
  return { columns, rows };
}

export default function Page() {
  const { agent } = useAgent();
  useDataEditorUI();

  const [uploadedFile, setUploadedFile] = useState<{
    name: string;
    content: string;
  } | null>(null);
  const [dragOver, setDragOver] = useState(false);

  const fileData = useMemo(() => {
    if (!uploadedFile) return null;
    return parseCSV(uploadedFile.content);
  }, [uploadedFile]);

  useCopilotReadable({
    description:
      "File the user uploaded into the dashboard. The data is displayed in the main canvas. Use this to answer questions about the file contents.",
    value: uploadedFile
      ? `File: ${uploadedFile.name}\n\n${uploadedFile.content.slice(0, 8000)}`
      : "",
  });

  const queryResult = agent.state?.query_result;
  const pendingMutation = agent.state?.pending_mutation;

  const displayResult =
    queryResult ??
    (fileData && fileData.rows.length > 0
      ? {
          sql: `Uploaded: ${uploadedFile!.name}`,
          columns: fileData.columns,
          rows: fileData.rows,
          row_count: fileData.rows.length,
          result_type: "table" as const,
        }
      : null);

  const hasResults =
    !!displayResult?.rows?.length &&
    !("error" in (displayResult.rows[0] || {}));
  const hasError =
    !!displayResult?.rows?.length && "error" in (displayResult.rows[0] || {});
  const isRunning = agent.isRunning;

  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [highlightedRow, setHighlightedRow] = useState<number | null>(null);
  const scrollRef = useRef<HTMLElement>(null);

  const highlightRow = useCallback((rowIndex: number) => {
    setHighlightedRow(rowIndex);
    setExpandedRow(rowIndex);
    setTimeout(() => setHighlightedRow(null), 3000);
  }, []);

  useDataEditorContext({
    selectedRowId:
      expandedRow !== null && displayResult?.rows?.[expandedRow]
        ? ((displayResult.rows[expandedRow].id as number) ?? null)
        : null,
    expandedRowId: expandedRow,
    currentView: hasResults
      ? `${displayResult!.row_count} rows from: ${displayResult!.sql.slice(0, 80)}`
      : "empty",
    rowCount: displayResult?.row_count ?? 0,
  });

  const getQueryResult = useCallback(() => {
    if (!displayResult?.rows?.length) return null;
    return { columns: displayResult.columns, rows: displayResult.rows };
  }, [displayResult]);

  useDataEditorTools({
    setExpandedRow,
    scrollRef,
    highlightRow,
    getQueryResult,
  });

  useSuggestions(hasResults);

  const handleFile = async (file: File) => {
    const text = await file.text();
    setUploadedFile({ name: file.name, content: text });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div className="flex h-screen bg-[var(--background)]">
      <main
        ref={scrollRef as React.RefObject<HTMLDivElement>}
        className="flex-1 overflow-auto"
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        {pendingMutation ? (
          <div className="flex items-start justify-center p-8">
            <div className="w-full max-w-2xl">
              <CanvasMutationPreview mutation={pendingMutation} />
            </div>
          </div>
        ) : hasError ? (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center max-w-md">
              <div className="text-red-400 text-sm font-mono bg-red-500/10 border border-red-500/20 rounded-lg p-4">
                {String(displayResult!.rows[0].error)}
              </div>
            </div>
          </div>
        ) : hasResults ? (
          <>
            {uploadedFile && !queryResult && (
              <div className="flex items-center gap-2 px-6 pt-4 text-xs text-[var(--muted-foreground)]">
                <Upload className="h-3 w-3" />
                <span>{uploadedFile.name}</span>
                <button
                  onClick={() => setUploadedFile(null)}
                  className="hover:text-[var(--foreground)] cursor-pointer"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}
            <CanvasDashboard
              queryResult={displayResult!}
              expandedRow={expandedRow}
              setExpandedRow={setExpandedRow}
              highlightedRow={highlightedRow}
            />
          </>
        ) : (
          <div
            className={`flex items-center justify-center h-full p-8 transition-colors ${dragOver ? "bg-blue-500/5" : ""}`}
          >
            <div className="text-center max-w-lg">
              <Database className="mx-auto h-12 w-12 text-[var(--muted-foreground)] mb-4" />
              <h1 className="text-xl font-semibold text-[var(--foreground)] mb-2">
                AI Data Editor
              </h1>
              {isRunning ? (
                <div className="flex items-center justify-center gap-2 text-sm text-[var(--muted-foreground)]">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading dashboard...
                </div>
              ) : (
                <>
                  <p className="text-sm text-[var(--muted-foreground)] mb-5">
                    Query and edit data with natural language. Try one of these
                    to get started:
                  </p>

                  <div className="flex flex-wrap justify-center gap-2 mb-6">
                    {[
                      "Show all accounts",
                      "Revenue by type",
                      "Overdue invoices",
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => {
                          const ta =
                            document.querySelector<HTMLTextAreaElement>(
                              'textarea[placeholder*="Ask"]',
                            );
                          if (!ta) return;
                          const set = Object.getOwnPropertyDescriptor(
                            HTMLTextAreaElement.prototype,
                            "value",
                          )?.set;
                          set?.call(ta, q);
                          ta.dispatchEvent(
                            new Event("input", { bubbles: true }),
                          );
                          ta.focus();
                        }}
                        className="px-3 py-1.5 text-xs rounded-full border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)] cursor-pointer transition-colors"
                      >
                        {q}
                      </button>
                    ))}
                  </div>

                  <label
                    className={`flex flex-col items-center gap-3 px-8 py-6 border-2 border-dashed rounded-xl cursor-pointer transition-colors ${
                      dragOver
                        ? "border-blue-500 bg-blue-500/10 text-blue-400"
                        : "border-[var(--border)] hover:border-[var(--foreground)] hover:bg-[var(--muted)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
                    }`}
                  >
                    <Upload className="h-6 w-6" />
                    <span className="text-sm">
                      Drop a file here or click to upload
                    </span>
                    <span className="text-xs opacity-60">
                      CSV, TSV, or JSON
                    </span>
                    <input
                      type="file"
                      className="hidden"
                      accept=".csv,.tsv,.json"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) handleFile(file);
                        e.target.value = "";
                      }}
                    />
                  </label>
                </>
              )}
            </div>
          </div>
        )}
      </main>
      <CopilotSidebar
        defaultOpen
        className="h-full"
        labels={{
          modalHeaderTitle: "AI Data Editor",
          chatInputPlaceholder: uploadedFile
            ? `Ask about ${uploadedFile.name}...`
            : "Ask about your data or request a change...",
        }}
      />
    </div>
  );
}
