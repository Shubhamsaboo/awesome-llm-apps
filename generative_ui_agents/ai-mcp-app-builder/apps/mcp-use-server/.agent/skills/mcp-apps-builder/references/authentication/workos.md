# WorkOS Authentication

Setting up OAuth with WorkOS AuthKit.

**Learn more:** [WorkOS MCP docs](https://workos.com/docs/authkit/mcp) · [WorkOS AuthKit](https://workos.com/docs/authkit)

---

## Quick Start

```typescript
import { MCPServer, oauthWorkOSProvider, object } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthWorkOSProvider(),
});

server.tool(
  { name: "whoami", description: "Get authenticated user info" },
  async (_args, ctx) =>
    object({
      userId: ctx.auth.user.userId,
      email: ctx.auth.user.email,
      name: ctx.auth.user.name,
    }),
);

server.listen();
```

With a `.env` file:

```bash
MCP_USE_OAUTH_WORKOS_SUBDOMAIN=your-company.authkit.app
```

That's it. JWT verification, OAuth discovery, and token proxying are handled automatically.

---

## Environment Variables

| Variable                         | Required | Description                                               |
| -------------------------------- | -------- | --------------------------------------------------------- |
| `MCP_USE_OAUTH_WORKOS_SUBDOMAIN` | Yes      | Your full AuthKit domain (e.g., `my-company.authkit.app`) |
| `MCP_USE_OAUTH_WORKOS_CLIENT_ID` | No       | Pre-registered OAuth client ID. Omit for DCR mode         |
| `MCP_USE_OAUTH_WORKOS_API_KEY`   | No       | WorkOS API key for making WorkOS API calls                |

### Finding Your Subdomain

WorkOS Dashboard → **Domains** tab → **AuthKit Domain**

Use the **full AuthKit domain** including `.authkit.app`. For example, if your AuthKit domain is `my-company.authkit.app`, set the value to `my-company.authkit.app` (not just `my-company`).

---

## Configuration Options

Zero-config (reads from env vars):

```typescript
oauth: oauthWorkOSProvider();
```

Explicit config (overrides env vars):

```typescript
oauth: oauthWorkOSProvider({
  subdomain: "my-company.authkit.app",
  clientId: "client_01KB5DRXBDDY1VGCBKY108SKJW", // optional
  apiKey: "sk_test_...", // optional
  verifyJwt: false, // development only
});
```

| Option      | Type       | Default | Description                                             |
| ----------- | ---------- | ------- | ------------------------------------------------------- |
| `subdomain` | `string`   | env var | Full AuthKit domain (e.g., `my-company.authkit.app`)    |
| `clientId`  | `string?`  | env var | Pre-registered client ID. Omit for DCR                  |
| `apiKey`    | `string?`  | env var | WorkOS API key                                          |
| `verifyJwt` | `boolean?` | `true`  | Set `false` to skip JWT verification (development only) |

---

## Dynamic Client Registration (DCR)

DCR lets MCP clients register themselves automatically with WorkOS. This is the recommended mode for MCP servers.

> **Testing with the MCP Inspector:** Use DCR mode (do **not** set `MCP_USE_OAUTH_WORKOS_CLIENT_ID`). The Inspector relies on DCR to self-register — without it, the OAuth flow will stall because the Inspector has no pre-configured `client_id`.

**Setup:**

1. Don't set `MCP_USE_OAUTH_WORKOS_CLIENT_ID`
2. Enable DCR in WorkOS Dashboard → **Connect** → **Configuration**

MCP clients (like the Inspector) will register themselves on first connection.

### Pre-registered Client (Alternative)

If you need a specific OAuth client instead of DCR:

1. Create an OAuth application in WorkOS Dashboard → **Connect** → **OAuth Applications**
2. Set `MCP_USE_OAUTH_WORKOS_CLIENT_ID` to the client ID
3. Configure redirect URIs in the dashboard to match your MCP client

---

## User Context

WorkOS populates these fields on `ctx.auth.user`:

| Field             | Type       | Source                     |
| ----------------- | ---------- | -------------------------- |
| `userId`          | `string`   | `sub` claim                |
| `email`           | `string?`  | `email` claim              |
| `name`            | `string?`  | `name` claim               |
| `username`        | `string?`  | `preferred_username` claim |
| `picture`         | `string?`  | `picture` claim            |
| `roles`           | `string[]` | `roles` claim              |
| `permissions`     | `string[]` | `permissions` claim        |
| `scopes`          | `string[]` | Parsed from `scope` claim  |
| `email_verified`  | `boolean?` | `email_verified` claim     |
| `organization_id` | `string?`  | `org_id` claim             |
| `sid`             | `string?`  | Session ID                 |

### Role-Based Access

```typescript
server.tool(
  { name: "admin-action", description: "Admin-only operation" },
  async (_args, ctx) => {
    if (!ctx.auth.user.roles?.includes("admin")) {
      return error("Forbidden: admin role required");
    }

    // ... admin logic
    return text("Done");
  },
);
```

---

## Making WorkOS API Calls

Use the WorkOS API key (not the user's access token) for WorkOS management API calls:

```typescript
const WORKOS_API_KEY = process.env.MCP_USE_OAUTH_WORKOS_API_KEY;

server.tool(
  { name: "get-workos-user", description: "Fetch user profile from WorkOS" },
  async (_args, ctx) => {
    if (!WORKOS_API_KEY) {
      return error("WorkOS API key not configured");
    }

    const res = await fetch(
      `https://api.workos.com/user_management/users/${ctx.auth.user.userId}`,
      {
        headers: {
          Authorization: `Bearer ${WORKOS_API_KEY}`,
          "Content-Type": "application/json",
        },
      },
    );

    if (!res.ok) {
      return error(`WorkOS API failed: ${res.status} ${res.statusText}`);
    }

    return object(await res.json());
  },
);
```

---

## Example `.env`

```bash
# Required: Full AuthKit domain (WorkOS Dashboard → Domains → AuthKit Domain)
MCP_USE_OAUTH_WORKOS_SUBDOMAIN=my-company.authkit.app

# Optional: Pre-registered OAuth client ID (omit for DCR mode)
# MCP_USE_OAUTH_WORKOS_CLIENT_ID=client_01KB5DRXBDDY1VGCBKY108SKJW

# Optional: WorkOS API key for management API calls
MCP_USE_OAUTH_WORKOS_API_KEY=sk_test_...
```

---

## Troubleshooting

### Redirect URI Mismatch

If you get a redirect URI error during the OAuth flow, add your client's callback URL to WorkOS:

1. Go to WorkOS Dashboard → **Developer** → **Redirects** tab
2. Click **Edit redirect URIs**
3. Add the redirect URI your MCP client expects

For example, if testing locally with the MCP Inspector on port 3000:

```
http://localhost:3000/oauth/callback
```

The exact URI depends on your client and port — check the error message for the expected value.

> **Note:** Changes to redirect URIs in WorkOS may take a few minutes to take effect.

---

## Next Steps

- **Auth overview** → [overview.md](overview.md)
- **Supabase setup** → [supabase.md](supabase.md)
- **Build tools** → [../server/tools.md](../server/tools.md)
