"use client";

import { useAgentContext } from "@copilotkit/react-core/v2";

export function useDataEditorContext(context: {
  selectedRowId: number | null;
  expandedRowId: number | null;
  currentView: string;
  rowCount: number;
}) {
  useAgentContext({
    description:
      "Current state of the data editor UI — what the user is viewing and has selected",
    value: context,
  });
}
