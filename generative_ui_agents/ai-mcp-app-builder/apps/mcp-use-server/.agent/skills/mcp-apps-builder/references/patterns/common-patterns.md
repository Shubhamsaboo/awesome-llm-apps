# Common Patterns

Complete end-to-end examples showing server + widget implementations for common use cases.

**Examples:** Weather app, Todo list, Recipe browser, File manager

---

## Weather App

### Server (index.ts)

```typescript
import { MCPServer, text, widget, object, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "weather-server",
  title: "Weather Server",
  version: "1.0.0",
  baseUrl: process.env.MCP_URL || "http://localhost:3000",
});

// Mock weather data
const weatherData: Record<
  string,
  { temp: number; conditions: string; icon: string }
> = {
  "New York": { temp: 22, conditions: "Partly Cloudy", icon: "⛅" },
  London: { temp: 15, conditions: "Rainy", icon: "🌧️" },
  Tokyo: { temp: 28, conditions: "Sunny", icon: "☀️" },
  Paris: { temp: 18, conditions: "Overcast", icon: "☁️" },
  Sydney: { temp: 25, conditions: "Clear", icon: "🌤️" },
};

// Tool: Get weather with widget
server.tool(
  {
    name: "get-weather",
    description: "Get current weather for a city",
    schema: z.object({
      city: z.string().describe("City name (e.g., 'New York', 'Tokyo')"),
    }),
    widget: {
      name: "weather-display",
      invoking: "Fetching weather...",
      invoked: "Weather loaded",
    },
  },
  async ({ city }) => {
    const data = weatherData[city];

    if (!data) {
      return error(
        `No weather data for ${city}. Available cities: ${Object.keys(weatherData).join(", ")}`,
      );
    }

    return widget({
      props: {
        city,
        temp: data.temp,
        conditions: data.conditions,
        icon: data.icon,
        timestamp: new Date().toISOString(),
      },
      output: text(`Weather in ${city}: ${data.temp}°C, ${data.conditions}`),
    });
  },
);

// Resource: Available cities
server.resource(
  {
    name: "available_cities",
    uri: "weather://cities",
    title: "Available Cities",
    description: "List of cities with weather data",
  },
  async () =>
    object({
      cities: Object.keys(weatherData),
    }),
);

server.listen();
```

### Widget (resources/weather-display.tsx)

```tsx
import {
  McpUseProvider,
  useWidget,
  useWidgetTheme,
  type WidgetMetadata,
} from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Display weather information for a city",
  props: z.object({
    city: z.string(),
    temp: z.number(),
    conditions: z.string(),
    icon: z.string(),
    timestamp: z.string(),
  }),
  exposeAsTool: false,
};

export default function WeatherDisplay() {
  const { props, isPending } = useWidget();
  const theme = useWidgetTheme();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div style={{ padding: 40, textAlign: "center" }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🌍</div>
          <p>Loading weather...</p>
        </div>
      </McpUseProvider>
    );
  }

  const bgColor = theme === "dark" ? "#1e1e1e" : "#ffffff";
  const textColor = theme === "dark" ? "#e0e0e0" : "#1a1a1a";
  const secondaryColor = theme === "dark" ? "#b0b0b0" : "#666";

  return (
    <McpUseProvider autoSize>
      <div
        style={{
          padding: 24,
          backgroundColor: bgColor,
          color: textColor,
          borderRadius: 8,
        }}
      >
        <h2 style={{ margin: "0 0 8px 0", fontSize: 24 }}>{props.city}</h2>
        <p
          style={{ margin: "0 0 20px 0", color: secondaryColor, fontSize: 12 }}
        >
          {new Date(props.timestamp).toLocaleString()}
        </p>

        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ fontSize: 64 }}>{props.icon}</div>
          <div>
            <div style={{ fontSize: 48, fontWeight: "bold" }}>
              {props.temp}°C
            </div>
            <div style={{ fontSize: 18, color: secondaryColor }}>
              {props.conditions}
            </div>
          </div>
        </div>
      </div>
    </McpUseProvider>
  );
}
```

---

## Todo List

