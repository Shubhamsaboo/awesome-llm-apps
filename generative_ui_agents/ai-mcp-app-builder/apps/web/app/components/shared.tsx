"use client";

import { useState } from "react";

export function LoadingSpinner() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-slate-400">
      <svg className="h-6 w-6 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      <p className="text-xs">Connecting to MCP servers&hellip;</p>
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex items-center justify-center py-12">
      <p className="text-xs text-slate-400">{message}</p>
    </div>
  );
}

export function ErrorBanner({
  errors,
}: {
  errors: { server: string; error: string }[];
}) {
  if (errors.length === 0) return null;
  return (
    <div className="space-y-1.5">
      {errors.map((e) => (
        <div
          key={e.server}
          className="rounded-xl border border-red-200 bg-red-50/70 p-2.5 text-xs text-red-800"
        >
          <span className="font-medium">{e.server}:</span> {e.error}
        </div>
      ))}
    </div>
  );
}

export function CreateToolForm({
  onSubmit,
  onCancel,
}: {
  onSubmit: (name: string, description: string) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!name.trim()) return;
        onSubmit(name.trim(), desc.trim() || `A tool called ${name.trim()}`);
        setName("");
        setDesc("");
      }}
      className="space-y-2 rounded-xl border border-slate-200 bg-slate-50 p-3"
    >
      <input
        type="text"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Tool name (e.g. show_chart)"
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
        required
      />
      <input
        type="text"
        value={desc}
        onChange={(e) => setDesc(e.target.value)}
        placeholder="Description (optional)"
        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
      />
      <div className="flex gap-2">
        <button
          type="submit"
          className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800"
        >
          Create
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
