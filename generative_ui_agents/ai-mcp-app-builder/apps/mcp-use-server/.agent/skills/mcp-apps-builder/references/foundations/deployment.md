# Deployment

Guide for deploying MCP servers to production.

## ⚠️ FIRST: Ensure the User is Logged In

**Before any deployment command, always verify authentication:**

```bash
mcp-use whoami
```

If this fails or the user has never logged in, run `mcp-use login` first — it opens a browser for OAuth.

---

## Quick Deploy (Manufact Cloud)

The fastest path to production — one command:

```bash
mcp-use deploy
```

Or via the npm script (pre-configured in all templates):

```bash
npm run deploy
```

Your server is live at `https://{slug}.run.mcp-use.com/mcp`.

---

## Prerequisites

Before running `mcp-use deploy`:

1. **Logged in** — run `mcp-use whoami` to verify, or `mcp-use login` if needed
2. **Git repository** — your project must be a git repo
3. **GitHub remote** — the `origin` remote must point to GitHub (SSH or HTTPS)
4. **Changes pushed** — deployment pulls from GitHub, not your local files. Commit and push first.
5. **GitHub App installed** — the mcp-use GitHub App must have access to the repo. The CLI will prompt you to install it if missing.

---

## Deploy Options

```bash
mcp-use deploy [options]
```

| Flag                  | Description                                     | Default                               |
| --------------------- | ----------------------------------------------- | ------------------------------------- |
| `--name <name>`       | Custom deployment name                          | `package.json` name or directory name |
| `--port <port>`       | Server port                                     | `3000`                                |
| `--runtime <runtime>` | `"node"` or `"python"`                          | Auto-detected from project files      |
| `--env <KEY=VALUE>`   | Set environment variable (repeatable)           | —                                     |
| `--env-file <path>`   | Load env vars from a file                       | —                                     |
| `--open`              | Open deployment in browser after success        | `false`                               |
| `--new`               | Force a fresh deployment (ignore existing link) | `false`                               |

### Setting Environment Variables

```bash
# Inline
mcp-use deploy --env API_KEY=sk-xxx --env DATABASE_URL=postgres://...

# From file
mcp-use deploy --env-file .env.production
```

**NEVER commit secrets to git.** Use `--env` or `--env-file` for API keys, database URLs, and other sensitive values.

---

## Common Mistakes

- ❌ Running `mcp-use deploy` without verifying auth first
  - ✅ Always run `mcp-use whoami` before deploying — run `mcp-use login` if needed
- ❌ Running `mcp-use deploy` with uncommitted/unpushed changes
  - ✅ The cloud builds from GitHub — always `git push` first
- ❌ Hardcoding secrets in code or committing `.env`
  - ✅ Use `--env` / `--env-file` flags, or `mcp-use deployments env set`
- ❌ Forgetting to install the mcp-use GitHub App on the repo
  - ✅ The CLI will prompt you, but you can also install it at `github.com/apps/mcp-use`
- ❌ Running `mcp-use start` without `mcp-use build` first
  - ✅ Always build before starting in production