### Server (index.ts)

```typescript
import { MCPServer, text, widget, object, error } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "todo-server",
  title: "Todo Server",
  version: "1.0.0",
});

// Mock database
let todos: Array<{ id: string; title: string; completed: boolean }> = [
  { id: "1", title: "Learn MCP", completed: true },
  { id: "2", title: "Build first widget", completed: false },
  { id: "3", title: "Deploy server", completed: false },
];

// Tool: List todos with widget
server.tool(
  {
    name: "list-todos",
    description: "List all todos",
    schema: z.object({}),
    widget: {
      name: "todo-list",
      invoking: "Loading todos...",
      invoked: "Todos loaded",
    },
  },
  async () => {
    return widget({
      props: {
        todos,
        totalCount: todos.length,
        completedCount: todos.filter((t) => t.completed).length,
      },
      output: text(
        `Found ${todos.length} todos (${todos.filter((t) => t.completed).length} completed)`,
      ),
    });
  },
);

// Tool: Create todo
server.tool(
  {
    name: "create-todo",
    description: "Create a new todo",
    schema: z.object({
      title: z.string().describe("Todo title"),
    }),
  },
  async ({ title }) => {
    const newTodo = {
      id: Date.now().toString(),
      title,
      completed: false,
    };

    todos.push(newTodo);

    return text(`Created todo: ${title}`);
  },
);

// Tool: Toggle todo
server.tool(
  {
    name: "toggle-todo",
    description: "Toggle todo completion status",
    schema: z.object({
      id: z.string().describe("Todo ID"),
      completed: z.boolean().describe("New completion status"),
    }),
  },
  async ({ id, completed }) => {
    const todo = todos.find((t) => t.id === id);

    if (!todo) {
      return error(`Todo not found: ${id}`);
    }

    todo.completed = completed;

    return text(`Todo ${completed ? "completed" : "uncompleted"}`);
  },
);

// Tool: Delete todo
server.tool(
  {
    name: "delete-todo",
    description: "Delete a todo",
    schema: z.object({
      id: z.string().describe("Todo ID"),
    }),
    annotations: {
      destructiveHint: true,
    },
  },
  async ({ id }) => {
    const index = todos.findIndex((t) => t.id === id);

    if (index === -1) {
      return error(`Todo not found: ${id}`);
    }

    const deleted = todos.splice(index, 1)[0];

    return text(`Deleted todo: ${deleted.title}`);
  },
);

server.listen();
```

### Widget (resources/todo-list.tsx)

