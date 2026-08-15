/**
 * MCP Use Server — entry point
 *
 * HOW TO ADD A NEW MCP APP WIDGET
 * ─────────────────────────────────────────────────────────────────────────────
 * 1. CREATE  resources/<widget-name>/widget.tsx
 *      React component that receives props via useWidget().
 *      See resources/product-search-result/widget.tsx as a reference.
 *
 * 2. CREATE  tools/<tool-name>.ts
 *      Exports a register(server) function that calls server.tool().
 *      The tool handler returns widget({ props, output: text(...) }).
 *      See tools/product-search.ts as a reference.
 *
 * 3. IMPORT and CALL register() in the two marked sections below.
 *
 * Then run:  npm run dev   (auto-rebuilds widgets + restarts server on save)
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { MCPServer } from "mcp-use/server";

// ── Tool imports ──────────────────────────────────────────────────────────────
import { register as registerProductSearch } from "./tools/product-search";
// ADD NEW TOOL IMPORTS HERE

// ── Server config ─────────────────────────────────────────────────────────────
const server = new MCPServer({
  name: "mcp-use-server",
  title: "mcp-use-server",
  version: "1.0.0",
  description: "MCP server with MCP Apps integration",
  baseUrl: process.env.MCP_URL || "http://localhost:3109",
  favicon: "favicon.ico",
  websiteUrl: "https://mcp-use.com",
  icons: [{ src: "icon.svg", mimeType: "image/svg+xml", sizes: ["512x512"] }],
});

// ── Tool registrations ────────────────────────────────────────────────────────
registerProductSearch(server);
// ADD NEW TOOL REGISTRATIONS HERE

// ── Start ─────────────────────────────────────────────────────────────────────
server.listen(parseInt(process.env.PORT ?? "3109", 10)).then(() => {
  console.log(`Server running on port ${process.env.PORT ?? "3109"}`);
});
