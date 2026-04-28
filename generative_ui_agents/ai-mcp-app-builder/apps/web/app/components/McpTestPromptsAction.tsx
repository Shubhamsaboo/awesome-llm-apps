"use client";

import { useCopilotAction, useCopilotChat } from "@copilotkit/react-core";
import { TextMessage, Role } from "@copilotkit/runtime-client-gql";

export type McpTestPrompt = { label: string; message: string };

function parsePrompts(raw: unknown): McpTestPrompt[] {
  if (typeof raw !== "string" || !raw.trim()) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    const out: McpTestPrompt[] = [];
    for (const item of parsed) {
      if (!item || typeof item !== "object") continue;
      const o = item as Record<string, unknown>;
      const label = o.label;
      const message = o.message;
      if (typeof label !== "string" || typeof message !== "string") continue;
      const l = label.trim();
      const m = message.trim();
      if (!l || !m) continue;
      out.push({ label: l, message: m });
    }
    return out.slice(0, 8);
  } catch {
    return [];
  }
}

function TestPromptButtons({ prompts }: { prompts: McpTestPrompt[] }) {
  const { appendMessage } = useCopilotChat();

  if (prompts.length === 0) return null;

  return (
    <div
      className="mt-2 rounded-xl border border-emerald-100 bg-emerald-50/50 px-3 py-2.5"
      data-slot="mcp-test-prompts"
    >
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-emerald-800">
        Try the MCP server
      </p>
      <div className="flex flex-wrap gap-1.5">
        {prompts.map((p, i) => (
          <button
            key={`${p.label}-${i}`}
            type="button"
            onClick={() => {
              void appendMessage(
                new TextMessage({ content: p.message, role: Role.User }),
              );
            }}
            className="rounded-full border border-emerald-200/90 bg-white px-2.5 py-1 text-[11px] font-medium text-emerald-900 shadow-sm transition hover:bg-emerald-100"
          >
            {p.label}
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * Registers a frontend-only CopilotKit action: the agent calls `show_mcp_test_prompts`
 * with a JSON string of `{ label, message }[]`; the chat renders chips that append
 * the message in the same thread when clicked (Option C).
 */
export function RegisterMcpTestPromptsAction() {
  useCopilotAction({
    name: "show_mcp_test_prompts",
    description:
      "Show clickable test prompts in the chat so the user can try the connected MCP server. " +
      "Call after refresh_mcp_tools when tools are visible. " +
      'Pass prompts_json: a JSON array string like [{"label":"List tools","message":"List all tools on the MCP server"}].',
    parameters: [
      {
        name: "prompts_json",
        type: "string",
        description:
          'JSON array of objects with "label" (short chip) and "message" (full text sent on click). Max ~8 items.',
        required: true,
      },
    ],
    handler: async ({ prompts_json }) => {
      const n = parsePrompts(prompts_json).length;
      return n > 0
        ? `Showing ${n} test prompt chip(s). The user can click one to send it in chat.`
        : "No valid prompts in prompts_json — use a JSON array of {label, message}.";
    },
    render: ({ args }) => {
      const prompts = parsePrompts(args?.prompts_json);
      if (prompts.length === 0) {
        return (
          <p className="text-xs text-amber-800">
            Could not parse test prompts. Pass prompts_json as a JSON array of
            objects with label and message fields.
          </p>
        );
      }
      return <TestPromptButtons prompts={prompts} />;
    },
  });

  return null;
}
