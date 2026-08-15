# Resources

Resources expose read-only data that clients can fetch. They don't take input parameters (use resource templates for that).

**Use resources for:** Configuration, static data, documentation, listings, app state

---

## Basic Resource

```typescript
import { MCPServer, object, text, markdown } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

server.resource(
  {
    name: "app_settings",
    uri: "config://settings",
    title: "Application Settings",
    description: "Current server configuration",
  },
  async () =>
    object({
      theme: "dark",
      version: "1.0.0",
      language: "en",
      features: {
        notifications: true,
        analytics: false,
      },
    }),
);
```

**Key points:**

- First argument: resource configuration (uri, name, description, mimeType)
- Second argument: async handler function (no input parameters)
- Handler returns response helper (`object()`, `text()`, `markdown()`, etc.)
- URI scheme is arbitrary (use meaningful prefixes: `config://`, `docs://`, `data://`)

---

## Resource Definition

### URI

Use a scheme-based format for organization:

```typescript
✅ "config://settings"          // Configuration data
✅ "docs://user-guide"          // Documentation
✅ "data://available-cities"    // Static data
✅ "state://current-user"       // Current state

❌ "settings"                   // Missing scheme
❌ "http://example.com/data"    // Don't use http:// (reserved)
```

### Name

Machine-readable identifier (kebab-case):

```typescript
✅ "app_settings"
✅ "user_guide"
✅ "available_cities"
```

### Title

Human-readable name shown to users:

```typescript
✅ "Application Settings"
✅ "User Guide"
✅ "Available Cities"
```

### Description

Optional but recommended. Explains what the resource contains:

```typescript
description: "Current server configuration including theme, language, and feature flags";
```

### MIME Type

Indicates content format:

| Content Type | MIME Type                  |
| ------------ | -------------------------- |
| JSON object  | `application/json`         |
| Plain text   | `text/plain`               |
| Markdown     | `text/markdown`            |
| HTML         | `text/html`                |
| Image        | `image/png`, `image/jpeg`  |
| Binary       | `application/octet-stream` |

---

## Static Resources

Resources that return fixed data:

```typescript
server.resource(
  {
    name: "supported_languages",
    uri: "data://supported-languages",
    title: "Supported Languages",
    description: "List of supported language codes",
  },
  async () =>
    object({
      languages: ["en", "es", "fr", "de", "ja"],
      default: "en",
    }),
);

server.resource(
  {
    name: "api_guide",
    uri: "docs://api-guide",
    title: "API Documentation",
    description: "Complete API reference and examples",
  },
  async () =>
    markdown(`
# API Guide

## Authentication
Use Bearer token in Authorization header...

## Endpoints
- POST /api/users - Create user
- GET /api/users/:id - Get user
  `),
);
```

---

## Dynamic Resources

Resources that fetch or compute data at request time:

```typescript
server.resource(
  {
    name: "current_stats",
    uri: "stats://current",
    title: "Current Statistics",
    description: "Real-time server statistics",
  },
  async () => {
    const stats = await calculateStats();

    return object({
      users: stats.totalUsers,
      requests: stats.requestCount,
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
    });
  },
);

server.resource(
  {
    name: "active_sessions",
    uri: "state://active-sessions",
    title: "Active Sessions",
    description: "Currently active user sessions",
  },
  async () => {
    const sessions = await getActiveSessions();

    return object({
      count: sessions.length,
      sessions: sessions.map((s) => ({
        id: s.id,
        user: s.userId,
        started: s.startTime,
      })),
    });
  },
);
```

**When to use dynamic resources:**

- Data changes over time
- Data is expensive to compute (compute on demand)
- Data reflects current server state

---

## Resource Templates

When you need parameters, use resource templates with URI placeholders:

```typescript
server.resourceTemplate(
  {
    name: "user_profile",
    uriTemplate: "user://{userId}/profile",
    title: "User Profile",
    description: "Get user profile by ID",
  },
  async (uri: URL, params: Record<string, string>) => {
    // Extract parameters from params object
    const { userId } = params;

    const user = await fetchUser(userId);

    if (!user) {
      return error(`User not found: ${userId}`);
    }

    return object({
      id: user.id,
      name: user.name,
      email: user.email,
      createdAt: user.createdAt,
    });
  },
);
```

**URI template syntax:**

- `{param}` - Single path segment
- `{param*}` - Multiple path segments (greedy)

**Examples:**

```typescript
// Single parameter
"user://{userId}/profile"; // Matches: user://123/profile
"docs://{section}"; // Matches: docs://getting-started

// Multiple parameters
"files://{folder}/{filename}"; // Matches: files://documents/report.pdf
"api://{version}/users/{id}"; // Matches: api://v1/users/42

// Greedy parameter (matches multiple segments)
"docs://{path*}"; // Matches: docs://guides/api/authentication
```

**Handler signature:**

```typescript
async (uri: URL, params: Record<string, string>) => {
  // uri: URL object of the matched URI
  // params: Record<string, string> with extracted template parameters

  // Extract the parameters you need
  const { userId } = params;
};
```

**⚠️ TypeScript Best Practice:**

- **Recommended:** Use explicit types and extract params inside the function body (as shown above)
- **Not recommended:** Parameter destructuring like `async (uri, { userId }) => {}` works at runtime but TypeScript has trouble matching it against the `Record<string, string>` type, potentially causing compilation errors

---

## Completion (Autocomplete) for Templates

