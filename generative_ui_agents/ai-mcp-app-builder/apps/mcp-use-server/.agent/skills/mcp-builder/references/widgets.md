# Widgets

Create interactive visual UIs for your MCP tools using React components.

## How Widgets Work

1. You create a React component in `resources/` folder
2. The component exports `widgetMetadata` (description + props schema) and a default React component
3. mcp-use auto-registers it as both a tool and a resource
4. When the tool is called, the widget renders with the tool's output data

## Widget File Patterns

### Single File

```
resources/weather-display.tsx     → widget name: "weather-display"
resources/recipe-card.tsx         → widget name: "recipe-card"
```

### Folder-Based (for complex widgets)

```
resources/product-search/
  widget.tsx                      → entry point (required name)
  components/ProductCard.tsx
  hooks/useFilter.ts
  types.ts
```

**Naming**: File/folder name becomes the widget name. Use kebab-case.

## Creating a Widget

### Step 1: Create the Widget File

```tsx
// resources/weather-display.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Display current weather conditions for a city",
  props: z.object({
    city: z.string().describe("City name"),
    temp: z.number().describe("Temperature in Celsius"),
    conditions: z.string().describe("Weather conditions"),
    humidity: z.number().describe("Humidity percentage"),
  }),
};

export default function WeatherDisplay() {
  const { props, isPending } = useWidget();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div style={{ padding: 16, textAlign: "center" }}>
          Loading weather...
        </div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20, borderRadius: 12, background: "#f0f9ff" }}>
        <h2 style={{ margin: 0, fontSize: 24 }}>{props.city}</h2>
        <div style={{ fontSize: 48, fontWeight: "bold" }}>{props.temp}°C</div>
        <p style={{ color: "#666" }}>{props.conditions}</p>
        <p style={{ color: "#999", fontSize: 14 }}>
          Humidity: {props.humidity}%
        </p>
      </div>
    </McpUseProvider>
  );
}
```

### Step 2: Register the Tool

```typescript
// index.ts
import { MCPServer, widget, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "weather-server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
    widget: {
      name: "weather-display", // Must match resources/weather-display.tsx
      invoking: "Fetching weather...",
      invoked: "Weather loaded",
    },
  },
  async ({ city }) => {
    const data = getWeather(city);
    return widget({
      props: {
        city,
        temp: data.temp,
        conditions: data.conditions,
        humidity: data.humidity,
      },
      output: text(`Weather in ${city}: ${data.temp}°C, ${data.conditions}`),
    });
  },
);

server.listen();
```

## Required Widget Exports

Every widget file MUST export:

1. **`widgetMetadata`** — Object with `description` and `props` (Zod schema):

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Human-readable description of what this widget shows",
  props: z.object({
    /* Zod schema for widget input */
  }),
};
```

2. **Default React component** — The UI:

```typescript
export default function MyWidget() { ... }
```

### WidgetMetadata Fields

| Field               | Type                                           | Required | Description                                                                                       |
| ------------------- | ---------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------- |
| `description`       | `string`                                       | Yes      | What the widget displays                                                                          |
| `props`             | `z.ZodObject`                                  | Yes      | Zod schema for widget input data                                                                  |
| `exposeAsTool`      | `boolean`                                      | No       | Auto-register as tool (default: `false`)                                                          |
| `toolOutput`        | `CallToolResult \| (params => CallToolResult)` | No       | What the AI model sees                                                                            |
| `title`             | `string`                                       | No       | Display title                                                                                     |
| `annotations`       | `object`                                       | No       | `readOnlyHint`, `destructiveHint`, etc.                                                           |
| `metadata`          | `object`                                       | No       | CSP, border, resize config, invocation status text                                                |
| `metadata.invoking` | `string`                                       | No       | Status text while tool runs — shown as shimmer in inspector (auto-default: `"Loading {name}..."`) |
| `metadata.invoked`  | `string`                                       | No       | Status text after tool completes — shown in inspector (auto-default: `"{name} ready"`)            |

**Invocation status text** in `metadata` is protocol-agnostic and works for both `mcpApps` and `appsSdk` widgets. For tools using `widget: { name, invoking, invoked }` in the tool config, the `invoking`/`invoked` values in `widget:` take effect instead.

### `exposeAsTool` defaults to `false`

Widgets are registered as MCP resources only by default. When you define a custom tool with `widget: { name: "my-widget" }`, omitting `exposeAsTool` is correct — the custom tool handles making the widget callable:

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Weather display",
  props: z.object({ city: z.string(), temp: z.number() }),
  // exposeAsTool defaults to false — custom tool handles registration
};
```

