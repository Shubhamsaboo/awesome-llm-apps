"use client";

import { useState } from "react";
import {
  ChevronDown,
  Pencil,
  ClipboardList,
  Search,
  Save,
  BookOpen,
  Check,
} from "lucide-react";

/**
 * ToolCard - Generative UI for tool call rendering in chat.
 *
 * Two rendering modes:
 * - SpecializedToolCard: Emoji-based cards for known tools with result previews
 * - DefaultToolCard: Generic JSON display for unknown tools
 *
 * Result structures expected from backend:
 * - internet_search: Array<{url, title, content, raw_content}>
 * - write_todos: { todos: Array<{id, content, status}> }
 * - write_file: just args (path, content) - result is confirmation
 * - task: completion message
 */

interface ToolCardProps {
  name: string;
  status: "inProgress" | "executing" | "complete";
  args: Record<string, unknown>;
  result?: unknown;
}

// Tool configuration mapping
const TOOL_CONFIG: Record<
  string,
  {
    icon: React.ComponentType<{
      size?: number;
      strokeWidth?: number;
      className?: string;
      style?: React.CSSProperties;
    }>;
    getDisplayText: (args: Record<string, unknown>) => string;
    getResultSummary?: (
      result: unknown,
      args: Record<string, unknown>,
    ) => string | null;
  }
> = {
  write_todos: {
    icon: Pencil,
    getDisplayText: () => "Updating research plan...",
    // Args contains the todos array (result is a Command with ToolMessage string)
    getResultSummary: (result, args) => {
      const todos = (args as { todos?: unknown[] })?.todos;
      if (Array.isArray(todos)) {
        return `${todos.length} todo${todos.length !== 1 ? "s" : ""} updated`;
      }
      return null;
    },
  },
  read_todos: {
    icon: ClipboardList,
    getDisplayText: () => "Checking research plan...",
    getResultSummary: (result) => {
      const todos = (result as { todos?: unknown[] })?.todos;
      if (Array.isArray(todos)) {
        return `${todos.length} todo${todos.length !== 1 ? "s" : ""} found`;
      }
      return null;
    },
  },
  research: {
    icon: Search,
    getDisplayText: (args) =>
      `Researching: ${((args.query as string) || "...").slice(0, 50)}${(args.query as string)?.length > 50 ? "..." : ""}`,
    // Result is now a dict with summary and sources
    getResultSummary: (result) => {
      if (result && typeof result === "object" && "sources" in result) {
        const { sources } = result as { summary: string; sources: unknown[] };
        return `Found ${sources.length} source${sources.length !== 1 ? "s" : ""}`;
      }
      return "Research complete";
    },
  },
  write_file: {
    icon: Save,
    getDisplayText: (args) => {
      const path = args.path as string | undefined;
      const filename =
        path?.split("/").pop() || (args.filename as string | undefined);
      return `Writing: ${filename || "file"}`;
    },
    // Show first line preview from args (content is in args, not result)
    getResultSummary: (_result, args) => {
      const content = args.content as string | undefined;
      if (content) {
        const firstLine = content.split("\n")[0].slice(0, 50);
        return firstLine + (content.length > 50 ? "..." : "");
      }
      return "File written";
    },
  },
  read_file: {
    icon: BookOpen,
    getDisplayText: (args) => {
      const path = args.path as string | undefined;
      const filename =
        path?.split("/").pop() || (args.filename as string | undefined);
      return `Reading: ${filename || "file"}`;
    },
    getResultSummary: (result) => {
      const content = (result as { content?: string })?.content;
      if (content && typeof content === "string") {
        const preview = content.slice(0, 50);
        return preview + (content.length > 50 ? "..." : "");
      }
      return null;
    },
  },
};

export function ToolCard({ name, status, args, result }: ToolCardProps) {
  const config = TOOL_CONFIG[name];

  if (config) {
    return (
      <SpecializedToolCard
        name={name}
        status={status}
        args={args}
        result={result}
        config={config}
      />
    );
  }

  return (
    <DefaultToolCard name={name} status={status} args={args} result={result} />
  );
}

interface SpecializedToolCardProps extends ToolCardProps {
  config: {
    icon: React.ComponentType<{
      size?: number;
      strokeWidth?: number;
      className?: string;
      style?: React.CSSProperties;
    }>;
    getDisplayText: (args: Record<string, unknown>) => string;
    getResultSummary?: (
      result: unknown,
      args: Record<string, unknown>,
    ) => string | null;
  };
}

