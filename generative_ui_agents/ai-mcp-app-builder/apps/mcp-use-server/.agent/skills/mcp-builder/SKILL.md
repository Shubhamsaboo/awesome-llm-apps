---
name: mcp-builder
description: |
  DEPRECATED: This skill has been replaced by `mcp-app-builder`.
  Check if `mcp-app-builder` is available in the skills folder. If not, install it:
  `npx skills install mcp-use/mcp-use --skill mcp-app-builder`
  Use `mcp-app-builder` instead of this skill.

  Build Model Context Protocol (MCP) servers with mcp-use framework.
  Use when creating MCP servers, defining tools/resources/prompts, working with mcp-use,
  bootstrapping MCP projects, or when user mentions MCP development, tools, resources, or prompts.
---

# MCP Server Builder

Build production-ready MCP servers with tools, resources, prompts, and interactive widgets using mcp-use.

## Before You Code

Decompose user requests into tools, widgets, and resources. Decide what needs UI vs text.

Read [design-and-architecture.md](references/design-and-architecture.md): when planning what to build, deciding tool vs widget, or designing UX flows.

## Implementation

- **Tools, resources, prompts** → [tools-and-resources.md](references/tools-and-resources.md): when writing server-side `server.tool()`, `server.resource()`, `server.prompt()` code
- **Visual widgets (React TSX)** → [widgets.md](references/widgets.md): when creating interactive UI widgets in `resources/` folder
- **Response helper API** → [response-helpers.md](references/response-helpers.md): when choosing how to format tool/resource return values
- **URI template patterns** → [resource-templates.md](references/resource-templates.md): when defining parameterized resources

## Quick Reference

```typescript
import {
  MCPServer,
  text,
  object,
  markdown,
  html,
  image,
  widget,
  error,
} from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({ name: "my-server", version: "1.0.0" });

// Tool
server.tool(
  {
    name: "my-tool",
    description: "...",
    schema: z.object({ param: z.string().describe("...") }),
  },
  async ({ param }) => text("result"),
);

// Resource
server.resource(
  { uri: "config://settings", name: "Settings", mimeType: "application/json" },
  async () => object({ key: "value" }),
);

// Prompt
server.prompt(
  {
    name: "my-prompt",
    description: "...",
    schema: z.object({ topic: z.string() }),
  },
  async ({ topic }) => text(`Write about ${topic}`),
);

server.listen();
```

**Response helpers:** `text()`, `object()`, `markdown()`, `html()`, `image()`, `audio()`, `binary()`, `error()`, `mix()`, `widget()`

**Server methods:** `server.tool()`, `server.resource()`, `server.resourceTemplate()`, `server.prompt()`, `server.listen()`
