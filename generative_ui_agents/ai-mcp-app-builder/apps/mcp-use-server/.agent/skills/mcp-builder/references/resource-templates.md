# Resource Templates Reference

Parameterized resources using URI templates.

## Basic Resource Template

```typescript
server.resourceTemplate(
  {
    uriTemplate: "user://{userId}/profile",
    name: "User Profile",
    description: "Get user profile by ID",
    mimeType: "application/json",
  },
  async ({ userId }) => {
    const user = await fetchUser(userId);
    return object(user);
  },
);
```

## URI Template Patterns

### Single Parameter

```typescript
// user://123/profile
server.resourceTemplate({
  uriTemplate: "user://{userId}/profile",
  // ...
});
```

### Multiple Parameters

```typescript
// org://acme/team/engineering
server.resourceTemplate(
  {
    uriTemplate: "org://{orgId}/team/{teamId}",
    name: "Team Details",
    // ...
  },
  async ({ orgId, teamId }) => {
    return object(await fetchTeam(orgId, teamId));
  },
);
```

### Optional Parameters

```typescript
// file://documents or file://documents?format=json
server.resourceTemplate(
  {
    uriTemplate: "file://{path}",
    name: "File Content",
    // ...
  },
  async ({ path }, { searchParams }) => {
    const format = searchParams?.get("format") || "text";
    const content = await readFile(path);
    return format === "json" ? object(content) : text(content);
  },
);
```

## URI Scheme Conventions

| Scheme      | Use Case           | Example                             |
| ----------- | ------------------ | ----------------------------------- |
| `config://` | Configuration data | `config://settings`, `config://env` |
| `user://`   | User-related data  | `user://{id}/profile`               |
| `docs://`   | Documentation      | `docs://api`, `docs://guide`        |
| `stats://`  | Statistics/metrics | `stats://current`, `stats://daily`  |
| `file://`   | File content       | `file://{path}`                     |
| `db://`     | Database records   | `db://users/{id}`                   |
| `api://`    | API endpoints      | `api://weather/{city}`              |
| `ui://`     | UI widgets         | `ui://widget/{name}.html`           |

## Complete Example

```typescript
import { MCPServer, object, text, markdown } from "mcp-use/server";

const server = new MCPServer({
  name: "data-server",
  version: "1.0.0",
});

// Static resource
server.resource(
  {
    uri: "config://database",
    name: "Database Config",
    mimeType: "application/json",
  },
  async () => object({ host: "localhost", port: 5432 }),
);

// Parameterized resource
server.resourceTemplate(
  {
    uriTemplate: "user://{userId}",
    name: "User Data",
    description: "Fetch user by ID",
    mimeType: "application/json",
  },
  async ({ userId }) => {
    const user = await db.users.findById(userId);
    if (!user) throw new Error(`User ${userId} not found`);
    return object(user);
  },
);

// Nested template
server.resourceTemplate(
  {
    uriTemplate: "user://{userId}/posts/{postId}",
    name: "User Post",
    description: "Fetch specific post by user",
    mimeType: "application/json",
  },
  async ({ userId, postId }) => {
    const post = await db.posts.findOne({ userId, id: postId });
    return object(post);
  },
);

// Documentation resource
server.resource(
  {
    uri: "docs://api",
    name: "API Documentation",
    mimeType: "text/markdown",
  },
  async () =>
    markdown(`
# API Documentation

## Endpoints
- GET /users - List all users
- GET /users/:id - Get user by ID
  `),
);
```
