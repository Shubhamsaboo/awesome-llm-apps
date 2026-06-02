"use client";

/**
 * Test panel: suggested prompts and short instructions so users can try MCP tools.
 * Tool calls from the assistant will appear in the chat thread when they run.
 */
export function ToolCallPreview() {
  const suggestions = [
    "Show me a rotating cube with Three.js",
    "Use learn_threejs to get Three.js documentation and examples",
    "Create a simple 3D scene with a sphere and lighting",
  ];

  return (
    <div className="flex flex-col gap-3">
      <div>
        <h2 className="text-sm font-semibold text-slate-900">Test MCP Tools</h2>
        <p className="mt-1 text-xs leading-relaxed text-slate-500">
          Use the chat to trigger tool calls. This panel gives you starter
          prompts while the conversation thread shows actual tool invocations
          and results.
        </p>
      </div>

      <div className="space-y-2">
        {suggestions.map((s, i) => (
          <div
            key={i}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs leading-relaxed text-slate-700 shadow-sm"
          >
            <span className="mr-2 inline-flex h-5 w-5 items-center justify-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-600">
              {i + 1}
            </span>
            <span>&quot;{s}&quot;</span>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-blue-100 bg-blue-50/70 p-3 text-xs text-blue-900">
        <p className="font-medium">Tip</p>
        <p className="mt-1 leading-relaxed text-blue-800">
          Make sure the Three.js MCP server is running (for example{" "}
          <code className="rounded bg-white px-1 py-0.5">pnpm dev</code> from
          the repo root) before testing `show_threejs_scene`.
        </p>
      </div>
    </div>
  );
}
