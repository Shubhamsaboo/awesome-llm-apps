# Widget Patterns

Advanced widget patterns and examples for ChatGPT apps.

## Table of Contents

- [Complex Widget (Folder Structure)](#complex-widget-folder-structure)
- [Data Fetching Widget](#data-fetching-widget)
- [Stateful Widget](#stateful-widget)
- [Themed Widget](#themed-widget)
- [Widget with Tool Calls](#widget-with-tool-calls)

## Complex Widget (Folder Structure)

For widgets with multiple components:

```
resources/
└── product-search/
    ├── widget.tsx          # Entry point (required name)
    ├── components/
    │   ├── ProductCard.tsx
    │   └── FilterBar.tsx
    ├── hooks/
    │   └── useFilter.ts
    ├── types.ts
    └── constants.ts
```

**Entry point (`widget.tsx`):**

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";
import { ProductCard } from "./components/ProductCard";
import { FilterBar } from "./components/FilterBar";

export const widgetMetadata: WidgetMetadata = {
  description: "Display product search results with filtering",
  props: z.object({
    products: z.array(
      z.object({
        id: z.string(),
        name: z.string(),
        price: z.number(),
        image: z.string(),
      }),
    ),
    query: z.string(),
  }),
};

const ProductSearch: React.FC = () => {
  const { props, isPending, state, setState } = useWidget();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div>
        <h1>Search: {props.query}</h1>
        <FilterBar onFilter={(filters) => setState({ filters })} />
        <div className="grid grid-cols-3 gap-4">
          {props.products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>
      </div>
    </McpUseProvider>
  );
};

export default ProductSearch;
```

## Data Fetching Widget

Widget that refreshes data via tool calls:

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Display data with refresh capability",
  props: z.object({
    id: z.string(),
    title: z.string(),
    data: z.array(z.any()),
  }),
};

const DataWidget: React.FC = () => {
  const { props, isPending, callTool } = useWidget();

  if (isPending) return <div>Loading...</div>;

  const refresh = async () => {
    try {
      await callTool("fetch-data", { id: props.id });
    } catch (error) {
      console.error("Refresh failed:", error);
    }
  };

  return (
    <McpUseProvider autoSize>
      <div>
        <h1>{props.title}</h1>
        <button onClick={refresh}>Refresh</button>
        <ul>
          {props.data.map((item, i) => (
            <li key={i}>{JSON.stringify(item)}</li>
          ))}
        </ul>
      </div>
    </McpUseProvider>
  );
};

export default DataWidget;
```

## Stateful Widget

Widget with persistent state across interactions:

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Counter with persistent state",
  props: z.object({
    initialValue: z.number().optional(),
  }),
};

const CounterWidget: React.FC = () => {
  const { props, isPending, state, setState } = useWidget();

  if (isPending) return <div>Loading...</div>;

  const count = state?.count ?? props.initialValue ?? 0;

  const increment = async () => {
    await setState({ count: count + 1 });
  };

  const decrement = async () => {
    await setState({ count: count - 1 });
  };

  return (
    <McpUseProvider autoSize>
      <div className="flex items-center gap-4">
        <button onClick={decrement}>-</button>
        <span className="text-2xl">{count}</span>
        <button onClick={increment}>+</button>
      </div>
    </McpUseProvider>
  );
};

export default CounterWidget;
```

## Themed Widget

Widget that respects light/dark theme:

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Theme-aware content display",
  props: z.object({
    title: z.string(),
    content: z.string(),
  }),
};

const ThemedWidget: React.FC = () => {
  const { props, isPending, theme } = useWidget();

  if (isPending) return <div>Loading...</div>;

  const isDark = theme === "dark";

  return (
    <McpUseProvider autoSize>
      <div
        className={`p-4 rounded-lg ${
          isDark ? "bg-gray-900 text-white" : "bg-white text-gray-900"
        }`}
      >
        <h1
          className={`text-xl font-bold ${isDark ? "text-blue-400" : "text-blue-600"}`}
        >
          {props.title}
        </h1>
        <p className={isDark ? "text-gray-300" : "text-gray-700"}>
          {props.content}
        </p>
      </div>
    </McpUseProvider>
  );
};

export default ThemedWidget;
```

## Widget with Tool Calls

Widget that calls other MCP tools:

```tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";
import { useState } from "react";

export const widgetMetadata: WidgetMetadata = {
  description: "City weather lookup with search",
  props: z.object({
    defaultCity: z.string().optional(),
  }),
};

const WeatherSearch: React.FC = () => {
  const { props, isPending, callTool, state, setState } = useWidget();
  const [loading, setLoading] = useState(false);
  const [city, setCity] = useState(props.defaultCity || "");

  if (isPending) return <div>Loading...</div>;

  const searchWeather = async () => {
    if (!city.trim()) return;
    setLoading(true);
    try {
      const result = await callTool("get-weather", { city });
      await setState({ lastResult: result.content, lastCity: city });
    } catch (error) {
      console.error("Search failed:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <McpUseProvider autoSize>
      <div className="p-4">
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Enter city name"
            className="border rounded px-2 py-1"
          />
          <button onClick={searchWeather} disabled={loading}>
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
        {state?.lastResult && (
          <div>
            <h3>Weather in {state.lastCity}:</h3>
            <pre>{JSON.stringify(state.lastResult, null, 2)}</pre>
          </div>
        )}
      </div>
    </McpUseProvider>
  );
};

export default WeatherSearch;
```
