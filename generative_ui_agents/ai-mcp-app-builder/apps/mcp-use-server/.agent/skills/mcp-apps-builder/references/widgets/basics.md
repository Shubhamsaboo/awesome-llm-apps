# Widget Basics

Widgets are React components that provide visual UI for MCP tools. They let users browse, compare, and interact with data visually.

**Use widgets for:** Product lists, calendars, dashboards, search results, file browsers, any visual data representation

---

## When to Use Widgets

**Use a widget when:**

- ✅ Browsing or comparing multiple items
- ✅ Visual representation improves understanding (charts, images, layouts)
- ✅ Interactive selection is easier visually than through text
- ✅ User needs to see data structure at a glance

**Use plain tool (no widget) when:**

- ❌ Output is simple text or a single value
- ❌ No visual representation adds value
- ❌ Quick conversational response is sufficient

**When in doubt:** Use a widget. It makes the experience better.

---

## Minimal Widget

### 1. Create Tool with Widget Config

```typescript
// index.ts
import { MCPServer, widget, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "my-server",
  version: "1.0.0",
});

server.tool(
  {
    name: "show-weather",
    description: "Display weather for a city",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
    widget: {
      name: "weather-display", // Must match filename: resources/weather-display.tsx
      invoking: "Fetching weather...", // Optional: shown while loading
      invoked: "Weather loaded", // Optional: shown when complete
    },
  },
  async ({ city }) => {
    const data = await getWeather(city);

    return widget({
      props: {
        city: data.city,
        temp: data.temperature,
        conditions: data.conditions,
        icon: data.icon,
      },
      output: text(
        `Weather in ${city}: ${data.temperature}°C, ${data.conditions}`,
      ),
    });
  },
);
```

### 2. Create Widget Component

```tsx
// resources/weather-display.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

const propsSchema = z.object({
  city: z.string(),
  temp: z.number(),
  conditions: z.string(),
  icon: z.string(),
});

export const widgetMetadata: WidgetMetadata = {
  description: "Display weather information for a city",
  props: propsSchema,
  exposeAsTool: false, // ← Critical: prevents duplicate tool registration
};

type Props = z.infer<typeof propsSchema>;

export default function WeatherDisplay() {
  const { props, isPending } = useWidget<Props>();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading weather...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <h2>{props.city}</h2>
        <img src={props.icon} alt={props.conditions} width={64} />
        <div style={{ fontSize: 48 }}>{props.temp}°C</div>
        <p>{props.conditions}</p>
      </div>
    </McpUseProvider>
  );
}
```

**Key requirements:**

1. Export `widgetMetadata` with props schema
2. Infer type from schema and pass to `useWidget<Props>()`
3. `exposeAsTool` defaults to `false` — correct when pairing with a custom tool
4. Wrap root in `<McpUseProvider autoSize>`
5. **Always check `isPending` before accessing `props`**

---

## Widget Metadata

The `widgetMetadata` export defines your widget's contract:

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Brief description of what this widget displays",
  props: z.object({
    // Define all props the widget expects
    id: z.string(),
    title: z.string(),
    count: z.number(),
    items: z.array(
      z.object({
        name: z.string(),
        value: z.number(),
      }),
    ),
  }),
  exposeAsTool: false, // Default; omit or set explicitly when pairing with a custom tool
};
```

**Fields:**

- `description` - What the widget displays/does
- `props` - Zod schema defining expected props shape
- `exposeAsTool` - Set to `true` to auto-register as a tool (default: `false`)
- `metadata.invoking` - Status text shown in inspector while tool runs (auto-default: `"Loading {name}..."`)
- `metadata.invoked` - Status text shown in inspector after tool completes (auto-default: `"{name} ready"`)

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Display weather information for a city",
  props: propsSchema,
  metadata: {
    invoking: "Fetching weather...", // Shimmer text while tool runs
    invoked: "Weather loaded", // Static text when complete
    csp: { connectDomains: ["https://api.weather.com"] },
  },
};
```

These status texts appear as animated shimmer text (pending) and static text (complete) in the MCP Inspector and ChatGPT. The values also flow to `openai/toolInvocation/invoking`/`invoked` in tool metadata automatically.

