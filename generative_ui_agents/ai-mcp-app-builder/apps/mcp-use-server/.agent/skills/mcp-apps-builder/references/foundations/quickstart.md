# Quick Start

Build your first MCP server tool in 5 minutes.

## Setup

### Scaffolding a New Project

```bash
npx create-mcp-use-app my-server
cd my-server
npm run dev
```

This installs dependencies, starts the server on port 3000, and opens the inspector at `http://localhost:3000/inspector`.

### Choosing a Template

Pick the template that matches what the user is building:

| Template              | Command                                                  | Use When                                                                  |
| --------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------- |
| **starter** (default) | `npx create-mcp-use-app my-server`                       | Full-featured server with tools, resources, prompts, and widget examples  |
| **mcp-apps**          | `npx create-mcp-use-app my-server --template mcp-apps`   | Widget-focused for ChatGPT, Claude, and other MCP Apps-compatible clients |
| **blank**             | `npx create-mcp-use-app my-server --template blank`      | Clean slate — bare server with commented-out examples                     |
| **GitHub repo**       | `npx create-mcp-use-app my-server --template owner/repo` | Custom or community templates from any GitHub repository                  |

**When unsure, use `mcp-apps`.** It's the recommended default with widget support for ChatGPT, Claude, and other MCP Apps-compatible clients.

### Common Flags

```bash
# Choose package manager
npx create-mcp-use-app my-server --npm
npx create-mcp-use-app my-server --pnpm

# Skip interactive prompts
npx create-mcp-use-app my-server --install --skills

# List all available templates
npx create-mcp-use-app --list-templates
```

### What Each Template Produces

**starter:**

```
my-server/
├── index.ts              # Server with example tool, resource, and prompt
├── resources/            # Widget directory (display-weather.tsx example)
├── public/               # Static assets (favicon, icon)
├── package.json          # Pre-configured scripts: dev, build, start, deploy
└── tsconfig.json
```

**mcp-apps:**

```
my-server/
├── index.ts              # Server with widget-returning tools
├── resources/            # Widget directory (product-search-result/ example)
│   └── product-search-result/
│       ├── widget.tsx    # React widget with carousel UI
│       └── components/   # Reusable widget components
├── public/
├── package.json
└── tsconfig.json
```

**blank:**

```
my-server/
├── index.ts              # Bare MCPServer with commented-out examples
├── public/
├── package.json
└── tsconfig.json
```

### Development Workflow

After scaffolding:

1. `npm run dev` — starts server with hot reload + inspector
2. Edit `index.ts` to add tools, resources, prompts
3. Add widgets as `.tsx` files in `resources/`
4. Test everything at `http://localhost:3000/inspector`
5. `npm run build` — production build
6. `npm run deploy` — deploy to production

---

## Your First Tool

Open `index.ts` and you'll see a basic server. Let's add a simple tool:

```typescript
import { MCPServer, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  title: "My Server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

// Add this tool
server.tool(
  {
    name: "greet",
    description: "Greet a user by name",
    schema: z.object({
      name: z.string().describe("User's name"),
    }),
  },
  async ({ name }) => {
    return text(`Hello, ${name}! Welcome to MCP.`);
  },
);

server.listen();
```

**Save the file** - the server auto-reloads!

**Test it:**

1. Open inspector (`http://localhost:3000/inspector`)
2. Click "List Tools"
3. Find "greet" tool
4. Click "Call Tool"
5. Enter `{"name": "Alice"}`
6. See response: "Hello, Alice! Welcome to MCP."

---

## Add Mock Data

Let's build a weather tool with mock data:

```typescript
// Mock weather data
const mockWeather: Record<string, { temp: number; conditions: string }> = {
  "New York": { temp: 22, conditions: "Partly Cloudy" },
  London: { temp: 15, conditions: "Rainy" },
  Tokyo: { temp: 28, conditions: "Sunny" },
  Paris: { temp: 18, conditions: "Overcast" },
};

server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
  },
  async ({ city }) => {
    const weather = mockWeather[city];

    if (!weather) {
      return text(`No weather data for ${city}`);
    }

    return text(`Weather in ${city}: ${weather.temp}°C, ${weather.conditions}`);
  },
);
```

**Test it:**

- Call tool with `{"city": "Tokyo"}`
- Response: "Weather in Tokyo: 28°C, Sunny"

---

## Add Structure

Return structured data with `object()`:

```typescript
import { MCPServer, text, object } from "mcp-use/server";

server.tool(
  {
    name: "get-weather-detailed",
    description: "Get detailed weather information",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
  },
  async ({ city }) => {
    const weather = mockWeather[city];

    if (!weather) {
      return object({ error: `No data for ${city}` });
    }

    return object({
      city,
      temperature: weather.temp,
      conditions: weather.conditions,
      unit: "celsius",
      timestamp: new Date().toISOString(),
    });
  },
);
```

---

## Add a Resource

Resources provide read-only data:

```typescript
server.resource(
  {
    name: "available_cities",
    uri: "weather://available-cities",
    title: "Available Cities",
    description: "List of cities with weather data",
  },
  async () =>
    object({
      cities: Object.keys(mockWeather),
    }),
);
```

**Test it:**

1. Inspector → "List Resources"
2. Find "Available Cities"
3. Click "Read Resource"
4. See: `{"cities": ["New York", "London", "Tokyo", "Paris"]}`

---

## Next Steps

**Now that you have the basics:**

1. **Learn response helpers** → [../server/response-helpers.md](../server/response-helpers.md)
2. **Build your first widget** → [../widgets/basics.md](../widgets/basics.md)
3. **See complete examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)

**Want to add visual UI?** Continue to widgets:

- [Widget Basics](../widgets/basics.md) - Create your first interactive widget
