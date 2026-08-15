# Tools

Tools are backend actions the AI can call. They take structured input and return output.

**Use tools for:** Actions, operations, API calls, mutations, data fetching

---

## Basic Tool

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.tool(
  {
    name: "send-email",
    description: "Send an email to a user",
    schema: z.object({
      to: z.string().email().describe("Recipient email address"),
      subject: z.string().describe("Email subject line"),
      body: z.string().describe("Email body content"),
      priority: z
        .enum(["low", "normal", "high"])
        .optional()
        .describe("Email priority"),
    }),
  },
  async ({ to, subject, body, priority = "normal" }) => {
    // Your logic here
    await sendEmail(to, subject, body, priority);
    return text(`Email sent to ${to}`);
  },
);
```

**Key points:**

- First argument: tool configuration (name, description, schema)
- Second argument: async handler function
- Handler receives validated input matching schema
- Must return a response helper (`text()`, `object()`, `widget()`, etc.)

---

## Tool Definition

### Name

- Use kebab-case: `send-email`, `fetch-user`, `create-todo`
- Be specific: ❌ `manage-users` ✅ `create-user`, `delete-user`, `list-users`
- One tool = one capability

### Description

Clear, actionable description of what the tool does:

```typescript
✅ "Send an email to a user with subject and body"
❌ "Email tool"
```

The AI uses this to decide when to call your tool.

### Schema (Zod)

**Always use `.describe()` on every field:**

```typescript
// ✅ Good
z.object({
  city: z.string().describe("City name (e.g., 'New York', 'Tokyo')"),
  units: z
    .enum(["celsius", "fahrenheit"])
    .optional()
    .describe("Temperature units"),
  limit: z.number().min(1).max(50).optional().describe("Max results to return"),
});

// ❌ Bad - no descriptions
z.object({
  city: z.string(),
  units: z.string(),
  limit: z.number(),
});
```

**Schema best practices:**

- Use `.optional()` for non-required fields
- Add validation: `.min()`, `.max()`, `.email()`, `.url()`
- Use `z.enum()` for fixed sets of values (not `z.string()`)
- Use `z.array()` for lists
- Use `z.record()` for key-value maps

---

## Tool Annotations

Declare the nature of your tool so clients can warn users:

```typescript
server.tool(
  {
    name: "delete-user",
    description: "Permanently delete a user account",
    schema: z.object({ userId: z.string().describe("User ID") }),
    annotations: {
      destructiveHint: true, // Deletes or overwrites data
      readOnlyHint: false, // Has side effects
      openWorldHint: false, // Stays within user's account (not external APIs)
    },
  },
  async ({ userId }) => {
    await deleteUser(userId);
    return text(`User ${userId} deleted`);
  },
);
```

**Annotations:**

- `destructiveHint: true` - Deletes/overwrites data, client may require confirmation
- `readOnlyHint: true` - No side effects, safe to call repeatedly
- `openWorldHint: true` - Calls external APIs or services outside user's control

---

## Tool Context

The second parameter to tool handlers provides advanced capabilities:

```typescript
server.tool(
  {
    name: "process-large-file",
    schema: z.object({ fileUrl: z.string().describe("URL to file") }),
  },
  async ({ fileUrl }, ctx) => {
    // Progress reporting
    await ctx.reportProgress?.(0, 100, "Starting download...");
    const file = await downloadFile(fileUrl);

    await ctx.reportProgress?.(50, 100, "Processing...");
    const result = await processFile(file);

    // Structured logging
    await ctx.log("info", `Processed ${file.size} bytes`);

    // Structured logging with additional context (optional third parameter)
    await ctx.log(
      "info",
      "Processing complete",
      `fileSize: ${file.size} bytes, duration: 2.5s`,
    );

    // Check client capabilities
    if (ctx.client.can("sampling")) {
      // Ask the LLM to help analyze results
      const summary = await ctx.sample(`Summarize this data: ${result}`);
      return text(summary);
    }

    await ctx.reportProgress?.(100, 100, "Complete");
    return object(result);
  },
);
```

**Context methods:**

- `ctx.reportProgress(current: number, total: number, message: string)` - Show progress to user
- `ctx.log(level: "debug" | "info" | "warn" | "error", message: string, data?: string)` - Structured logging with optional additional context as a string
- `ctx.sample(prompt: string)` - Ask the LLM for help (requires client support)
- `ctx.client.can(capability: string)` - Check if client supports a feature

---

## Error Handling

**Always use `error()` helper, don't throw:**

```typescript
import { text, error } from "mcp-use/server";

server.tool(
  { name: "fetch-user", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    try {
      const user = await fetchUser(id);

      if (!user) {
        return error(`User not found: ${id}`);
      }

      return object(user);
    } catch (err) {
      // Log for debugging
      console.error("Failed to fetch user:", err);

      // Return error to client
      return error(
        `Failed to fetch user: ${err instanceof Error ? err.message : "Unknown error"}`,
      );
    }
  },
);
```

**Error handling rules:**

- ✅ Return `error()` for graceful failure
- ❌ Don't throw exceptions (client sees raw error)
- ✅ Include helpful context in error messages
- ✅ Log errors server-side for debugging

---

## Tool with Widget

When your tool returns visual UI:

```typescript
import { widget, text } from "mcp-use/server";

