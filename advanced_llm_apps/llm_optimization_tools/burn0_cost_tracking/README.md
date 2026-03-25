# 🔥 burn0 — Zero-Config API Cost Tracking

Track every API cost in your Node.js stack with one import. See per-request costs for LLMs, SaaS, databases, and external services — right in your terminal.

## Features

- **One import** — Add `import "@burn0/burn0"` and costs appear in your terminal
- **50+ services** — Auto-detects OpenAI, Anthropic, Gemini, Stripe, Supabase, SendGrid, Twilio, and more
- **Sub-millisecond overhead** — Async event processing, never blocks your requests
- **Feature attribution** — Track costs per feature, per user, per request
- **Privacy-first** — Local by default, never reads request/response bodies
- **MIT licensed** — Free and open source forever

## How It Works

burn0 patches `globalThis.fetch` and `node:http` at import time. When your app makes outbound HTTP calls, burn0 identifies the service from the hostname, extracts token counts from response metadata, and calculates costs.

## Getting Started

### Prerequisites
- Node.js >= 18
- npm

### Installation

```bash
npm install @burn0/burn0
```

### Quick Start

Add one line to your entry file:

```javascript
import "@burn0/burn0";  // Must be first import
import OpenAI from "openai";

const openai = new OpenAI();

const response = await openai.chat.completions.create({
  model: "gpt-4o",
  messages: [{ role: "user", content: "Hello world" }],
});

// Terminal shows: burn0 > $0.08 today (1 call) -- openai: $0.08
```

### Feature Attribution

```javascript
import { track } from "@burn0/burn0";

await track("onboarding", async () => {
  await openai.chat.completions.create({ model: "gpt-4o", messages: [...] });
  await stripe.customers.create({ email: user.email });
});
// burn0 > feature "onboarding" -- $0.47/user
```

### CLI Usage

```bash
npx burn0 dev -- node app.js   # Zero code changes
npx burn0 report                # Cost report
npx burn0 init                  # Setup wizard
```

## Supported Services

| Category | Services |
|----------|----------|
| AI/LLMs | OpenAI, Anthropic, Gemini, Mistral, Cohere, Groq, Together AI, DeepSeek, Replicate |
| Payments | Stripe, PayPal, Plaid |
| Email/SMS | SendGrid, Resend, Twilio, Vonage |
| Databases | Supabase, PlanetScale, MongoDB Atlas, Upstash, Neon, Turso, Firebase |
| Infrastructure | AWS S3, AWS Lambda, Vercel, Cloudinary |
| Analytics | Algolia, Sentry, Segment, Mixpanel |

## Links
- [GitHub](https://github.com/burn0-dev/burn0) | [Website](https://burn0.dev) | [npm](https://www.npmjs.com/package/@burn0/burn0) | [Docs](https://docs.burn0.dev)
