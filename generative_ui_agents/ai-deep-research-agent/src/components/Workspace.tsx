"use client";

import { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  ListTodo,
  FileText,
  Download,
  Globe,
  Check,
  Circle,
  CircleDot,
  X,
} from "lucide-react";
import { ResearchState, Todo, ResearchFile, Source } from "@/types/research";
import { FileViewerModal } from "@/components/FileViewerModal";

// Helper function to download file content
function downloadFile(file: ResearchFile) {
  const blob = new Blob([file.content], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = file.path.split("/").pop() || "file.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

interface WorkspaceProps {
  state: ResearchState;
}

// Collapsible section component with smooth transitions
function Section({
  title,
  icon: Icon,
  children,
  defaultOpen = true,
  badge,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  defaultOpen?: boolean;
  badge?: number;
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="workspace-section">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="workspace-section-header w-full transition-all duration-200"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-[var(--color-text-secondary)]" />
          <span className="font-semibold text-[var(--color-text-primary)]">
            {title}
          </span>
          {badge !== undefined && badge > 0 && (
            <span
              style={{
                background: "var(--color-accent)",
                color: "var(--color-background)",
                padding: "var(--space-1) var(--space-2)",
                fontSize: "var(--text-xs)",
                fontWeight: "var(--font-semibold)",
                borderRadius: "var(--radius-lg)",
              }}
            >
              {badge}
            </span>
          )}
        </div>
        {isOpen ? (
          <ChevronDown className="w-5 h-5 text-[var(--color-text-tertiary)] transition-transform" />
        ) : (
          <ChevronRight className="w-5 h-5 text-[var(--color-text-tertiary)] transition-transform" />
        )}
      </button>
      {isOpen && <div className="workspace-section-content">{children}</div>}
    </div>
  );
}

// Todo list component with animations
function TodoList({ todos }: { todos: Todo[] }) {
  if (todos.length === 0) {
    return (
      <div
        className="empty-state"
        style={{
          paddingTop: "var(--space-8)",
          paddingBottom: "var(--space-8)",
          animation: "fadeIn 0.4s ease",
        }}
      >
        <ListTodo
          size={32}
          strokeWidth={1.5}
          style={{
            color: "var(--color-text-tertiary)",
            marginBottom: "var(--space-3)",
          }}
        />
        <p style={{ fontSize: "var(--text-sm)" }}>No tasks yet</p>
        <p className="text-xs mt-1">Research tasks will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {todos.map((todo) => (
        <div
          key={todo.id}
          className={`todo-item animate-fadeSlideIn ${
            todo.status === "completed"
              ? "todo-item-completed"
              : todo.status === "in_progress"
                ? "todo-item-inprogress"
                : "todo-item-pending"
          }`}
        >
          <span
            className={`${
              todo.status === "completed"
                ? "status-completed"
                : todo.status === "in_progress"
                  ? "status-inprogress"
                  : "status-pending"
            }`}
          >
            {todo.status === "completed" ? (
              <Check size={14} />
            ) : todo.status === "in_progress" ? (
              <CircleDot size={14} />
            ) : (
              <Circle size={14} />
            )}
          </span>
          <span className="text-sm">{todo.content}</span>
        </div>
      ))}
    </div>
  );
}

// File list component with click-to-view and animations
function FileList({
  files,
  onFileClick,
}: {
  files: ResearchFile[];
  onFileClick: (file: ResearchFile) => void;
}) {
  if (files.length === 0) {
    return (
      <div
        className="empty-state"
        style={{
          paddingTop: "var(--space-8)",
          paddingBottom: "var(--space-8)",
          animation: "fadeIn 0.4s ease",
        }}
      >
        <FileText
          size={32}
          strokeWidth={1.5}
          style={{
            color: "var(--color-text-tertiary)",
            marginBottom: "var(--space-3)",
          }}
        />
        <p style={{ fontSize: "var(--text-sm)" }}>No files yet</p>
        <p className="text-xs mt-1">Research artifacts will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {files.map((file, i) => (
        <div
          key={`${file.path}-${i}`}
          className="file-item animate-fadeSlideIn"
          onClick={() => onFileClick(file)}
        >
          <div className="flex items-center gap-3">
            <div className="file-item-icon">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--color-text-primary)]">
                {file.path.split("/").pop()}
              </p>
              <p className="text-xs text-[var(--color-text-tertiary)]">
                {file.path}
              </p>
            </div>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation(); // Don't trigger file view on download click
              downloadFile(file);
            }}
            className="p-2 rounded-lg hover:bg-[var(--color-glass-subtle)] transition-colors"
            aria-label="Download file"
            title="Download file"
          >
            <Download className="w-4 h-4 text-[var(--color-text-secondary)]" />
          </button>
        </div>
      ))}
    </div>
  );
}

