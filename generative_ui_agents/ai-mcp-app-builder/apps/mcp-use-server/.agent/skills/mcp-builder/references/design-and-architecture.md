# Design and Architecture

Before writing code, think about what the user actually wants and how to decompose it into MCP primitives.

## Concepts

- **Tool**: A backend action the AI model can call. Takes input, returns data. Use `server.tool()`.
- **Widget tool**: A tool that returns visual UI. Same `server.tool()` but with a `widget` config and a React component in `resources/`.
- **Resource**: Read-only data the client can fetch. Use `server.resource()` or `server.resourceTemplate()`.
- **Prompt**: A reusable message template. Use `server.prompt()`.

## Step 1: Identify What to Build

Extract the core actions from the user's request. Stick to what they asked -- don't invent extra features.

**Examples:**

| User says       | Core actions                                     |
| --------------- | ------------------------------------------------ |
| "weather app"   | Get current weather, get forecast                |
| "todo list"     | Add todo, list todos, complete todo, delete todo |
| "recipe finder" | Search recipes, get recipe details               |
| "translator"    | Translate text, detect language                  |
| "stock tracker" | Get stock price, compare stocks                  |
| "quiz app"      | Generate quiz, check answer                      |

## Step 2: Does It Need a Widget?

For each action, decide if visual UI would meaningfully improve the experience.

**YES → widget** if:

- Browsing or comparing multiple items (search results, product cards)
- Visual data improves understanding (charts, maps, images, dashboards)
- Interactive selection is easier visually (seat picker, calendar, color picker)

**NO → tool only** if:

- Output is simple text (translation, calculation, status check)
- Input is naturally conversational (dates, amounts, descriptions)
- No visual element would meaningfully help

**When in doubt, use a widget** -- it makes the experience better.

## Step 3: Design the API

### Naming

Tools and widgets start with a verb: `get-weather`, `search-recipes`, `add-todo`, `translate-text`.

### One tool = one focused capability

Don't create one massive tool that does everything. Break it into focused actions:

❌ `manage-todos` (too broad)
✅ `add-todo`, `list-todos`, `complete-todo`, `delete-todo`

### One widget per flow

Different flows can have separate widgets. Don't split one flow into multiple widgets.

❌ `search-recipes` widget + `view-recipe` widget (same flow → merge)
✅ `search-recipes` widget (handles both list and detail views) + `meal-planner` widget (different flow)

### Don't lazy-load

Tool calls are expensive. Return all needed data upfront.

❌ `search-recipes` widget + `get-recipe-details` tool (lazy-loading details)
✅ `search-recipes` widget returns full recipe data including details

### Widget handles its own state

Selections, filters, and UI state live in the widget -- not as separate tools.

❌ `select-recipe` tool, `set-filter` tool (these are widget state)
✅ Widget manages selections and filters internally via `useState` or `setState`

### `exposeAsTool` defaults to `false`

Widgets are not auto-registered as tools by default. When you create a custom tool with `widget: { name: "my-widget" }`, omitting `exposeAsTool` in the widget file is correct — the custom tool handles making the widget callable:

```typescript
// resources/my-widget.tsx
export const widgetMetadata: WidgetMetadata = {
  description: "...",
  props: z.object({ ... }),
  // exposeAsTool defaults to false — custom tool definition handles registration
};
```

## Common App Patterns

### Weather App

```
Widget tool: get-weather
  - Input: { city }
  - Widget: temperature, conditions, icon, humidity
  - Output to model: text summary
Tool: get-forecast
  - Input: { city, days }
  - Returns: text or object with daily forecast
```

### Todo List

```
Widget tool: list-todos
  - Widget: interactive checklist with complete/delete buttons
  - Widget calls add-todo, complete-todo, delete-todo via callTool
Tool: add-todo       { title, priority? }
Tool: complete-todo  { id }
Tool: delete-todo    { id }
```

### Recipe Finder

```
Widget tool: search-recipes
  - Input: { query, cuisine? }
  - Widget: recipe cards with images, ingredients, instructions
  - Output to model: text summary of results
Resource: recipe://favorites  (user's saved recipes)
```

### Translator

```
Tool: translate-text
  - Input: { text, targetLanguage, sourceLanguage? }
  - Returns: text (translated result)
Tool: detect-language
  - Input: { text }
  - Returns: object({ language, confidence })
```

### Stock Tracker

```
Widget tool: get-stock
  - Input: { symbol }
  - Widget: price chart, key metrics, news
  - Output to model: price and change summary
Tool: compare-stocks
  - Input: { symbols[] }
  - Returns: object with comparison data
```

## Mock Data Strategy

When the user doesn't specify a real API, use realistic mock data:

```typescript
// Mock data - replace with real API
const mockWeather: Record<
  string,
  { temp: number; conditions: string; humidity: number }
> = {
  "New York": { temp: 22, conditions: "Partly Cloudy", humidity: 65 },
  London: { temp: 15, conditions: "Overcast", humidity: 80 },
  Tokyo: { temp: 28, conditions: "Sunny", humidity: 55 },
  Paris: { temp: 18, conditions: "Light Rain", humidity: 75 },
};

function getWeather(city: string) {
  // Add slight randomization to feel dynamic
  const base = mockWeather[city] || {
    temp: 20,
    conditions: "Clear",
    humidity: 60,
  };
  return {
    ...base,
    temp: base.temp + Math.round((Math.random() - 0.5) * 4),
    humidity: base.humidity + Math.round((Math.random() - 0.5) * 10),
  };
}
```

**Guidelines:**

- Use real names (cities, recipes, products) -- not "Example 1"
- Add slight randomization so it feels dynamic
- Structure like a real API would return
- Comment with `// Mock data - replace with real API`

## Iterative Development

When the user asks to modify or extend existing code:

1. **Read** the current `index.ts` to see what exists
2. **Preserve** all existing tools, resources, and widgets
3. **Add** new functionality alongside existing code
4. **Update** existing widget files rather than creating duplicates
