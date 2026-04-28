# Authentication

Adding OAuth authentication to your MCP server.

**Use for:** Protecting tools behind user authentication, accessing user identity in tool handlers, integrating with identity providers (WorkOS, Supabase, etc.)

> **Recommended providers:** WorkOS and Supabase have been fully tested with the MCP Inspector and support Dynamic Client Registration (DCR) out of the box. Start with one of those if possible. The custom provider (`oauthCustomProvider`) works for any OIDC-compliant provider, but requires the provider to either support DCR or the user to supply a pre-registered `client_id` — most providers (e.g., Asana, Google, Okta) do not support DCR, which means the MCP Inspector cannot self-register and the OAuth flow will stall silently.

---

## How It Works

Pass an OAuth provider to the `oauth` option on `MCPServer`. Everything else is automatic:

```typescript
import { MCPServer } from "mcp-use/server";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: yourProvider(), // see provider-specific guides
});
```

This single property:

- Protects all `/mcp/*` routes with bearer token authentication
- Verifies JWTs using the provider's JWKS endpoint
- Sets up OAuth discovery endpoints (`/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource`)
- Sets up `/authorize` and `/token` proxy endpoints for browser clients
- Populates `ctx.auth` in all tool/resource/prompt handlers

---

## Accessing User Context

Every tool handler receives `ctx.auth` when OAuth is enabled:

```typescript
server.tool(
  {
    name: "get-profile",
    description: "Get the authenticated user's profile",
  },
  async (_args, ctx) =>
    object({
      userId: ctx.auth.user.userId,
      email: ctx.auth.user.email,
      name: ctx.auth.user.name,
    }),
);
```

### `ctx.auth` Shape

```typescript
ctx.auth.user; // UserInfo object (see below)
ctx.auth.accessToken; // Raw bearer token string
ctx.auth.scopes; // string[] — parsed from JWT `scope` claim
ctx.auth.permissions; // string[] — parsed from JWT `permissions` claim
ctx.auth.payload; // Raw JWT payload (all claims)
```

### `ctx.auth.user` (UserInfo)

All providers populate these base fields:

| Field         | Type        | Description                          |
| ------------- | ----------- | ------------------------------------ |
| `userId`      | `string`    | Unique user identifier (`sub` claim) |
| `email`       | `string?`   | User's email                         |
| `name`        | `string?`   | Display name                         |
| `username`    | `string?`   | Username                             |
| `nickname`    | `string?`   | Nickname                             |
| `picture`     | `string?`   | Avatar URL                           |
| `roles`       | `string[]?` | User roles                           |
| `permissions` | `string[]?` | User permissions                     |

Providers may add extra fields (e.g., WorkOS adds `organization_id`, Supabase adds `aal`). Access them via `ctx.auth.user.organization_id` or `ctx.auth.payload` for raw claims.

### `ctx.auth.payload` (Raw Claims)

**Type:** `Record<string, unknown>` — all values are `unknown` and require explicit casts.

This applies to **all providers** (WorkOS, Supabase, Auth0, Custom, etc.) since every provider's `verifyToken` returns `Record<string, unknown>`.

**Prefer typed accessors** (`ctx.auth.user.*`, `ctx.auth.scopes`, `ctx.auth.permissions`) over raw payload access. If your provider has non-standard claims, map them into typed `ctx.auth.user` fields via the `getUserInfo` option rather than casting in every tool handler:

```typescript
// ✅ Preferred: map claims once in getUserInfo (custom provider example)
oauth: oauthCustomProvider({
  // ...endpoints and verifyToken...
  getUserInfo: (payload) => ({
    userId: payload.sub as string,
    email: payload.mail as string,
    name: payload.display_name as string,
    roles: (payload.groups as string[]) || [],
  }),
});

// Then access typed fields in tools:
async (_args, ctx) => object({ email: ctx.auth.user.email });
```

```typescript
// ❌ Avoid: casting raw payload in every tool handler
async (_args, ctx) => {
  const exp = ctx.auth.payload.exp as number; // unknown → number cast needed
  return object({ expiresAt: new Date(exp * 1000).toISOString() });
};
```

If you must read raw claims (e.g., for debugging or provider-specific fields not in `UserInfo`), cast explicitly:

```typescript
const exp = ctx.auth.payload.exp as number | undefined;
const iat = ctx.auth.payload.iat as number | undefined;
const customField = ctx.auth.payload.my_field as string;
```

---

## Zero-Config Setup

All built-in providers support zero-config via environment variables. Call the factory with no arguments and it reads from `MCP_USE_OAUTH_*` env vars:

```typescript
oauth: oauthWorkOSProvider(); // reads MCP_USE_OAUTH_WORKOS_*
oauth: oauthSupabaseProvider(); // reads MCP_USE_OAUTH_SUPABASE_*
```

Or pass config explicitly to override env vars. See each provider's guide for available options.

---

## Available Providers

| Provider     | Factory Function             | Required Env Vars                   | Guide                      |
| ------------ | ---------------------------- | ----------------------------------- | -------------------------- |
| **WorkOS**   | `oauthWorkOSProvider()`      | `MCP_USE_OAUTH_WORKOS_SUBDOMAIN`    | [workos.md](workos.md)     |
| **Supabase** | `oauthSupabaseProvider()`    | `MCP_USE_OAUTH_SUPABASE_PROJECT_ID` | [supabase.md](supabase.md) |
| **Custom**   | `oauthCustomProvider({...})` | None (all passed via config)        | [custom.md](custom.md)     |

---

## Making Authenticated API Calls

Use `ctx.auth.accessToken` to call your provider's API on behalf of the user:

```typescript
server.tool(
  { name: "fetch-data", description: "Fetch user data from API" },
  async (_args, ctx) => {
    const res = await fetch("https://api.example.com/me", {
      headers: {
        Authorization: `Bearer ${ctx.auth.accessToken}`,
      },
    });

    if (!res.ok) {
      return error(`API call failed: ${res.status}`);
    }

    return object(await res.json());
  },
);
```

---

## Common Mistakes

- **Wrong `ctx.auth` shape** — User info is nested: `ctx.auth.user.email`, not `ctx.auth.email`
- **Hardcoding provider credentials** — Use env vars or pass config; never commit secrets
- **Skipping JWT verification in production** — `verifyJwt: false` / `skipVerification: true` are for development only
- **Throwing errors instead of returning `error()`** — Use the `error()` response helper for auth-related failures

---

## Next Steps

- **WorkOS setup** → [workos.md](workos.md)
- **Supabase setup** → [supabase.md](supabase.md)
- **Custom provider** → [custom.md](custom.md)
- **Build tools** → [../server/tools.md](../server/tools.md)
- **See examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)
