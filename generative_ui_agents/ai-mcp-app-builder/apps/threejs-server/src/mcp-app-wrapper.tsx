/**
 * Three.js Widget - MCP App Wrapper
 *
 * Generic wrapper that handles MCP App connection and passes all relevant
 * props to the actual widget component.
 */
import type { App, McpUiHostContext } from "@modelcontextprotocol/ext-apps";
import { useApp } from "@modelcontextprotocol/ext-apps/react";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { StrictMode, useState, useCallback, useEffect } from "react";
import { createRoot } from "react-dom/client";
import ThreeJSApp from "./threejs-app.tsx";
import "./global.css";

// =============================================================================
// Types
// =============================================================================

/**
 * Props passed to the widget component.
 * This interface can be reused for other widgets.
 */
export interface WidgetProps<TToolInput = Record<string, unknown>> {
  /** Complete tool input (after streaming finishes) */
  toolInputs: TToolInput | null;
  /** Partial tool input (during streaming) */
  toolInputsPartial: TToolInput | null;
  /** Tool execution result from the server */
  toolResult: CallToolResult | null;
  /** Host context (theme, dimensions, locale, etc.) */
  hostContext: McpUiHostContext | null;
  /** Call a tool on the MCP server */
  callServerTool: App["callServerTool"];
  /** Send a message to the host's chat */
  sendMessage: App["sendMessage"];
  /** Request the host to open a URL */
  openLink: App["openLink"];
  /** Send log messages to the host */
  sendLog: App["sendLog"];
}

// =============================================================================
// MCP App Wrapper
// =============================================================================

function McpAppWrapper() {
  const [toolInputs, setToolInputs] = useState<Record<string, unknown> | null>(
    null,
  );
  const [toolInputsPartial, setToolInputsPartial] = useState<Record<
    string,
    unknown
  > | null>(null);
  const [toolResult, setToolResult] = useState<CallToolResult | null>(null);
  const [hostContext, setHostContext] = useState<McpUiHostContext | null>(null);

  const { app, error } = useApp({
    appInfo: { name: "Three.js Widget", version: "1.0.0" },
    capabilities: {},
    onAppCreated: (app) => {
      // Complete tool input (streaming finished)
      app.ontoolinput = (params) => {
        setToolInputs(params.arguments as Record<string, unknown>);
        setToolInputsPartial(null);
      };
      // Partial tool input (streaming in progress)
      app.ontoolinputpartial = (params) => {
        setToolInputsPartial(params.arguments as Record<string, unknown>);
      };
      // Tool execution result
      app.ontoolresult = (params) => {
        setToolResult(params as CallToolResult);
      };
      // Host context changes (theme, dimensions, etc.)
      app.onhostcontextchanged = (params) => {
        setHostContext((prev) => ({ ...prev, ...params }));
      };
    },
  });

  // Get initial host context after connection
  useEffect(() => {
    if (app) {
      const ctx = app.getHostContext();
      if (ctx) {
        setHostContext(ctx);
      }
    }
  }, [app]);

  // Memoized callbacks that forward to app methods
  const callServerTool = useCallback<App["callServerTool"]>(
    (params, options) => app!.callServerTool(params, options),
    [app],
  );
  const sendMessage = useCallback<App["sendMessage"]>(
    (params, options) => app!.sendMessage(params, options),
    [app],
  );
  const openLink = useCallback<App["openLink"]>(
    (params, options) => app!.openLink(params, options),
    [app],
  );
  const sendLog = useCallback<App["sendLog"]>(
    (params) => app!.sendLog(params),
    [app],
  );

  if (error) {
    return <div className="error">Error: {error.message}</div>;
  }

  if (!app) {
    return <div className="loading">Connecting...</div>;
  }

  return (
    <ThreeJSApp
      toolInputs={toolInputs}
      toolInputsPartial={toolInputsPartial}
      toolResult={toolResult}
      hostContext={hostContext}
      callServerTool={callServerTool}
      sendMessage={sendMessage}
      openLink={openLink}
      sendLog={sendLog}
    />
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <McpAppWrapper />
  </StrictMode>,
);
