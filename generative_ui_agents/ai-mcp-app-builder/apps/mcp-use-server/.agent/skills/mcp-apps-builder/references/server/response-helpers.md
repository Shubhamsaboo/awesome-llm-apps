# Response Helpers

Response helpers format output from tools, resources, and prompts. Always use helpers instead of returning raw values.

**Available helpers:** `text()`, `object()`, `markdown()`, `image()`, `error()`, `widget()`, `mix()`, `resource()`

---

## Why Use Response Helpers?

```typescript
// ❌ Bad - Raw return value
server.tool({ name: "get-data", schema: z.object({}) }, async () => {
  return { status: "ok", data: [1, 2, 3] }; // Wrong!
});

// ✅ Good - Using helper
server.tool({ name: "get-data", schema: z.object({}) }, async () => {
  return object({ status: "ok", data: [1, 2, 3] });
});
```

**Why:**

- Helpers set correct MIME types
- Ensure proper serialization
- Enable client-side rendering
- Support multi-content responses

---

## text()

Simple string responses. Most common helper.

```typescript
import { text } from "mcp-use/server";

server.tool(
  { name: "greet", schema: z.object({ name: z.string() }) },
  async ({ name }) => {
    return text(`Hello, ${name}!`);
  },
);

// Multi-line text
server.tool(
  {
    name: "format-address",
    schema: z.object({
      address: z.object({
        street: z.string(),
        city: z.string(),
        state: z.string(),
        zip: z.string(),
        country: z.string(),
      }),
    }),
  },
  async ({ address }) => {
    return text(
      `${address.street}\n` +
        `${address.city}, ${address.state} ${address.zip}\n` +
        `${address.country}`,
    );
  },
);
```

**Use for:**

- Simple messages
- Confirmation text
- Status updates
- Plain text output

---

## object()

Structured JSON data. Use when AI or client needs structured information.

```typescript
import { object } from "mcp-use/server";

server.tool(
  { name: "get-user", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    const user = await fetchUser(id);

    return object({
      id: user.id,
      name: user.name,
      email: user.email,
      createdAt: user.createdAt,
      settings: {
        theme: user.theme,
        notifications: user.notifications,
      },
    });
  },
);

// With arrays
server.tool({ name: "list-todos", schema: z.object({}) }, async () => {
  const todos = await getTodos();

  return object({
    total: todos.length,
    items: todos.map((t) => ({
      id: t.id,
      title: t.title,
      completed: t.completed,
      dueDate: t.dueDate,
    })),
  });
});
```

**Use for:**

- Structured data
- Lists and arrays
- Nested objects
- Data that AI needs to parse

---

## markdown()

Formatted text with markdown syntax. Great for documentation, reports, explanations.

```typescript
import { markdown } from "mcp-use/server";

server.tool(
  { name: "generate-report", schema: z.object({ data: z.array(z.any()) }) },
  async ({ data }) => {
    return markdown(`
# Daily Report

## Summary
Total items processed: ${data.length}

## Breakdown
| Category | Count |
|----------|-------|
| Success  | ${data.filter((d) => d.status === "ok").length} |
| Failed   | ${data.filter((d) => d.status === "error").length} |

## Details
${data.map((d) => `- **${d.id}**: ${d.message}`).join("\n")}

---
*Generated at ${new Date().toISOString()}*
    `);
  },
);

// Code examples in markdown
server.tool(
  { name: "explain-function", schema: z.object({ name: z.string() }) },
  async ({ name }) => {
    return markdown(`
# ${name}() Function

## Usage
\`\`\`typescript
const result = await ${name}(params);
\`\`\`

## Description
This function performs...

## Parameters
- \`params\` - Configuration object

## Returns
Returns a Promise that resolves to...
    `);
  },
);
```

**Use for:**

- Documentation
- Formatted reports
- Explanations with structure
- Code examples
- Rich text output

---

## image()

Embed images in responses. Supports URLs or base64 data.

```typescript
import { image } from "mcp-use/server";

