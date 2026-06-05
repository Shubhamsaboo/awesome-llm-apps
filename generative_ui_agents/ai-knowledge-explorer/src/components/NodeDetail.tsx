"use client";

import { KnowledgeNode, KnowledgeEdge } from "@/lib/types";
import { X, Expand, FileText } from "lucide-react";

const TYPE_COLORS: Record<string, string> = {
  entity: "var(--node-entity)",
  concept: "var(--node-concept)",
  theme: "var(--node-theme)",
  document: "var(--node-document)",
  module: "var(--node-module)",
  class: "var(--node-class)",
  function: "var(--node-function)",
  variable: "var(--node-variable)",
};

interface NodeDetailProps {
  node: KnowledgeNode;
  edges: KnowledgeEdge[];
  allNodes: KnowledgeNode[];
  onClose: () => void;
  onExpand: (nodeId: string) => void;
}

export function NodeDetail({
  node,
  edges,
  allNodes,
  onClose,
  onExpand,
}: NodeDetailProps) {
  const connectedEdges = edges.filter(
    (e) => e.source === node.id || e.target === node.id,
  );
  const nodeMap = Object.fromEntries(allNodes.map((n) => [n.id, n]));

  return (
    <div className="relative z-10 border-t border-[var(--border)] bg-[var(--card)] p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <div
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: TYPE_COLORS[node.type] || "#6b7280" }}
          />
          <h3 className="text-sm font-semibold text-[var(--card-foreground)]">
            {node.label}
          </h3>
          <span className="rounded-full bg-[var(--secondary)] px-2 py-0.5 text-[10px] text-[var(--muted-foreground)]">
            {node.type}
          </span>
        </div>
        <button
          onClick={onClose}
          className="rounded p-1 text-[var(--muted-foreground)] hover:bg-[var(--secondary)]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <p className="mt-2 text-xs text-[var(--muted-foreground)]">
        {node.detail || node.description}
      </p>

      {connectedEdges.length > 0 && (
        <div className="mt-3">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-[var(--muted-foreground)]">
            Connections
          </p>
          <div className="flex flex-wrap gap-1">
            {connectedEdges.map((edge) => {
              const otherId =
                edge.source === node.id ? edge.target : edge.source;
              const other = nodeMap[otherId];
              if (!other) return null;
              return (
                <span
                  key={edge.id}
                  className="inline-flex items-center gap-1 rounded-full bg-[var(--secondary)] px-2 py-0.5 text-[10px] text-[var(--secondary-foreground)]"
                >
                  <span className="text-[var(--muted-foreground)]">
                    {edge.label}
                  </span>
                  {other.label}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {node.sourceDocuments && node.sourceDocuments.length > 0 && (
        <div className="mt-3">
          <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-[var(--muted-foreground)]">
            Sources
          </p>
          <div className="flex flex-wrap gap-1">
            {node.sourceDocuments.map((doc) => (
              <span
                key={doc}
                className="inline-flex items-center gap-1 rounded bg-[var(--secondary)] px-2 py-0.5 text-[10px]"
              >
                <FileText className="h-2.5 w-2.5" />
                {doc}
              </span>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={() => onExpand(node.id)}
        className="mt-3 flex items-center gap-1.5 rounded-lg bg-[var(--secondary)] px-3 py-1.5 text-xs font-medium text-[var(--secondary-foreground)] transition-colors hover:bg-[var(--muted)]"
      >
        <Expand className="h-3 w-3" />
        Expand
      </button>
    </div>
  );
}