function SpecializedToolCard({
  name,
  status,
  args,
  result,
  config,
}: SpecializedToolCardProps) {
  const [expanded, setExpanded] = useState(false);
  const isComplete = status === "complete";
  const isExecuting = status === "inProgress" || status === "executing";

  // Get result summary for completed tools
  const resultSummary =
    isComplete && config.getResultSummary
      ? config.getResultSummary(result, args)
      : null;

  // Determine if this tool has expandable content
  const hasExpandableContent =
    isComplete && (name === "research" || name === "write_todos");

  return (
    <div
      className={`
        glass-subtle
        transition-all duration-200
        ${isComplete ? "opacity-80" : ""}
        ${hasExpandableContent ? "cursor-pointer" : ""}
      `}
      style={{
        padding: "var(--space-4)",
        marginBottom: "var(--space-2)",
      }}
      onClick={hasExpandableContent ? () => setExpanded(!expanded) : undefined}
    >
      <div className="flex items-center" style={{ gap: "var(--space-3)" }}>
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{
            background: isComplete
              ? "rgba(21, 128, 61, 0.1)"
              : "rgba(217, 119, 6, 0.1)",
          }}
        >
          {isComplete ? (
            <Check
              size={16}
              strokeWidth={2}
              style={{ color: "var(--color-success)" }}
            />
          ) : (
            <config.icon
              size={16}
              strokeWidth={2}
              className={isExecuting ? "animate-spin-slow" : ""}
              style={{ color: "var(--color-accent)" }}
            />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p
            className={`
              text-sm font-medium
              ${
                isComplete
                  ? "text-[var(--color-text-tertiary)]"
                  : "text-[var(--color-text-primary)]"
              }
            `}
          >
            {config.getDisplayText(args)}
          </p>
          {/* Result summary shown below the display text when complete */}
          {resultSummary && (
            <p
              className="text-xs mt-0.5"
              style={{ color: "var(--color-success)" }}
            >
              {resultSummary}
            </p>
          )}
        </div>
        {/* Expand indicator for expandable tools */}
        {hasExpandableContent && (
          <ChevronDown
            className={`w-4 h-4 text-[var(--color-text-tertiary)] transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        )}
      </div>

      {/* Expanded details section */}
      {expanded && isComplete && (
        <div
          style={{ marginTop: "var(--space-3)", paddingTop: "var(--space-3)" }}
          className="border-t border-[var(--color-border-glass)]"
        >
          <ExpandedDetails name={name} result={result} args={args} />
        </div>
      )}
    </div>
  );
}

/**
 * Renders expanded details based on tool type.
 * Each tool has its own structured view of the result.
 */
function ExpandedDetails({
  name,
  result,
  args,
}: {
  name: string;
  result: unknown;
  args: Record<string, unknown>;
}) {
  // research: show the full prose summary
  if (name === "research") {
    // Extract summary from object or use string directly
    const summary =
      typeof result === "object" && result && "summary" in result
        ? (result as { summary: string; sources: unknown[] }).summary
        : typeof result === "string"
          ? result
          : "";
    if (!summary)
      return (
        <p className="text-xs text-[var(--color-text-tertiary)]">No findings</p>
      );
    return (
      <div className="space-y-2">
        <p className="text-xs font-medium text-[var(--color-text-tertiary)]">
          Query:
        </p>
        <p className="text-xs text-[var(--color-text-secondary)]">
          {(args.query as string) || "..."}
        </p>
        <p className="text-xs font-medium text-[var(--color-text-tertiary)] mt-2">
          Findings:
        </p>
        <p className="text-sm text-[var(--color-text-primary)] whitespace-pre-wrap">
          {summary}
        </p>
      </div>
    );
  }

  // write_todos: show todo list (from args, not result)
  if (name === "write_todos") {
    const todos = (
      args as { todos?: Array<{ id: string; content: string; status: string }> }
    )?.todos;
    if (!todos?.length)
      return (
        <p className="text-xs text-[var(--color-text-tertiary)]">No todos</p>
      );
    return (
      <div className="space-y-1 max-h-40 overflow-y-auto">
        {todos.map((todo, i) => (
          <div key={todo.id || i} className="flex items-start gap-2 text-xs">
            <span
              className="mt-0.5"
              style={{
                color:
                  todo.status === "completed"
                    ? "var(--color-success)"
                    : todo.status === "in_progress"
                      ? "var(--color-accent-dark)"
                      : "var(--color-text-tertiary)",
              }}
            >
              {todo.status === "completed"
                ? "✓"
                : todo.status === "in_progress"
                  ? "●"
                  : "○"}
            </span>
            <span
              className={
                todo.status === "completed"
                  ? "line-through text-[var(--color-text-tertiary)]"
                  : ""
              }
            >
              {todo.content}
            </span>
          </div>
        ))}
      </div>
    );
  }

  // Fallback: JSON display
  return (
    <pre className="text-xs bg-[var(--color-container)] p-2 rounded-md overflow-auto max-h-32 border border-[var(--color-border)]">
      {typeof result === "string" ? result : JSON.stringify(result, null, 2)}
    </pre>
  );
}

function DefaultToolCard({ name, status, args, result }: ToolCardProps) {
  const [expanded, setExpanded] = useState(false);
  const isComplete = status === "complete";

  return (
    <div className="glass-subtle p-3 my-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className={`
              w-8 h-8 rounded-lg flex items-center justify-center
              text-lg
              ${
                isComplete
                  ? "bg-[var(--color-mint)]/20"
                  : "bg-[var(--color-lilac)]/20"
              }
            `}
          >
            {isComplete ? "✓" : "⚙️"}
          </div>
          <div className="flex items-center gap-2">
            <code className="text-sm text-[var(--color-text-primary)]">
              {name}
            </code>
            <span
              className={`
                text-xs px-2 py-0.5 rounded-full
                ${
                  isComplete
                    ? "bg-[var(--color-mint)]/20 text-[var(--color-mint-dark)]"
                    : "bg-[var(--color-lilac)]/20 text-[var(--color-lilac-dark)]"
                }
              `}
            >
              {status}
            </span>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[var(--color-text-tertiary)] hover:text-[var(--color-text-secondary)] transition-colors"
        >
          <ChevronDown
            className={`w-4 h-4 transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        </button>
      </div>
      {expanded && (
        <div className="mt-3 space-y-2">
          <div>
            <p className="text-xs text-[var(--color-text-tertiary)] mb-1">
              Arguments:
            </p>
            <pre className="text-xs bg-[var(--color-container)] p-2 rounded-md overflow-auto max-h-32 border border-[var(--color-border)]">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
          {result !== undefined && result !== null && (
            <div>
              <p className="text-xs text-[var(--color-text-tertiary)] mb-1">
                Result:
              </p>
              <pre className="text-xs bg-[var(--color-container)] p-2 rounded-md overflow-auto max-h-32 border border-[var(--color-border)]">
                {typeof result === "string"
                  ? result
                  : JSON.stringify(result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
