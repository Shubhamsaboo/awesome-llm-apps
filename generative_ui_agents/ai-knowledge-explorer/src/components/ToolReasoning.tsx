"use client";

import { useEffect, useRef } from "react";
import { Wrench, Check, ChevronDown } from "lucide-react";

interface ToolReasoningProps {
  name: string;
  args?: object | unknown;
  status: string;
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return `[${value.length} items]`;
  if (typeof value === "object" && value !== null)
    return `{${Object.keys(value).length} keys}`;
  if (typeof value === "string") return `"${value}"`;
  return String(value);
}

export function ToolReasoning({ name, args, status }: ToolReasoningProps) {
  const entries = args ? Object.entries(args) : [];
  const detailsRef = useRef<HTMLDetailsElement>(null);
  const isRunning = status === "executing" || status === "inProgress";

  useEffect(() => {
    if (!detailsRef.current) return;
    detailsRef.current.open = isRunning;
  }, [isRunning]);

  const statusIcon = isRunning ? (
    <div className="h-3 w-3 animate-spin rounded-full border-2 border-[var(--muted-foreground)] border-t-transparent" />
  ) : (
    <Check className="h-3 w-3 text-emerald-500" />
  );

  return (
    <div className="my-1.5">
      {entries.length > 0 ? (
        <details ref={detailsRef} open className="group">
          <summary className="flex cursor-pointer list-none items-center gap-2 text-sm text-[var(--muted-foreground)] transition-colors hover:text-[var(--foreground)]">
            {statusIcon}
            <Wrench className="h-3 w-3" />
            <span
              className="font-medium"
              style={{ fontFamily: "var(--font-code)" }}
            >
              {name}
            </span>
            <ChevronDown className="ml-auto h-3 w-3 transition-transform group-open:rotate-180" />
          </summary>
          <div className="ml-5 mt-1.5 space-y-1 rounded-md bg-[var(--secondary)] px-3 py-2">
            {entries.map(([key, value]) => (
              <div
                key={key}
                className="flex min-w-0 gap-2 text-xs"
                style={{ fontFamily: "var(--font-code)" }}
              >
                <span className="shrink-0 text-[var(--muted-foreground)]">
                  {key}:
                </span>
                <span className="truncate text-[var(--foreground)]">
                  {formatValue(value)}
                </span>
              </div>
            ))}
          </div>
        </details>
      ) : (
        <div className="flex items-center gap-2 text-sm text-[var(--muted-foreground)]">
          {statusIcon}
          <Wrench className="h-3 w-3" />
          <span
            className="font-medium"
            style={{ fontFamily: "var(--font-code)" }}
          >
            {name}
          </span>
        </div>
      )}
    </div>
  );
}
