# 📣 Publora MCP Agent

A terminal agent that drafts, schedules and reviews social media posts across ten
networks through the [Publora](https://publora.com) MCP server.

Publora is a **remote** MCP server, so there is nothing to install or run locally:
the agent connects over streamable HTTP and authenticates with an API key.

## Features

- Ask in plain language: draft a post, schedule it, check the queue
- Publishes to LinkedIn, X, Instagram, Threads, TikTok, YouTube, Facebook,
  Bluesky, Mastodon and Telegram from one call
- Attaches images and video by URL; multi-file posts go out as a carousel
- Applies each network's rules (caption limits, media requirements) before the
  post is queued
- Comments, reacts and reshares on LinkedIn
- Defaults to drafts, so nothing goes public until you say so
- Remembers the conversation across turns via a local SQLite session

## Prerequisites

- Python 3.10+
- An OpenAI API key
- A Publora account with at least one connected social account. The free plan
  works, and accounts are connected in the Publora dashboard.

## Setup

1. Install the dependencies:

```bash
pip install -r requirements.txt
```

2. Get your Publora API key at [publora.com](https://publora.com) → Settings → API.

3. Put both keys in a `.env` file next to the script:

```bash
PUBLORA_API_KEY=sk_your_key
OPENAI_API_KEY=sk-your_key
```

4. Run it:

```bash
python publora_mcp_agent.py
```

## Try it

Start with a read-only question to confirm the connection:

```
Which social accounts do I have connected?
```

Then work through a post:

```
Draft a LinkedIn post about our new changelog page and keep it as a draft.
Schedule that draft for tomorrow at 9:00 UTC.
What do I have scheduled this week?
```

Attach media by giving a public direct URL:

```
Schedule this image to Instagram and Threads for Friday at 6pm UTC:
https://example.com/launch.png
```

## Testing without publishing

Publora reserves a target that accepts a post and throws it away:

```
Send a test post to publora-playground.
```

Nothing reaches a real account. Useful for a first run, or after changing keys.

## How it works

The agent connects to `https://mcp.publora.com/mcp` with `MCPTools` over
`streamable-http` and passes the API key as a bearer token. The server exposes 16
tools; reads (`list_connections`, `list_posts`, `get_post`) are separate from
writes (`create_post`, `update_post`, `delete_post`), and each write tool carries
the annotations that let a client decide what needs confirmation.

The system prompt encodes the rules that matter in practice: read the connections
before posting, copy platform ids verbatim, prefer drafts, and read the stored
time back from the response instead of repeating the requested one.