```tsx
import { useState } from "react";
import {
  McpUseProvider,
  useWidget,
  useWidgetTheme,
  useCallTool,
  type WidgetMetadata,
} from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Interactive todo list",
  props: z.object({
    todos: z.array(
      z.object({
        id: z.string(),
        title: z.string(),
        completed: z.boolean(),
      }),
    ),
    totalCount: z.number(),
    completedCount: z.number(),
  }),
  exposeAsTool: false,
};

export default function TodoList() {
  const { props, isPending } = useWidget();
  const theme = useWidgetTheme();
  const { callTool: createTodo, isPending: isCreating } =
    useCallTool("create-todo");
  const { callTool: toggleTodo } = useCallTool("toggle-todo");
  const { callTool: deleteTodo } = useCallTool("delete-todo");
  const [newTodo, setNewTodo] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div style={{ padding: 20 }}>Loading todos...</div>
      </McpUseProvider>
    );
  }

  // Theme-aware colors (see ui-guidelines.md for useColors() hook pattern)
  const colors = {
    bg: theme === "dark" ? "#1e1e1e" : "#ffffff",
    text: theme === "dark" ? "#e0e0e0" : "#1a1a1a",
    border: theme === "dark" ? "#404040" : "#e0e0e0",
    hover: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
  };

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTodo.trim()) return;

    createTodo(
      { title: newTodo },
      {
        onSuccess: () => setNewTodo(""),
        onError: () => alert("Failed to create todo"),
      },
    );
  };

  const handleToggle = (id: string, completed: boolean) => {
    toggleTodo({ id, completed: !completed });
  };

  const handleDelete = (id: string) => {
    setDeletingId(id);
    deleteTodo(
      { id },
      {
        onError: () => alert("Failed to delete"),
        onSettled: () => setDeletingId(null),
      },
    );
  };

  return (
    <McpUseProvider autoSize>
      <div
        style={{ padding: 20, backgroundColor: colors.bg, color: colors.text }}
      >
        <h2 style={{ margin: "0 0 8px 0" }}>
          Todos ({props.completedCount}/{props.totalCount})
        </h2>

        {/* Create form */}
        <form
          onSubmit={handleCreate}
          style={{ marginBottom: 16, display: "flex", gap: 8 }}
        >
          <input
            type="text"
            value={newTodo}
            onChange={(e) => setNewTodo(e.target.value)}
            placeholder="New todo..."
            disabled={isCreating}
            style={{
              flex: 1,
              padding: 8,
              border: `1px solid ${colors.border}`,
              borderRadius: 4,
              backgroundColor: colors.bg,
              color: colors.text,
            }}
          />
          <button
            type="submit"
            disabled={isCreating}
            style={{
              padding: "8px 16px",
              border: "none",
              borderRadius: 4,
              backgroundColor: "#0066cc",
              color: "white",
              cursor: isCreating ? "not-allowed" : "pointer",
            }}
          >
            {isCreating ? "Adding..." : "Add"}
          </button>
        </form>

        {/* Todo list */}
        <div>
          {props.todos.map((todo) => (
            <div
              key={todo.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: 12,
                borderBottom: `1px solid ${colors.border}`,
                backgroundColor: colors.bg,
              }}
            >
              <input
                type="checkbox"
                checked={todo.completed}
                onChange={() => handleToggle(todo.id, todo.completed)}
                style={{ cursor: "pointer" }}
              />
              <span
                style={{
                  flex: 1,
                  textDecoration: todo.completed ? "line-through" : "none",
                  opacity: todo.completed ? 0.6 : 1,
                }}
              >
                {todo.title}
              </span>
              <button
                onClick={() => handleDelete(todo.id)}
                disabled={deletingId === todo.id}
                style={{
                  padding: "4px 12px",
                  border: "none",
                  borderRadius: 4,
                  backgroundColor: "transparent",
                  color: "#dc3545",
                  cursor: deletingId === todo.id ? "not-allowed" : "pointer",
                }}
              >
                {deletingId === todo.id ? "..." : "Delete"}
              </button>
            </div>
          ))}
        </div>

        {props.todos.length === 0 && (
          <p style={{ textAlign: "center", color: colors.border, padding: 40 }}>
            No todos yet. Create one above!
          </p>
        )}
      </div>
    </McpUseProvider>
  );
}
```

---

## Recipe Browser

### Server (index.ts)

```typescript
import { MCPServer, widget, text } from "mcp-use/server";
import { z } from "zod";

const server = new MCPServer({
  name: "recipe-server",
  title: "Recipe Server",
  version: "1.0.0",
});

// Mock recipe data
const recipes = [
  {
    id: "1",
    name: "Spaghetti Carbonara",
    category: "Italian",
    time: 20,
    difficulty: "Easy",
    ingredients: ["Spaghetti", "Eggs", "Bacon", "Parmesan", "Black pepper"],
    instructions:
      "Cook pasta. Fry bacon. Mix eggs and cheese. Combine all with pasta.",
  },
  {
    id: "2",
    name: "Chicken Tikka Masala",
    category: "Indian",
    time: 45,
    difficulty: "Medium",
    ingredients: ["Chicken", "Yogurt", "Tomatoes", "Cream", "Spices"],
    instructions: "Marinate chicken. Cook in spiced tomato sauce. Add cream.",
  },
  {
    id: "3",
    name: "Caesar Salad",
    category: "Salad",
    time: 15,
    difficulty: "Easy",
    ingredients: ["Romaine lettuce", "Croutons", "Parmesan", "Caesar dressing"],
    instructions: "Toss lettuce with dressing. Top with croutons and cheese.",
  },
];

// Tool: Browse recipes
server.tool(
  {
    name: "browse-recipes",
    description: "Browse recipe collection",
    schema: z.object({
      category: z
        .string()
        .optional()
        .describe("Filter by category (Italian, Indian, Salad)"),
    }),
    widget: {
      name: "recipe-browser",
      invoking: "Loading recipes...",
      invoked: "Recipes loaded",
    },
  },
  async ({ category }) => {
    const filtered = category
      ? recipes.filter((r) => r.category === category)
      : recipes;

    return widget({
      props: {
        recipes: filtered,
        categories: ["All", ...new Set(recipes.map((r) => r.category))],
        selectedCategory: category || "All",
      },
      output: text(`Found ${filtered.length} recipes`),
    });
  },
);

server.listen();
```

