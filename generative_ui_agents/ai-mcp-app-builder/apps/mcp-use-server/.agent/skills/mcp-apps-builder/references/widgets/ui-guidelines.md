# Widget UI Guidelines

Build widgets that adapt to themes, look professional, and provide great user experience.

**Key topics:** Theme support, light/dark mode, responsive layouts, accessibility, CSS best practices

---

## Theme Support with useWidgetTheme()

Widgets should adapt to the user's theme (light/dark mode):

```tsx
import {
  McpUseProvider,
  useWidget,
  useWidgetTheme,
  type WidgetMetadata,
} from "mcp-use/react";
import { z } from "zod";

export const widgetMetadata: WidgetMetadata = {
  description: "Theme-aware widget",
  props: z.object({
    message: z.string(),
  }),
  exposeAsTool: false,
};

export default function ThemedWidget() {
  const { props, isPending } = useWidget();
  const theme = useWidgetTheme();

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );
  }

  return (
    <McpUseProvider autoSize>
      <div
        style={{
          padding: 20,
          backgroundColor: theme === "dark" ? "#1e1e1e" : "#ffffff",
          color: theme === "dark" ? "#ffffff" : "#000000",
        }}
      >
        <p>{props.message}</p>
      </div>
    </McpUseProvider>
  );
}
```

**useWidgetTheme() returns:** `"light"` or `"dark"`

---

## Theme-Aware Colors

Define color palettes for both themes:

```tsx
const theme = useWidgetTheme();

const colors = {
  background: theme === "dark" ? "#1e1e1e" : "#ffffff",
  text: theme === "dark" ? "#e0e0e0" : "#1a1a1a",
  border: theme === "dark" ? "#404040" : "#e0e0e0",
  primary: theme === "dark" ? "#4a9eff" : "#0066cc",
  secondary: theme === "dark" ? "#6c757d" : "#6c757d",
  hover: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
  error: theme === "dark" ? "#ff6b6b" : "#dc3545",
  success: theme === "dark" ? "#51cf66" : "#28a745",
};

return (
  <McpUseProvider autoSize>
    <div
      style={{
        backgroundColor: colors.background,
        color: colors.text,
        border: `1px solid ${colors.border}`,
      }}
    >
      {/* Your content */}
    </div>
  </McpUseProvider>
);
```

Or extract to a hook:

```tsx
function useColors() {
  const theme = useWidgetTheme();

  return {
    background: theme === "dark" ? "#1e1e1e" : "#ffffff",
    text: theme === "dark" ? "#e0e0e0" : "#1a1a1a",
    border: theme === "dark" ? "#404040" : "#e0e0e0",
    primary: theme === "dark" ? "#4a9eff" : "#0066cc",
    hover: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
    error: theme === "dark" ? "#ff6b6b" : "#dc3545",
  };
}

export default function ThemedWidget() {
  const colors = useColors();
  // ... rest of component
}
```

---

## Responsive Layouts

### Grid Layout

```tsx
<div
  style={{
    display: "grid",
    gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
    gap: 16,
    padding: 20,
  }}
>
  {props.items.map((item) => (
    <div
      key={item.id}
      style={{
        padding: 12,
        border: `1px solid ${colors.border}`,
        borderRadius: 8,
      }}
    >
      {item.name}
    </div>
  ))}
</div>
```

### Flexbox Layout

```tsx
<div
  style={{
    display: "flex",
    gap: 16,
    padding: 20,
    flexWrap: "wrap",
  }}
>
  {props.items.map((item) => (
    <div
      key={item.id}
      style={{
        flex: "1 1 200px",
        padding: 12,
        border: `1px solid ${colors.border}`,
      }}
    >
      {item.name}
    </div>
  ))}
</div>
```

### Two-Column Layout

```tsx
<div
  style={{
    display: "flex",
    gap: 16,
    padding: 20,
  }}
>
  {/* Sidebar */}
  <div style={{ flex: "0 0 250px" }}>{/* Navigation or filters */}</div>

  {/* Main content */}
  <div style={{ flex: 1 }}>{/* Primary content */}</div>
</div>
```

---

## Button Styles

Theme-aware buttons:

