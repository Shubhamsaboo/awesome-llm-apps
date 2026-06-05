"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { useAgent } from "@copilotkit/react-core/v2";
import { CopilotChat } from "@copilotkit/react-core/v2";
import { useKnowledgeUI, useSuggestions } from "@/hooks";
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
import { NodeDetail } from "@/components/NodeDetail";
import { KnowledgeNode, KnowledgeEdge } from "@/lib/types";
import { EXAMPLE_FILES, CODE_EXAMPLE_FILES } from "@/lib/example-content";
import { Network, Code, Sparkles, RotateCcw, Plus } from "lucide-react";
import { JsonCollapser } from "@/components/JsonCollapser";

const ALLOWED_EXTENSIONS = [
  ".txt",
  ".md",
  ".json",
  ".csv",
  ".py",
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".java",
  ".go",
  ".rs",
  ".rb",
  ".vue",
  ".svelte",
  ".c",
  ".cpp",
  ".h",
  ".cs",
  ".swift",
  ".kt",
];

const IGNORE_DIRS = new Set([
  "node_modules",
  ".git",
  "dist",
  "build",
  ".next",
  "__pycache__",
  ".venv",
  "venv",
  "target",
  ".idea",
  ".vscode",
  "coverage",
  ".cache",
  ".turbo",
  ".output",
  "out",
]);

const IGNORE_FILES = new Set([
  ".DS_Store",
  "package-lock.json",
  "yarn.lock",
  "pnpm-lock.yaml",
  "uv.lock",
  "Cargo.lock",
  "go.sum",
]);

const MAX_FILES = 30;
const MAX_TOTAL_SIZE = 102400;

function hasAllowedExtension(name: string): boolean {
  return ALLOWED_EXTENSIONS.some((ext) => name.toLowerCase().endsWith(ext));
}

async function readDirectoryEntries(
  entry: FileSystemDirectoryEntry,
): Promise<FileSystemEntry[]> {
  const reader = entry.createReader();
  const entries: FileSystemEntry[] = [];
  let batch: FileSystemEntry[];
  do {
    batch = await new Promise((resolve, reject) =>
      reader.readEntries(resolve, reject),
    );
    entries.push(...batch);
  } while (batch.length > 0);
  return entries;
}

async function collectFiles(
  entry: FileSystemEntry,
  path: string,
  results: { name: string; file: File }[],
) {
  if (results.length >= MAX_FILES) return;

  if (entry.isFile) {
    if (IGNORE_FILES.has(entry.name)) return;
    if (!hasAllowedExtension(entry.name)) return;
    const file = await new Promise<File>((resolve, reject) =>
      (entry as FileSystemFileEntry).file(resolve, reject),
    );
    results.push({ name: path + entry.name, file });
  } else if (entry.isDirectory) {
    if (IGNORE_DIRS.has(entry.name)) return;
    const children = await readDirectoryEntries(
      entry as FileSystemDirectoryEntry,
    );
    for (const child of children) {
      if (results.length >= MAX_FILES) break;
      await collectFiles(child, path + entry.name + "/", results);
    }
  }
}

