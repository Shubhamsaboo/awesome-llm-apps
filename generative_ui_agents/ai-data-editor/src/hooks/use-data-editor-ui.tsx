"use client";

import { useDefaultRenderTool } from "@copilotkit/react-core/v2";
import { useMutationConfirmation } from "./use-mutation-confirmation";
import { useToolRendering } from "./use-tool-rendering";

const HIDDEN_TOOLS = [
  "render_a2ui",
  "generate_a2ui",
  "log_a2ui_event",
  "confirm_mutation",
];

export function useDataEditorUI() {
  useMutationConfirmation();
  useToolRendering();

  useDefaultRenderTool({
    render: ({ name, status }) => {
      if (HIDDEN_TOOLS.includes(name)) return <></>;

      const statusLabel =
        status === "executing"
          ? "Running..."
          : status === "complete"
            ? "Done"
            : "Preparing...";

      const toolLabel = name
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());

      return (
        <div className="flex items-center gap-2 text-xs text-[var(--muted-foreground)] py-1">
          <div
            className={`h-1.5 w-1.5 rounded-full ${
              status === "executing"
                ? "bg-blue-500 animate-pulse"
                : status === "complete"
                  ? "bg-green-500"
                  : "bg-gray-400"
            }`}
          />
          <span>
            {toolLabel}: {statusLabel}
          </span>
        </div>
      );
    },
  });
}