```tsx
const theme = useWidgetTheme();

const buttonStyle: React.CSSProperties = {
  padding: "8px 16px",
  border: "none",
  borderRadius: 4,
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 500,
  backgroundColor: theme === "dark" ? "#4a9eff" : "#0066cc",
  color: "#ffffff",
};

const secondaryButtonStyle: React.CSSProperties = {
  ...buttonStyle,
  backgroundColor: "transparent",
  border: `1px solid ${theme === "dark" ? "#404040" : "#e0e0e0"}`,
  color: theme === "dark" ? "#e0e0e0" : "#1a1a1a",
};

return (
  <McpUseProvider autoSize>
    <div>
      <button style={buttonStyle}>Primary Action</button>
      <button style={secondaryButtonStyle}>Secondary</button>
    </div>
  </McpUseProvider>
);
```

### Button States

```tsx
const [hovered, setHovered] = useState(false);

<button
  style={{
    padding: "8px 16px",
    backgroundColor: hovered
      ? theme === "dark"
        ? "#5aa8ff"
        : "#0052a3"
      : theme === "dark"
        ? "#4a9eff"
        : "#0066cc",
    color: "#ffffff",
    border: "none",
    borderRadius: 4,
    cursor: "pointer",
    transition: "background-color 0.2s",
  }}
  onMouseEnter={() => setHovered(true)}
  onMouseLeave={() => setHovered(false)}
>
  Hover Me
</button>;
```

---

## Card Components

```tsx
const theme = useWidgetTheme();

const cardStyle: React.CSSProperties = {
  padding: 16,
  border: `1px solid ${theme === "dark" ? "#404040" : "#e0e0e0"}`,
  borderRadius: 8,
  backgroundColor: theme === "dark" ? "#1e1e1e" : "#ffffff",
  color: theme === "dark" ? "#e0e0e0" : "#1a1a1a",
};

return (
  <McpUseProvider autoSize>
    <div style={{ padding: 20 }}>
      {props.items.map((item) => (
        <div
          key={item.id}
          style={{
            ...cardStyle,
            marginBottom: 12,
          }}
        >
          <h3 style={{ margin: "0 0 8px 0" }}>{item.title}</h3>
          <p
            style={{ margin: 0, color: theme === "dark" ? "#b0b0b0" : "#666" }}
          >
            {item.description}
          </p>
        </div>
      ))}
    </div>
  </McpUseProvider>
);
```

---

## Typography

```tsx
const theme = useWidgetTheme();

<div style={{ padding: 20 }}>
  {/* Heading */}
  <h1
    style={{
      fontSize: 24,
      fontWeight: 600,
      margin: "0 0 16px 0",
      color: theme === "dark" ? "#ffffff" : "#1a1a1a",
    }}
  >
    Title
  </h1>

  {/* Subheading */}
  <h2
    style={{
      fontSize: 18,
      fontWeight: 500,
      margin: "0 0 12px 0",
      color: theme === "dark" ? "#e0e0e0" : "#333",
    }}
  >
    Subtitle
  </h2>

  {/* Body text */}
  <p
    style={{
      fontSize: 14,
      lineHeight: 1.5,
      margin: "0 0 12px 0",
      color: theme === "dark" ? "#b0b0b0" : "#666",
    }}
  >
    Body content here
  </p>

  {/* Small text */}
  <span
    style={{
      fontSize: 12,
      color: theme === "dark" ? "#808080" : "#999",
    }}
  >
    Small text or metadata
  </span>
</div>;
```

---

## Form Inputs

```tsx
const theme = useWidgetTheme();

const inputStyle: React.CSSProperties = {
  padding: 8,
  fontSize: 14,
  border: `1px solid ${theme === "dark" ? "#404040" : "#d0d0d0"}`,
  borderRadius: 4,
  backgroundColor: theme === "dark" ? "#2a2a2a" : "#ffffff",
  color: theme === "dark" ? "#e0e0e0" : "#1a1a1a",
  outline: "none",
};

<form style={{ padding: 20 }}>
  <label
    style={{
      display: "block",
      marginBottom: 4,
      fontSize: 14,
      fontWeight: 500,
      color: theme === "dark" ? "#e0e0e0" : "#333",
    }}
  >
    Name
  </label>
  <input type="text" style={inputStyle} placeholder="Enter name..." />

  <label style={{ display: "block", marginTop: 12, marginBottom: 4 }}>
    Description
  </label>
  <textarea
    style={{
      ...inputStyle,
      width: "100%",
      minHeight: 80,
      resize: "vertical",
    }}
    placeholder="Enter description..."
  />
</form>;
```