export default function Page() {
  const { agent } = useAgent();
  useKnowledgeUI();

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dragCounter = useRef(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const inject = () => {
      const cpkBtn = document.querySelector(
        '[data-copilotkit] button[data-slot="tooltip-trigger"]',
      ) as HTMLButtonElement | null;
      if (!cpkBtn || cpkBtn.getAttribute("data-replaced")) return;
      cpkBtn.setAttribute("data-replaced", "true");
      cpkBtn.style.display = "none";

      const ourBtn = document.createElement("button");
      ourBtn.type = "button";
      ourBtn.innerHTML = cpkBtn.innerHTML;
      ourBtn.className = cpkBtn.className;
      ourBtn.title = "Upload files";
      ourBtn.addEventListener("click", () => fileInputRef.current?.click());
      cpkBtn.parentElement?.insertBefore(ourBtn, cpkBtn);
    };
    const observer = new MutationObserver(inject);
    observer.observe(document.body, { childList: true, subtree: true });
    inject();
    return () => observer.disconnect();
  }, []);

  const nodes: KnowledgeNode[] = agent.state?.nodes || [];
  const edges: KnowledgeEdge[] = agent.state?.edges || [];
  const hasGraph = nodes.length > 0;

  useSuggestions(hasGraph);

  const selectedNode = selectedNodeId
    ? nodes.find((n) => n.id === selectedNodeId) || null
    : null;

  const sendChatMessage = useCallback((text: string) => {
    const input = document.querySelector(
      ".json-collapse-chat textarea, .json-collapse-chat input[type='text']",
    ) as HTMLTextAreaElement | HTMLInputElement | null;
    if (!input) return;
    const nativeSet =
      Object.getOwnPropertyDescriptor(
        window.HTMLTextAreaElement.prototype,
        "value",
      )?.set ||
      Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype,
        "value",
      )?.set;
    nativeSet?.call(input, text);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    setTimeout(() => {
      const form = input.closest("form");
      if (form) {
        form.dispatchEvent(
          new Event("submit", { bubbles: true, cancelable: true }),
        );
      } else {
        input.dispatchEvent(
          new KeyboardEvent("keydown", {
            key: "Enter",
            code: "Enter",
            bubbles: true,
          }),
        );
      }
    }, 50);
  }, []);

  const handleFilesReady = useCallback(
    async (files: { name: string; content: string }[]) => {
      const res = await fetch("/api/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files }),
      });
      await res.json();

      sendChatMessage(
        `Uploaded ${files.map((f) => f.name).join(", ")}. Build a knowledge graph.`,
      );
    },
    [sendChatMessage],
  );

  const processFileList = useCallback(
    async (fileList: FileList) => {
      const files = Array.from(fileList).filter((f) =>
        ALLOWED_EXTENSIONS.some((ext) => f.name.toLowerCase().endsWith(ext)),
      );
      if (files.length === 0) return;
      const results: { name: string; content: string }[] = [];
      for (const file of files) {
        const text = await file.text();
        const limit = 20480;
        const content =
          text.length > limit ? text.slice(0, limit) + "\n\n[truncated]" : text;
        results.push({ name: file.name, content });
      }
      handleFilesReady(results);
    },
    [handleFilesReady],
  );

  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const items = Array.from(e.dataTransfer.items);
      const entries = items
        .map((item) => item.webkitGetAsEntry?.())
        .filter(Boolean) as FileSystemEntry[];
      const hasDirectory = entries.some((entry) => entry.isDirectory);

      if (hasDirectory) {
        const collected: { name: string; file: File }[] = [];
        for (const entry of entries) {
          await collectFiles(entry, "", collected);
        }
        if (collected.length === 0) return;

        const results: { name: string; content: string }[] = [];
        let totalSize = 0;
        for (const { name, file } of collected) {
          const text = await file.text();
          const limit = 20480;
          const content =
            text.length > limit
              ? text.slice(0, limit) + "\n\n[truncated]"
              : text;
          totalSize += content.length;
          if (totalSize > MAX_TOTAL_SIZE) break;
          results.push({ name, content });
        }
        if (results.length > 0) handleFilesReady(results);
      } else if (e.dataTransfer.files.length > 0) {
        processFileList(e.dataTransfer.files);
      }
    },
    [processFileList, handleFilesReady],
  );

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelectedNodeId(nodeId);
  }, []);

  const handleNodeDoubleClick = useCallback(
    (nodeId: string) => {
      const node = nodes.find((n) => n.id === nodeId);
      if (!node) return;
      sendChatMessage(`Expand the node "${node.label}" (id: ${nodeId})`);
    },
    [nodes, sendChatMessage],
  );

  const handleExpand = useCallback(
    (nodeId: string) => {
      const node = nodes.find((n) => n.id === nodeId);
      if (!node) return;
      sendChatMessage(`Expand the node "${node.label}" (id: ${nodeId})`);
    },
    [nodes, sendChatMessage],
  );

  return (
    <div
      className="flex h-screen overflow-hidden relative"
      onDragEnter={(e) => {
        e.preventDefault();
        dragCounter.current++;
        setIsDragging(true);
      }}
      onDragOver={(e) => {
        e.preventDefault();
      }}
      onDragLeave={() => {
        dragCounter.current--;
        if (dragCounter.current <= 0) {
          dragCounter.current = 0;
          setIsDragging(false);
        }
      }}
      onDrop={(e) => {
        dragCounter.current = 0;
        setIsDragging(false);
        handleDrop(e);
      }}
    >
      <JsonCollapser />
      {/* Drop overlay */}
      {isDragging && (
        <div className="pointer-events-none absolute inset-0 z-50 flex items-center justify-center bg-[var(--background)]/80 backdrop-blur-sm">
          <div className="rounded-2xl border-2 border-dashed border-[var(--ring)] bg-[var(--accent)] px-12 py-8 text-sm font-medium text-[var(--foreground)]">
            Drop files or a folder to explore
          </div>
        </div>
      )}

      {/* Chat sidebar — always 38% */}
      <div className="flex h-full w-[38%] flex-col border-r border-[var(--border)]">
        <header className="shrink-0 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network className="h-5 w-5 text-[var(--muted-foreground)]" />
            <h1
              className="text-lg font-bold"
              style={{ fontFamily: "var(--font-body)" }}
            >
              Knowledge Explorer
            </h1>
          </div>
          {hasGraph && (
            <button
              onClick={() => {
                agent.setState({
                  nodes: [],
                  edges: [],
                  selectedNodeId: "",
                  processingStatus: "idle",
                });
                setSelectedNodeId(null);
                window.location.reload();
              }}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-[var(--muted-foreground)] transition-colors hover:bg-[var(--secondary)] hover:text-[var(--foreground)]"
              title="Start over"
            >
              <Plus className="h-3.5 w-3.5" />
              New
            </button>
          )}
        </header>

        <div className="min-h-0 flex-1 overflow-hidden px-4 py-2">
          <CopilotChat
            className="h-full json-collapse-chat"
            labels={{
              welcomeMessageText: hasGraph
                ? ""
                : "Generate an interactive knowledge graph.",
              chatInputPlaceholder: hasGraph
                ? "Ask about the graph or add more content..."
                : "Paste content or describe a topic...",
            }}
          />
        </div>

        {/* Starting prompt — only when no graph */}
        {!hasGraph && (
          <div className="shrink-0 px-6 pb-4 flex items-center justify-center gap-2">
            <button
              onClick={() => handleFilesReady(EXAMPLE_FILES)}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] px-4 py-2 text-xs font-medium text-[var(--muted-foreground)] transition-colors hover:bg-[var(--secondary)] hover:text-[var(--foreground)]"
            >
              <Sparkles className="h-3 w-3" />
              Try example docs
            </button>
            <button
              onClick={() => handleFilesReady(CODE_EXAMPLE_FILES)}
              className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] px-4 py-2 text-xs font-medium text-[var(--muted-foreground)] transition-colors hover:bg-[var(--secondary)] hover:text-[var(--foreground)]"
            >
              <Code className="h-3 w-3" />
              Try example code
            </button>
          </div>
        )}
      </div>

      {/* Graph canvas — always visible */}
      <div className="flex h-full flex-1 flex-col">
        <div className="min-h-0 flex-1">
          <KnowledgeGraph
            nodes={nodes}
            edges={edges}
            selectedNodeId={selectedNodeId}
            onNodeClick={handleNodeClick}
            onNodeDoubleClick={handleNodeDoubleClick}
          />
        </div>

        {selectedNode && (
          <NodeDetail
            node={selectedNode}
            edges={edges}
            allNodes={nodes}
            onClose={() => setSelectedNodeId(null)}
            onExpand={handleExpand}
          />
        )}

        {hasGraph && (
          <div className="shrink-0 border-t border-[var(--border)] px-4 py-2">
            <div className="flex items-center gap-4 text-[10px] text-[var(--muted-foreground)]">
              <span>{nodes.length} nodes</span>
              <span>{edges.length} edges</span>
              {agent.isRunning && (
                <span className="flex items-center gap-1">
                  <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
                  Processing...
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Hidden file input for + button */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept={ALLOWED_EXTENSIONS.join(",")}
        className="hidden"
        onChange={(e) => {
          if (e.target.files) processFileList(e.target.files);
          e.target.value = "";
        }}
      />
    </div>
  );
}
