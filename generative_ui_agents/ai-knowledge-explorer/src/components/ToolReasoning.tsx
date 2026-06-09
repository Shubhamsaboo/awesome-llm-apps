"use client";

import { Loader2, Check } from "lucide-react";

const TOOL_LABELS: Record<string, string> = {
  extract_knowledge: "Extracting knowledge",
  find_connections: "Finding connections",
  expand_node: "Expanding node",
};

interface ToolReasoningProps {
  name: string;
  args?: object | unknown;
  status: string;
}

export function ToolReasoning({ name, status }: ToolReasoningProps) {
  const isRunning = status === "executing" || status === "inProgress";
  const label = TOOL_LABELS[name] || name;

  return (
    <div className="flex items-center gap-2 py-1 text-sm text-[var(--muted-foreground)]">
      {isRunning ? (
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
      ) : (
        <Check className="h-3.5 w-3.5 text-emerald-500" />
      )}
      <span>{label}</span>
    </div>
  );
}
