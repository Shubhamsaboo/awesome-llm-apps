# Widget State

Widgets manage their own UI state (selections, filters, tabs, pagination). Never create tools to manage widget state.

**Key principle:** UI state lives in the widget. Server state lives in tools.

---

## Widget State vs Tool State

### Widget State (UI State)

**Managed by widget with `useState` or `setState`:**

- Current selected item
- Active tab
- Filter settings
- Sort order
- Pagination page
- Expanded/collapsed sections
- Form input values (before submission)

### Tool State (Server State)

**Managed by server, returned in tool response:**

- List of items
- User data
- API results
- Computation results
- Database queries

---

## Using React useState

Standard React state management works in widgets:

```tsx
import { useState } from "react";
import { McpUseProvider, useWidget, type WidgetMetadata } from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Product list with filtering",
  props: z.object({
    products: z.array(
      z.object({
        id: z.string(),
        name: z.string(),
        category: z.string(),
        price: z.number(),
      }),
    ),
  }),
  exposeAsTool: false,
};

export default function ProductList() {
  const { props, isPending } = useWidget();
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [sortBy, setSortBy] = useState<"name" | "price">("name");

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  // Filter and sort based on state
  const filtered =
    selectedCategory === "all"
      ? props.products
      : props.products.filter((p) => p.category === selectedCategory);

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === "name") return a.name.localeCompare(b.name);
    return a.price - b.price;
  });

  const categories = ["all", ...new Set(props.products.map((p) => p.category))];

  return (
    <McpUseProvider autoSize>
      <div style={{ padding: 20 }}>
        {/* Category filter */}
        <div style={{ marginBottom: 16 }}>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                padding: "8px 16px",
                margin: "0 4px",
                backgroundColor:
                  selectedCategory === cat ? "#007bff" : "#f0f0f0",
                color: selectedCategory === cat ? "white" : "black",
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Sort controls */}
        <div style={{ marginBottom: 16 }}>
          <label>
            Sort by:
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              style={{ marginLeft: 8 }}
            >
              <option value="name">Name</option>
              <option value="price">Price</option>
            </select>
          </label>
        </div>

        {/* Product list */}
        <div>
          {sorted.map((product) => (
            <div
              key={product.id}
              style={{ padding: 12, border: "1px solid #ddd", marginBottom: 8 }}
            >
              <h3>{product.name}</h3>
              <p>
                Category: {product.category} | ${product.price}
              </p>
            </div>
          ))}
        </div>
      </div>
    </McpUseProvider>
  );
}
```

**Pattern:**

- Tool provides data (products)
- Widget manages UI state (selectedCategory, sortBy)
- Widget renders filtered/sorted view
- No additional tool calls needed

---

## Using setState from useWidget

The `setState` method from `useWidget()` is an alternative to React's `useState` with automatic state persistence across widget interactions. See [basics.md](basics.md#usewidget-hook) for full `useWidget()` API reference.

**When to use `setState` vs `useState`:**

- Use `useState` for simple, ephemeral UI state (resets on widget unmount)
- Use `setState` from `useWidget` for state that persists across interactions

---

## Selection State

Track which item(s) are selected:

```tsx
import { useState } from "react";

export default function ItemSelector() {
  const { props, isPending } = useWidget();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  if (isPending)
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );

  return (
    <McpUseProvider autoSize>
      <div>
        {props.items.map((item) => (
          <div
            key={item.id}
            onClick={() => setSelectedId(item.id)}
            style={{
              padding: 12,
              border: `2px solid ${selectedId === item.id ? "#007bff" : "#ddd"}`,
              marginBottom: 8,
              cursor: "pointer",
            }}
          >
            {item.name}
          </div>
        ))}
      </div>
    </McpUseProvider>
  );
}
```

### Multi-Select

```tsx
const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

const toggleSelection = (id: string) => {
  const newSelection = new Set(selectedIds);
  if (newSelection.has(id)) {
    newSelection.delete(id);
  } else {
    newSelection.add(id);
  }
  setSelectedIds(newSelection);
};

return (
  <McpUseProvider autoSize>
    <div>
      {props.items.map((item) => (
        <div
          key={item.id}
          onClick={() => toggleSelection(item.id)}
          style={{
            padding: 12,
            backgroundColor: selectedIds.has(item.id) ? "#e3f2fd" : "white",
            border: "1px solid #ddd",
          }}
        >
          <input type="checkbox" checked={selectedIds.has(item.id)} readOnly />
          {item.name}
        </div>
      ))}
    </div>
  </McpUseProvider>
);
```

---

## Tab State

Manage tabs without additional tool calls:

