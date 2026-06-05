"use client";

import { z } from "zod";
import {
  useFrontendTool,
  useDefaultRenderTool,
} from "@copilotkit/react-core/v2";
import { ToolReasoning } from "@/components/ToolReasoning";

export function useKnowledgeUI() {
  const ignoredTools = ["render_a2ui", "generate_a2ui", "log_a2ui_event"];

  useDefaultRenderTool({
    render: ({ name, status, parameters }) => {
      if (ignoredTools.includes(name)) return <></>;
      return <ToolReasoning name={name} status={status} args={parameters} />;
    },
  });
}
