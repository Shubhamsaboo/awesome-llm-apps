"use client";

import { useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import { X, Download, FileText } from "lucide-react";
import type { ResearchFile } from "@/types/research";

/**
 * FileViewerModal - Modal for viewing file content with markdown rendering.
 *
 * Features:
 * - Markdown rendering via react-markdown with typography styles
 * - Download button to save file content
 * - Closes on backdrop click, X button, or Escape key
 * - Responsive sizing with scrollable content
 */

interface FileViewerModalProps {
  file: ResearchFile | null;
  onClose: () => void;
}

export function FileViewerModal({ file, onClose }: FileViewerModalProps) {
  // Handle Escape key to close modal
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  useEffect(() => {
    if (file) {
      document.addEventListener("keydown", handleKeyDown);
      // Prevent body scroll when modal is open
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [file, handleKeyDown]);

  // Don't render if no file selected
  if (!file) return null;

  // Extract filename from path
  const filename = file.path.split("/").pop() || file.path;

  // Download file content
  const handleDownload = () => {
    const blob = new Blob([file.content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop with blur */}
      <div
        className="absolute inset-0 bg-black/30 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal container */}
      <div
        className="relative max-w-3xl w-full max-h-[85vh] flex flex-col"
        style={{
          background: "var(--color-glass-elevated)",
          backdropFilter: "blur(20px)",
          WebkitBackdropFilter: "blur(20px)",
          padding: 0,
          borderRadius: "var(--radius-2xl)",
          border: "1px solid var(--color-border-glass)",
          boxShadow: "0 4px 30px rgba(0, 0, 0, 0.1)",
        }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="file-viewer-title"
      >
        {/* Header */}
        <div
          style={{
            padding:
              "var(--space-6) var(--space-6) var(--space-4) var(--space-6)",
          }}
          className="flex items-center justify-between border-b border-[var(--color-border-glass)]"
        >
          <div className="flex items-center gap-3">
            <div
              style={{
                background:
                  "linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-dark) 100%)",
                padding: "var(--space-3)",
                borderRadius: "var(--radius-md)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <FileText
                style={{ width: "20px", height: "20px", color: "white" }}
              />
            </div>
            <h2
              id="file-viewer-title"
              style={{
                fontSize: "var(--text-2xl)",
                fontWeight: "var(--font-bold)",
                fontFamily: "var(--font-display)",
                color: "var(--color-text-primary)",
              }}
              className="truncate max-w-md"
            >
              {filename}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleDownload}
              className="p-2 hover:bg-[var(--color-glass-subtle)] rounded-lg transition-colors"
              aria-label="Download file"
              title="Download file"
            >
              <Download className="w-5 h-5 text-[var(--color-text-secondary)]" />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-[var(--color-glass-subtle)] rounded-lg transition-colors"
              aria-label="Close modal"
              title="Close (Escape)"
            >
              <X className="w-5 h-5 text-[var(--color-text-secondary)]" />
            </button>
          </div>
        </div>

        {/* Scrollable content with markdown rendering */}
        <div
          className="flex-1 overflow-y-auto"
          style={{ padding: "var(--space-8)" }}
        >
          <div className="prose prose-sm prose-slate max-w-none">
            <ReactMarkdown>{file.content}</ReactMarkdown>
          </div>
        </div>

        {/* Footer with file path */}
        <div
          style={{ padding: "var(--space-3) var(--space-6)" }}
          className="border-t border-[var(--color-border-glass)]"
        >
          <code
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "var(--text-sm)",
              color: "var(--color-text-tertiary)",
            }}
          >
            {file.path}
          </code>
        </div>
      </div>
    </div>
  );
}
