# Setup

Scaffold a project and run the dev server.

## Create Project

```bash
npx create-mcp-use-app my-chatgpt-app --template mcp-apps
cd my-chatgpt-app
npm install
```

**Templates:**

- `--template mcp-apps` -- ChatGPT widgets with dual-protocol support (recommended)
- `--template starter` -- Full-featured with tools, resources, prompts, and widgets
- `--template blank` -- Minimal starting point

## Project Structure

```
my-chatgpt-app/
├── resources/              # React widgets (auto-registered!)
│   └── weather-display.tsx
├── public/                 # Static assets (images, fonts)
├── index.ts               # MCP server entry point
├── package.json
└── tsconfig.json
```

## Run Dev Server

```bash
npm run dev
```

- Hot reload enabled for both server and widgets
- Inspector at `http://localhost:3000/inspector`
- MCP endpoint at `http://localhost:3000/mcp`

## Test with Inspector

Open `http://localhost:3000/inspector` to:

- Execute tools with parameters
- View resources
- Try prompts
- Debug widget rendering and state

## Connect to ChatGPT

### Prerequisites

- ChatGPT Plus, Pro, Business, or Enterprise plan
- Developer Mode enabled: Settings → Connectors → Advanced → Developer Mode

### Steps

1. Expose local server via tunnel:

   ```bash
   mcp-use start --port 3000 --tunnel
   ```

   Or use ngrok: `ngrok http 3000`

2. In ChatGPT → Apps Settings → Create App
3. Enter a name and description
4. Paste the tunnel URL: `{tunnel-url}/mcp`
5. Set Authentication: "No Authentication" (or configure OAuth)
6. Click Create

### Testing

- Type `@{app-name}` in a ChatGPT chat
- Be explicit: "Use the {app-name} connector's {tool-name} tool"
- Disallow alternatives: "Do not use built-in tools, only use my connector"

## Connect to Claude

1. Go to Claude Settings → Connectors → Add Custom Connector
2. Enter name and URL: `{tunnel-url}/mcp`
3. Click Create
4. In Claude chat, click `+` and select your connector

## Deployment

```bash
npx mcp-use login
npm run deploy
```

After deployment:

- Public URL provided
- Auto-scaled and monitored
- HTTPS enabled
- Push updates with `npm run deploy`
