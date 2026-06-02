import { Hono } from "hono";
import { serve } from "@hono/node-server";
import { cors } from "hono/cors";
import { CopilotRuntime, createCopilotEndpointSingleRoute } from "@copilotkit/runtime/v2";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";
import { isShuttingDown, onShutdown } from "./resilience.js";

const agentHost = process.env.LANGGRAPH_DEPLOYMENT_URL || "http://localhost:8123";
const agentUrl = agentHost.startsWith("http") ? agentHost : `http://${agentHost}`;

const runtime = new CopilotRuntime({
  agents: {
    default: new LangGraphHttpAgent({
      url: agentUrl,
    }),
  },
});

const copilotApp = createCopilotEndpointSingleRoute({
  runtime,
  basePath: "/api/copilotkit",
});

const app = new Hono();
app.use("/*", cors());

// Reject new requests during graceful OOM shutdown so in-flight ones can drain
app.use("/*", async (c, next) => {
  if (isShuttingDown()) {
    c.header("Connection", "close");
    c.header("Retry-After", "5");
    return c.text("Service restarting", 503);
  }
  return next();
});

app.route("/", copilotApp as any);

const port = Number(process.env.PORT || 4000);
let server: ReturnType<typeof serve> | undefined;
server = serve({ fetch: app.fetch, port });
onShutdown(() => server?.close());
console.log(`Runtime server listening at http://localhost:${port}/api/copilotkit`);
