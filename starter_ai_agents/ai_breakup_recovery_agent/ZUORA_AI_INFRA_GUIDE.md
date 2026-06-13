# 🔗 Using Zuora AI Infrastructure with Anthropic SDK

This guide explains how to route your Anthropic SDK requests through Zuora's internal AI infrastructure instead of using OpenAI's public API.

## Overview

Zuora operates a centralized AI Gateway that provides:
- **Unified LLM Access** — Route Claude, Sonnet, Opus, and non-Claude models through a single endpoint
- **Cost Tracking** — Per-user billing and budget enforcement
- **Rate Limiting** — Fair usage across teams
- **Observability** — Langfuse traces for debugging and analytics

**Endpoints (Staging):**
- `http://claude-proxy.tools.stg.uw2.aws.zuora` — Claude Code CLI (recommended for Python apps)
- `http://ai-gateway.tools.stg.uw2.aws.zuora` — Direct API access

---

## Prerequisites

✅ **Network Access:** Must be on Zuora VPN or internal network (Zscaler)  
✅ **Azure AD Account:** Zuora corporate credentials  
✅ **Anthropic SDK:** `pip install anthropic`

---

## Quick Setup

### 1. Get JWT Token

Zuora uses Azure AD JWT tokens instead of API keys. Get token from local cache:

```bash
# Token cached locally by Claude Code setup script
cat ~/.claude/tokens/id_token.txt

# Or re-authenticate (auto-refreshes every 24 hours)
~/.claude/scripts/get-current-token.sh
```

### 2. Configure Anthropic Client

```python
from anthropic import Anthropic
import os
import subprocess

# Read JWT token from local file (cached by setup script)
token_file = os.path.expanduser("~/.claude/tokens/id_token.txt")
with open(token_file, "r") as f:
    jwt_token = f.read().strip()

# Create client pointing to Zuora gateway
client = Anthropic(
    api_key=jwt_token,
    base_url="http://claude-proxy.tools.stg.uw2.aws.zuora",
)

# Use normally — SDK handles rest
message = client.messages.create(
    model="aws-bedrock-claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "What is 2+2?"}
    ],
)
print(message.content[0].text)
```

---

## Authentication Flow

### JWT Token Lifecycle

```
1. Get token: ~/.claude/tokens/id_token.txt (cached, 24h expiry)
2. Pass as: Authorization: Bearer {JWT}
3. Gateway validates via Azure AD
4. Cost tracked with x-user-id header
```

### Handling Token Expiry

Token auto-refreshes on first request after expiry. If using cached file:

```python
import subprocess
import os
from datetime import datetime, timedelta

def get_fresh_token():
    """Get current valid JWT token, refresh if needed."""
    token_file = os.path.expanduser("~/.claude/tokens/id_token.txt")
    
    # Check if token exists and is recent
    if os.path.exists(token_file):
        mtime = os.path.getmtime(token_file)
        age = datetime.now().timestamp() - mtime
        if age < 86000:  # < 24 hours
            with open(token_file, "r") as f:
                return f.read().strip()
    
    # Token missing or stale — refresh
    result = subprocess.run(
        [os.path.expanduser("~/.claude/scripts/get-current-token.sh")],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Token refresh failed: {result.stderr}")
    return result.stdout.strip()

# Use in client creation
client = Anthropic(
    api_key=get_fresh_token(),
    base_url="http://claude-proxy.tools.stg.uw2.aws.zuora",
)
```

---

## Model Selection

### Claude Models (Recommended)

| Model | Alias | Speed | Cost (input/output) | Best For |
|-------|-------|-------|------------------|----------|
| **Haiku 4.5** | `aws-bedrock-claude-haiku-4-5` | ⚡⚡⚡ | $0.90 / $4.50 per M | Automation, high-volume |
| **Sonnet 4.6** | `aws-bedrock-claude-sonnet-4-6` | ⚡⚡ | $2.70 / $13.50 per M | General engineering (default) |
| **Opus 4.7** | `aws-bedrock-claude-opus-4-7` | ⚡ | $4.50 / $22.50 per M | Hard reasoning, architecture |

### Non-Claude Models (Cost-Effective)

