# Tools, Resources, and Prompts

Server-side implementation patterns for `server.tool()`, `server.resource()`, and `server.prompt()`.

## Tools

Tools are actions the AI model can call.

### Basic Tool

```typescript
import { MCPServer, text, object, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.tool(
  {
    name: "translate-text",
    description: "Translate text between languages",
    schema: z.object({
      text: z.string().describe("Text to translate"),
      targetLanguage: z
        .string()
        .describe("Target language (e.g., 'Spanish', 'French')"),
      sourceLanguage: z
        .string()
        .optional()
        .describe("Source language (auto-detected if omitted)"),
    }),
  },
  async ({ text: inputText, targetLanguage, sourceLanguage }) => {
    // Your logic here
    const translated = await translateAPI(
      inputText,
      targetLanguage,
      sourceLanguage,
    );
    return text(`${translated}`);
  },
);
```

### Tool with Widget

When a tool returns visual UI, add `widget` config and return `widget()`:

```typescript
import { widget, text } from "mcp-use/server";

server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
    widget: {
      name: "weather-display", // Must match resources/weather-display.tsx
      invoking: "Fetching weather...",
      invoked: "Weather loaded",
    },
  },
  async ({ city }) => {
    const data = getWeather(city);
    return widget({
      props: { city, temp: data.temp, conditions: data.conditions }, // Sent to widget UI
      output: text(`Weather in ${city}: ${data.temp}°C, ${data.conditions}`), // Model sees this
    });
  },
);
```

### Tool Annotations

Declare the nature of your tool:

```typescript
server.tool(
  {
    name: "delete-item",
    description: "Delete an item permanently",
    schema: z.object({ id: z.string().describe("Item ID") }),
    annotations: {
      destructiveHint: true, // Deletes or overwrites data
      readOnlyHint: false, // Has side effects
      openWorldHint: false, // Stays within user's account
    },
  },
  async ({ id }) => {
    await deleteItem(id);
    return text(`Item ${id} deleted.`);
  },
);
```

### Tool Context

The second parameter to tool callbacks provides advanced capabilities:

```typescript
server.tool(
  { name: "process-data", schema: z.object({ data: z.string() }) },
  async ({ data }, ctx) => {
    // Progress reporting
    await ctx.reportProgress?.(0, 100, "Starting...");

    // Structured logging
    await ctx.log("info", `Processing ${data.length} chars`);

    // Check client capabilities
    if (ctx.client.can("sampling")) {
      // Ask the LLM to help process
      const result = await ctx.sample(`Summarize this: ${data}`);
    }

    await ctx.reportProgress?.(100, 100, "Done");
    return text("Processed successfully");
  },
);
```

### Structured Output

Use `outputSchema` for typed, validated output:

```typescript
server.tool(
  {
    name: "get-stats",
    schema: z.object({ period: z.string() }),
    outputSchema: z.object({
      total: z.number(),
      average: z.number(),
      trend: z.enum(["up", "down", "flat"]),
    }),
  },
  async ({ period }) => {
    return object({ total: 150, average: 42.5, trend: "up" });
  },
);
```

## Resources

Resources expose read-only data clients can fetch.

### Static Resource

```typescript
import { object, text, markdown } from "mcp-use/server";

server.resource(
  {
    uri: "config://settings",
    name: "Application Settings",
    description: "Current server configuration",
    mimeType: "application/json",
  },
  async () => object({ theme: "dark", version: "1.0.0", language: "en" }),
);

server.resource(
  {
    uri: "docs://guide",
    name: "User Guide",
    mimeType: "text/markdown",
  },
  async () => markdown("# User Guide\n\nWelcome to the app!"),
);
```

### Dynamic Resource

```typescript
server.resource(
  {
    uri: "stats://current",
    name: "Current Stats",
    mimeType: "application/json",
  },
  async () => {
    const stats = await getStats();
    return object(stats);
  },
);
```

### Parameterized Resource (Templates)

```typescript
server.resourceTemplate(
  {
    uriTemplate: "user://{userId}/profile",
    name: "User Profile",
    description: "Get user profile by ID",
    mimeType: "application/json",
  },
  async (uri, { userId }) => {
    const user = await fetchUser(userId);
    return object(user);
  },
);
```

For advanced URI patterns, see [resource-templates.md](resource-templates.md).

## Prompts

Prompts are reusable message templates for AI interactions.

```typescript
server.prompt(
  {
    name: "code-review",
    description: "Generate a code review for the given language",
    schema: z.object({
      language: z.string().describe("Programming language"),
      focusArea: z.string().optional().describe("Specific area to focus on"),
    }),
  },
  async ({ language, focusArea }) => {
    const focus = focusArea ? ` Focus on ${focusArea}.` : "";
    return text(
      `Please review this ${language} code for best practices and potential issues.${focus}`,
    );
  },
);
```

## Zod Schema Best Practices

```typescript
// Good: descriptive, with constraints
const schema = z.object({
  city: z.string().describe("City name (e.g., 'New York', 'Tokyo')"),
  units: z
    .enum(["celsius", "fahrenheit"])
    .optional()
    .describe("Temperature units"),
  limit: z.number().min(1).max(50).optional().describe("Max results to return"),
});

// Bad: no descriptions
const schema = z.object({
  city: z.string(),
  units: z.string(),
  limit: z.number(),
});
```

**Rules:**

- Always add `.describe()` to every field
- Use `.optional()` for non-required fields
- Add validation (`.min()`, `.max()`, `.enum()`) where appropriate
- Use `z.enum()` instead of `z.string()` when there's a fixed set of values

## Error Handling

```typescript
import { text, error } from "mcp-use/server";

server.tool(
  { name: "fetch-data", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    try {
      const data = await fetchFromAPI(id);
      if (!data) {
        return error(`No data found for ID: ${id}`);
      }
      return object(data);
    } catch (err) {
      return error(
        `Failed to fetch data: ${err instanceof Error ? err.message : "Unknown error"}`,
      );
    }
  },
);
```

## Environment Variables

When your server needs API keys or configuration:

```typescript
// index.ts - read from environment
const API_KEY = process.env.WEATHER_API_KEY;

server.tool(
  { name: "get-weather", schema: z.object({ city: z.string() }) },
  async ({ city }) => {
    if (!API_KEY) {
      return error(
        "WEATHER_API_KEY not configured. Please set it in the Env tab.",
      );
    }
    const data = await fetch(
      `https://api.weather.com/v1?key=${API_KEY}&city=${city}`,
    );
    // ...
  },
);
```

Create a `.env.example` documenting required variables:

```
# Weather API key (get from weatherapi.com)
WEATHER_API_KEY=
```

## Custom HTTP Routes

MCPServer extends Hono, so you can add custom API endpoints:

```typescript
server.get("/api/health", (c) => c.json({ status: "ok" }));

server.post("/api/webhook", async (c) => {
  const body = await c.req.json();
  // Handle webhook
  return c.json({ received: true });
});
```

## Server Startup

```typescript
const PORT = process.env.PORT ? parseInt(process.env.PORT) : 3000;
server.listen(PORT);
```
