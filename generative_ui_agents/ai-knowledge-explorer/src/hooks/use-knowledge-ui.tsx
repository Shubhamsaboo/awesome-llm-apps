"use client";

import { useDefaultRenderTool } from "@copilotkit/react-core/v2";
import { ToolReasoning } from "@/components/ToolReasoning";

export function useKnowledgeUI() {
  useDefaultRenderTool({
    render: ({ name, status, parameters }) => {
      return <ToolReasoning name={name} status={status} args={parameters} />;
    },
  });
}