---

## Lists

```tsx
const theme = useWidgetTheme();

<ul
  style={{
    listStyle: "none",
    padding: 0,
    margin: 0,
  }}
>
  {props.items.map((item) => (
    <li
      key={item.id}
      style={{
        padding: 12,
        borderBottom: `1px solid ${theme === "dark" ? "#2a2a2a" : "#f0f0f0"}`,
        cursor: "pointer",
        transition: "background-color 0.15s",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor =
          theme === "dark" ? "#2a2a2a" : "#f5f5f5";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "transparent";
      }}
    >
      {item.name}
    </li>
  ))}
</ul>;
```

---

## Badges and Tags

```tsx
const theme = useWidgetTheme();

const badgeStyle: React.CSSProperties = {
  display: "inline-block",
  padding: "4px 8px",
  fontSize: 12,
  fontWeight: 500,
  borderRadius: 12,
  backgroundColor: theme === "dark" ? "#2a4a6a" : "#e3f2fd",
  color: theme === "dark" ? "#4a9eff" : "#0066cc",
};

<div>
  <span style={badgeStyle}>New</span>
  <span style={{ ...badgeStyle, marginLeft: 8 }}>Featured</span>
</div>;
```

---

## Loading States

```tsx
const theme = useWidgetTheme();

if (isPending) {
  return (
    <McpUseProvider autoSize>
      <div
        style={{
          padding: 40,
          textAlign: "center",
          color: theme === "dark" ? "#808080" : "#999",
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            border: `4px solid ${theme === "dark" ? "#404040" : "#e0e0e0"}`,
            borderTop: `4px solid ${theme === "dark" ? "#4a9eff" : "#0066cc"}`,
            borderRadius: "50%",
            margin: "0 auto 16px",
            animation: "spin 1s linear infinite",
          }}
        />
        <p>Loading...</p>
      </div>
    </McpUseProvider>
  );
}
```

Add spin animation:

```tsx
<style>
  {`
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `}
</style>
```

---

## Empty States

```tsx
const theme = useWidgetTheme();

{
  props.items.length === 0 && (
    <div
      style={{
        padding: 40,
        textAlign: "center",
        color: theme === "dark" ? "#808080" : "#999",
      }}
    >
      <div
        style={{
          fontSize: 48,
          marginBottom: 16,
          opacity: 0.5,
        }}
      >
        📭
      </div>
      <h3
        style={{
          fontSize: 18,
          fontWeight: 500,
          margin: "0 0 8px 0",
          color: theme === "dark" ? "#b0b0b0" : "#666",
        }}
      >
        No items yet
      </h3>
      <p
        style={{
          fontSize: 14,
          margin: 0,
          color: theme === "dark" ? "#808080" : "#999",
        }}
      >
        Get started by creating your first item
      </p>
    </div>
  );
}
```

---

## Error States

```tsx
const theme = useWidgetTheme();

{
  error && (
    <div
      style={{
        padding: 12,
        marginBottom: 16,
        backgroundColor: theme === "dark" ? "#3d1f1f" : "#ffebee",
        color: theme === "dark" ? "#ff6b6b" : "#c62828",
        border: `1px solid ${theme === "dark" ? "#6b2a2a" : "#ffcdd2"}`,
        borderRadius: 4,
      }}
    >
      <strong>Error:</strong> {error}
    </div>
  );
}
```

---

## Icons

Use Unicode emojis or SVG icons:

```tsx
// Emojis
<span style={{ fontSize: 24, marginRight: 8 }}>⚙️</span>
<span style={{ fontSize: 20 }}>✓</span>
<span>❌</span>

// SVG icon
<svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
  <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z"/>
</svg>
```

---

## Spacing Guidelines

```tsx
// Consistent spacing units
const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
};

<div
  style={{
    padding: spacing.lg,
    gap: spacing.md,
  }}
>
  {/* Content */}
</div>;
```

---

## Accessibility

### Labels for Inputs

```tsx
<label htmlFor="email-input">Email</label>
<input id="email-input" type="email" />
```

### Alt Text for Images

```tsx
<img src={item.image} alt={item.name} />
```

### Button Labels

```tsx
<button aria-label="Delete item">🗑️</button>
```

### Keyboard Navigation

