# Custom Authentication

Setting up OAuth with any identity provider (GitHub, Okta, Azure AD, Google, etc.).

---

## Quick Start

```typescript
import { MCPServer, oauthCustomProvider, object } from "mcp-use/server";
import { createRemoteJWKSet, jwtVerify } from "jose";

const JWKS = createRemoteJWKSet(
  new URL("https://login.example.com/.well-known/jwks.json"),
);

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
  oauth: oauthCustomProvider({
    issuer: "https://login.example.com",
    jwksUrl: "https://login.example.com/.well-known/jwks.json",
    authEndpoint: "https://login.example.com/oauth2/authorize",
    tokenEndpoint: "https://login.example.com/oauth2/token",
    verifyToken: async (token) => {
      const result = await jwtVerify(token, JWKS, {
        issuer: "https://login.example.com",
      });
      return result;
    },
  }),
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

---

## Configuration Options

```typescript
oauth: oauthCustomProvider({
  issuer: "https://login.example.com",              // required
  jwksUrl: "https://login.example.com/.well-known/jwks.json",  // required
  authEndpoint: "https://login.example.com/authorize",          // required
  tokenEndpoint: "https://login.example.com/token",             // required
  verifyToken: async (token) => { ... },             // required
  getUserInfo: (payload) => ({ ... }),                // optional
  scopesSupported: ["openid", "profile", "email"],   // optional
  grantTypesSupported: ["authorization_code", "refresh_token"], // optional
})
```

| Option                | Type                                      | Required | Description                                           |
| --------------------- | ----------------------------------------- | -------- | ----------------------------------------------------- |
| `issuer`              | `string`                                  | Yes      | OAuth issuer URL                                      |
| `jwksUrl`             | `string`                                  | Yes      | JWKS endpoint for key discovery                       |
| `authEndpoint`        | `string`                                  | Yes      | Authorization endpoint                                |
| `tokenEndpoint`       | `string`                                  | Yes      | Token endpoint                                        |
| `verifyToken`         | `(token: string) => Promise<{ payload }>` | Yes      | Custom JWT verification function                      |
| `getUserInfo`         | `(payload) => UserInfo`                   | No       | Custom user info extraction                           |
| `scopesSupported`     | `string[]`                                | No       | Defaults to `["openid", "profile", "email"]`          |
| `grantTypesSupported` | `string[]`                                | No       | Defaults to `["authorization_code", "refresh_token"]` |

---

## Token Verification

You must provide a `verifyToken` function that validates the JWT and returns `{ payload }`:

```typescript
import { createRemoteJWKSet, jwtVerify } from "jose";

const JWKS = createRemoteJWKSet(
  new URL("https://login.example.com/.well-known/jwks.json"),
);

verifyToken: async (token) => {
  const result = await jwtVerify(token, JWKS, {
    issuer: "https://login.example.com",
    audience: "my-api", // if your provider requires audience validation
  });
  return result;
};
```

The `jose` library is already a dependency of mcp-use, so no additional install is needed.

---

## Custom User Info Extraction

Without `getUserInfo`, the provider extracts standard OIDC claims automatically:

| Field         | Extracted From                     |
| ------------- | ---------------------------------- |
| `userId`      | `sub`, `user_id`, or `id`          |
| `email`       | `email`                            |
| `name`        | `name`                             |
| `username`    | `username` or `preferred_username` |
| `nickname`    | `nickname`                         |
| `picture`     | `picture` or `avatar_url`          |
| `roles`       | `roles` (if array)                 |
| `permissions` | `permissions` (if array)           |
| `scopes`      | Parsed from `scope` string         |

Override this if your provider uses non-standard claim names:

```typescript
getUserInfo: (payload) => ({
  userId: payload.user_id as string,
  email: payload.mail as string,
  name: payload.display_name as string,
  roles: (payload.groups as string[]) || [],
});
```

---

## Provider Examples

### GitHub (via GitHub Apps)

```typescript
oauth: oauthCustomProvider({
  issuer: "https://github.com",
  jwksUrl: "https://token.actions.githubusercontent.com/.well-known/jwks",
  authEndpoint: "https://github.com/login/oauth/authorize",
  tokenEndpoint: "https://github.com/login/oauth/access_token",
  verifyToken: async (token) => {
    // GitHub tokens may need introspection rather than local JWT verification
    const res = await fetch("https://api.github.com/user", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Invalid token");
    const user = await res.json();
    return { payload: user };
  },
  getUserInfo: (payload) => ({
    userId: String(payload.id),
    email: payload.email as string,
    name: payload.name as string,
    username: payload.login as string,
    picture: payload.avatar_url as string,
  }),
});
```

### Okta

```typescript
import { createRemoteJWKSet, jwtVerify } from "jose";

const OKTA_DOMAIN = process.env.OKTA_DOMAIN; // e.g., "dev-123456.okta.com"
const JWKS = createRemoteJWKSet(
  new URL(`https://${OKTA_DOMAIN}/oauth2/default/v1/keys`),
);

oauth: oauthCustomProvider({
  issuer: `https://${OKTA_DOMAIN}/oauth2/default`,
  jwksUrl: `https://${OKTA_DOMAIN}/oauth2/default/v1/keys`,
  authEndpoint: `https://${OKTA_DOMAIN}/oauth2/default/v1/authorize`,
  tokenEndpoint: `https://${OKTA_DOMAIN}/oauth2/default/v1/token`,
  verifyToken: async (token) =>
    jwtVerify(token, JWKS, {
      issuer: `https://${OKTA_DOMAIN}/oauth2/default`,
    }),
});
```

### Azure AD

```typescript
import { createRemoteJWKSet, jwtVerify } from "jose";

const TENANT_ID = process.env.AZURE_TENANT_ID;
const JWKS = createRemoteJWKSet(
  new URL(`https://login.microsoftonline.com/${TENANT_ID}/discovery/v2.0/keys`),
);

oauth: oauthCustomProvider({
  issuer: `https://login.microsoftonline.com/${TENANT_ID}/v2.0`,
  jwksUrl: `https://login.microsoftonline.com/${TENANT_ID}/discovery/v2.0/keys`,
  authEndpoint: `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/authorize`,
  tokenEndpoint: `https://login.microsoftonline.com/${TENANT_ID}/oauth2/v2.0/token`,
  verifyToken: async (token) =>
    jwtVerify(token, JWKS, {
      issuer: `https://login.microsoftonline.com/${TENANT_ID}/v2.0`,
    }),
  getUserInfo: (payload) => ({
    userId: payload.oid as string,
    email: payload.preferred_username as string,
    name: payload.name as string,
    roles: (payload.roles as string[]) || [],
  }),
});
```

---

## Next Steps

- **Auth overview** → [overview.md](overview.md)
- **WorkOS setup** → [workos.md](workos.md)
- **Supabase setup** → [supabase.md](supabase.md)
- **Build tools** → [../server/tools.md](../server/tools.md)