```python
# GLM-5: Best non-Claude alternative
client.messages.create(
    model="aws-bedrock-zai-glm-5",
    max_tokens=1024,
    messages=[...],
)

# DeepSeek: Strong coding tasks
client.messages.create(
    model="aws-bedrock-deepseek-v3-2",
    max_tokens=1024,
    messages=[...],
)

# Kimi: Excellent long-context (256K tokens)
client.messages.create(
    model="aws-bedrock-moonshot-kimi-k2-5",
    max_tokens=1024,
    messages=[...],
)
```

---

## Full Example: AI Agent with Cost Tracking

```python
from anthropic import Anthropic
import os
import json

class ZuoraAIAgent:
    def __init__(self, user_id: str, environment: str = "local"):
        """Initialize agent with Zuora gateway credentials."""
        token_file = os.path.expanduser("~/.claude/tokens/id_token.txt")
        with open(token_file, "r") as f:
            jwt_token = f.read().strip()
        
        self.client = Anthropic(
            api_key=jwt_token,
            base_url="http://claude-proxy.tools.stg.uw2.aws.zuora",
            default_headers={
                "x-user-id": user_id,
                "x-environment": environment,
                "x-client-type": "python-agent",
            },
        )
        self.user_id = user_id
        self.conversation = []
    
    def chat(self, message: str, model: str = "aws-bedrock-claude-sonnet-4-6") -> str:
        """Send message and get response."""
        self.conversation.append({
            "role": "user",
            "content": message,
        })
        
        response = self.client.messages.create(
            model=model,
            max_tokens=2048,
            system="You are a helpful AI assistant.",
            messages=self.conversation,
        )
        
        assistant_message = response.content[0].text
        self.conversation.append({
            "role": "assistant",
            "content": assistant_message,
        })
        
        # Log usage for cost tracking
        print(f"[{self.user_id}] Tokens: {response.usage.input_tokens} in, "
              f"{response.usage.output_tokens} out | "
              f"Model: {model}")
        
        return assistant_message

# Usage
agent = ZuoraAIAgent(user_id="your.email@zuora.com")

# Cheap model for volume
response = agent.chat(
    "Summarize breakup recovery tips",
    model="aws-bedrock-claude-haiku-4-5"
)
print(f"Haiku: {response}\n")

# Powerful model for reasoning
response = agent.chat(
    "What's the psychological impact of breakups?",
    model="aws-bedrock-claude-opus-4-7"
)
print(f"Opus: {response}\n")

# Non-Claude alternative (cost-effective)
response = agent.chat(
    "List 5 recovery strategies",
    model="aws-bedrock-zai-glm-5"
)
print(f"GLM-5: {response}")
```

---

## Streaming Responses

```python
# Stream tokens in real-time
with client.messages.stream(
    model="aws-bedrock-claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Write a poem about recovery"}
    ],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()
```

---

## Embeddings (RAG/Vector Search)

```python
# Get embeddings for RAG pipelines
response = client.beta.messages.create(
    model="aws-bedrock-claude-sonnet-4-6",
    max_tokens=100,
    # Embeddings endpoint available at /v1/embeddings
)

# Or use direct embeddings API
import requests

token_file = os.path.expanduser("~/.claude/tokens/id_token.txt")
with open(token_file, "r") as f:
    jwt_token = f.read().strip()

headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json",
}

payload = {
    "model": "aws-bedrock-titan-embed-text-v2",
    "input": ["Help me recover from my breakup"],
}

response = requests.post(
    "http://ai-gateway.tools.stg.uw2.aws.zuora/v1/embeddings",
    json=payload,
    headers=headers,
)

print(response.json())  # Returns embedding vectors
```

---

## Configuration Reference

### Environment Variables (Optional)

```bash
# Set in ~/.bashrc or .env file
export ZUORA_AI_GATEWAY="http://claude-proxy.tools.stg.uw2.aws.zuora"
export ZUORA_USER_ID="your.email@zuora.com"
export ZUORA_ENVIRONMENT="local"
```

### SDK Client Parameters

| Parameter | Value |
|-----------|-------|
| `api_key` | JWT token (Bearer authentication) |
| `base_url` | `http://claude-proxy.tools.stg.uw2.aws.zuora` |
| `model` | `aws-bedrock-*` aliases |
| `max_tokens` | Up to 200K context |
| `timeout` | Default 50 minutes (set via env) |

