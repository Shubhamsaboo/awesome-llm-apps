"use client";

import { useCallback, useState } from "react";
import { Upload, FileText, AlertCircle, Sparkles } from "lucide-react";
import { EXAMPLE_FILES } from "@/lib/example-content";

const MAX_FILES = 10;
const MAX_FILE_SIZE = 10 * 1024;
const MAX_TOTAL_SIZE = 50 * 1024;
const ALLOWED_EXTENSIONS = [".txt", ".md", ".json", ".csv"];

interface FileDropZoneProps {
  onFilesReady: (files: { name: string; content: string }[]) => void;
  hasGraph: boolean;
}

export function FileDropZone({ onFilesReady, hasGraph }: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processFiles = useCallback(
    async (fileList: FileList) => {
      setError(null);
      const files = Array.from(fileList);

      const valid = files.filter((f) =>
        ALLOWED_EXTENSIONS.some((ext) => f.name.toLowerCase().endsWith(ext)),
      );
      if (valid.length === 0) {
        setError("No supported files. Use .txt, .md, .json, or .csv");
        return;
      }
      if (valid.length > MAX_FILES) {
        setError(`Max ${MAX_FILES} files per upload.`);
        return;
      }

      const results: { name: string; content: string }[] = [];
      let totalSize = 0;

      for (const file of valid) {
        const text = await file.text();
        const content =
          text.length > MAX_FILE_SIZE
            ? text.slice(0, MAX_FILE_SIZE) + "\n\n[truncated]"
            : text;
        totalSize += content.length;
        if (totalSize > MAX_TOTAL_SIZE) {
          setError(`Total content exceeds ${MAX_TOTAL_SIZE / 1024}KB limit.`);
          return;
        }
        results.push({ name: file.name, content });
      }

      onFilesReady(results);
    },
    [onFilesReady],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (e.dataTransfer.files.length > 0) {
        processFiles(e.dataTransfer.files);
      }
    },
    [processFiles],
  );

  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-8 transition-colors ${
        isDragging
          ? "border-[var(--ring)] bg-[var(--accent)]"
          : "border-[var(--border)] bg-[var(--card)]"
      } ${hasGraph ? "h-auto" : "h-full"}`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
    >
      <Upload
        className="h-10 w-10 text-[var(--muted-foreground)]"
        strokeWidth={1.5}
      />
      <div className="text-center">
        <p className="text-sm font-medium text-[var(--foreground)]">
          Drop files here to explore
        </p>
        <p className="mt-1 text-xs text-[var(--muted-foreground)]">
          .txt, .md, .json, .csv — max 10 files, 50KB total
        </p>
      </div>
      <label className="cursor-pointer rounded-lg bg-[var(--secondary)] px-4 py-2 text-sm font-medium text-[var(--secondary-foreground)] transition-colors hover:bg-[var(--muted)]">
        Browse files
        <input
          type="file"
          multiple
          accept=".txt,.md,.json,.csv"
          className="hidden"
          onChange={(e) => {
            if (e.target.files) processFiles(e.target.files);
          }}
        />
      </label>
      {!hasGraph && (
        <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
          <span>or</span>
          <button
            onClick={() => onFilesReady(EXAMPLE_FILES)}
            className="inline-flex items-center gap-1 rounded-lg bg-[var(--accent)] px-3 py-1.5 text-xs font-medium text-[var(--accent-foreground)] transition-colors hover:opacity-80"
          >
            <Sparkles className="h-3 w-3" />
            Load example content
          </button>
        </div>
      )}
      {error && (
        <div className="flex items-center gap-2 text-xs text-red-500">
          <AlertCircle className="h-3 w-3" />
          {error}
        </div>
      )}
    </div>
  );
}
