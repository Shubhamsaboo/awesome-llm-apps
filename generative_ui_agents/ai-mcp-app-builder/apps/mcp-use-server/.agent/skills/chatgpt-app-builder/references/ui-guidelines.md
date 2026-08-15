# UI Guidelines

Display modes, theme, layout constraints, and adapting to host and user context.

## Display Modes

Widgets render **inline by default**. Add fullscreen and/or PiP when the use case benefits.

### Inline (Default)

Widget appears embedded in conversation above the model response.

**Use for:** Single result display, quick actions, browsing items.

**Constraints:**

- Max 2 CTAs (one primary, one secondary)
- No `overflow: scroll/auto` -- content must fit within available space
- No tabs or deep navigation

### Fullscreen

Immersive experience for complex tasks. Host composer remains overlaid at bottom.

**Use for:** Multi-step workflows, rich editing, explorable content, detailed comparisons.

### Picture-in-Picture (PiP)

Persistent floating window during conversation.

**Use for:** Live sessions (timers, streams), games, real-time status.

**Note:** On mobile, PiP coerces to fullscreen.

### Switching Modes

Use `displayMode` and `requestDisplayMode` from `useWidget`:

```tsx
import { useWidget, McpUseProvider } from "mcp-use/react";

function ExpandableWidget() {
  const { props, isPending, displayMode, requestDisplayMode } = useWidget();

  if (isPending)
    return (
      <McpUseProvider autoSize>
        <div>Loading...</div>
      </McpUseProvider>
    );

  const isFullscreen = displayMode === "fullscreen";

  return (
    <McpUseProvider autoSize viewControls>
      {isFullscreen ? (
        <div>
          {/* Expanded layout with more detail */}
          <button onClick={() => requestDisplayMode("inline")}>Collapse</button>
        </div>
      ) : (
        <div>
          {/* Compact layout */}
          <button onClick={() => requestDisplayMode("fullscreen")}>
            Expand
          </button>
        </div>
      )}
    </McpUseProvider>
  );
}
```

**Rules:**

- Switching should be user-triggered only (button click, gesture)
- Host may reject the request
- Always provide a way to return to inline mode

## Theme

Match the host color scheme:

```tsx
import { useWidget } from "mcp-use/react";

function ThemedCard() {
  const { theme } = useWidget();
  const isDark = theme === "dark";

  return (
    <div
      style={{
        background: isDark ? "#1a1a2e" : "#ffffff",
        color: isDark ? "#e0e0e0" : "#1a1a1a",
        padding: 16,
        borderRadius: 8,
      }}
    >
      Content
    </div>
  );
}
```

Or with Tailwind:

```tsx
const { theme } = useWidget();
<div className={theme === "dark" ? "bg-gray-900 text-white" : "bg-white text-gray-900"}>
```

### Convenience Hook

```tsx
import { useWidgetTheme } from "mcp-use/react";
const theme = useWidgetTheme(); // 'light' | 'dark'
```

## Layout Constraints

Use `safeArea` and `maxHeight` from `useWidget` to respect host boundaries:

```tsx
import { useWidget } from "mcp-use/react";

function Container({ children }) {
  const { safeArea, maxHeight } = useWidget();

  return (
    <div
      style={{
        maxHeight,
        paddingTop: safeArea.insets.top,
        paddingBottom: safeArea.insets.bottom,
        paddingLeft: safeArea.insets.left,
        paddingRight: safeArea.insets.right,
      }}
    >
      {children}
    </div>
  );
}
```

| Field       | Type                                       | Description                                          |
| ----------- | ------------------------------------------ | ---------------------------------------------------- |
| `safeArea`  | `{ insets: { top, bottom, left, right } }` | Padding to avoid notches, composer overlay, nav bars |
| `maxHeight` | `number`                                   | Maximum height in pixels (default: 600)              |
| `maxWidth`  | `number \| undefined`                      | Maximum width (MCP Apps only)                        |

## Adapting to User

### Device Type

```tsx
import { useWidget } from "mcp-use/react";

function ResponsiveLayout() {
  const { userAgent } = useWidget();
  const isMobile = userAgent.device.type === "mobile";

  return isMobile ? <MobileLayout /> : <DesktopLayout />;
}
```

### Touch vs Hover

```tsx
const { userAgent } = useWidget();
const canHover = userAgent.capabilities.hover;
const isTouch = userAgent.capabilities.touch;

// Show tooltips only on hover-capable devices
{
  canHover && <Tooltip text="More info" />;
}

// Show tap hint on touch devices
{
  isTouch && <p>Tap to select</p>;
}
```

### Locale

```tsx
import { useWidget } from "mcp-use/react";

function FormattedPrice({ amount }) {
  const { locale } = useWidget();

  const formatted = new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "USD",
  }).format(amount);

  return <span>{formatted}</span>;
}
```

### Time Zone

```tsx
const { timeZone } = useWidget();

const localTime = new Date().toLocaleTimeString("en-US", { timeZone });
```

## McpUseProvider Options

| Prop           | Type                               | Default | Description                       |
| -------------- | ---------------------------------- | ------- | --------------------------------- |
| `autoSize`     | `boolean`                          | `false` | Auto-resize widget to fit content |
| `viewControls` | `boolean \| "pip" \| "fullscreen"` | `false` | Show display mode buttons         |
| `debugger`     | `boolean`                          | `false` | Show debug inspector overlay      |

```tsx
<McpUseProvider autoSize viewControls>
  <div>Widget with auto-size and view controls</div>
</McpUseProvider>
```

## Best Practices

- **Always handle `isPending`** -- widgets render before tool completes
- **Respect `maxHeight`** -- don't force scroll in inline mode
- **Support both themes** -- test light and dark
- **Use `autoSize`** -- let the host know your widget's dimensions
- **User-triggered mode switches** -- never switch programmatically
- **Mobile-first** -- PiP coerces to fullscreen on mobile