### Widget (resources/recipe-browser.tsx)

```tsx
import { useState, useEffect } from "react";
import {
  McpUseProvider,
  useWidget,
  useWidgetTheme,
  type WidgetMetadata,
} from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Browse and view recipes",
  props: z.object({
    recipes: z.array(
      z.object({
        id: z.string(),
        name: z.string(),
        category: z.string(),
        time: z.number(),
        difficulty: z.string(),
        ingredients: z.array(z.string()),
        instructions: z.string(),
      }),
    ),
    categories: z.array(z.string()),
    selectedCategory: z.string(),
  }),
  exposeAsTool: false,
};

export default function RecipeBrowser() {
  const { props, isPending } = useWidget();
  const theme = useWidgetTheme();
  const [selectedRecipe, setSelectedRecipe] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");

  // Sync initial filter from props once loaded
  useEffect(() => {
    if (!isPending && props.selectedCategory) {
      setFilter(props.selectedCategory);
    }
  }, [isPending, props.selectedCategory]);

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div style={{ padding: 20 }}>Loading recipes...</div>
      </McpUseProvider>
    );
  }

  // Theme-aware colors (see ui-guidelines.md for useColors() hook pattern)
  const colors = {
    bg: theme === "dark" ? "#1e1e1e" : "#ffffff",
    text: theme === "dark" ? "#e0e0e0" : "#1a1a1a",
    secondary: theme === "dark" ? "#b0b0b0" : "#666",
    border: theme === "dark" ? "#404040" : "#e0e0e0",
    hover: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
  };

  const filteredRecipes =
    filter === "All"
      ? props.recipes
      : props.recipes.filter((r) => r.category === filter);

  const selected = filteredRecipes.find((r) => r.id === selectedRecipe);

  return (
    <McpUseProvider autoSize>
      <div style={{ backgroundColor: colors.bg, color: colors.text }}>
        {/* Header */}
        <div
          style={{ padding: 16, borderBottom: `1px solid ${colors.border}` }}
        >
          <h2 style={{ margin: "0 0 12px 0" }}>Recipe Browser</h2>

          {/* Category filters */}
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {props.categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                style={{
                  padding: "6px 12px",
                  border: `1px solid ${colors.border}`,
                  borderRadius: 4,
                  backgroundColor: filter === cat ? "#0066cc" : "transparent",
                  color: filter === cat ? "white" : colors.text,
                  cursor: "pointer",
                  fontSize: 14,
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Recipe list */}
        <div style={{ display: "flex" }}>
          <div style={{ flex: 1, borderRight: `1px solid ${colors.border}` }}>
            {filteredRecipes.map((recipe) => (
              <div
                key={recipe.id}
                onClick={() => setSelectedRecipe(recipe.id)}
                style={{
                  padding: 16,
                  borderBottom: `1px solid ${colors.border}`,
                  cursor: "pointer",
                  backgroundColor:
                    selectedRecipe === recipe.id ? colors.hover : "transparent",
                }}
              >
                <h3 style={{ margin: "0 0 4px 0", fontSize: 16 }}>
                  {recipe.name}
                </h3>
                <p
                  style={{
                    margin: 0,
                    fontSize: 12,
                    color: colors.secondary,
                  }}
                >
                  {recipe.category} • {recipe.time} min • {recipe.difficulty}
                </p>
              </div>
            ))}
          </div>

          {/* Recipe detail */}
          <div style={{ flex: 2, padding: 16 }}>
            {selected ? (
              <div>
                <h2 style={{ margin: "0 0 8px 0" }}>{selected.name}</h2>
                <p style={{ margin: "0 0 16px 0", color: colors.secondary }}>
                  {selected.category} • {selected.time} minutes •{" "}
                  {selected.difficulty}
                </p>

                <h3 style={{ fontSize: 16, marginBottom: 8 }}>Ingredients</h3>
                <ul style={{ marginBottom: 16, paddingLeft: 20 }}>
                  {selected.ingredients.map((ing, i) => (
                    <li key={i}>{ing}</li>
                  ))}
                </ul>

                <h3 style={{ fontSize: 16, marginBottom: 8 }}>Instructions</h3>
                <p style={{ lineHeight: 1.6 }}>{selected.instructions}</p>
              </div>
            ) : (
              <p
                style={{
                  color: colors.secondary,
                  textAlign: "center",
                  paddingTop: 40,
                }}
              >
                Select a recipe to view details
              </p>
            )}
          </div>
        </div>
      </div>
    </McpUseProvider>
  );
}
```

