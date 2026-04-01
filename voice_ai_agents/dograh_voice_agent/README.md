# 🎙️ Dograh - Open Source Voice Agent Platform

[Dograh](https://dograh.com) is an open-source, self-hostable alternative to Vapi, Retell AI, and Bland AI. It lets you build and deploy AI voice agents with a no-code drag-and-drop workflow builder, bring-your-own LLM/TTS/STT support, and full telephony integration (Twilio, Vonage, Telnyx and others).

## Features

- **No-code workflow builder** — drag-and-drop interface to design conversation flows
- **Inbound & outbound calling** — phone number integration via Twilio, Vonage, Telnyx, Cloudonix, Vobiz
- **Bring your own stack** — connect any LLM, TTS, or STT provider
- **Bulk outbound campaigns** — upload a CSV of contacts and dial at scale with auto-retry
- **Pre-recorded audio** — reduce latency and TTS costs with your own voice recordings
- **API trigger** — fire voice agents programmatically from any external system
- **100% open source** — BSD-2-Clause licensed, self-hostable via Docker

## Prerequisites

- Python 3.8+
- A Dograh account ([cloud](https://app.dograh.com) or [self-hosted](https://docs.dograh.com/deployment/introduction))

## Setup

### Step 1: Get your API Key

Sign up at [app.dograh.com](https://app.dograh.com) → go to **Settings → API Keys** and create a new key.

> API keys are prefixed with `dg_`. See the [API Keys docs](https://docs.dograh.com/configurations/api-keys) for details.
>
> **Self-hosted:** If you're running Dograh locally, open your instance (default: `http://localhost:3010`) and access Settings → API Keys the same way.

### Step 2: Create a Voice Agent with an API Trigger node

1. In the Dograh dashboard, create a new agent
2. Build your workflow in the visual editor
3. Add an **API Trigger** node — this is what enables programmatic outbound calling
4. The API Trigger node will give you an endpoint URL in this format:
   ```
   https://api.dograh.com/api/v1/public/agent/<your-agent-id>
   ```
   Copy this URL — it's your `DOGRAH_AGENT_URL`.

> For self-hosted deployments, the base URL will be your own instance, e.g. `https://your-dograh-instance/api/v1/public/agent/<your-agent-id>`.

See the [API Trigger docs](https://docs.dograh.com/voice-agent/api-trigger) for more details.

### Step 3: Configure environment variables

Create a `.env` file:

```bash
DOGRAH_API_KEY=dg_your_api_key
DOGRAH_AGENT_URL=https://api.dograh.com/api/v1/public/agent/your-agent-id
```

> **Self-hosted:** Replace `https://api.dograh.com` with your own instance URL, e.g. `https://your-dograh-instance/api/v1/public/agent/your-agent-id`.

### Step 4: Install dependencies

```bash
pip install -r requirements.txt
```

## Run

```bash
python trigger_voice_agent.py
```

This triggers your Dograh voice agent to make an outbound call to the specified number.

## How Initial Context Works

The `initial_context` field lets you pass dynamic data into your agent at call time. You can reference these values anywhere in your agent's prompt using `{{initial_context.key}}` syntax.

For example, if you pass:

```json
{
  "initial_context": {
    "customer_name": "Jane Smith",
    "order_id": "ORD-001"
  }
}
```

You can use `{{initial_context.customer_name}}` and `{{initial_context.order_id}}` directly in your agent's prompt.

## Self-Hosting

Run the full Dograh platform locally with a single command:

```bash
curl -o docker-compose.yaml https://raw.githubusercontent.com/dograh-hq/dograh/main/docker-compose.yaml && \
REGISTRY=ghcr.io/dograh-hq ENABLE_TELEMETRY=true docker compose up --pull always
```

Open [http://localhost:3010](http://localhost:3010) once running. For remote server deployment with HTTPS, see the [Deployment Guide](https://docs.dograh.com/deployment/introduction).

## Documentation

- [Full Documentation](https://docs.dograh.com)
- [API Trigger docs](https://docs.dograh.com/voice-agent/api-trigger)
- [Deployment Guide](https://docs.dograh.com/deployment/introduction)
- [Telephony Integration](https://docs.dograh.com/integrations/telephony/overview)
- [GitHub Repository](https://github.com/dograh-hq/dograh)