---

## useWidget() Hook

The `useWidget()` hook provides access to props and widget state:

```typescript
const {
  props, // Widget props from tool response
  isPending, // True while props are loading
  setState, // Update widget state
  state, // Current widget state
} = useWidget();
```

**To call tools from a widget**, use the dedicated `useCallTool()` hook — see [interactivity.md](interactivity.md).

### props

Data passed from tool's `widget({ props })` response:

```typescript
const { props } = useWidget();

// Access props after isPending check
if (!isPending) {
  console.log(props.city); // "Tokyo"
  console.log(props.temp); // 28
}
```

**Always check `isPending` before accessing `props`:**

```typescript
❌ const { props } = useWidget();
   return <div>{props.city}</div>;  // Error! props undefined while loading

✅ const { props, isPending } = useWidget();
   if (isPending) return <div>Loading...</div>;
   return <div>{props.city}</div>;  // Safe
```

### isPending

Boolean indicating if props are still loading.

**CRITICAL:** Widgets render **before** the tool completes execution. On first render:

- `isPending` is `true`
- `props` is an empty object `{}`
- Accessing `props` fields will cause errors

**Widget Lifecycle:**

1. Widget mounts immediately when tool is called → `isPending = true`, `props = {}`
2. Tool executes and returns `widget({ props })`
3. Widget re-renders → `isPending = false`, `props` contains data

```typescript
const { isPending } = useWidget();

if (isPending) {
  return (
    <McpUseProvider autoSize>
      <div>Loading...</div>
    </McpUseProvider>
  );
}

// Now safe to access props - guaranteed to have data
```

**Multiple patterns for handling isPending:**

```typescript
// ✅ Pattern 1: Early return (recommended)
if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;
return <McpUseProvider autoSize><div>{props.data}</div></McpUseProvider>;

// ✅ Pattern 2: Conditional rendering
return (
  <McpUseProvider autoSize>
    {isPending ? <div>Loading...</div> : <div>{props.data}</div>}
  </McpUseProvider>
);

// ✅ Pattern 3: Optional chaining (when props might be undefined)
return <McpUseProvider autoSize><div>{props?.data ?? "Loading..."}</div></McpUseProvider>;
```

---

## McpUseProvider

**Required wrapper** for all widgets. Provides context and handles iframe sizing.

```typescript
import { McpUseProvider } from "mcp-use/react";

export default function MyWidget() {
  const { props, isPending } = useWidget();

  if (isPending) {
    return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;
  }

  return (
    <McpUseProvider autoSize>
      <div>
        {/* Your widget content */}
      </div>
    </McpUseProvider>
  );
}
```

**Props:**

- `autoSize={true}` - Automatically resize iframe to content (recommended)
- `autoSize={false}` - Fixed height, widget handles scrolling

**Must wrap:**

- ✅ Every return path (including loading states)
- ✅ Root element of component

---

## Props Handling Patterns

### Simple Props

```typescript
export const widgetMetadata: WidgetMetadata = {
  props: z.object({
    message: z.string(),
    count: z.number()
  }),
  exposeAsTool: false
};

export default function SimpleWidget() {
  const { props, isPending } = useWidget();

  if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;

  return (
    <McpUseProvider autoSize>
      <div>
        <p>{props.message}</p>
        <p>Count: {props.count}</p>
      </div>
    </McpUseProvider>
  );
}
```

### Array Props

```typescript
export const widgetMetadata: WidgetMetadata = {
  props: z.object({
    items: z.array(z.object({
      id: z.string(),
      name: z.string()
    }))
  }),
  exposeAsTool: false
};

export default function ListWidget() {
  const { props, isPending } = useWidget();

  if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;

  return (
    <McpUseProvider autoSize>
      <ul>
        {props.items.map(item => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </McpUseProvider>
  );
}
```

### Nested Props