// Image from URL
server.tool(
  { name: "get-chart", schema: z.object({ data: z.array(z.number()) }) },
  async ({ data }) => {
    const chartUrl = await generateChart(data);
    return image(chartUrl);
  },
);

// Base64 image
server.tool(
  { name: "generate-qr", schema: z.object({ text: z.string() }) },
  async ({ text }) => {
    const qrCodeBase64 = await generateQRCode(text);
    return image(`data:image/png;base64,${qrCodeBase64}`);
  },
);

// Image with MIME type
server.tool(
  { name: "get-diagram", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    const diagramUrl = await getDiagram(id);
    return image(diagramUrl, "image/svg+xml");
  },
);
```

**Use for:**

- Charts and graphs
- QR codes
- Diagrams
- Generated images
- Visual output

---

## error()

Error responses. Always use this instead of throwing exceptions.

```typescript
import { error } from "mcp-use/server";

server.tool(
  { name: "fetch-data", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    try {
      const data = await fetchData(id);

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

// Multiple error cases
server.tool(
  {
    name: "update-user",
    schema: z.object({ id: z.string(), name: z.string() }),
  },
  async ({ id, name }) => {
    const user = await getUser(id);

    if (!user) {
      return error(`User not found: ${id}`);
    }

    if (!name.trim()) {
      return error("Name cannot be empty");
    }

    await updateUser(id, { name });
    return text("User updated successfully");
  },
);
```

**Use for:**

- Validation errors
- Not found errors
- Permission errors
- Operation failures

---

## widget()

Return visual UI alongside data. Tool must have `widget: { name }` config.

```typescript
import { widget, text } from "mcp-use/server";

server.tool(
  {
    name: "search-products",
    description: "Search products by query",
    schema: z.object({
      query: z.string().describe("Search query"),
    }),
    widget: {
      name: "product-list", // Must match resources/product-list.tsx
      invoking: "Searching...",
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

**Widget response structure:**

- `props` - Data sent to widget component
- `output` - Text/object the AI model sees

**Use for:**

- Browsing lists
- Comparing items
- Interactive selection
- Visual data representation

See [../widgets/basics.md](../widgets/basics.md) for widget implementation.

---

## mix()

Combine multiple content types in a single response.

```typescript
import { mix, text, image, markdown } from "mcp-use/server";

server.tool(
  { name: "generate-report", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    const report = await getReport(id);
    const chartUrl = await generateChart(report.data);

    return mix(
      markdown(`# Report: ${report.title}\n\n${report.summary}`),
      image(chartUrl),
      text(`Generated at ${new Date().toISOString()}`),
    );
  },
);

// Text + structured data
server.tool(
  { name: "analyze-code", schema: z.object({ code: z.string() }) },
  async ({ code }) => {
    const analysis = await analyzeCode(code);

    return mix(
      text(`Analysis complete. Found ${analysis.issues.length} issues.`),
      object({
        complexity: analysis.complexity,
        issues: analysis.issues,
        suggestions: analysis.suggestions,
      }),
    );
  },
);
```

**Use for:**

- Rich responses with multiple formats
- Text + image combinations
- Summary + detailed data
- Multiple related pieces of content

---

## Embedding Resources

Reference resources in tool responses:

```typescript
import { text, resource } from "mcp-use/server";

server.tool(
  { name: "get-help", schema: z.object({ topic: z.string() }) },
  async ({ topic }) => {
    return mix(
      text(`Help documentation for: ${topic}`),
      resource(`docs://${topic}`, "text/markdown"),
    );
  },
);
```

---

## Response Patterns

### Success with Data

```typescript
return object({
  success: true,
  data: { ... },
  message: "Operation completed successfully"
});
```

### Success with Message

```typescript
return text("User created successfully");
```

### Not Found

```typescript
if (!item) {
  return error(`Item not found: ${id}`);
}
```

### Validation Error

```typescript
if (!email.includes("@")) {
  return error("Invalid email address");
}
```

### Server Error

```typescript
try {
  // ... operation
} catch (err) {
  console.error("Operation failed:", err);
  return error("Operation failed. Please try again.");
}
```

---

## Complete Example

```typescript
import {
  MCPServer,
  text,
  object,
  markdown,
  image,
  error,
  widget,
  mix,
} from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "response-examples",
  version: "1.0.0",
});

// Simple text
server.tool(
  { name: "greet", schema: z.object({ name: z.string() }) },
  async ({ name }) => text(`Hello, ${name}!`),
);

// Structured data
server.tool({ name: "get-stats", schema: z.object({}) }, async () =>
  object({
    users: 1523,
    active: 342,
    growth: "+12%",
  }),
);

// Markdown report
server.tool({ name: "daily-summary", schema: z.object({}) }, async () =>
  markdown(`
# Daily Summary

## Metrics
- **Users**: 1,523
- **Revenue**: $4,231
- **Orders**: 87

## Top Products
1. Widget Pro
2. Gadget Plus
3. Tool Kit
  `),
);

// Error handling
server.tool(
  { name: "fetch-item", schema: z.object({ id: z.string() }) },
  async ({ id }) => {
    try {
      const item = await db.get(id);

      if (!item) {
        return error(`Item not found: ${id}`);
      }

      return object(item);
    } catch (err) {
      return error("Database error");
    }
  },
);

// Mixed content
server.tool(
  { name: "analyze", schema: z.object({ data: z.array(z.number()) }) },
  async ({ data }) => {
    const stats = calculateStats(data);
    const chartUrl = await generateChart(data);

    return mix(
      markdown(`## Analysis Results\n\nProcessed ${data.length} data points`),
      object(stats),
      image(chartUrl),
    );
  },
);

// Widget response
server.tool(
  {
    name: "browse-items",
    schema: z.object({ category: z.string() }),
    widget: { name: "item-browser" },
  },
  async ({ category }) => {
    const items = await getItems(category);

    return widget({
      props: { items, category },
      output: text(`Found ${items.length} items in ${category}`),
    });
  },
);

server.listen();
```

---

## Best Practices

### 1. Always Use Helpers

```typescript
❌ return { data: "value" };
✅ return object({ data: "value" });
```

### 2. Match Helper to Content

```typescript
✅ text("Simple message")
✅ object({ structured: "data" })
✅ markdown("# Formatted text")
✅ error("Error message")
```

### 3. Handle Errors Gracefully

```typescript
✅ return error("User not found: userId_123");
❌ throw new Error("Raw exception");
```

### 4. Provide Context in Errors

```typescript
✅ error(`User not found: ${userId}`);
✅ error(`Invalid email format: ${email}`);
❌ error("Error");
```

### 5. Use Markdown for Rich Content

```typescript
✅ markdown(`# Title\n\n- Point 1\n- Point 2`);
❌ text("Title\nPoint 1\nPoint 2");  // No formatting
```

### 6. Widget Output is for AI

```typescript
return widget({
  props: {
    /* visual data */
  },
  output: text("Concise summary for AI"), // AI only sees this
});
```

---

## Response Helper Reference

| Helper                | Returns        | Use For                | Example                                     |
| --------------------- | -------------- | ---------------------- | ------------------------------------------- |
| `text(string)`        | Plain text     | Simple messages        | `text("Hello")`                             |
| `object(any)`         | JSON           | Structured data        | `object({ id: 1 })`                         |
| `markdown(string)`    | Formatted text | Documentation, reports | `markdown("# Title")`                       |
| `image(url, mime?)`   | Image          | Charts, diagrams       | `image(url)`                                |
| `error(msg)`          | Error          | Failures               | `error("Not found")`                        |
| `widget(config)`      | UI + data      | Visual interfaces      | `widget({ props, output })`                 |
| `mix(...results)`     | Multiple       | Rich responses         | `mix(text(), image())`                      |
| `resource(uri, mime)` | Resource ref   | Embed resources        | `resource("docs://guide", "text/markdown")` |

---

## Next Steps

- **Create tools** → [tools.md](tools.md)
- **Add resources** → [resources.md](resources.md)
- **Build widgets** → [../widgets/basics.md](../widgets/basics.md)
- **See examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)
