"use client";

import { useState, useCallback, useRef } from "react";
import { useAgent } from "@copilotkit/react-core/v2";
import { CopilotSidebar } from "@copilotkit/react-core/v2";
import { useKnowledgeUI, useSuggestions } from "@/hooks";
import { KnowledgeGraph } from "@/components/KnowledgeGraph";
import { NodeDetail } from "@/components/NodeDetail";
import { KnowledgeNode, KnowledgeEdge } from "@/lib/types";
import { EXAMPLE_FILES, CODE_EXAMPLE_FILES } from "@/lib/example-content";
import { Network, Code, Sparkles, Upload } from "lucide-react";
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

  const nodes: KnowledgeNode[] = agent.state?.nodes || [];
  const edges: KnowledgeEdge[] = agent.state?.edges || [];
  const hasGraph = nodes.length > 0;

  useSuggestions(hasGraph);

  const selectedNode = selectedNodeId
    ? nodes.find((n) => n.id === selectedNodeId) || null
    : null;

  const typeIntoChat = useCallback((text: string) => {
    const input = document.querySelector(
      "[data-copilotkit] textarea",
    ) as HTMLTextAreaElement | null;
    if (!input) return;
    input.focus();
    const nativeSet = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype,
      "value",
    )?.set;
    nativeSet?.call(input, text);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    setTimeout(() => {
      const sendBtn = document.querySelector(
        '[data-testid="copilot-send-button"]',
      ) as HTMLButtonElement | null;
      sendBtn?.click();
    }, 100);
  }, []);

  const handleFilesReady = useCallback(
    async (files: { name: string; content: string }[]) => {
      const res = await fetch("/api/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ files }),
      });
      await res.json();
      typeIntoChat(
        `Uploaded ${files.map((f) => f.name).join(", ")}. Build a knowledge graph.`,
      );
    },
    [typeIntoChat],
  );

  const sendChatMessage = useCallback(
    (text: string) => {
      typeIntoChat(text);
    },
    [typeIntoChat],
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
      className="flex h-screen bg-[var(--background)]"
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
      {isDragging && (
        <div className="pointer-events-none absolute inset-0 z-50 flex items-center justify-center bg-[var(--background)]/80 backdrop-blur-sm">
          <div className="rounded-2xl border-2 border-dashed border-[var(--ring)] bg-[var(--accent)] px-12 py-8 text-sm font-medium text-[var(--foreground)]">
            Drop files or a folder to explore
          </div>
        </div>
      )}

      <JsonCollapser />
      <main className="flex-1 flex flex-col overflow-hidden">
        <div className="min-h-0 flex-1">
          {hasGraph ? (
            <KnowledgeGraph
              nodes={nodes}
              edges={edges}
              selectedNodeId={selectedNodeId}
              onNodeClick={handleNodeClick}
              onNodeDoubleClick={handleNodeDoubleClick}
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-6">
              <div className="flex flex-col items-center gap-2 text-[var(--muted-foreground)]">
                <Network className="h-10 w-10 opacity-20" />
                <p className="text-sm">
                  Drop files or use an example to get started
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] px-4 py-2 text-xs font-medium text-[var(--muted-foreground)] transition-colors hover:bg-[var(--secondary)] hover:text-[var(--foreground)]"
                >
                  <Upload className="h-3 w-3" />
                  Upload files
                </button>
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
            </div>
          )}
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
              <button
                onClick={() => fileInputRef.current?.click()}
                className="ml-auto flex items-center gap-1 transition-colors hover:text-[var(--foreground)]"
              >
                <Upload className="h-3 w-3" />
                Add files
              </button>
            </div>
          </div>
        )}
      </main>

      <CopilotSidebar
        defaultOpen
        className="h-full"
        labels={{
          modalHeaderTitle: "Knowledge Explorer",
          chatInputPlaceholder: hasGraph
            ? "Ask about the graph or add more content..."
            : "Paste a document or article to explore...",
        }}
      />

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
