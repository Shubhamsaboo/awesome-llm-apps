# 📧 Email MCP Agent

A Streamlit app that gives AI agents their own email addresses using [NornWeave](https://github.com/DataCovey/nornweave) and the Model Context Protocol (MCP). Create inboxes, send and receive emails, search threads, and manage attachments — all through natural language.

## Features

- **Create Inboxes**: Provision email addresses for your AI agents on the fly
- **Send Emails**: Compose and send emails with Markdown-to-HTML conversion
- **Search & Read**: Search messages by keyword, list threads, read conversations
- **Attachments**: List and retrieve email attachments
- **Wait for Reply**: Block until a response arrives in a thread (experimental)
- **Interactive UI**: Streamlit interface with example queries

## How It Works

```
┌──────────────┐     MCP (stdio)     ┌──────────────────┐     REST API     ┌──────────────┐
│  OpenAI LLM  │◄───────────────────►│  NornWeave MCP   │◄────────────────►│  NornWeave   │
│  (via Agno)  │   tool calls        │  Server           │   HTTP           │  API Server  │
└──────────────┘                     └──────────────────┘                  └──────────────┘
```

1. **NornWeave** is a self-hosted Inbox-as-a-Service API that gives AI agents stateful email — inboxes, threading, Markdown parsing, and semantic search.
2. The **NornWeave MCP server** (`nornweave mcp`) exposes email operations as MCP tools.
3. This app connects an **OpenAI-powered agent** (via Agno) to those MCP tools so you can manage email through conversation.

## MCP Tools Available

| Tool | Description |
|------|-------------|
| `create_inbox` | Provision a new email address |
| `send_email` | Send an email (Markdown → HTML) |
| `search_email` | Find messages by keyword |
| `list_messages` | List messages in an inbox or thread |
| `wait_for_reply` | Block until a reply arrives |
| `list_attachments` | List attachment metadata |
| `get_attachment_content` | Download attachment content |
| `send_email_with_attachments` | Send email with file attachments |

## Setup

### Prerequisites

- Python 3.10+
- A running NornWeave server (see below)
- An OpenAI API key

### 1. Install NornWeave

```bash
# Install with MCP support
pip install nornweave[mcp]

# Start the API server (uses SQLite by default — no database setup needed)
nornweave api
```

> NornWeave runs at `http://localhost:8000` by default. For production, see the [NornWeave docs](https://github.com/DataCovey/nornweave) for PostgreSQL and Docker setup.

### 2. Install the agent dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run email_mcp_agent.py
```

### 4. In the app

1. Enter your **OpenAI API key** in the sidebar
2. Confirm the **NornWeave API URL** (default: `http://localhost:8000`)
3. Type a query and click **Run**

## Example Queries

**Creating an inbox:**
> Create an inbox called "Support Bot" with username "support"

**Sending email:**
> Send an email from inbox ibx_abc to bob@example.com with subject "Hello" and body "Hi Bob, just checking in!"

**Searching:**
> Search for emails about "pricing" in inbox ibx_abc

**Reading threads:**
> Show me the messages in thread th_123

**Waiting for replies:**
> Send a follow-up to thread th_123 and wait for a response
