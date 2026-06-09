"use client";

import { useState, useRef, useCallback } from "react";
import { useCopilotReadable } from "@copilotkit/react-core";
import { Upload } from "lucide-react";

export function PasteArea() {
  const [rawInput, setRawInput] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounter = useRef(0);

  useCopilotReadable({
    description:
      "Data the user has pasted into the paste area. Use this as the raw input when the user asks to structure or analyze data.",
    value: rawInput,
  });

  const handleFiles = useCallback(async (files: FileList) => {
    const results: string[] = [];
    for (const file of Array.from(files)) {
      const text = await file.text();
      results.push(`--- ${file.name} ---\n${text}`);
    }
    const content = results.join("\n\n");
    setRawInput((prev) => (prev ? prev + "\n\n" + content : content));
  }, []);

  return (
    <div
      className="h-full flex flex-col p-6 gap-4"
      onDragEnter={(e) => {
        e.preventDefault();
        dragCounter.current++;
        setIsDragging(true);
      }}
      onDragOver={(e) => e.preventDefault()}
      onDragLeave={() => {
        dragCounter.current--;
        if (dragCounter.current <= 0) {
          dragCounter.current = 0;
          setIsDragging(false);
        }
      }}
      onDrop={(e) => {
        e.preventDefault();
        dragCounter.current = 0;
        setIsDragging(false);
        if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
      }}
    >
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Data Input</h2>
        <div className="flex items-center gap-3">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-1.5 text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
          >
            <Upload className="h-3.5 w-3.5" />
            Upload file
          </button>
          {rawInput && (
            <button
              onClick={() => setRawInput("")}
              className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {!rawInput && !isDragging && (
        <div className="flex flex-wrap gap-2">
          {[
            {
              label: "Try sample CSV",
              data: "name,age,role\nAlice,32,Engineer\nBob,28,Designer\nCarol,45,Manager\nDave,36,Engineer\nEve,29,Analyst",
            },
            {
              label: "Try sample JSON",
              data: '[{"product":"Widget A","sales":1200,"region":"US"},{"product":"Widget B","sales":850,"region":"EU"},{"product":"Widget C","sales":2100,"region":"US"}]',
            },
          ].map((s) => (
            <button
              key={s.label}
              onClick={() => setRawInput(s.data)}
              className="px-3 py-1.5 text-xs rounded-full border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)] cursor-pointer transition-colors"
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      <div className="relative flex-1">
        {isDragging && (
          <div className="absolute inset-0 z-10 flex items-center justify-center rounded-lg border-2 border-dashed border-[var(--ring)] bg-[var(--accent)]/80">
            <span className="text-sm font-medium text-[var(--foreground)]">
              Drop files here
            </span>
          </div>
        )}
        <textarea
          value={rawInput}
          onChange={(e) => setRawInput(e.target.value)}
          placeholder="Paste your data here — CSV, JSON, markdown table, or plain text. Or drop a file. Then ask the agent to structure it."
          className="h-full w-full p-4 rounded-lg border border-[var(--border)] bg-[var(--card)] text-[var(--card-foreground)] text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
        />
      </div>

      {rawInput && (
        <div className="text-xs text-[var(--muted-foreground)]">
          {rawInput.split("\n").filter((l) => l.trim()).length} lines
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".csv,.json,.txt,.md,.tsv,.xml,.yaml,.yml"
        className="hidden"
        onChange={(e) => {
          if (e.target.files) handleFiles(e.target.files);
          e.target.value = "";
        }}
      />
    </div>
  );
}
