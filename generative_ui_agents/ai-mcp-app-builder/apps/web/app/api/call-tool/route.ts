import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { NextRequest, NextResponse } from "next/server";

async function connectClient(url: string) {
  try {
    const client = new Client(
      { name: "mcp-studio-call-tool", version: "1.0.0" },
      { capabilities: {} },
    );
    await client.connect(new StreamableHTTPClientTransport(new URL(url)));
    return client;
  } catch {
    const client = new Client(
      { name: "mcp-studio-call-tool", version: "1.0.0" },
      { capabilities: {} },
    );
    await client.connect(new SSEClientTransport(new URL(url)));
    return client;
  }
}

export async function POST(req: NextRequest) {
  let body: {
    endpoint: string;
    toolName: string;
    args?: Record<string, unknown>;
  };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { endpoint, toolName, args = {} } = body;
  if (!endpoint || !toolName) {
    return NextResponse.json(
      { error: "Missing endpoint or toolName" },
      { status: 400 },
    );
  }

  let client: Client | null = null;
  try {
    client = await connectClient(endpoint);
    const result = await client.callTool({ name: toolName, arguments: args });
    await client.close();

    // Extract structuredContent — this is the widget output props
    const structuredContent =
      (result as Record<string, unknown>).structuredContent ?? null;

    return NextResponse.json({ result, structuredContent });
  } catch (err) {
    try {
      await client?.close();
    } catch {
      /* ignore */
    }
    return NextResponse.json(
      { error: err instanceof Error ? err.message : String(err) },
      { status: 502 },
    );
  }
}
