# Server Handlers and Widget Components

How to define server tools that render widgets, and how the data flows between server and UI.

## Data Flow

```
User prompt → LLM calls tool → Server handler runs → Returns widget() response
                                                          ↓
                              Widget component renders ← props (hidden from LLM)
                              LLM sees ← output (text/object/markdown)
```

1. LLM calls the tool with user input
2. Server handler fetches data, processes it
3. Handler returns `widget({ props, output })`
   - `props` → sent to widget UI via `useWidget().props` (LLM never sees this)
   - `output` → response helper result the LLM reads for conversation

## Server Handler

```typescript
import { MCPServer, widget, text, object } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-app",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

server.tool(
  {
    name: "search-restaurants",
    description: "Search for restaurants by cuisine and location",
    schema: z.object({
      cuisine: z.string().describe("Type of cuisine (e.g., Italian, Japanese)"),
      location: z.string().describe("City or neighborhood"),
    }),
    widget: {
      name: "restaurant-list", // Must match resources/restaurant-list.tsx
      invoking: "Searching restaurants...",
      invoked: "Restaurants found",
    },
    annotations: {
      readOnlyHint: true, // Only reads data, no side effects
    },
  },
  async ({ cuisine, location }) => {
    const restaurants = await searchRestaurants(cuisine, location);
    return widget({
      props: {
        restaurants, // Full data for the widget
        cuisine,
        location,
      },
      output: text(
        `Found ${restaurants.length} ${cuisine} restaurants near ${location}`,
      ),
    });
  },
);
```

### `widget()` Response Helper

| Field     | Type                  | Description                                                   |
| --------- | --------------------- | ------------------------------------------------------------- |
| `props`   | `Record<string, any>` | Data sent to widget via `useWidget().props`. Hidden from LLM. |
| `output`  | `CallToolResult`      | Response helper (`text()`, `object()`, etc.) the LLM sees.    |
| `message` | `string` (optional)   | Override text message for the LLM.                            |

### Tool `widget` Config

| Field              | Type      | Default             | Description                                   |
| ------------------ | --------- | ------------------- | --------------------------------------------- |
| `name`             | `string`  | required            | Widget name matching `resources/` file/folder |
| `invoking`         | `string`  | "Loading {name}..." | Text shown while tool executes                |
| `invoked`          | `string`  | "{name} ready"      | Text shown when complete                      |
| `widgetAccessible` | `boolean` | `true`              | Widget can call other tools                   |

## Widget Component

```tsx
// resources/restaurant-list.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Display restaurant search results",
  props: z.object({
    restaurants: z.array(
      z.object({
        id: z.string(),
        name: z.string(),
        cuisine: z.string(),
        rating: z.number(),
        priceRange: z.string(),
      }),
    ),
    cuisine: z.string(),
    location: z.string(),
  }),
  exposeAsTool: false, // Custom tool in index.ts handles registration
};

export default function RestaurantList() {
  const { props, isPending, callTool } = useWidget();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div style={{ padding: 16, textAlign: "center" }}>
          Searching restaurants...
        </div>
      </McpUseProvider>
    );
  }

  const handleReserve = async (restaurantId: string) => {
    try {
      const result = await callTool("make-reservation", {
        restaurantId,
        partySize: 2,
        date: new Date().toISOString(),
      });
      alert("Reservation made!");
    } catch (err) {
      console.error("Reservation failed:", err);
    }
  };

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 16 }}>
        <h2>
          {props.cuisine} restaurants near {props.location}
        </h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {props.restaurants.map((r) => (
            <div
              key={r.id}
              style={{
                padding: 12,
                borderRadius: 8,
                border: "1px solid #e5e7eb",
              }}
            >
              <h3 style={{ margin: 0 }}>{r.name}</h3>
              <p style={{ margin: "4px 0", color: "#666" }}>
                {"⭐".repeat(Math.round(r.rating))} · {r.priceRange}
              </p>
              <button onClick={() => handleReserve(r.id)}>Reserve</button>
            </div>
          ))}
        </div>
      </div>
    </McpUseProvider>
  );
}
```

## Required Widget Exports

Every widget file MUST export:

1. **`widgetMetadata`** with `description` and `props` (Zod schema)
2. **Default React component**

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "What this widget shows",
  props: z.object({
    /* ... */
  }),
  // exposeAsTool defaults to false — custom tool in index.ts handles registration
};

export default function MyWidget() {
  /* ... */
}
```

## `useWidget` Core Fields

```typescript
const {
  props, // Widget input data
  isPending, // true while tool still running (props may be partial!)
  output, // Additional output data from the tool
  callTool, // Call another tool: await callTool("name", { args })
} = useWidget();
```

**Critical:** Always check `isPending` first. Props are empty/partial while tool executes.

## Tools Called by Widgets

Define backend tools that widgets invoke via `callTool`:

```typescript
// index.ts
server.tool(
  {
    name: "make-reservation",
    description: "Make a restaurant reservation",
    schema: z.object({
      restaurantId: z.string().describe("Restaurant ID"),
      partySize: z.number().describe("Number of guests"),
      date: z.string().describe("Reservation date"),
    }),
    annotations: {
      readOnlyHint: false,
      destructiveHint: false,
    },
  },
  async ({ restaurantId, partySize, date }) => {
    const reservation = await createReservation(restaurantId, partySize, date);
    return object({ confirmationId: reservation.id, time: reservation.time });
  },
);
```

## Static Assets

Use `public/` folder for images, fonts:

```tsx
import { Image } from "mcp-use/react";

function Logo() {
  return <Image src="/images/logo.svg" alt="Logo" />;
}
```

Relative paths (starting with `/`) auto-resolve to the MCP server's public URL.