```typescript
export const widgetMetadata: WidgetMetadata = {
  props: z.object({
    user: z.object({
      name: z.string(),
      profile: z.object({
        bio: z.string(),
        avatar: z.string()
      })
    })
  }),
  exposeAsTool: false
};

export default function ProfileWidget() {
  const { props, isPending } = useWidget();

  if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;

  const { user } = props;

  return (
    <McpUseProvider autoSize>
      <div>
        <img src={user.profile.avatar} alt={user.name} />
        <h2>{user.name}</h2>
        <p>{user.profile.bio}</p>
      </div>
    </McpUseProvider>
  );
}
```

### Optional Props

```typescript
export const widgetMetadata: WidgetMetadata = {
  props: z.object({
    title: z.string(),
    subtitle: z.string().optional(),  // May be undefined
    items: z.array(z.string())
  }),
  exposeAsTool: false
};

export default function FlexibleWidget() {
  const { props, isPending } = useWidget();

  if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;

  return (
    <McpUseProvider autoSize>
      <div>
        <h1>{props.title}</h1>
        {props.subtitle && <h2>{props.subtitle}</h2>}
        <ul>
          {props.items.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
      </div>
    </McpUseProvider>
  );
}
```

---

## File Location

Widgets live in `resources/` directory:

```
my-server/
├── index.ts              # Server code
├── resources/
│   ├── weather-display.tsx    # Widget component
│   ├── product-list.tsx
│   └── calendar-view.tsx
└── package.json
```

**Naming convention:**

- Use kebab-case for widget names
- Tool config: `widget: { name: "weather-display" }`
- File: `resources/weather-display.tsx`

---

## TypeScript Types

For type safety, infer props type from schema:

⚠️ **CRITICAL:** Always define your Zod schema in a separate constant before `widgetMetadata`. Never infer types from `widgetMetadata.props` - TypeScript will lose type information and the result will be `unknown`.

```typescript
import { z } from "zod";
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";

const propsSchema = z.object({
  city: z.string(),
  temp: z.number(),
  conditions: z.string()
});

export const widgetMetadata: WidgetMetadata = {
  description: "Display weather",
  props: propsSchema,
  exposeAsTool: false
};

type Props = z.infer<typeof propsSchema>;

export default function WeatherWidget() {
  const { props, isPending } = useWidget<Props>();

  if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;

  // Now props is fully typed!
  return (
    <McpUseProvider autoSize>
      <div>
        <h2>{props.city}</h2>  {/* ✓ TypeScript knows this is string */}
        <p>{props.temp}°C</p>   {/* ✓ TypeScript knows this is number */}
      </div>
    </McpUseProvider>
  );
}
```

---

## Common Mistakes

### ❌ Missing isPending Check

```typescript
// ❌ Bad - props undefined during loading
export default function BadWidget() {
  const { props } = useWidget();

  return (
    <McpUseProvider autoSize>
      <div>{props.title}</div>  {/* Error! */}
    </McpUseProvider>
  );
}

// ✅ Good
export default function GoodWidget() {
  const { props, isPending } = useWidget();

  if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;

  return (
    <McpUseProvider autoSize>
      <div>{props.title}</div>
    </McpUseProvider>
  );
}
```

### ❌ Missing McpUseProvider

```typescript
// ❌ Bad - Missing provider
export default function BadWidget() {
  const { props, isPending } = useWidget();

  if (isPending) return <div>Loading...</div>;

  return <div>{props.title}</div>;  {/* Won't render correctly */}
}

// ✅ Good
export default function GoodWidget() {
  const { props, isPending } = useWidget();

  if (isPending) return <McpUseProvider autoSize><div>Loading...</div></McpUseProvider>;

  return (
    <McpUseProvider autoSize>
      <div>{props.title}</div>
    </McpUseProvider>
  );
}
```

### `exposeAsTool` — default is `false`

```typescript
// ✅ Default — widget is a resource only, exposed via a custom tool
export const widgetMetadata: WidgetMetadata = {
  description: "...",
  props: z.object({ ... })
  // exposeAsTool defaults to false
};

// ✅ Explicit opt-in to auto-registration
export const widgetMetadata: WidgetMetadata = {
  description: "...",
  props: z.object({ ... }),
  exposeAsTool: true  // Auto-registers widget as a tool
};
```

### ❌ Missing Type Parameter on useWidget

