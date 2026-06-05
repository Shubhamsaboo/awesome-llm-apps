"use client";

import { useCallback, useRef, useState } from "react";
import { useAgent } from "@copilotkit/react-core/v2";
import { CopilotSidebar } from "@copilotkit/react-core/v2";
import { useDataEditorUI } from "@/hooks/use-data-editor-ui";
import { useSuggestions } from "@/hooks/use-suggestions";
import { useDataEditorContext } from "@/hooks/use-agent-context";
import { useDataEditorTools } from "@/hooks/use-frontend-tools";
import { BarChart3, Loader2 } from "lucide-react";
import { CanvasDashboard } from "@/components/canvas-dashboard";
import { CanvasMutationPreview } from "@/components/canvas-mutation-preview";

export default function Page() {
  const { agent } = useAgent();
  useDataEditorUI();

  const queryResult = agent.state?.query_result;
  const pendingMutation = agent.state?.pending_mutation;
  const hasResults =
    !!queryResult?.rows?.length && !("error" in (queryResult.rows[0] || {}));
  const hasError =
    !!queryResult?.rows?.length && "error" in (queryResult.rows[0] || {});
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
      expandedRow !== null && queryResult?.rows?.[expandedRow]
        ? ((queryResult.rows[expandedRow].id as number) ?? null)
        : null,
    expandedRowId: expandedRow,
    currentView: hasResults
      ? `${queryResult!.row_count} rows from: ${queryResult!.sql.slice(0, 80)}`
      : "empty",
    rowCount: queryResult?.row_count ?? 0,
  });

  const getQueryResult = useCallback(() => {
    if (!queryResult?.rows?.length) return null;
    return { columns: queryResult.columns, rows: queryResult.rows };
  }, [queryResult]);

  useDataEditorTools({
    setExpandedRow,
    scrollRef,
    highlightRow,
    getQueryResult,
  });

  useSuggestions(hasResults);

  return (
    <div className="flex h-screen bg-[var(--background)]">
      <main
        ref={scrollRef as React.RefObject<HTMLDivElement>}
        className="flex-1 overflow-auto"
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
                {String(queryResult!.rows[0].error)}
              </div>
            </div>
          </div>
        ) : hasResults ? (
          <CanvasDashboard
            queryResult={queryResult!}
            expandedRow={expandedRow}
            setExpandedRow={setExpandedRow}
            highlightedRow={highlightedRow}
          />
        ) : (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center max-w-md">
              <BarChart3 className="mx-auto h-12 w-12 text-[var(--muted-foreground)] mb-4" />
              <h1 className="text-xl font-semibold text-[var(--foreground)] mb-2">
                Your Account
              </h1>
              {isRunning ? (
                <div className="flex items-center justify-center gap-2 text-sm text-[var(--muted-foreground)]">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading your dashboard...
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-[var(--muted-foreground)]">
                    Ask about your usage, billing, or plan.
                  </p>
                  <p className="text-xs text-[var(--muted-foreground)]">
                    Try: &quot;Show me my usage this month&quot;
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
      <CopilotSidebar
        defaultOpen
        className="h-full"
        labels={{
          chatInputPlaceholder: "Ask about your usage, billing, or plan...",
        }}
      />
    </div>
  );
}