---

## Key Patterns Demonstrated

### 1. **Mock Data First**

All examples use mock data, making it easy to prototype and test before connecting real APIs.

### 2. **Widget + Tool Combination**

Each example shows how to pair a tool with a widget for visual output.

### 3. **Interactive Actions**

Todo list shows create/update/delete operations from within widgets using `useCallTool()`.

### 4. **Theme Support**

All widgets use `useWidgetTheme()` to adapt to light/dark mode.

### 5. **State Management**

Recipe browser demonstrates local widget state (selected recipe, filters) vs server state (recipe data).

### 6. **Error Handling**

Weather app shows proper error responses when data not found.

### 7. **Loading States**

All widgets check `isPending` and show loading UI.

### 8. **Master-Detail Layout**

Recipe browser shows a master-detail pattern with list + detail view.

---

## Expanding These Examples

### Add Real APIs

Replace mock data with API calls:

```typescript
// Weather with real API
const WEATHER_API_KEY = process.env.WEATHER_API_KEY;

server.tool(
  {
    name: "get-weather",
    schema: z.object({ city: z.string() }),
    widget: { name: "weather-display" },
  },
  async ({ city }) => {
    if (!WEATHER_API_KEY) {
      return error(
        "WEATHER_API_KEY not configured. Set it in environment variables.",
      );
    }

    const response = await fetch(
      `https://api.weatherapi.com/v1/current.json?key=${WEATHER_API_KEY}&q=${city}`,
    );

    if (!response.ok) {
      return error(`Weather API error: ${response.statusText}`);
    }

    const data = await response.json();

    return widget({
      props: {
        city: data.location.name,
        temp: data.current.temp_c,
        conditions: data.current.condition.text,
        icon: data.current.condition.icon,
        timestamp: data.current.last_updated,
      },
      output: text(
        `Weather in ${city}: ${data.current.temp_c}°C, ${data.current.condition.text}`,
      ),
    });
  },
);
```

### Add Database

Replace in-memory data with database:

```typescript
import { Database } from "better-sqlite3";

const db = new Database("todos.db");

db.exec(`
  CREATE TABLE IF NOT EXISTS todos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    completed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
  )
`);

server.tool(
  { name: "list-todos", schema: z.object({}), widget: { name: "todo-list" } },
  async () => {
    const todos = db
      .prepare("SELECT * FROM todos ORDER BY created_at DESC")
      .all();

    return widget({
      props: {
        todos: todos.map((t) => ({ ...t, completed: Boolean(t.completed) })),
        totalCount: todos.length,
        completedCount: todos.filter((t) => t.completed).length,
      },
      output: text(`Found ${todos.length} todos`),
    });
  },
);
```

---

## Next Steps

- **Review server concepts** → [../server/tools.md](../server/tools.md)
- **Learn widget basics** → [../widgets/basics.md](../widgets/basics.md)
- **Check best practices** → [../../SKILL.md](../../SKILL.md)