```tsx
const [activeTab, setActiveTab] = useState<"overview" | "details" | "history">(
  "overview",
);

return (
  <McpUseProvider autoSize>
    <div>
      {/* Tab buttons */}
      <div style={{ borderBottom: "1px solid #ddd", marginBottom: 16 }}>
        {["overview", "details", "history"].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            style={{
              padding: "8px 16px",
              border: "none",
              borderBottom: activeTab === tab ? "2px solid #007bff" : "none",
              background: "none",
              cursor: "pointer",
            }}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "overview" && <div>{/* Overview content */}</div>}
      {activeTab === "details" && <div>{/* Details content */}</div>}
      {activeTab === "history" && <div>{/* History content */}</div>}
    </div>
  </McpUseProvider>
);
```

---

## Pagination State

Paginate large lists client-side:

```tsx
const [currentPage, setCurrentPage] = useState(1);
const itemsPerPage = 10;

const totalPages = Math.ceil(props.items.length / itemsPerPage);
const startIndex = (currentPage - 1) * itemsPerPage;
const currentItems = props.items.slice(startIndex, startIndex + itemsPerPage);

return (
  <McpUseProvider autoSize>
    <div>
      {/* Items */}
      <div>
        {currentItems.map((item) => (
          <div key={item.id}>{item.name}</div>
        ))}
      </div>

      {/* Pagination controls */}
      <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <button
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
        >
          Previous
        </button>

        <span>
          Page {currentPage} of {totalPages}
        </span>

        <button
          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          disabled={currentPage === totalPages}
        >
          Next
        </button>
      </div>
    </div>
  </McpUseProvider>
);
```

---

## Filter State

Complex filtering:

```tsx
interface Filters {
  search: string;
  category: string;
  priceMin: number;
  priceMax: number;
}

const [filters, setFilters] = useState<Filters>({
  search: "",
  category: "all",
  priceMin: 0,
  priceMax: 1000,
});

const filteredItems = props.items.filter((item) => {
  if (
    filters.search &&
    !item.name.toLowerCase().includes(filters.search.toLowerCase())
  ) {
    return false;
  }
  if (filters.category !== "all" && item.category !== filters.category) {
    return false;
  }
  if (item.price < filters.priceMin || item.price > filters.priceMax) {
    return false;
  }
  return true;
});

return (
  <McpUseProvider autoSize>
    <div>
      {/* Filter controls */}
      <div style={{ marginBottom: 16 }}>
        <input
          type="text"
          placeholder="Search..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          style={{ padding: 8, marginRight: 8 }}
        />

        <select
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          style={{ padding: 8, marginRight: 8 }}
        >
          <option value="all">All Categories</option>
          {/* ... category options */}
        </select>

        <input
          type="number"
          value={filters.priceMin}
          onChange={(e) =>
            setFilters({ ...filters, priceMin: Number(e.target.value) })
          }
          placeholder="Min price"
          style={{ width: 80, padding: 8, marginRight: 8 }}
        />

        <input
          type="number"
          value={filters.priceMax}
          onChange={(e) =>
            setFilters({ ...filters, priceMax: Number(e.target.value) })
          }
          placeholder="Max price"
          style={{ width: 80, padding: 8 }}
        />
      </div>

      {/* Filtered items */}
      <div>
        {filteredItems.map((item) => (
          <div key={item.id}>
            {item.name} - ${item.price}
          </div>
        ))}
      </div>
    </div>
  </McpUseProvider>
);
```

---

## Expand/Collapse State

Accordion or expandable sections:

```tsx
const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

const toggleExpand = (id: string) => {
  const newExpanded = new Set(expandedIds);
  if (newExpanded.has(id)) {
    newExpanded.delete(id);
  } else {
    newExpanded.add(id);
  }
  setExpandedIds(newExpanded);
};

return (
  <McpUseProvider autoSize>
    <div>
      {props.items.map((item) => (
        <div key={item.id} style={{ marginBottom: 8 }}>
          <div
            onClick={() => toggleExpand(item.id)}
            style={{
              padding: 12,
              backgroundColor: "#f5f5f5",
              cursor: "pointer",
              display: "flex",
              justifyContent: "space-between",
            }}
          >
            <span>{item.title}</span>
            <span>{expandedIds.has(item.id) ? "▼" : "▶"}</span>
          </div>

          {expandedIds.has(item.id) && (
            <div style={{ padding: 12, border: "1px solid #ddd" }}>
              {item.details}
            </div>
          )}
        </div>
      ))}
    </div>
  </McpUseProvider>
);
```

---

## Form State

Track form inputs before submission:

