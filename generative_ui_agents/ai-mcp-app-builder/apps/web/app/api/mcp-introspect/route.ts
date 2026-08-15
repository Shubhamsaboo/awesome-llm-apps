import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { NextRequest, NextResponse } from "next/server";

/** Listing tools + fetching widget HTML can be slow; allow up to 5 min. */
export const maxDuration = 300;

/** Shape returned for each discovered tool. */
export interface IntrospectedTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  hasUI: boolean;
  uiResourceUri: string | null;
  uiHtml: string | null;
  uiPreviewData: Record<string, unknown> | null;
  _meta: Record<string, unknown> | null;
}

async function connectClient(url: string) {
  console.log(`[mcp-introspect] Connecting to ${url}...`);

  // Try Streamable HTTP first, fall back to SSE
  try {
    const client = new Client(
      { name: "mcp-studio-introspect", version: "1.0.0" },
      { capabilities: {} },
    );
    const transport = new StreamableHTTPClientTransport(new URL(url));
    await client.connect(transport);
    console.log(`[mcp-introspect] Connected via StreamableHTTP to ${url}`);
    return client;
  } catch (err) {
    console.log(
      `[mcp-introspect] StreamableHTTP failed for ${url}:`,
      (err as Error).message,
    );
    try {
      const client = new Client(
        { name: "mcp-studio-introspect", version: "1.0.0" },
        { capabilities: {} },
      );
      const transport = new SSEClientTransport(new URL(url));
      await client.connect(transport);
      console.log(`[mcp-introspect] Connected via SSE to ${url}`);
      return client;
    } catch (sseErr) {
      console.error(
        `[mcp-introspect] SSE also failed for ${url}:`,
        (sseErr as Error).message,
      );
      throw sseErr;
    }
  }
}

export async function POST(req: NextRequest) {
  let body: { endpoint: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { endpoint } = body;
  if (!endpoint) {
    return NextResponse.json(
      { error: "Missing `endpoint` field" },
      { status: 400 },
    );
  }

  console.log(`[mcp-introspect] POST received for endpoint: ${endpoint}`);
  let client: Client | null = null;
  try {
    client = await connectClient(endpoint);

    // 1. List all tools
    console.log(`[mcp-introspect] Calling listTools()...`);
    const allTools: IntrospectedTool[] = [];
    let cursor: string | undefined;
    do {
      const res = await client.listTools(cursor ? { cursor } : undefined);
      console.log(
        `[mcp-introspect] listTools returned ${res.tools.length} tools`,
      );
      for (const t of res.tools) {
        const meta = (t as Record<string, unknown>)._meta as
          | Record<string, unknown>
          | undefined;
        const uiResourceUri = (meta?.["ui/resourceUri"] as string) ?? null;
        const uiPreviewData =
          (meta?.["ui/previewData"] as Record<string, unknown>) ?? null;
        allTools.push({
          name: t.name,
          description: t.description ?? "",
          inputSchema: t.inputSchema as Record<string, unknown>,
          hasUI: uiResourceUri !== null,
          uiResourceUri,
          uiHtml: null, // populated below
          uiPreviewData,
          _meta: meta ?? null,
        });
      }
      cursor = res.nextCursor;
    } while (cursor);

    console.log(
      `[mcp-introspect] Discovered tools:`,
      allTools.map(
        (t) =>
          `${t.name} (UI: ${t.hasUI}, previewData: ${t.uiPreviewData !== null})`,
      ),
    );

    // 2. For tools with UI, fetch the resource HTML
    for (const tool of allTools) {
      if (tool.uiResourceUri) {
        console.log(
          `[mcp-introspect] Reading resource for ${tool.name}: ${tool.uiResourceUri}`,
        );
        try {
          const res = await client.readResource({
            uri: tool.uiResourceUri,
          });
          const textContent = res.contents.find(
            (c) => typeof (c as Record<string, unknown>).text === "string",
          );
          if (textContent) {
            let html = (textContent as Record<string, unknown>).text as string;
            // Fix widget HTML for CSP-safe rendering in sandboxed iframes:
            // 1. Extract internal origin from <base> tag (e.g. http://localhost:3109)
            // 2. Strip <base> tag — blocked by CSP base-uri 'self' and unnecessary
            //    when JS/CSS are inlined (--inline build) and images use __mcpPublicUrl
            // 3. Rewrite remaining internal origin refs to the external endpoint origin
            //    (for window.__mcpPublicUrl, window.__getFile, etc.)
            const serverOrigin = new URL(endpoint).origin;
            const baseTagMatch = html.match(/<base\s+href="([^"]*)"[^>]*>/i);
            if (baseTagMatch) {
              try {
                const internalOrigin = new URL(baseTagMatch[1]).origin;
                // Strip <base> tag (violates CSP base-uri 'self')
                html = html.replace(/<base\b[^>]*>/gi, "");
                // Rewrite all remaining internal origin references
                if (internalOrigin !== serverOrigin) {
                  html = html.replaceAll(internalOrigin, serverOrigin);
                }
              } catch {
                /* ignore malformed base href */
              }
            }
            tool.uiHtml = html;
            console.log(
              `[mcp-introspect] UI HTML for ${tool.name} (${tool.uiHtml.length} chars)`,
            );
          } else {
            console.log(
              `[mcp-introspect] No text content found in resource for ${tool.name}. Contents:`,
              JSON.stringify(res.contents).slice(0, 300),
            );
          }
        } catch (e) {
          console.warn(`Failed to read resource ${tool.uiResourceUri}:`, e);
        }
      }
    }

    // 3. Also list raw resources
    const allResources: Array<{
      uri: string;
      name: string;
      mimeType?: string;
    }> = [];
    let rCursor: string | undefined;
    do {
      const res = await client.listResources(
        rCursor ? { cursor: rCursor } : undefined,
      );
      for (const r of res.resources) {
        allResources.push({
          uri: r.uri,
          name: r.name ?? r.uri,
          mimeType: r.mimeType,
        });
      }
      rCursor = res.nextCursor;
    } while (rCursor);

    await client.close();

    console.log(
      `[mcp-introspect] Done. ${allTools.length} tools, ${allResources.length} resources`,
    );
    return NextResponse.json({ tools: allTools, resources: allResources });
  } catch (err) {
    console.error(`[mcp-introspect] Error for ${endpoint}:`, err);
    try {
      await client?.close();
    } catch {
      /* ignore */
    }
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
