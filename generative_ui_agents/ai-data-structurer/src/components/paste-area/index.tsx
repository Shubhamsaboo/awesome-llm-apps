"use client";

import { useState } from "react";
import { useCopilotReadable } from "@copilotkit/react-core";

export function PasteArea() {
  const [rawInput, setRawInput] = useState("");

  useCopilotReadable({
    description:
      "Data the user has pasted into the paste area. Use this as the raw input when the user asks to structure or analyze data.",
    value: rawInput,
  });

  return (
    <div className="h-full flex flex-col p-6 gap-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Data Input</h2>
        {rawInput && (
          <button
            onClick={() => setRawInput("")}
            className="text-sm text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
          >
            Clear
          </button>
        )}
      </div>
      <textarea
        value={rawInput}
        onChange={(e) => setRawInput(e.target.value)}
        placeholder="Paste your data here — CSV, JSON, markdown table, or plain text. Then ask the agent to structure it."
        className="flex-1 w-full p-4 rounded-lg border border-[var(--border)] bg-[var(--card)] text-[var(--card-foreground)] text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-[var(--ring)]"
      />
      {rawInput && (
        <div className="text-xs text-[var(--muted-foreground)]">
          {rawInput.split("\n").filter((l) => l.trim()).length} lines pasted
        </div>
      )}
    </div>
  );
}
