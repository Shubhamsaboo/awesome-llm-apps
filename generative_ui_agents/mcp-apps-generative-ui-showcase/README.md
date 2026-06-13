# MCP Apps Generative UI Showcase

https://github.com/user-attachments/assets/48eeab8d-7845-4d06-83ef-d518a807da03

Book flights, reserve hotels, manage portfolios, and run a kanban board — all inside the chat. Built with [CopilotKit](https://github.com/CopilotKit/CopilotKit), [AG-UI](https://github.com/ag-ui-protocol/ag-ui), and [MCP Apps](https://github.com/modelcontextprotocol/ext-apps), showcasing the MCP Apps Extension (SEP-1865) for rendering interactive UIs directly in the chat.

**Gen UI concept — sandboxed in-chat apps over a tool protocol.** The MCP server registers tools (`workout-generator`, `create-portfolio`, `create-board`…) and links each to an HTML/JS resource via `_meta["ui/resourceUri"]`. When the agent calls a tool, CopilotKit mounts the linked app as a sandboxed iframe in the chat; the iframe talks back to MCP tools over JSON-RPC `postMessage`. Result: full, interactive product surfaces (multi-step wizards, drag-drop boards, live charts) running inline — server-owned logic, chat-owned presentation.

## Live Demo

**https://web-app-production-9af6.up.railway.app**

## Featured Apps

| App                         | Description                                                          | Example Prompt                                                   |
| --------------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **✈️ Airline Booking**      | 5-step wizard: search flights, select seats, enter passenger details | "Book a flight from JFK to LAX on January 20th for 2 passengers" |
| **🏨 Hotel Booking**        | 4-step wizard: search hotels, compare rooms, book accommodation      | "Find a hotel in Paris from January 15 to 18 for 2 guests"       |
| **📈 Investment Simulator** | Portfolio management with live charts, buy/sell trades               | "Create a $10,000 tech-focused portfolio"                        |
| **📋 Kanban Board**         | Drag-drop task management with columns and cards                     | "Create a kanban board for my software project"                  |

## Quick Start

### 1. Install Dependencies

```bash
# From the mcp-apps directory
npm install

cd mcp-server
npm install
cd ..
```

### 2. Set Environment Variables

Create `.env.local` in the `mcp-apps` directory:

```bash
OPENAI_API_KEY=sk-...
```

### 3. Build & Run

```bash
# Terminal 1: Build and run MCP Server
cd mcp-server
npm run build
npm run dev
# Server runs at http://localhost:3001/mcp

# Terminal 2: Run Next.js Frontend (from mcp-apps directory)
npm run dev
# Frontend at http://localhost:3000
```

Open http://localhost:3000 and try one of the example prompts!

## How It Works

MCP Apps are interactive HTML/JS applications that render in sandboxed iframes within the chat sidebar. They communicate with the MCP server via JSON-RPC over postMessage.

```
User: "Book a flight from JFK to LAX"
        ↓
AI calls search-flights tool
        ↓
MCPAppsMiddleware intercepts, fetches HTML resource
        ↓
CopilotKit renders flights-app.html in iframe
        ↓
User interacts with wizard UI
        ↓
UI calls MCP tools via postMessage → server
```

### Tool Registration Pattern

```typescript
// Tool declares its UI resource via _meta
server.registerTool(
  "search-flights",
  {
    inputSchema: { origin, destination, departureDate, passengers },
    _meta: { "ui/resourceUri": "ui://flights/flights-app.html" },
  },
  handler,
);

// Resource serves the HTML
server.registerResource(
  "flights-app",
  "ui://flights/flights-app.html",
  {
    mimeType: "text/html+mcp", // Marks as MCP App
  },
  () => ({ contents: [{ text: htmlContent }] }),
);
```

## Project Structure

```
mcp-apps/
├── src/app/
│   ├── page.tsx                    # Main demo page
│   └── api/copilotkit/route.ts     # CopilotKit + MCPAppsMiddleware
├── mcp-server/
│   ├── server.ts                   # MCP server with all tools
│   ├── src/
│   │   ├── flights.ts              # 15 airports, 6 airlines
│   │   ├── hotels.ts               # 10 cities, 30 hotels
│   │   ├── stocks.ts               # 18 stocks, portfolios
│   │   └── kanban.ts               # Board templates
│   └── apps/
│       ├── flights-app.html        # Airline booking wizard
│       ├── hotels-app.html         # Hotel booking wizard
│       ├── trading-app.html        # Investment simulator
│       └── kanban-app.html         # Kanban board
└── README.md
```

## Key Technologies

- **CopilotKit** (`@copilotkit/*`) - AI chat interface with MCP Apps support
- **AG-UI MCP Apps Middleware** - Bridges MCP servers with CopilotKit
- **MCP SDK** (`@modelcontextprotocol/sdk`) - Model Context Protocol server
- **Vite** - Bundles each app into single self-contained HTML files

## Deployment

The demo is deployed on Railway with two services:

| Service    | URL                                               |
| ---------- | ------------------------------------------------- |
| Web App    | https://web-app-production-9af6.up.railway.app    |
| MCP Server | https://mcp-server-production-bbb4.up.railway.app |

For production, set `MCP_SERVER_URL` environment variable to point to your deployed MCP server.
