# Advanced Widget Patterns

Advanced techniques for building complex, performant widgets.

**Topics:** Error boundaries, memoization, async data fetching, code splitting, complex state management

---

## Error Boundaries

Catch React errors and display fallback UI:

```tsx
import { Component, ReactNode } from "react";
import { McpUseProvider, useWidget } from "mcp-use/react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error("Widget error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 20, color: "#c62828" }}>
          <h3>Something went wrong</h3>
          <p>{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Usage
export default function SafeWidget() {
  const { props, isPending } = useWidget();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <ErrorBoundary>
        <WidgetContent props={props} />
      </ErrorBoundary>
    </McpUseProvider>
  );
}
```

---

## useMemo for Performance

Memoize expensive computations:

```tsx
import { useMemo } from "react";
import { McpUseProvider, useWidget } from "mcp-use/react";

export default function OptimizedWidget() {
  const { props, isPending } = useWidget();

  // Expensive computation - only runs when props.items changes
  // Guard against isPending where props.items is undefined
  const sortedAndFiltered = useMemo(() => {
    if (!props.items) return { items: [], total: 0, avgScore: 0 };

    let result = props.items;

    // Filter
    result = result.filter((item) => item.active);

    // Sort
    result.sort((a, b) => b.score - a.score);

    // Compute stats
    return {
      items: result,
      total: result.length,
      avgScore:
        result.length > 0
          ? result.reduce((sum, item) => sum + item.score, 0) / result.length
          : 0,
    };
  }, [props.items]);

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <p>Total: {sortedAndFiltered.total}</p>
        <p>Average: {sortedAndFiltered.avgScore.toFixed(2)}</p>

        {sortedAndFiltered.items.map((item) => (
          <div key={item.id}>{item.name}</div>
        ))}
      </div>
    </McpUseProvider>
  );
}
```

---

## useCallback for Stable Functions

Prevent unnecessary re-renders:

```tsx
import { useCallback, useState } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

export default function CallbackWidget() {
  const { props, isPending } = useWidget();
  const { callToolAsync } = useCallTool("process-item");
  const [loadingId, setLoadingId] = useState<string | null>(null);

  // Stable function reference
  const handleAction = useCallback(
    async (id: string) => {
      setLoadingId(id);
      try {
        await callToolAsync({ id });
      } finally {
        setLoadingId(null);
      }
    },
    [callToolAsync],
  );

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
        {props.items.map((item) => (
          <ItemRow
            key={item.id}
            item={item}
            onAction={handleAction}
            loading={loadingId === item.id}
          />
        ))}
      </div>
    </McpUseProvider>
  );
}

// Child component won't re-render unnecessarily
const ItemRow = React.memo(({ item, onAction, loading }: any) => (
  <div>
    <span>{item.name}</span>
    <button onClick={() => onAction(item.id)} disabled={loading}>
      {loading ? "Processing..." : "Process"}
    </button>
  </div>
));
```

---

## Async Data Fetching (Client-Side)

Fetch additional data from widget:

```tsx
import { useState, useEffect } from "react";
import { McpUseProvider, useWidget } from "mcp-use/react";

export default function AsyncWidget() {
  const { props, isPending } = useWidget();
  const [details, setDetails] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!isPending && props.itemId) {
      setLoading(true);
      fetch(`/api/items/${props.itemId}/details`)
        .then((res) => res.json())
        .then((data) => setDetails(data))
        .catch((err) => console.error("Failed to load details:", err))
        .finally(() => setLoading(false));
    }
  }, [isPending, props.itemId]);

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <h2>{props.title}</h2>

        {loading && <p>Loading details...</p>}

        {details && (
          <div>
            <h3>Details</h3>
            <pre>{JSON.stringify(details, null, 2)}</pre>
          </div>
        )}
      </div>
    </McpUseProvider>
  );
}
```

**Prefer tool calls over direct API calls:**

```tsx
// ✅ Better - Use useCallTool
const { callToolAsync } = useCallTool("get-item-details");

useEffect(() => {
  if (!isPending && props.itemId) {
    setLoading(true);
    callToolAsync({ id: props.itemId })
      .then((result) => setDetails(result))
      .finally(() => setLoading(false));
  }
}, [isPending, props.itemId, callToolAsync]);
```

---

## Complex State Management

Use useReducer for complex state:

```tsx
import { useReducer } from "react";
import { McpUseProvider, useWidget } from "mcp-use/react";

type State = {
  selectedIds: Set<string>;
  filters: { category: string; search: string };
  sortBy: string;
  sortOrder: "asc" | "desc";
};

type Action =
  | { type: "TOGGLE_SELECT"; id: string }
  | { type: "SET_FILTER"; key: string; value: string }
  | { type: "SET_SORT"; by: string }
  | { type: "TOGGLE_SORT_ORDER" }
  | { type: "RESET" };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "TOGGLE_SELECT":
      const newSelection = new Set(state.selectedIds);
      if (newSelection.has(action.id)) {
        newSelection.delete(action.id);
      } else {
        newSelection.add(action.id);
      }
      return { ...state, selectedIds: newSelection };

    case "SET_FILTER":
      return {
        ...state,
        filters: { ...state.filters, [action.key]: action.value },
      };

    case "SET_SORT":
      return { ...state, sortBy: action.by };

    case "TOGGLE_SORT_ORDER":
      return {
        ...state,
        sortOrder: state.sortOrder === "asc" ? "desc" : "asc",
      };

    case "RESET":
      return {
        selectedIds: new Set(),
        filters: { category: "all", search: "" },
        sortBy: "name",
        sortOrder: "asc",
      };

    default:
      return state;
  }
}

export default function ComplexWidget() {
  const { props, isPending } = useWidget();
  const [state, dispatch] = useReducer(reducer, {
    selectedIds: new Set(),
    filters: { category: "all", search: "" },
    sortBy: "name",
    sortOrder: "asc",
  });

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <input
          type="text"
          value={state.filters.search}
          onChange={(e) =>
            dispatch({
              type: "SET_FILTER",
              key: "search",
              value: e.target.value,
            })
          }
          placeholder="Search..."
        />

        <button onClick={() => dispatch({ type: "RESET" })}>
          Reset Filters
        </button>

        {/* ... render items with state */}
      </div>
    </McpUseProvider>
  );
}
```

---

## Virtualization for Large Lists

Render only visible items:

```tsx
import { useState, useRef, useEffect } from "react";
import { McpUseProvider, useWidget } from "mcp-use/react";

export default function VirtualizedList() {
  const { props, isPending } = useWidget();
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const itemHeight = 50;
  const containerHeight = 400;
  const overscan = 3;

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  const visibleStart = Math.max(
    0,
    Math.floor(scrollTop / itemHeight) - overscan,
  );
  const visibleEnd = Math.min(
    props.items.length,
    Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan,
  );

  const visibleItems = props.items.slice(visibleStart, visibleEnd);

  return (
    <McpUseProvider autoSize>
      <div
        ref={containerRef}
        onScroll={(e) => setScrollTop(e.currentTarget.scrollTop)}
        style={{
          height: containerHeight,
          overflow: "auto",
          position: "relative",
        }}
      >
        <div
          style={{
            height: props.items.length * itemHeight,
            position: "relative",
          }}
        >
          {visibleItems.map((item, index) => (
            <div
              key={item.id}
              style={{
                position: "absolute",
                top: (visibleStart + index) * itemHeight,
                height: itemHeight,
                width: "100%",
                padding: 12,
                borderBottom: "1px solid #eee",
              }}
            >
              {item.name}
            </div>
          ))}
        </div>
      </div>
    </McpUseProvider>
  );
}
```

---

## Debounced Search

> **Prerequisites:** For interactive widgets (buttons, forms, tool calls), read [interactivity.md](interactivity.md) first for foundational patterns.

Delay search to avoid excessive calls:

```tsx
import { useState, useEffect } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

export default function DebouncedSearchWidget() {
  const { props, isPending } = useWidget();
  const { callToolAsync } = useCallTool("search");
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<{ id: string; name: string }[]>([]);
  const [searching, setSearching] = useState(false);

  const debouncedSearch = useDebounce(search, 300);

  useEffect(() => {
    if (!debouncedSearch.trim()) {
      setResults([]);
      return;
    }

    setSearching(true);
    callToolAsync({ query: debouncedSearch })
      .then((result) => setResults(result.structuredContent?.items || []))
      .catch((err) => console.error("Search failed:", err))
      .finally(() => setSearching(false));
  }, [debouncedSearch, callToolAsync]);

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search..."
          style={{ width: "100%", padding: 8 }}
        />

        {searching && <p>Searching...</p>}

        <div>
          {results.map((item) => (
            <div key={item.id}>{item.name}</div>
          ))}
        </div>
      </div>
    </McpUseProvider>
  );
}
```

---

## Infinite Scroll

Load more items as user scrolls:

```tsx
import { useState, useRef, useEffect } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

interface Item {
  id: string;
  name: string;
}

export default function InfiniteScrollWidget() {
  const { props, isPending } = useWidget<{ items: Item[] }>();
  const { callToolAsync } = useCallTool("load-more");
  const [items, setItems] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const observerTarget = useRef<HTMLDivElement>(null);

  // Sync initial items from props once loaded
  useEffect(() => {
    if (!isPending && props.items) {
      setItems(props.items);
    }
  }, [isPending, props.items]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          loadMore();
        }
      },
      { threshold: 1.0 },
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [hasMore, loading]);

  const loadMore = async () => {
    setLoading(true);
    try {
      const result = await callToolAsync({
        offset: items.length,
        limit: 20,
      });

      const newItems = result.structuredContent?.items || [];
      if (newItems.length === 0) {
        setHasMore(false);
      } else {
        setItems((prev) => [...prev, ...newItems]);
      }
    } catch (error) {
      console.error("Failed to load more:", error);
    } finally {
      setLoading(false);
    }
  };

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        {items.map((item) => (
          <div
            key={item.id}
            style={{ padding: 12, borderBottom: "1px solid #eee" }}
          >
            {item.name}
          </div>
        ))}

        <div ref={observerTarget} style={{ height: 20 }}>
          {loading && <p>Loading more...</p>}
          {!hasMore && <p>No more items</p>}
        </div>
      </div>
    </McpUseProvider>
  );
}
```