Set `exposeAsTool: true` to auto-register a widget as a tool without a custom tool definition.

### `toolOutput`

Control what the AI model sees when the auto-registered tool is called:

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Recipe card",
  props: z.object({ name: z.string(), ingredients: z.array(z.string()) }),
  toolOutput: (params) =>
    text(
      `Showing recipe: ${params.name} (${params.ingredients.length} ingredients)`,
    ),
};
```

## `useWidget` Hook

The primary hook for accessing widget data and capabilities.

```typescript
const {
  // Core data
  props, // Widget input data (from tool's widget() call or auto-registered tool)
  isPending, // true while tool is still executing (props may be partial)
  toolInput, // Original tool input arguments
  output, // Additional tool output data
  metadata, // Response metadata

  // Persistent state
  state, // Persisted widget state (survives re-renders)
  setState, // Update persistent state: setState(newState) or setState(prev => newState)

  // Host environment
  theme, // 'light' | 'dark'
  displayMode, // 'inline' | 'pip' | 'fullscreen'
  safeArea, // { insets: { top, bottom, left, right } }
  maxHeight, // Max available height in pixels
  userAgent, // { device: { type }, capabilities: { hover, touch } }
  locale, // User locale (e.g., 'en-US')
  timeZone, // IANA timezone

  // Actions
  callTool, // Call another MCP tool: callTool("tool-name", { args })
  sendFollowUpMessage, // Trigger LLM response: sendFollowUpMessage("analyze this")
  openExternal, // Open external URL: openExternal("https://example.com")
  requestDisplayMode, // Request mode change: requestDisplayMode("fullscreen")
  mcp_url, // MCP server base URL for custom API requests
} = useWidget();
```

### Loading State (Critical)

Widgets render BEFORE tool execution completes. **Always handle `isPending`:**

```tsx
const { props, isPending } = useWidget();

if (isPending) {
  return (
    <McpUseProvider autoSize>
      <div>Loading...</div>
    </McpUseProvider>
  );
}

// Now props are safe to use
return (
  <McpUseProvider autoSize>
    <div>
      {props.city}: {props.temp}°C
    </div>
  </McpUseProvider>
);
```

### Calling Other Tools

```tsx
const { callTool } = useWidget();

const handleRefresh = async () => {
  try {
    const result = await callTool("get-weather", { city: "Tokyo" });
    console.log(result.content);
  } catch (err) {
    console.error("Tool call failed:", err);
  }
};
```

### Triggering LLM Response

```tsx
const { sendFollowUpMessage } = useWidget();

<button
  onClick={() => sendFollowUpMessage("Compare the weather in these cities")}
>
  Ask AI to Compare
</button>;
```

### Persistent State

```tsx
const { state, setState } = useWidget();

// Set state
await setState({ favorites: [...(state?.favorites || []), city] });

// Update with function
await setState((prev) => ({ ...prev, count: (prev?.count || 0) + 1 }));
```

## Convenience Hooks

For simpler use cases:

```typescript
import { useWidgetProps, useWidgetTheme, useWidgetState } from "mcp-use/react";

// Just props
const props = useWidgetProps<MyProps>();

// Just theme
const theme = useWidgetTheme(); // 'light' | 'dark'

// Just state (like useState)
const [state, setState] = useWidgetState<MyState>({ count: 0 });
```

## McpUseProvider

Wrap your widget content in `McpUseProvider`:

```tsx
import { McpUseProvider } from "mcp-use/react";

export default function MyWidget() {
  return (
    <McpUseProvider autoSize>
      <div>Widget content</div>
    </McpUseProvider>
  );
}
```

| Prop           | Type                               | Default | Description                              |
| -------------- | ---------------------------------- | ------- | ---------------------------------------- |
| `autoSize`     | `boolean`                          | `false` | Auto-resize widget height to fit content |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | Show display mode control buttons        |
| `debugger`     | `boolean`                          | `false` | Show debug inspector overlay             |

## Styling

Both inline styles and Tailwind classes work:

```tsx
// Inline styles
<div style={{ padding: 20, borderRadius: 12, background: "#f0f9ff" }}>

