# Components API Reference

React components provided by mcp-use for ChatGPT widgets.

## Table of Contents

- [McpUseProvider](#mcpuseprovider)
- [Image](#image)
- [ErrorBoundary](#errorboundary)
- [useWidget Hook](#usewidget-hook)

## McpUseProvider

Unified provider combining all common setup. Wrap your widget content:

```tsx
import { McpUseProvider } from "mcp-use/react";

function MyWidget() {
  return (
    <McpUseProvider
      autoSize // Auto-resize widget to content
      viewControls // Add debug/fullscreen buttons
      debug // Show debug info
    >
      <div>Widget content</div>
    </McpUseProvider>
  );
}
```

### Props

| Prop           | Type      | Default  | Description                           |
| -------------- | --------- | -------- | ------------------------------------- |
| `autoSize`     | boolean   | false    | Auto-resize widget height to content  |
| `viewControls` | boolean   | false    | Show debug/fullscreen control buttons |
| `debug`        | boolean   | false    | Display debug information overlay     |
| `children`     | ReactNode | required | Widget content                        |

### What It Includes

- `StrictMode` - React strict mode
- `ThemeProvider` - Theme context (light/dark)
- `BrowserRouter` - React Router support
- `WidgetControls` - Optional debug controls
- `ErrorBoundary` - Graceful error handling

## Image

Handles both data URLs and public paths:

```tsx
import { Image } from "mcp-use/react";

function MyWidget() {
  return (
    <div>
      {/* From public/ folder */}
      <Image src="/images/photo.jpg" alt="Photo" />

      {/* Data URL */}
      <Image src="data:image/png;base64,..." alt="Base64 image" />

      {/* With styling */}
      <Image
        src="/icons/logo.svg"
        alt="Logo"
        className="w-16 h-16"
        style={{ borderRadius: "8px" }}
      />
    </div>
  );
}
```

### Props

| Prop        | Type              | Description                                  |
| ----------- | ----------------- | -------------------------------------------- |
| `src`       | string            | Image path (relative to public/) or data URL |
| `alt`       | string            | Alt text for accessibility                   |
| `className` | string            | CSS classes                                  |
| `style`     | CSSProperties     | Inline styles                                |
| ...rest     | ImgHTMLAttributes | All standard img attributes                  |

### Alternative: window.**getFile**

For non-Image elements or dynamic paths:

```tsx
function MyWidget() {
  const bannerUrl = window.__getFile__?.("images/banner.png");

  return (
    <div style={{ backgroundImage: `url(${bannerUrl})` }}>
      Content with background
    </div>
  );
}
```

## ErrorBoundary

Graceful error handling for widgets:

```tsx
import { ErrorBoundary } from "mcp-use/react";

function MyWidget() {
  return (
    <ErrorBoundary
      fallback={<div className="error">Something went wrong</div>}
      onError={(error, errorInfo) => {
        console.error("Widget error:", error);
        // Optional: send to error tracking service
      }}
    >
      <RiskyComponent />
    </ErrorBoundary>
  );
}
```

### Props

| Prop       | Type                       | Description                   |
| ---------- | -------------------------- | ----------------------------- |
| `fallback` | ReactNode                  | UI to show when error occurs  |
| `onError`  | (error, errorInfo) => void | Callback when error is caught |
| `children` | ReactNode                  | Components that might throw   |

### Custom Fallback with Reset

```tsx
function ErrorFallback({ error, reset }) {
  return (
    <div className="p-4 bg-red-100 rounded">
      <h3>Error occurred</h3>
      <p>{error.message}</p>
      <button onClick={reset}>Try again</button>
    </div>
  );
}

function MyWidget() {
  return (
    <ErrorBoundary fallback={ErrorFallback}>
      <MyComponent />
    </ErrorBoundary>
  );
}
```

## useWidget Hook

Complete hook API reference:

```tsx
const {
  // Core data
  props, // Widget input from tool call (empty {} while pending)
  isPending, // True while tool still executing
  toolInput, // Original tool input arguments
  output, // Additional tool output
  metadata, // Response metadata

  // Persistent state
  state, // Persisted widget state (survives re-renders and reopens)
  setState, // Update persistent state

  // Host environment
  theme, // 'light' | 'dark'
  displayMode, // 'inline' | 'pip' | 'fullscreen'
  safeArea, // { insets: { top, bottom, left, right } }
  maxHeight, // Max available height (default 600)
  maxWidth, // Max available width (MCP Apps only)
  userAgent, // { device: { type }, capabilities: { hover, touch } }
  locale, // User locale (e.g., 'en-US')
  timeZone, // IANA timezone

  // Actions
  callTool, // Call another MCP tool
  sendFollowUpMessage, // Trigger LLM response from widget
  openExternal, // Open external URL
  requestDisplayMode, // Request display mode change
  mcp_url, // MCP server base URL
  isAvailable, // Whether widget API is available
} = useWidget<PropsType, OutputType>();
```

### Return Values

| Value                 | Type                              | Description                                              |
| --------------------- | --------------------------------- | -------------------------------------------------------- |
| `props`               | PropsType                         | Widget input from tool call (empty `{}` while pending)   |
| `isPending`           | boolean                           | True while tool is still executing                       |
| `toolInput`           | object                            | Original input arguments passed to the tool              |
| `output`              | OutputType                        | Additional output data from tool                         |
| `metadata`            | object                            | Response metadata                                        |
| `state`               | any                               | Persisted widget state (survives re-renders and reopens) |
| `setState`            | (state \| updater) => Promise     | Update persistent state                                  |
| `theme`               | 'light' \| 'dark'                 | Current theme from host                                  |
| `displayMode`         | 'inline' \| 'pip' \| 'fullscreen' | Current display mode                                     |
| `safeArea`            | object                            | `{ insets: { top, bottom, left, right } }` for safe area |
| `maxHeight`           | number                            | Max available height in pixels (default: 600)            |
| `userAgent`           | object                            | `{ device: { type }, capabilities: { hover, touch } }`   |
| `locale`              | string                            | User locale (default: 'en')                              |
| `timeZone`            | string                            | IANA timezone identifier                                 |
| `callTool`            | (name, args) => Promise           | Call another MCP tool                                    |
| `sendFollowUpMessage` | (prompt) => Promise               | Trigger LLM response                                     |
| `openExternal`        | (href) => void                    | Open external URL                                        |
| `requestDisplayMode`  | (mode) => Promise                 | Request display mode change                              |
| `mcp_url`             | string                            | MCP server base URL                                      |

### setState Usage

```tsx
// Object form
await setState({ count: 5, items: ["a", "b"] });

// Updater function form
await setState((prev) => ({
  ...prev,
  count: (prev?.count || 0) + 1,
}));
```

### callTool Usage

```tsx
const handleRefresh = async () => {
  try {
    const result = await callTool("fetch-data", { id: "123" });
    console.log("Result:", result.content);

    // Check for errors
    if (result.isError) {
      console.error("Tool returned error");
    }
  } catch (error) {
    console.error("Tool call failed:", error);
  }
};
```

### requestDisplayMode Usage

```tsx
const goFullscreen = async () => {
  await requestDisplayMode("fullscreen");
};

const exitFullscreen = async () => {
  await requestDisplayMode("inline");
};

// Check current mode
if (displayMode === "fullscreen") {
  // Show exit button
}
```

### sendFollowUpMessage Usage

```tsx
const { sendFollowUpMessage } = useWidget();

// Trigger LLM to respond based on widget state
<button
  onClick={() =>
    sendFollowUpMessage("Analyze the selected items and recommend the best one")
  }
>
  Get AI Recommendation
</button>;
```

### openExternal Usage

```tsx
const { openExternal } = useWidget();

// Open external URL (shows confirmation dialog in ChatGPT)
<button onClick={() => openExternal("https://checkout.example.com/order/123")}>
  Proceed to Checkout
</button>;
```

## Convenience Hooks

For simpler use cases, mcp-use provides focused hooks:

### useWidgetProps

```tsx
import { useWidgetProps } from "mcp-use/react";

function MyWidget() {
  const props = useWidgetProps<{ city: string; temp: number }>();
  return (
    <div>
      {props.city}: {props.temp}°C
    </div>
  );
}
```

### useWidgetTheme

```tsx
import { useWidgetTheme } from "mcp-use/react";

function ThemedBox() {
  const theme = useWidgetTheme(); // 'light' | 'dark'
  return (
    <div className={theme === "dark" ? "bg-gray-900" : "bg-white"}>Content</div>
  );
}
```

### useWidgetState

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