```tsx
<div
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === "Enter" || e.key === " ") {
      handleClick();
    }
  }}
>
  Clickable item
</div>
```

---

## Auto-Size Best Practices

`<McpUseProvider autoSize>` automatically resizes iframe to content.

**Tips:**

- Use `autoSize` for dynamic content
- Avoid fixed heights unless necessary
- Widget resizes when content changes
- Test with varying content sizes

```tsx
// ✅ Good - autoSize handles height
<McpUseProvider autoSize>
  <div style={{ padding: 20 }}>
    {/* Dynamic content */}
  </div>
</McpUseProvider>

// ❌ Bad - Fixed height defeats autoSize
<McpUseProvider autoSize>
  <div style={{ height: 400, overflow: "auto" }}>
    {/* Content */}
  </div>
</McpUseProvider>
```

---

## Complete Themed Widget

```tsx
import { useState } from "react";
import {
  McpUseProvider,
  useWidget,
  useWidgetTheme,
  type WidgetMetadata,
} from "mcp-use/react";
import { z } from "zod";

function useColors() {
  const theme = useWidgetTheme();

  return {
    background: theme === "dark" ? "#1e1e1e" : "#ffffff",
    text: theme === "dark" ? "#e0e0e0" : "#1a1a1a",
    textSecondary: theme === "dark" ? "#b0b0b0" : "#666",
    border: theme === "dark" ? "#404040" : "#e0e0e0",
    hover: theme === "dark" ? "#2a2a2a" : "#f5f5f5",
    primary: theme === "dark" ? "#4a9eff" : "#0066cc",
  };
}

export const widgetMetadata: WidgetMetadata = {
  description: "Fully themed product list",
  props: z.object({
    products: z.array(
      z.object({
        id: z.string(),
        name: z.string(),
        price: z.number(),
        category: z.string(),
      }),
    ),
  }),
  exposeAsTool: false,
};

export default function ThemedProductList() {
  const { props, isPending } = useWidget();
  const colors = useColors();
  const [selectedCategory, setSelectedCategory] = useState("all");

  if (isPending) {
    return (
      <McpUseProvider autoSize>
        <div
          style={{
            padding: 40,
            textAlign: "center",
            color: colors.textSecondary,
          }}
        >
          Loading...
        </div>
      </McpUseProvider>
    );
  }

  const categories = ["all", ...new Set(props.products.map((p) => p.category))];
  const filtered =
    selectedCategory === "all"
      ? props.products
      : props.products.filter((p) => p.category === selectedCategory);

  return (
    <McpUseProvider autoSize>
      <div
        style={{
          padding: 20,
          backgroundColor: colors.background,
          color: colors.text,
        }}
      >
        <h2 style={{ margin: "0 0 16px 0" }}>Products</h2>

        {/* Category filters */}
        <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              style={{
                padding: "8px 16px",
                borderRadius: 4,
                cursor: "pointer",
                backgroundColor:
                  selectedCategory === cat ? colors.primary : "transparent",
                color: selectedCategory === cat ? "#fff" : colors.text,
                border: `1px solid ${selectedCategory === cat ? colors.primary : colors.border}`,
              }}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Product grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: 12,
          }}
        >
          {filtered.map((product) => (
            <div
              key={product.id}
              style={{
                padding: 12,
                border: `1px solid ${colors.border}`,
                borderRadius: 8,
                backgroundColor: colors.background,
              }}
            >
              <h3 style={{ margin: "0 0 4px 0", fontSize: 16 }}>
                {product.name}
              </h3>
              <p
                style={{
                  margin: "0 0 8px 0",
                  fontSize: 12,
                  color: colors.textSecondary,
                }}
              >
                {product.category}
              </p>
              <p
                style={{
                  margin: 0,
                  fontSize: 18,
                  fontWeight: "bold",
                  color: colors.primary,
                }}
              >
                ${product.price}
              </p>
            </div>
          ))}
        </div>

        {filtered.length === 0 && (
          <div
            style={{
              padding: 40,
              textAlign: "center",
              color: colors.textSecondary,
            }}
          >
            No products in this category
          </div>
        )}
      </div>
    </McpUseProvider>
  );
}
```

---

## Next Steps

- **Advanced patterns** → [advanced.md](advanced.md)
- **See examples** → [../patterns/common-patterns.md](../patterns/common-patterns.md)
