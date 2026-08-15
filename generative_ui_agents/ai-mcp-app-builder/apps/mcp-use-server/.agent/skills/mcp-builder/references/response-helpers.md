# Response Helpers Reference

Complete reference for mcp-use response helpers.

All helpers are imported from `mcp-use/server`:

```typescript
import {
  text,
  object,
  markdown,
  html,
  image,
  audio,
  binary,
  error,
  mix,
  widget,
  resource,
} from "mcp-use/server";
```

## Table of Contents

- [Text Responses](#text-responses)
- [JSON Responses](#json-responses)
- [Markdown Responses](#markdown-responses)
- [HTML Responses](#html-responses)
- [Error Responses](#error-responses)
- [Binary Responses](#binary-responses)
- [Embedded Resources](#embedded-resources)
- [Mixed Responses](#mixed-responses)
- [Widget Responses](#widget-responses)
- [Autocompletion](#autocompletion)

## Text Responses

```typescript
import { text } from "mcp-use/server";

// Simple text
return text("Hello, world!");

// Multi-line text
return text(`
  Analysis complete.
  Found 15 items.
  Processing took 2.3 seconds.
`);
```

## JSON Responses

```typescript
import { object } from "mcp-use/server";

// Object response
return object({
  status: "success",
  count: 42,
  items: ["a", "b", "c"],
});

// Nested objects
return object({
  user: { id: 1, name: "John" },
  metadata: { created: new Date().toISOString() },
});
```

## Markdown Responses

```typescript
import { markdown } from "mcp-use/server";

return markdown(`
# Report Title

## Summary
- Item 1: **complete**
- Item 2: *in progress*

## Details
\`\`\`json
{ "score": 95 }
\`\`\`
`);
```

## HTML Responses

```typescript
import { html } from "mcp-use/server";

return html(`
  <div style="padding: 20px;">
    <h1>Welcome</h1>
    <p>This is <strong>HTML</strong> content.</p>
  </div>
`);
```

## Error Responses

```typescript
import { error } from "mcp-use/server";

// Simple error
return error("Something went wrong");

// With context
return error(`User ${userId} not found`);

// In try/catch
try {
  const data = await fetchData(id);
  return object(data);
} catch (err) {
  return error(
    `Failed to fetch: ${err instanceof Error ? err.message : "Unknown error"}`,
  );
}
```

The `error()` helper sets `isError: true` on the response, signaling to the model that the operation failed.

## Binary Responses

### Images

```typescript
import { image } from "mcp-use/server";

// From base64 data
return image(base64Data, "image/png");

// From buffer
return image(imageBuffer, "image/jpeg");

// From file path (async)
return await image("/path/to/image.png");
```

### Audio

```typescript
import { audio } from "mcp-use/server";

// From base64 data
return audio(base64Data, "audio/wav");

// From buffer
return audio(audioBuffer, "audio/mp3");

// From file path (async)
return await audio("/path/to/audio.mp3");
```

### Generic Binary

```typescript
import { binary } from "mcp-use/server";

// PDF
return binary(pdfBuffer, "application/pdf");

// ZIP
return binary(zipBuffer, "application/zip");

// Any binary data
return binary(data, "application/octet-stream");
```

## Embedded Resources

Embed a resource reference inside a tool response:

```typescript
import { resource, text } from "mcp-use/server";

// 2-arg: uri + helper result
return resource("report://analysis-123", text("Full report content here..."));

// 3-arg: uri + mimeType + raw text
return resource("data://export", "application/json", '{"items": [1, 2, 3]}');
```

## Mixed Responses

Combine multiple content types:

```typescript
import { mix, text, object, markdown, resource } from "mcp-use/server";

// Multiple content items
return mix(
  text("Analysis complete:"),
  object({ score: 95, status: "pass" }),
  markdown("## Recommendations\n- Optimize query\n- Add index"),
);

// With embedded resource
return mix(
  text("Report generated:"),
  resource("report://analysis-123", text("Full report content here...")),
  object({ id: "analysis-123", timestamp: Date.now() }),
);
```

## Widget Responses

Return interactive widgets from tools:

```typescript
import { widget, text } from "mcp-use/server";

server.tool(
  {
    name: "show-data",
    schema: z.object({ query: z.string() }),
    widget: {
      name: "data-display", // Widget in resources/
      invoking: "Loading...",
      invoked: "Data loaded",
    },
  },
  async ({ query }) => {
    const data = await fetchData(query);

    return widget({
      // Props passed to widget (hidden from model)
      props: {
        items: data.items,
        query: query,
        total: data.total,
      },
      // Output shown to model
      output: text(`Found ${data.total} results for "${query}"`),
      // Optional message
      message: `Displaying ${data.total} results`,
    });
  },
);
```

### Widget Response Fields

| Field     | Type           | Description                     |
| --------- | -------------- | ------------------------------- |
| `props`   | object         | Data passed to widget component |
| `output`  | ResponseHelper | Content shown to the AI model   |
| `message` | string         | Optional text message           |

### Widget Tool Configuration

| Field             | Description                         |
| ----------------- | ----------------------------------- |
| `widget.name`     | Name of widget file in `resources/` |
| `widget.invoking` | Text shown while tool executes      |
| `widget.invoked`  | Text shown after completion         |

## Autocompletion

Add autocompletion to prompt arguments and resource template parameters:

```typescript
import { completable } from "mcp-use/server";

// Static list
server.prompt(
  {
    name: "code-review",
    schema: z.object({
      language: completable(z.string(), [
        "python",
        "typescript",
        "go",
        "rust",
        "java",
      ]),
    }),
  },
  async ({ language }) => text(`Review this ${language} code.`),
);

// Dynamic callback
server.prompt(
  {
    name: "get-user",
    schema: z.object({
      username: completable(z.string(), async (value) => {
        const users = await searchUsers(value);
        return users.map((u) => u.name);
      }),
    }),
  },
  async ({ username }) => text(`Get info for ${username}`),
);
```

## Quick Reference Table

| Helper                      | Return Type | Use When                                          |
| --------------------------- | ----------- | ------------------------------------------------- |
| `text(str)`                 | Plain text  | Simple text responses                             |
| `object(data)`              | JSON        | Structured data                                   |
| `markdown(str)`             | Markdown    | Formatted text with headings, lists, code         |
| `html(str)`                 | HTML        | Rich HTML content                                 |
| `image(data, mime?)`        | Image       | Base64 or file path images                        |
| `audio(data, mime?)`        | Audio       | Base64 or file path audio                         |
| `binary(data, mime)`        | Binary      | PDFs, ZIPs, other binary                          |
| `error(msg)`                | Error       | Operation failed                                  |
| `resource(uri, content)`    | Resource    | Embed a resource reference                        |
| `mix(...results)`           | Combined    | Multiple content types in one response            |
| `widget({ props, output })` | Widget      | Interactive UI with data for the widget component |
