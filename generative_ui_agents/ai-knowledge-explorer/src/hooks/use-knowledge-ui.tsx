"use client";

import { useDefaultRenderTool } from "@copilotkit/react-core/v2";
import { ToolReasoning } from "@/components/ToolReasoning";

export function useKnowledgeUI() {
  useDefaultRenderTool({
    render: ({ name, status }) => {
      return <ToolReasoning name={name} status={status} />;
    },
  });
}