// Source list component with error states and animations
function SourceList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) {
    return (
      <div
        className="empty-state"
        style={{
          paddingTop: "var(--space-8)",
          paddingBottom: "var(--space-8)",
          animation: "fadeIn 0.4s ease",
        }}
      >
        <Globe
          size={32}
          strokeWidth={1.5}
          style={{
            color: "var(--color-text-tertiary)",
            marginBottom: "var(--space-3)",
          }}
        />
        <p style={{ fontSize: "var(--text-sm)" }}>No sources yet</p>
        <p className="text-xs mt-1">Web sources will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sources.map((source, i) => (
        <div
          key={`${source.url}-${i}`}
          className={`file-item animate-fadeSlideIn ${source.status === "failed" ? "source-failed" : ""}`}
          title={
            source.status === "failed"
              ? "Failed to scrape this source"
              : undefined
          }
        >
          <div className="flex items-center gap-3">
            <span
              className={`source-indicator ${
                source.status === "scraped"
                  ? "status-completed"
                  : source.status === "failed"
                    ? ""
                    : "status-pending"
              }`}
              style={
                source.status === "failed"
                  ? { color: "var(--color-error)" }
                  : undefined
              }
            >
              {source.status === "scraped" ? (
                <Check size={14} style={{ color: "var(--color-success)" }} />
              ) : source.status === "failed" ? (
                <X size={14} style={{ color: "var(--color-error)" }} />
              ) : (
                <Circle size={14} />
              )}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-[var(--color-text-primary)] truncate">
                {source.title ||
                  (() => {
                    try {
                      return new URL(source.url).hostname;
                    } catch {
                      return source.url.slice(0, 40);
                    }
                  })()}
              </p>
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-[var(--color-text-tertiary)] hover:text-[var(--color-accent)] truncate block"
              >
                {source.url}
              </a>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Main Workspace component
export function Workspace({ state }: WorkspaceProps) {
  const { todos, files, sources } = state;
  const fileCount = files.length;
  const todoCount = todos.length;
  const sourceCount = sources.length;

  // State for file viewer modal
  const [selectedFile, setSelectedFile] = useState<ResearchFile | null>(null);

  return (
    <div className="workspace-panel p-6">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-[var(--color-text-primary)]">
          Workspace
        </h2>
        <p className="text-sm text-[var(--color-text-secondary)]">
          Research progress and artifacts
        </p>
      </div>

      <Section title="Research Plan" icon={ListTodo} badge={todoCount}>
        <TodoList todos={todos} />
      </Section>

      <Section title="Files" icon={FileText} badge={fileCount}>
        <FileList files={files} onFileClick={setSelectedFile} />
      </Section>

      <Section title="Sources" icon={Globe} badge={sourceCount}>
        <SourceList sources={sources} />
      </Section>

      {/* File Viewer Modal */}
      <FileViewerModal
        file={selectedFile}
        onClose={() => setSelectedFile(null)}
      />
    </div>
  );
}