Add autocomplete suggestions for resource template variables using the `callbacks.complete` option:

```typescript
// Static list of suggestions per variable
server.resourceTemplate(
  {
    uriTemplate: "docs://{docId}",
    name: "Documentation",
    description: "Get documentation by ID",
    callbacks: {
      complete: {
        docId: ["getting-started", "api-reference", "faq", "changelog"],
      },
    },
  },
  async (uri: URL, params: Record<string, string>) => {
    const { docId } = params;
    return markdown(await fetchDoc(docId));
  },
);

// Dynamic suggestions via callback
server.resourceTemplate(
  {
    uriTemplate: "user://{userId}/profile",
    name: "User Profile",
    callbacks: {
      complete: {
        userId: async (value: string) => {
          const users = await searchUsers(value);
          return users.map((u) => u.id);
        },
      },
    },
  },
  async (uri: URL, params: Record<string, string>) => {
    const { userId } = params;
    return object(await fetchUser(userId));
  },
);
```

**Key points:**

- `complete` maps each template variable to either a `string[]` (prefix-matched automatically) or a callback `(value: string) => Promise<string[]>`
- Clients request suggestions via MCP `completion/complete`

---

## Error Handling

Resources can fail - handle errors gracefully with `error()` helper:

```typescript
server.resource({ uri: "data://external-api", ... }, async () => {
  try {
    const data = await fetch("https://api.example.com/data");
    if (!data.ok) return error(`API returned status ${data.status}`);
    return object(await data.json());
  } catch (err) {
    return error(`Failed to fetch: ${err.message}`);
  }
});
```

See [tools.md](tools.md#error-handling) for comprehensive error handling patterns.

---

## Listing Resources

Clients can list all available resources. Organize resources by URI scheme for discoverability:

```typescript
// Good organization
server.resource({ uri: "config://settings", ... });
server.resource({ uri: "config://features", ... });
server.resource({ uri: "config://limits", ... });

server.resource({ uri: "docs://guide", ... });
server.resource({ uri: "docs://api", ... });
server.resource({ uri: "docs://faq", ... });

server.resource({ uri: "data://cities", ... });
server.resource({ uri: "data://countries", ... });
```

When a client lists resources, they see:

```json
{
  "resources": [
    { "uri": "config://settings", "name": "Application Settings", ... },
    { "uri": "config://features", "name": "Feature Flags", ... },
    { "uri": "docs://guide", "name": "User Guide", ... },
    ...
  ]
}
```

---

## Resource vs Tool

**Use a resource when:**

- ✅ Read-only data
- ✅ No input parameters (or use resource templates)
- ✅ Data that clients might browse or list
- ✅ Configuration, docs, static data

**Use a tool when:**

- ✅ Action with side effects
- ✅ Complex input validation needed
- ✅ Needs Zod schema for structured input
- ✅ May return visual UI (widgets)

**Example:**

```typescript
// ❌ Bad - Use resource instead
server.tool(
  { name: "get-settings", schema: z.object({}) },
  async () => object({ theme: "dark" })
);

// ✅ Good
server.resource(
  { uri: "config://settings", ... },
  async () => object({ theme: "dark" })
);

// ✅ Good - Tool appropriate here (has input)
server.tool(
  { name: "update-settings", schema: z.object({ theme: z.string() }) },
  async ({ theme }) => {
    await saveSettings({ theme });
    return text("Settings updated");
  }
);
```

---

## Caching Resources

Since resources are read-only, caching is often beneficial:

```typescript
const cache = new Map<string, { data: any; expires: number }>();

server.resource(
  {
    uri: "data://expensive-computation",
    name: "Expensive Data",
    mimeType: "application/json",
  },
  async () => {
    const cacheKey = "expensive-computation";
    const cached = cache.get(cacheKey);

    // Return cached data if not expired
    if (cached && cached.expires > Date.now()) {
      return object(cached.data);
    }

    // Compute fresh data
    const data = await expensiveComputation();

    // Cache for 10 minutes
    cache.set(cacheKey, {
      data,
      expires: Date.now() + 10 * 60 * 1000,
    });

    return object(data);
  },
);
```

---

## Complete Example

```typescript
import { MCPServer, object, markdown, error } from "mcp-use/server";

const server = new MCPServer({
  name: "docs-server",
  version: "1.0.0",
});

// Static configuration
server.resource(
  {
    uri: "config://settings",
    name: "Server Settings",
    mimeType: "application/json",
  },
  async () =>
    object({
      version: "1.0.0",
      environment: process.env.NODE_ENV || "development",
    }),
);

// Dynamic list
server.resource(
  {
    uri: "data://available-docs",
    name: "Available Documentation",
    mimeType: "application/json",
  },
  async () => {
    const docs = await listDocuments();
    return object({ docs });
  },
);

// Parameterized access
server.resourceTemplate(
  {
    uriTemplate: "docs://{docId}",
    name: "Documentation",
    description: "Get documentation by ID",
    mimeType: "text/markdown",
  },
  async (uri: URL, params: Record<string, string>) => {
    const { docId } = params;
    const doc = await fetchDocument(docId);

    if (!doc) {
      return error(`Document not found: ${docId}`);
    }

    return markdown(doc.content);
  },
);

server.listen();
```

---

## Next Steps

- **Format responses** → [response-helpers.md](response-helpers.md)
- **Create tools** → [tools.md](tools.md)
- **See examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)
