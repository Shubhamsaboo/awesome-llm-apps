/**
 * Docker-specific route override.
 * In Docker, the agent is served via AG-UI (not LangGraph Platform)
 * because langgraph-cli dev requires Docker-in-Docker.
 * The original route.ts (using LangGraphAgent) is preserved unchanged.
 */
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

const agentUrl = process.env.AGENT_URL || "http://localhost:8123";

const defaultAgent = new HttpAgent({
  url: `${agentUrl}/`,
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    endpoint: "/api/copilotkit",
    serviceAdapter: new ExperimentalEmptyAdapter(),
    runtime: new CopilotRuntime({
      agents: { default: defaultAgent },
    }),
  });

  return handleRequest(req);
};
