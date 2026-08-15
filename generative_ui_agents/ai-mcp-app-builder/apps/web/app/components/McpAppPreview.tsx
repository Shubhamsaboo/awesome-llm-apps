"use client";

import { useState, useRef, useEffect } from "react";

export function McpAppPreview({
  toolName,
  toolDescription,
  inputSchema,
  htmlSource,
  hasUI,
  previewData,
  height = "300px",
}: {
  toolName: string;
  toolDescription: string;
  inputSchema: Record<string, unknown>;
  htmlSource: string | null;
  hasUI: boolean;
  previewData: Record<string, unknown>;
  height?: string;
}) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [status, setStatus] = useState<
    "loading" | "connecting" | "ready" | "error"
  >("loading");

  useEffect(() => {
    if (!htmlSource) return;
    setStatus("connecting");
    let disposed = false;

    const handleMessage = (event: MessageEvent) => {
      if (disposed) return;
      if (event.source !== iframeRef.current?.contentWindow) return;

      const msg = event.data;
      if (!msg || msg.jsonrpc !== "2.0") return;

      const iframe = iframeRef.current?.contentWindow;
      if (!iframe) return;

      if (msg.method === "ui/initialize" && msg.id !== undefined) {
        iframe.postMessage(
          {
            jsonrpc: "2.0",
            id: msg.id,
            result: {
              protocolVersion: "2025-11-21",
              hostInfo: { name: "mcp-studio-preview", version: "1.0.0" },
              hostCapabilities: { tools: {} },
              hostContext: {
                toolInfo: {
                  tool: {
                    name: toolName,
                    description: toolDescription,
                    inputSchema,
                  },
                },
                theme: "light",
                displayMode: "fullscreen",
                containerDimensions: {
                  width: 800,
                  maxWidth: 1200,
                  height: 600,
                  maxHeight: 900,
                },
              },
            },
          },
          "*",
        );
        return;
      }

      if (msg.method === "ui/notifications/initialized") {
        setStatus("ready");
        const hasPreviewData = Object.keys(previewData).length > 0;
        iframe.postMessage(
          {
            jsonrpc: "2.0",
            method: "ui/notifications/tool-input",
            params: {
              toolCallId: "preview-mock-001",
              name: toolName,
              arguments: previewData,
            },
          },
          "*",
        );
        if (hasPreviewData) {
          setTimeout(() => {
            if (disposed) return;
            iframe.postMessage(
              {
                jsonrpc: "2.0",
                method: "ui/notifications/tool-result",
                params: {
                  toolCallId: "preview-mock-001",
                  name: toolName,
                  result: {
                    content: [
                      { type: "text", text: JSON.stringify(previewData) },
                    ],
                    structuredContent: previewData,
                  },
                },
              },
              "*",
            );
          }, 500);
        }
        return;
      }

      if (msg.method === "tools/call" && msg.id !== undefined) {
        iframe.postMessage(
          {
            jsonrpc: "2.0",
            id: msg.id,
            result: {
              content: [{ type: "text", text: "Mock result" }],
              isError: false,
            },
          },
          "*",
        );
        return;
      }

      if (msg.method === "tools/list" && msg.id !== undefined) {
        iframe.postMessage(
          { jsonrpc: "2.0", id: msg.id, result: { tools: [] } },
          "*",
        );
        return;
      }

      if (msg.id !== undefined && msg.method) {
        iframe.postMessage({ jsonrpc: "2.0", id: msg.id, result: {} }, "*");
      }
    };

    window.addEventListener("message", handleMessage);
    return () => {
      disposed = true;
      window.removeEventListener("message", handleMessage);
    };
  }, [htmlSource, toolName, toolDescription, inputSchema, previewData]);

  if (!htmlSource) {
    return (
      <div className="flex items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-6">
        <p className="text-xs text-slate-400">
          {hasUI
            ? "Loading UI HTML from server…"
            : "No UI available for this tool"}
        </p>
      </div>
    );
  }

  return (
    <div
      className="relative w-full overflow-hidden rounded-xl border border-slate-200"
      style={{ height }}
    >
      {status !== "ready" && (
        <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 bg-white/90">
          <svg
            className="h-5 w-5 animate-spin text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <p className="text-[11px] text-slate-400">
            {status === "loading"
              ? "Loading preview…"
              : "Initializing MCP app…"}
          </p>
        </div>
      )}
      <iframe
        ref={iframeRef}
        srcDoc={htmlSource}
        className="h-full w-full border-0"
        sandbox="allow-scripts allow-same-origin"
        title={`Preview: ${toolName}`}
      />
    </div>
  );
}
