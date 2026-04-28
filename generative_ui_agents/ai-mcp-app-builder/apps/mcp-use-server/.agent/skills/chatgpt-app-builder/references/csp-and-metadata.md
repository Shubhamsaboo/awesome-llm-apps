# CSP and Metadata Configuration

Content Security Policy and metadata configuration for ChatGPT widgets.

## Table of Contents

- [CSP Configuration](#csp-configuration)
- [Metadata Configuration](#metadata-configuration)
- [Legacy Apps SDK Format](#legacy-apps-sdk-format)
- [Combining Both Formats](#combining-both-formats)

## CSP Configuration

Control what external resources your widget can access:

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Weather widget",
  props: z.object({ city: z.string() }),
  metadata: {
    csp: {
      // APIs your widget needs to call (fetch, WebSocket, XMLHttpRequest)
      connectDomains: [
        "https://api.weather.com",
        "https://backup-api.weather.com",
      ],

      // Static assets (images, fonts, stylesheets, videos)
      resourceDomains: ["https://cdn.weather.com"],

      // External content to embed in iframes
      frameDomains: ["https://embed.weather.com"],

      // Script CSP directives (use carefully!)
      scriptDirectives: ["'unsafe-inline'"],
    },
  },
};
```

### CSP Field Reference

| Field              | Purpose                          | Example                         |
| ------------------ | -------------------------------- | ------------------------------- |
| `connectDomains`   | APIs to call via fetch/WebSocket | `["https://api.example.com"]`   |
| `resourceDomains`  | Load images, fonts, stylesheets  | `["https://cdn.example.com"]`   |
| `frameDomains`     | Embed external iframes           | `["https://embed.example.com"]` |
| `scriptDirectives` | Script-src CSP directives        | `["'unsafe-inline'"]`           |

### Security Best Practices

1. **Specify exact domains**: `https://api.weather.com` (not wildcards)
2. **Avoid wildcards**: `https://*.weather.com` is less secure
3. **Never use `'unsafe-eval'`** unless absolutely necessary
4. **Test CSP in development** before deploying
5. **Use HTTPS** for all resources

### Troubleshooting CSP Errors

**Problem:** Widget loads but assets fail

**Solutions:**

1. Check browser console for CSP violation messages
2. Add missing domains to CSP:
   ```typescript
   metadata: {
     csp: {
       connectDomains: ['https://api.example.com'], // Add missing API
       resourceDomains: ['https://cdn.example.com'], // Add missing CDN
     }
   }
   ```
3. Use exact domains - avoid wildcards in production
4. Test in Inspector before deploying
5. Set `CSP_URLS` environment variable for additional domains

## Metadata Configuration

### Modern Unified Approach (Recommended)

Use `metadata` field for dual-protocol support (both ChatGPT and MCP Apps clients):

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Weather widget",
  props: propSchema,
  metadata: {
    // CSP configuration
    csp: {
      connectDomains: ["https://api.weather.com"],
      resourceDomains: ["https://cdn.weather.com"],
    },
    // Display options
    prefersBorder: true,
    autoResize: true,
    // Widget description (shown to users)
    widgetDescription: "Displays current weather conditions",
  },
};
```

### All Metadata Fields

| Field               | Type    | Description                           |
| ------------------- | ------- | ------------------------------------- |
| `csp`               | object  | Content Security Policy configuration |
| `prefersBorder`     | boolean | Show border around widget             |
| `autoResize`        | boolean | Auto-resize widget to content         |
| `widgetDescription` | string  | Human-readable widget description     |

## Legacy Apps SDK Format

The old ChatGPT-only format (still supported but not recommended):

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Weather widget",
  props: propSchema,
  appsSdkMetadata: {
    // ChatGPT only - uses openai/ prefix and snake_case
    "openai/widgetCSP": {
      connect_domains: ["https://api.weather.com"],
      resource_domains: ["https://cdn.weather.com"],
    },
    "openai/widgetPrefersBorder": true,
    "openai/widgetDomain": "https://chatgpt.com",
    "openai/toolInvocation/invoking": "Loading weather...",
    "openai/toolInvocation/invoked": "Weather loaded",
  },
};
```

### Migration Guide

| Legacy (appsSdkMetadata)            | Modern (metadata)     |
| ----------------------------------- | --------------------- |
| `openai/widgetCSP.connect_domains`  | `csp.connectDomains`  |
| `openai/widgetCSP.resource_domains` | `csp.resourceDomains` |
| `openai/widgetPrefersBorder`        | `prefersBorder`       |
| `openai/widgetDescription`          | `widgetDescription`   |

**Key differences:**

- Legacy uses `openai/` prefixes
- Legacy uses `snake_case` for CSP fields
- Modern uses `camelCase` and works with both protocols

## Combining Both Formats

Use both for standard metadata plus ChatGPT-specific overrides:

```typescript
export const widgetMetadata: WidgetMetadata = {
  description: "Weather widget",
  props: propSchema,
  // Unified metadata (dual-protocol)
  metadata: {
    csp: { connectDomains: ["https://api.weather.com"] },
    prefersBorder: true,
  },
  // ChatGPT-specific additions
  appsSdkMetadata: {
    "openai/widgetDescription": "ChatGPT-specific description override",
    "openai/customFeature": "some-value", // Any custom OpenAI metadata
    "openai/locale": "en-US",
  },
};
```

**Use case:** When you need ChatGPT-specific metadata that doesn't exist in the unified format, add it to `appsSdkMetadata`. Fields pass directly to ChatGPT with `openai/` prefix.