---

## Local Storage Persistence

Persist widget state across sessions:

```tsx
import { useState, useEffect } from "react";
import { McpUseProvider, useWidget } from "mcp-use/react";

function useLocalStorage<T>(
  key: string,
  initialValue: T,
): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error("Error reading from localStorage:", error);
      return initialValue;
    }
  });

  const setValue = (value: T) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error("Error writing to localStorage:", error);
    }
  };

  return [storedValue, setValue];
}

export default function PersistentWidget() {
  const { props, isPending } = useWidget();
  const [favorites, setFavorites] = useLocalStorage<string[]>("favorites", []);

  const toggleFavorite = (id: string) => {
    setFavorites((prev) =>
      prev.includes(id) ? prev.filter((fav) => fav !== id) : [...prev, id],
    );
  };

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
        {props.items.map((item) => (
          <div key={item.id}>
            <button onClick={() => toggleFavorite(item.id)}>
              {favorites.includes(item.id) ? "⭐" : "☆"}
            </button>
            {item.name}
          </div>
        ))}
      </div>
    </McpUseProvider>
  );
}
```

---

## Drag and Drop

Reorder items with drag and drop:

```tsx
import { useState, useEffect } from "react";
import { McpUseProvider, useWidget } from "mcp-use/react";

interface Item {
  id: string;
  name: string;
}

export default function DraggableList() {
  const { props, isPending } = useWidget<{ items: Item[] }>();
  const [items, setItems] = useState<Item[]>([]);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // Sync items from props once loaded
  useEffect(() => {
    if (!isPending && props.items) {
      setItems(props.items);
    }
  }, [isPending, props.items]);

  const handleDragStart = (index: number) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e: React.DragEvent, index: number) => {
    e.preventDefault();

    if (draggedIndex === null || draggedIndex === index) return;

    const newItems = [...items];
    const draggedItem = newItems[draggedIndex];

    newItems.splice(draggedIndex, 1);
    newItems.splice(index, 0, draggedItem);

    setItems(newItems);
    setDraggedIndex(index);
  };

  const handleDragEnd = () => {
    setDraggedIndex(null);
    // Optionally save new order with useCallTool
  };

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
        {items.map((item, index) => (
          <div
            key={item.id}
            draggable
            onDragStart={() => handleDragStart(index)}
            onDragOver={(e) => handleDragOver(e, index)}
            onDragEnd={handleDragEnd}
            style={{
              padding: 12,
              margin: "4px 0",
              backgroundColor: draggedIndex === index ? "#e3f2fd" : "white",
              border: "1px solid #ddd",
              cursor: "move",
            }}
          >
            ⋮⋮ {item.name}
          </div>
        ))}
      </div>
    </McpUseProvider>
  );
}
```

---

## Keyboard Shortcuts

```tsx
import { useEffect } from "react";
import { McpUseProvider, useWidget, useCallTool } from "mcp-use/react";

export default function KeyboardWidget() {
  const { props, isPending } = useWidget();
  const { callTool: save } = useCallTool("save");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+S to save
      if (e.ctrlKey && e.key === "s") {
        e.preventDefault();
        save({});
      }

      // Escape to cancel
      if (e.key === "Escape") {
        // Handle escape
      }

      // Arrow keys for navigation
      if (e.key === "ArrowDown") {
        // Navigate down
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [save]);

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
        <p>Keyboard shortcuts:</p>
        <ul>
          <li>
            <kbd>Ctrl+S</kbd> - Save
          </li>
          <li>
            <kbd>Esc</kbd> - Cancel
          </li>
          <li>
            <kbd>↑/↓</kbd> - Navigate
          </li>
        </ul>
      </div>
    </McpUseProvider>
  );
}
```

---

## Best Practices

1. **Use Error Boundaries** - Catch errors gracefully
2. **Memoize Expensive Computations** - Use `useMemo` for performance
3. **Debounce User Input** - Avoid excessive API calls
4. **Virtualize Large Lists** - Render only visible items
5. **Persist State When Useful** - Use localStorage for preferences
6. **Handle Loading States** - Show spinners, disable buttons
7. **Implement Keyboard Shortcuts** - Improve power user experience
8. **Profile Performance** - Use React DevTools Profiler

---

## Performance Checklist

- [ ] Large lists virtualized or paginated
- [ ] Expensive computations memoized with `useMemo`
- [ ] Event handlers memoized with `useCallback`
- [ ] Search inputs debounced
- [ ] Images lazy-loaded
- [ ] Error boundaries in place
- [ ] Console warnings addressed

---

## Next Steps

- **See examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)
- **Review best practices** → [../../SKILL.md](../../SKILL.md)