```tsx
const [formData, setFormData] = useState({
  name: "",
  email: "",
  message: "",
});

const handleChange = (field: string, value: string) => {
  setFormData((prev) => ({ ...prev, [field]: value }));
};

return (
  <McpUseProvider autoSize>
    <form
      onSubmit={(e) => {
        e.preventDefault();
        // Handle submission (see interactivity.md)
      }}
    >
      <input
        type="text"
        value={formData.name}
        onChange={(e) => handleChange("name", e.target.value)}
        placeholder="Name"
      />

      <input
        type="email"
        value={formData.email}
        onChange={(e) => handleChange("email", e.target.value)}
        placeholder="Email"
      />

      <textarea
        value={formData.message}
        onChange={(e) => handleChange("message", e.target.value)}
        placeholder="Message"
      />

      <button type="submit">Send</button>
    </form>
  </McpUseProvider>
);
```

---

## State Initialization

Initialize state based on props:

```tsx
const [selectedCategory, setSelectedCategory] = useState<string>("");

// Initialize when props load
useEffect(() => {
  if (props.categories && props.categories.length > 0 && !selectedCategory) {
    setSelectedCategory(props.categories[0]);
  }
}, [props.categories, selectedCategory]);
```

**Note:** Lazy initialization like `useState(() => props.categories?.[0] || "all")` won't work here — on the first render `isPending` is `true` and `props` is `{}`, so the initializer always resolves to `"all"`. The `useEffect` pattern above is the correct approach for props that arrive asynchronously.

---

## Common Patterns

### Search + Filter + Sort

```tsx
const [search, setSearch] = useState("");
const [category, setCategory] = useState("all");
const [sortBy, setSortBy] = useState("name");

let filtered = props.items;

// Apply search
if (search) {
  filtered = filtered.filter((item) =>
    item.name.toLowerCase().includes(search.toLowerCase()),
  );
}

// Apply category filter
if (category !== "all") {
  filtered = filtered.filter((item) => item.category === category);
}

// Apply sort
filtered.sort((a, b) => {
  if (sortBy === "name") return a.name.localeCompare(b.name);
  if (sortBy === "price") return a.price - b.price;
  return 0;
});
```

### Master-Detail View

```tsx
const [selectedId, setSelectedId] = useState<string | null>(null);

const selectedItem = selectedId
  ? props.items.find((item) => item.id === selectedId)
  : null;

return (
  <div style={{ display: "flex", gap: 16 }}>
    {/* Master list */}
    <div style={{ flex: 1 }}>
      {props.items.map((item) => (
        <div
          key={item.id}
          onClick={() => setSelectedId(item.id)}
          style={{
            padding: 12,
            backgroundColor: selectedId === item.id ? "#e3f2fd" : "white",
          }}
        >
          {item.name}
        </div>
      ))}
    </div>

    {/* Detail panel */}
    <div style={{ flex: 2 }}>
      {selectedItem ? (
        <div>
          <h2>{selectedItem.name}</h2>
          <p>{selectedItem.description}</p>
        </div>
      ) : (
        <p>Select an item to view details</p>
      )}
    </div>
  </div>
);
```

---

## Anti-Patterns

### ❌ Don't Create Tools for UI State

```typescript
// ❌ Bad - Tool for UI state
server.tool(
  { name: "set-filter", schema: z.object({ category: z.string() }) },
  async ({ category }) => {
    // This is wrong! Filters should be widget state
  },
);

// ✅ Good - Widget manages its own filters
const [filter, setFilter] = useState("all");
```

### ❌ Don't Call Tools for Filtering/Sorting

```typescript
// ❌ Bad - Using a tool call for client-side filtering
const { callTool: filterItems } = useCallTool("filter-items");
<button onClick={() => filterItems({ category: "electronics" })}>
  Filter
</button>

// ✅ Good - Filter in widget
<button onClick={() => setCategory("electronics")}>
  Filter
</button>
```

### ❌ Don't Store UI State in Props

```typescript
// ❌ Bad - Trying to mutate props
props.selectedId = "123"; // Error! Props are read-only

// ✅ Good - Use state
const [selectedId, setSelectedId] = useState<string | null>(null);
```

---

## Best Practices

1. **Keep state local** - Don't lift state unless necessary
2. **Initialize from props** - Use props as initial data, state for UI
3. **Use descriptive names** - `selectedCategory` not `filter`
4. **Reset state appropriately** - When props change, update dependent state
5. **Avoid unnecessary re-renders** - Use `useMemo` for expensive computations

---

## Next Steps

- **Add interactivity** → [interactivity.md](interactivity.md)
- **Style widgets** → [ui-guidelines.md](ui-guidelines.md)
- **Advanced patterns** → [advanced.md](advanced.md)
