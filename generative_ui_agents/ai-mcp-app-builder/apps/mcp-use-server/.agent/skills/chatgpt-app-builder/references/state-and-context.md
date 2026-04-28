# Widget State and LLM Context

Manage persistent state, ephemeral UI state, and LLM interaction from widgets.

## Decision Guide

| Need                                             | Use                                    | Visible to LLM? | Persists? |
| ------------------------------------------------ | -------------------------------------- | --------------- | --------- |
| Persist data across widget reopens               | `state` + `setState` from `useWidget`  | Yes             | Yes       |
| Ephemeral UI only (hover, animation, local form) | React `useState`                       | No              | No        |
| Trigger LLM response from widget                 | `sendFollowUpMessage` from `useWidget` | N/A             | N/A       |
| Call another tool from widget                    | `callTool` from `useWidget`            | N/A             | N/A       |

## Persistent State: `state` + `setState`

State from `useWidget()` persists across widget reopens and is visible to the LLM.

```tsx
import { useWidget } from "mcp-use/react";

function TodoList() {
  const { state, setState } = useWidget();

  const tasks = state?.tasks || [];

  const addTask = async (title: string) => {
    await setState((prev) => ({
      ...prev,
      tasks: [
        ...(prev?.tasks || []),
        { id: Date.now(), title, completed: false },
      ],
    }));
  };

  const toggleTask = async (id: number) => {
    await setState((prev) => ({
      ...prev,
      tasks: prev.tasks.map((t: any) =>
        t.id === id ? { ...t, completed: !t.completed } : t,
      ),
    }));
  };

  return (
    <div>
      {tasks.map((t: any) => (
        <div key={t.id} onClick={() => toggleTask(t.id)}>
          {t.completed ? "✓" : "○"} {t.title}
        </div>
      ))}
    </div>
  );
}
```

**Why `state`:** Tasks and progress survive widget close/reopen. The LLM can read the state to answer "how many tasks are left?"

### Convenience Hook: `useWidgetState`

For simpler access:

```tsx
import { useWidgetState } from "mcp-use/react";

function Counter() {
  const [state, setState] = useWidgetState({ count: 0 });

  return (
    <button
      onClick={() => setState((prev) => ({ count: (prev?.count || 0) + 1 }))}
    >
      Count: {state?.count || 0}
    </button>
  );
}
```

## Ephemeral State: React `useState`

Use React `useState` for UI-only state that doesn't need to persist or be visible to the LLM.

```tsx
import { useState } from "react";

function ProductCard({ product }) {
  // Ephemeral: hover state resets on reopen, LLM doesn't need it
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{ transform: isHovered ? "scale(1.02)" : "scale(1)" }}
    >
      {product.name}
    </div>
  );
}
```

**Why `useState`:** Hover state is purely visual, resets on reopen, and the LLM never needs to know about it.

## Common Mistake

```tsx
// DON'T: useState loses data on close, LLM can't see it
const [selected, setSelected] = useState(null);

// DO: state persists, LLM sees selections
const { state, setState } = useWidget();
const selected = state?.selected;
```

## Calling Other Tools: `callTool`

Widgets can call any tool registered on the server:

```tsx
import { useWidget } from "mcp-use/react";
import { useState } from "react";

function SearchWidget() {
  const { callTool } = useWidget();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (query: string) => {
    setLoading(true);
    try {
      const response = await callTool("search-items", { query });
      setResult(response.content);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={() => handleSearch("shoes")} disabled={loading}>
        {loading ? "Searching..." : "Search"}
      </button>
      {result && <pre>{JSON.stringify(result, null, 2)}</pre>}
    </div>
  );
}
```

## Triggering LLM Response: `sendFollowUpMessage`

Trigger the LLM to respond from a widget interaction:

```tsx
import { useWidget } from "mcp-use/react";

function AnalyzeButton() {
  const { sendFollowUpMessage } = useWidget();

  return (
    <button
      onClick={() =>
        sendFollowUpMessage(
          "Compare the top 3 results and recommend the best one based on price and reviews.",
        )
      }
    >
      Ask AI to Analyze
    </button>
  );
}
```

Use this when:

- User clicks "Find best option" and the LLM should reason about the data
- User completes a selection and the LLM should provide recommendations
- Widget needs the LLM to take action based on current state

## Opening External URLs: `openExternal`

Redirect users to external sites:

```tsx
import { useWidget } from "mcp-use/react";

function CheckoutButton({ checkoutUrl }) {
  const { openExternal } = useWidget();

  return (
    <button onClick={() => openExternal(checkoutUrl)}>
      Proceed to Payment
    </button>
  );
}
```

## Combined Example

Todo list with persistent tasks, ephemeral viewing state, and LLM interaction:

```tsx
import { McpUseProvider, useWidget } from "mcp-use/react";
import { useState } from "react";

export default function TodoWidget() {
  const { props, isPending, state, setState, sendFollowUpMessage } =
    useWidget();

  // PERSISTENT: Tasks survive widget close/reopen, LLM sees them
  const tasks = state?.tasks || props.tasks || [];

  // EPHEMERAL: Which task is being viewed (resets on reopen)
  const [viewing, setViewing] = useState<string | null>(null);

  if (isPending)
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );

  const toggleTask = async (id: string) => {
    await setState((prev: any) => ({
      ...prev,
      tasks: (prev?.tasks || tasks).map((t: any) =>
        t.id === id ? { ...t, completed: !t.completed } : t,
      ),
    }));
  };

  const remaining = tasks.filter((t: any) => !t.completed).length;

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 16 }}>
        <h2>{remaining} tasks remaining</h2>
        {tasks.map((t: any) => (
          <div
            key={t.id}
            onClick={() => setViewing(t.id)}
            style={{
              padding: 8,
              cursor: "pointer",
              opacity: t.completed ? 0.5 : 1,
            }}
          >
            <input
              type="checkbox"
              checked={t.completed}
              onChange={() => toggleTask(t.id)}
            />
            {t.title}
          </div>
        ))}
        <button
          onClick={() =>
            sendFollowUpMessage(
              `I have ${remaining} tasks left. Help me prioritize them.`,
            )
          }
        >
          Ask AI to Prioritize
        </button>
      </div>
    </McpUseProvider>
  );
}
```

**Why each?**

| What                 | API                   | Why                                                             |
| -------------------- | --------------------- | --------------------------------------------------------------- |
| `tasks`              | `state` + `setState`  | Persists. Progress survives reopen. LLM sees completion status. |
| `viewing`            | `useState`            | Ephemeral. Current focus resets on reopen.                      |
| "Help me prioritize" | `sendFollowUpMessage` | Triggers LLM reasoning based on current tasks.                  |