```typescript
// ❌ Bad - props is UnknownObject, no autocomplete or type safety
const propsSchema = z.object({
  title: z.string(),
  count: z.number()
});

export default function BadWidget() {
  const { props } = useWidget();  // props is UnknownObject
  return <div>{props.title}</div>;  // No IDE support, runtime errors possible
}

// ✅ Good - props is fully typed with IDE support
const propsSchema = z.object({
  title: z.string(),
  count: z.number()
});

type Props = z.infer<typeof propsSchema>;

export default function GoodWidget() {
  const { props } = useWidget<Props>();  // props is properly typed
  return <div>{props.title}</div>;  // Full autocomplete and type checking
}
```

### ❌ Inferring Type from widgetMetadata.props

```typescript
// ❌ Bad - Type inference fails, Props is unknown
export const widgetMetadata: WidgetMetadata = {
  description: "...",
  props: z.object({
    title: z.string(),
    count: z.number()
  })  // Inline schema definition
};

type Props = z.infer<typeof widgetMetadata.props>;  // Props is unknown!

export default function BadWidget() {
  const { props } = useWidget<Props>();
  return <div>{props.title}</div>;  // No autocomplete, no type safety
}

// ✅ Good - Extract schema first for proper type inference
const propsSchema = z.object({
  title: z.string(),
  count: z.number()
});

export const widgetMetadata: WidgetMetadata = {
  description: "...",
  props: propsSchema  // Reference the schema variable
};

type Props = z.infer<typeof propsSchema>;  // Props is properly typed!

export default function GoodWidget() {
  const { props } = useWidget<Props>();
  return <div>{props.title}</div>;  // Full autocomplete and type checking
}
```

**Why this happens:** The `WidgetMetadata` type is generic, so TypeScript can't preserve the specific Zod schema type when defined inline. Always extract your schema to a separate constant before using it in `widgetMetadata`.

---

## Testing Widgets

Use the inspector to test widgets during development:

1. Start dev server: `npm run dev`
2. Open inspector: `http://localhost:3000/inspector`
3. Click "List Tools" → Find your tool
4. Click "Call Tool" → Enter test input
5. Widget renders in inspector

**Quick iteration:**

- Change widget code → Auto-reload
- Adjust props schema → Update tool call input
- Test edge cases (empty lists, missing optional props)

---

## Complete Example

```typescript
// index.ts
import { MCPServer, widget, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "product-server",
  version: "1.0.0",
});

server.tool(
  {
    name: "search-products",
    description: "Search products by keyword",
    schema: z.object({
      query: z.string().describe("Search query"),
    }),
    widget: {
      name: "product-list",
      invoking: "Searching products...",
      invoked: "Products loaded",
    },
  },
  async ({ query }) => {
    const products = await searchProducts(query);

    return widget({
      props: {
        products,
        query,
        totalCount: products.length,
      },
      output: text(`Found ${products.length} products matching "${query}"`),
    });
  },
);

server.listen();
```

```tsx
// resources/product-list.tsx
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Display product search results",
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
    totalCount: z.number(),
  }),
  exposeAsTool: false,
};

export default function ProductList() {
  const { props, isPending } = useWidget();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div style={{ padding: 20 }}>Loading products...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <h2>Search: "{props.query}"</h2>
        <p>Found {props.totalCount} products</p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: 16,
          }}
        >
          {props.products.map((product) => (
            <div
              key={product.id}
              style={{ border: "1px solid #ddd", padding: 12, borderRadius: 8 }}
            >
              <img
                src={product.image}
                alt={product.name}
                style={{ width: "100%", height: 150, objectFit: "cover" }}
              />
              <h3 style={{ fontSize: 16, margin: "8px 0" }}>{product.name}</h3>
              <p style={{ fontSize: 18, fontWeight: "bold" }}>
                ${product.price}
              </p>
            </div>
          ))}
        </div>
      </div>
    </McpUseProvider>
  );
}
```

---

## Next Steps

- **Manage widget state** → [state.md](state.md)
- **Add interactivity** → [interactivity.md](interactivity.md)
- **Style with themes** → [ui-guidelines.md](ui-guidelines.md)
- **Advanced patterns** → [advanced.md](advanced.md)