// Tailwind
<div className="p-5 rounded-xl bg-blue-50">
```

## `widget()` Response Helper

Used in tool callbacks to send data to the widget:

```typescript
import { widget, text } from "mcp-use/server";

return widget({
  props: { city: "Tokyo", temp: 25 }, // Sent to widget via useWidget().props
  output: text("Weather in Tokyo: 25°C"), // What the AI model sees
  message: "Current weather for Tokyo", // Optional text override
});
```

| Field     | Type                  | Description                                                        |
| --------- | --------------------- | ------------------------------------------------------------------ |
| `props`   | `Record<string, any>` | Data for the widget UI (hidden from model)                         |
| `output`  | `CallToolResult`      | Response helper result the model sees (`text()`, `object()`, etc.) |
| `message` | `string`              | Optional text message override                                     |

## Tool `widget` Config

```typescript
server.tool({
  name: "tool-name",
  schema: z.object({ ... }),
  widget: {
    name: "widget-name",           // Must match resources/ file/folder name
    invoking: "Loading...",         // Text shown while tool runs
    invoked: "Ready",              // Text shown when complete
    widgetAccessible: true,         // Widget can call other tools (default: true)
  },
}, async (input) => { ... });
```

## Complete End-to-End Example

**`index.ts`:**

```typescript
import { MCPServer, widget, text, object } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "recipe-finder",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

const mockRecipes = [
  {
    id: "1",
    name: "Pasta Carbonara",
    cuisine: "Italian",
    time: 30,
    ingredients: ["pasta", "eggs", "bacon", "parmesan"],
  },
  {
    id: "2",
    name: "Chicken Tikka",
    cuisine: "Indian",
    time: 45,
    ingredients: ["chicken", "yogurt", "spices", "rice"],
  },
  {
    id: "3",
    name: "Sushi Rolls",
    cuisine: "Japanese",
    time: 60,
    ingredients: ["rice", "nori", "fish", "avocado"],
  },
];

server.tool(
  {
    name: "search-recipes",
    description: "Search for recipes by query or cuisine",
    schema: z.object({
      query: z.string().describe("Search query (e.g., 'pasta', 'chicken')"),
      cuisine: z.string().optional().describe("Filter by cuisine"),
    }),
    widget: {
      name: "recipe-list",
      invoking: "Searching recipes...",
      invoked: "Recipes found",
    },
  },
  async ({ query, cuisine }) => {
    const results = mockRecipes.filter(
      (r) =>
        r.name.toLowerCase().includes(query.toLowerCase()) ||
        (cuisine && r.cuisine.toLowerCase() === cuisine.toLowerCase()),
    );
    return widget({
      props: { recipes: results, query },
      output: text(`Found ${results.length} recipes for "${query}"`),
    });
  },
);

server.listen();
```

**`resources/recipe-list.tsx`:**

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Display recipe search results",
  props: z.object({
    recipes: z.array(
      z.object({
        id: z.string(),
        name: z.string(),
        cuisine: z.string(),
        time: z.number(),
        ingredients: z.array(z.string()),
      }),
    ),
    query: z.string(),
  }),
  exposeAsTool: false,
};

export default function RecipeList() {
  const { props, isPending } = useWidget();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div style={{ padding: 16 }}>Searching...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 16 }}>
        <h2 style={{ margin: "0 0 12px" }}>Recipes for "{props.query}"</h2>
        {props.recipes.length === 0 ? (
          <p style={{ color: "#999" }}>No recipes found.</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {props.recipes.map((recipe) => (
              <div
                key={recipe.id}
                style={{
                  padding: 16,
                  borderRadius: 8,
                  border: "1px solid #e5e7eb",
                  background: "#fff",
                }}
              >
                <h3 style={{ margin: "0 0 4px" }}>{recipe.name}</h3>
                <p style={{ margin: 0, color: "#666", fontSize: 14 }}>
                  {recipe.cuisine} · {recipe.time} min ·{" "}
                  {recipe.ingredients.join(", ")}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </McpUseProvider>
  );
}
```