server.tool(
  {
    name: "search-products",
    description: "Search products by keyword",
    schema: z.object({
      query: z.string().describe("Search query"),
    }),
    widget: {
      name: "product-list", // Must match resources/product-list.tsx
      invoking: "Searching products...",
      invoked: "Products loaded",
    },
  },
  async ({ query }) => {
    const products = await searchProducts(query);

    return widget({
      props: {
        products,
        query,
        totalCount: products.length,
      },
      output: text(`Found ${products.length} products matching "${query}"`),
    });
  },
);
```

**Widget tool requirements:**

- Add `widget: { name }` to tool config
- Return `widget({ props, output })` from handler
- Create matching widget file: `resources/{name}.tsx`
- `exposeAsTool` defaults to `false` — omitting it is correct for this pattern

See [../widgets/basics.md](../widgets/basics.md) for widget implementation.

---

## Structured Output Schema

Validate tool output at runtime:

```typescript
server.tool(
  {
    name: "calculate-stats",
    schema: z.object({
      data: z.array(z.number()).describe("Array of numbers"),
    }),
    outputSchema: z.object({
      mean: z.number(),
      median: z.number(),
      stdDev: z.number(),
      count: z.number(),
    }),
  },
  async ({ data }) => {
    const stats = calculateStats(data);

    // Output is validated against outputSchema
    return object({
      mean: stats.mean,
      median: stats.median,
      stdDev: stats.stdDev,
      count: data.length,
    });
  },
);
```

**When to use `outputSchema`:**

- You want runtime validation of tool output
- Multiple code paths return different shapes
- Debugging output consistency issues

---

## Environment Variables

Securely handle API keys and configuration:

```typescript
// index.ts
const WEATHER_API_KEY = process.env.WEATHER_API_KEY;

server.tool(
  {
    name: "get-weather",
    schema: z.object({ city: z.string() }),
  },
  async ({ city }) => {
    if (!WEATHER_API_KEY) {
      return error(
        "WEATHER_API_KEY not configured. Please set it in environment variables.",
      );
    }

    const data = await fetch(
      `https://api.weather.com/v1?key=${WEATHER_API_KEY}&city=${city}`,
    );

    // ... rest of logic
  },
);
```

**Best practices:**

- ❌ Never hardcode secrets in code
- ✅ Use `process.env.VAR_NAME`
- ✅ Check if required vars are set
- ✅ Document required vars in `.env.example`

**Example `.env.example`:**

```bash
# Weather API key (get from weatherapi.com)
WEATHER_API_KEY=

# Database connection string
DATABASE_URL=
```

---

## Performance Patterns

### Caching

Cache expensive operations:

```typescript
const cache = new Map<string, { data: any; expires: number }>();

server.tool(
  { name: "fetch-weather", schema: z.object({ city: z.string() }) },
  async ({ city }) => {
    const cacheKey = `weather:${city}`;
    const cached = cache.get(cacheKey);

    // Return cached data if not expired
    if (cached && cached.expires > Date.now()) {
      return object(cached.data);
    }

    // Fetch fresh data
    const data = await fetchWeather(city);

    // Cache for 5 minutes
    cache.set(cacheKey, {
      data,
      expires: Date.now() + 5 * 60 * 1000,
    });

    return object(data);
  },
);
```

### Rate Limiting

Prevent abuse using `hono-rate-limiter`:

```typescript
import { rateLimiter } from "hono-rate-limiter";

server.use(
  rateLimiter({
    windowMs: 15 * 60 * 1000, // 15 minutes
    limit: 100, // 100 requests per window per key
    keyGenerator: (c) =>
      c.req.header("x-forwarded-for")?.split(",")[0]?.trim() ??
      c.req.header("cf-connecting-ip") ??
      c.req.header("x-real-ip") ??
      "unknown",
  }),
);
```

> Adjust the key generator depending on your hosting environment.

**Note:** mcp-use is built on Hono. Use Hono-compatible middleware — Express middleware (e.g., `express-rate-limit`) is **not** compatible. For custom middleware or advanced routing, see [../foundations/architecture.md](../foundations/architecture.md).

---

## Security Checklist

Before deploying tools:

- [ ] All schema fields have `.describe()`
- [ ] Input validation with Zod
- [ ] User input sanitized (no SQL injection, XSS)
- [ ] API keys in environment variables
- [ ] Errors return `error()` helper (not thrown)
- [ ] Try/catch around async operations
- [ ] Rate limiting on expensive operations
- [ ] Destructive operations have `destructiveHint: true`

---

## Next Steps

- **Format responses** → [response-helpers.md](response-helpers.md)
- **Add visual UI** → [../widgets/basics.md](../widgets/basics.md)
- **See examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)