### Custom Headers (Cost Tracking)

```python
client = Anthropic(
    api_key=jwt_token,
    base_url="http://claude-proxy.tools.stg.uw2.aws.zuora",
    default_headers={
        "x-user-id": "your.email@zuora.com",         # Required for billing
        "x-environment": "local",                    # local/dev/stg/prod
        "x-client-type": "python-agent",             # Client identifier
        "x-claude-session-id": "session-123",        # Session tracking (optional)
    }
)
```

---

## Troubleshooting

### Error: "401 Unauthorized"

**Cause:** Token expired or invalid  
**Fix:**
```bash
# Re-authenticate
~/.claude/scripts/get-current-token.sh

# Verify token
cat ~/.claude/tokens/id_token.txt
```

### Error: "Model not found"

**Cause:** Using incorrect model alias  
**Fix:** Check available models in [Zuora AI Gateway docs](https://ai-gateway-portal.tools.stg.uw2.aws.zuora/home#/api-docs)

### Error: "429 Rate Limited"

**Cause:** Monthly budget exceeded ($100 Claude / $200 Non-Claude)  
**Fix:**
- Check usage: https://ai-gateway-portal.tools.stg.uw2.aws.zuora/home/costs
- Switch to cheaper model (Sonnet → Haiku)
- Request budget increase

### Error: "Connection refused"

**Cause:** Not on VPN or internal network  
**Fix:**
- Enable Zscaler/VPN
- Verify network: `curl -I http://claude-proxy.tools.stg.uw2.aws.zuora/health`

---

## Migration from OpenAI to Zuora

### Before (OpenAI)
```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
```

### After (Zuora)
```python
from anthropic import Anthropic

token_file = os.path.expanduser("~/.claude/tokens/id_token.txt")
with open(token_file, "r") as f:
    jwt_token = f.read().strip()

client = Anthropic(
    api_key=jwt_token,
    base_url="http://claude-proxy.tools.stg.uw2.aws.zuora",
)
response = client.messages.create(
    model="aws-bedrock-claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)
```

**Key Changes:**
- API key → JWT token from local file
- OpenAI endpoint → Zuora gateway URL
- `gpt-4o` → `aws-bedrock-claude-sonnet-4-6` (or other aliases)
- `chat.completions` → `messages` (Anthropic API shape)

---

## Cost Tracking & Budget Management

### View Your Usage

**Admin Portal (Per-User Costs):**
https://ai-gateway-portal.tools.stg.uw2.aws.zuora/home/costs

Shows:
- Real-time cost breakdown (Claude vs Non-Claude)
- Token usage per model
- Budget status and remaining quota
- Monthly spend trends

### Budget Limits

| Tier | Claude Budget | Non-Claude Budget |
|------|--------------|-------------------|
| Power/Premium/Standard | $100/month | $200/month |
| Unknown | $10/month | $20/month |
| Unlicensed | $0 | $0 |

Budget resets on 1st of each month.

---

## Best Practices

✅ **Use Haiku for High-Volume Tasks** — Lowest cost, fastest  
✅ **Reserve Sonnet for General Work** — Best price/performance  
✅ **Use Opus for Hard Problems** — Reasoning, architecture  
✅ **Monitor Costs Weekly** — Check portal to avoid surprises  
✅ **Include Custom Headers** — Helps with billing attribution  
✅ **Implement Token Refresh** — Handle 24h JWT expiry gracefully  
✅ **Use Streaming** — Better UX, same cost  

❌ **Don't Use Direct Bedrock Calls** — Route through gateway  
❌ **Don't Hardcode Tokens** — Use local cache or env vars  
❌ **Don't Mix Anthropic + OpenAI** — Use one consistently  

---

## Additional Resources

- **Zuora AI Infra Docs:** `/Users/xili/Documents/codes/git.zias.io/ai-system-infra/docs/`
- **Claude Code Setup:** `ai-system-infra/docs/integration/CLAUDE_CODE_SETUP.md`
- **Model Pricing:** `ai-system-infra/docs/envoy-ai-gateway/MODEL_PRICING_REFERENCE.md`
- **Anthropic SDK Docs:** https://docs.anthropic.com

