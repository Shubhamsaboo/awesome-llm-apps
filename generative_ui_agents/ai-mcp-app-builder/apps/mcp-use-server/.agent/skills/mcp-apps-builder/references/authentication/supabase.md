# Supabase Authentication

Setting up OAuth with Supabase.

**Learn more:** [Supabase MCP Authentication](https://supabase.com/docs/guides/auth/oauth-server/mcp-authentication)

---

## Quick Start

```typescript
import { MCPServer, oauthSupabaseProvider, object } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthSupabaseProvider(),
});

server.tool(
  { name: "whoami", description: "Get authenticated user info" },
  async (_args, ctx) =>
    object({
      userId: ctx.auth.user.userId,
      email: ctx.auth.user.email,
    }),
);

server.listen();
```

With a `.env` file:

```bash
MCP_USE_OAUTH_SUPABASE_PROJECT_ID=your-project-id
```

JWT verification, OAuth discovery, and token proxying are handled automatically.

---

## Environment Variables

| Variable                            | Required | Description                             |
| ----------------------------------- | -------- | --------------------------------------- |
| `MCP_USE_OAUTH_SUPABASE_PROJECT_ID` | Yes      | Your Supabase project ID                |
| `MCP_USE_OAUTH_SUPABASE_JWT_SECRET` | No       | JWT secret for HS256 token verification |

> `NEXT_PUBLIC_SUPABASE_ANON_KEY` is not read by the SDK. It's a user-defined env var you'll need if your tools make Supabase REST API calls (see [Making Supabase API Calls](#making-supabase-api-calls)).

### Finding Your Credentials

- **Project ID**: Supabase Dashboard → **Project Settings** → **General** → Reference ID
- **JWT Secret**: Supabase Dashboard → **Project Settings** → **JWT Settings** (Legacy section)
- **Anon Key**: Supabase Dashboard → **Project Settings** → **API Keys**

---

## Configuration Options

Zero-config (reads from env vars):

```typescript
oauth: oauthSupabaseProvider();
```

Explicit config (overrides env vars):

```typescript
oauth: oauthSupabaseProvider({
  projectId: "my-project-id",
  jwtSecret: process.env.SUPABASE_JWT_SECRET,
  skipVerification: false,
});
```

| Option             | Type       | Default | Description                              |
| ------------------ | ---------- | ------- | ---------------------------------------- |
| `projectId`        | `string`   | env var | Supabase project ID                      |
| `jwtSecret`        | `string?`  | env var | JWT secret for HS256 tokens              |
| `skipVerification` | `boolean?` | `false` | Skip JWT verification (development only) |

---

## JWT Signing: HS256 vs ES256

Supabase supports two JWT signing algorithms:

### ES256 (Newer Projects)

Asymmetric signing using elliptic curve keys. Tokens are verified via Supabase's JWKS endpoint automatically. No `jwtSecret` needed.

### HS256 (Legacy Projects)

Symmetric signing using a shared secret. You must provide `MCP_USE_OAUTH_SUPABASE_JWT_SECRET` for verification.

The provider auto-detects the algorithm from the token header. If your project uses HS256, make sure the JWT secret is configured. If it uses ES256, you can omit it.

---

## User Context

Supabase populates these fields on `ctx.auth.user`:

| Field         | Type       | Source                                            |
| ------------- | ---------- | ------------------------------------------------- |
| `userId`      | `string`   | `sub` or `user_id` claim                          |
| `email`       | `string?`  | `email` claim                                     |
| `name`        | `string?`  | `user_metadata.name` or `user_metadata.full_name` |
| `username`    | `string?`  | `user_metadata.username`                          |
| `picture`     | `string?`  | `user_metadata.avatar_url`                        |
| `roles`       | `string[]` | `role` claim (e.g., `["authenticated"]`)          |
| `permissions` | `string[]` | Derived from AAL (e.g., `["aal:aal1"]`)           |
| `aal`         | `string?`  | Authentication Assurance Level                    |
| `amr`         | `array?`   | Authentication Methods References                 |
| `session_id`  | `string?`  | Supabase session ID                               |

---

## Making Supabase API Calls

Use `ctx.auth.accessToken` as the bearer token for Supabase REST API calls. This ensures Row Level Security (RLS) policies apply to the authenticated user:

```typescript
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

server.tool(
  { name: "get-notes", description: "Fetch user's notes from Supabase" },
  async (_args, ctx) => {
    const projectId = process.env.MCP_USE_OAUTH_SUPABASE_PROJECT_ID;

    if (!projectId || !SUPABASE_ANON_KEY) {
      return error("Supabase credentials not configured");
    }

    const res = await fetch(`https://${projectId}.supabase.co/rest/v1/notes`, {
      headers: {
        Authorization: `Bearer ${ctx.auth.accessToken}`,
        apikey: SUPABASE_ANON_KEY,
      },
    });

    if (!res.ok) {
      return error(`Supabase API failed: ${res.status}`);
    }

    return object(await res.json());
  },
);
```

**Key point:** The `Authorization` header uses the user's access token (for RLS), while the `apikey` header uses the anon key (for API access).

---

## Example `.env`

```bash
# Required: Supabase project ID (Dashboard → Project Settings → General)
MCP_USE_OAUTH_SUPABASE_PROJECT_ID=your-project-id

# Optional: JWT secret for HS256 verification (Dashboard → Project Settings → JWT Settings)
MCP_USE_OAUTH_SUPABASE_JWT_SECRET=your-jwt-secret

# Optional: Anon key for Supabase REST API calls (Dashboard → Project Settings → API Keys)
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

---

## Next Steps

- **Auth overview** → [overview.md](overview.md)
- **WorkOS setup** → [workos.md](workos.md)
- **Build tools** → [../server/tools.md](../server/tools.md)
