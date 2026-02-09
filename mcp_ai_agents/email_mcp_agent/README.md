# 📧 Email MCP Agent

A Streamlit app that gives AI agents their own email addresses using [NornWeave](https://github.com/DataCovey/nornweave) and the Model Context Protocol (MCP). Built around **real use cases** — support triage, task coordination, and inbox automation — with a self-contained tutorial you can run end-to-end.

---

## When would you use this?

Email-powered agents make sense when the **workflow** is the product:

- **Support inbox assistant** — Monitor a shared support address, triage by topic, and draft replies (or escalate) so humans only approve and send.
- **Task coordination via email** — An agent that owns an address like `tasks@yourdomain.com`: receives requests, parses them into tasks, and keeps a thread-based paper trail with stakeholders.
- **Stakeholder updates** — Digest internal events or reports and send summary emails to a list; replies can feed back into the agent for follow-up.

This app focuses on the **support inbox** scenario — a complete flow from creating an inbox to triaging, drafting, searching, handling attachments, escalating, and batch-processing threads. The same tools power the other use cases; only the prompts change.

---

## Tutorial: Support inbox assistant

**Goal:** Build a working support-agent loop — create an inbox, receive tickets, triage by topic, draft replies, handle attachments, escalate the hard ones, and batch-process what's left. This is the kind of flow you'd automate on a schedule or webhook in production; here you drive each step by hand to learn how it works.

### What you'll need

- Python 3.10+
- A running NornWeave server (see below)
- An OpenAI API key

### Step 1: Run NornWeave

NornWeave is the email backend: it gives the agent stateful inboxes, threading, and search. Run it locally (SQLite, no DB setup):

```bash
pip install nornweave[mcp]
nornweave api
```

Default URL: `http://localhost:8000`. For production, see [NornWeave docs](https://github.com/DataCovey/nornweave) (PostgreSQL, Docker).

### Step 2: Install and run the agent app

```bash
cd mcp_ai_agents/email_mcp_agent
pip install -r requirements.txt
streamlit run email_mcp_agent.py
```

In the sidebar: set your **OpenAI API key** and confirm **NornWeave API URL** (e.g. `http://localhost:8000`).

### Step 3: Create the support inbox

In the main text area, ask the agent to provision an inbox:

```text
Create an inbox named "Support Bot" with username "support". Tell me the inbox id and email address.
```

The agent uses the NornWeave MCP tool `create_inbox` and returns the new address (e.g. `support@mail.yourdomain.com` — the domain comes from `EMAIL_DOMAIN` in your `.env`). **Note the inbox id** (e.g. `ibx_...`) — you'll use it in every step below.

### Step 4: Seed the inbox with test tickets

To simulate real support traffic, you have two options:

- **Option A — Send real mail:** If NornWeave is configured with a provider (Mailgun, Resend, etc.) and a domain, send a few emails to the support address from your personal account. Try different subjects — "Can't reset my password," "Billing question," "Bug: page won't load" — so there are several threads to work with.
- **Option B — Use the agent itself:** Ask the agent to send test messages into the inbox:

```text
Send three separate emails to support@[your domain]:
1. From alice@example.com, subject "Can't log in", body "I've tried resetting my password twice and it still doesn't work. Help!"
2. From bob@example.com, subject "Billing question", body "I was charged twice this month. Can you check my account?"
3. From carol@example.com, subject "Bug: dashboard is blank", body "After the update, my dashboard shows nothing. I attached a screenshot." 
Tell me the thread ids for each.
```

Now you have a few threads to triage.

### Step 5: Triage and draft a reply

Ask the agent to look at the inbox and draft a reply for a thread:

```text
In inbox [inbox id], list the most recent messages. Pick the thread about the login issue, show me the conversation, and draft a short, professional reply that acknowledges the problem and says we'll investigate. Don't send yet — just show me the draft.
```

The agent uses `list_messages` to read the thread, then produces a draft in the chat. You can tweak the wording and, when ready:

```text
Send that draft as a reply in thread [thread id].
```

That's the core loop: **inbox → read → draft → (human approve) → send**.

### Step 6: Search and categorize by topic

A real support inbox has many threads. Use search to zero in on a topic:

```text
Search inbox [inbox id] for messages about "billing". For each match, give me a one-line summary and the thread id.
```

Then drill into a specific thread:

```text
Show me the full conversation in thread [thread id] and draft a reply that explains our refund policy.
```

This is how you'd build a triage dashboard: the agent searches by keyword, categorizes, and lets you pick which threads to handle first.

### Step 7: Handle attachments

Support tickets often include screenshots, logs, or documents. The agent can inspect them:

```text
List the attachments in thread [thread id]. For the first attachment, download it and tell me what it contains.
```

The agent uses `list_attachments` to see what's attached, then `get_attachment_content` to retrieve it. For text-based files (logs, CSVs), the agent can summarize content directly. For images, it reports metadata (filename, size, type).

You can also send attachments back:

```text
Send a reply in thread [thread id] with the message "Here's the updated config" and attach the file at /path/to/config.yaml.
```

### Step 8: Escalate what the agent can't handle

Not every ticket should get an auto-drafted reply. Ask the agent to flag ones that need a human:

```text
In inbox [inbox id], list the 10 most recent messages. For each thread, classify it as "can auto-reply" or "needs human review" based on how complex the issue seems. Show me the list with thread ids, subjects, and your classification.
```

The agent reads each thread and uses its judgment to sort them. Threads tagged "needs human review" stay untouched; you only draft replies for the straightforward ones. In production, you'd pipe the "needs human" list into a ticketing system or Slack channel.

### Step 9: Batch-process multiple threads

Once you're comfortable with single-thread flows, try a batch:

```text
In inbox [inbox id], find all threads where the last message is from the customer (not from us). For each one, draft a reply. Show me all drafts with thread ids so I can review them before sending.
```

The agent iterates over open threads, drafts replies, and presents them as a batch. You review, edit if needed, then:

```text
Send the drafts for threads [thread id 1], [thread id 2], and [thread id 3].
```

This is the pattern for scheduled support: run it every hour, review the batch, send.

### Step 10: Wait for a reply (synchronous flow)

For a "send and wait" loop — useful in scripts or bots that need to hold a conversation:

```text
Send a follow-up in thread [thread id] asking if the customer needs anything else, then wait up to 2 minutes for a reply.
```

The agent uses `send_email` followed by the experimental `wait_for_reply` tool. When the customer replies, the agent can continue the conversation — e.g., close the ticket or escalate further.

### Putting it together

The full support-agent loop in production looks like this:

```
Every N minutes (or on webhook trigger):
  1. List new messages in the support inbox
  2. Search / categorize by topic
  3. Check for attachments — summarize or flag
  4. For simple threads → draft a reply
  5. For complex threads → flag for human review
  6. Present drafts for approval → send approved ones
  7. Optionally wait for follow-up replies
```

This tutorial lets you drive each step by hand. When you're ready to automate, wrap the same prompts in a script or cron job — the MCP tools and NornWeave API stay the same.

---

## Other scenarios (same app, different prompts)

The support tutorial covers the full toolkit. Here are other workflows you can build with the same app:

- **Task coordination:** Create an inbox like `tasks@...`, then: "List new messages in inbox [id]. For each message, summarize the request and suggest a one-line task; put them in a single reply to the sender."
- **Stakeholder digest:** "Search inbox [id] for messages about 'weekly report'. Compose one summary email that I can send to leadership."
- **Meeting follow-up:** "After my meeting notes arrive in inbox [id], draft individual follow-up emails to each attendee with their action items."

The same MCP tools power all of these; only the instructions and prompts change.

---

## How it works (under the hood)

```
┌──────────────┐     MCP (stdio)     ┌──────────────────┐     REST API     ┌──────────────┐
│  OpenAI LLM  │◄───────────────────►│  NornWeave MCP   │◄────────────────►│  NornWeave   │
│  (via Agno)  │   tool calls        │  Server          │   HTTP           │  API Server  │
└──────────────┘                     └──────────────────┘                  └──────────────┘
```

1. **NornWeave** — Self-hosted Inbox-as-a-Service: inboxes, threads, Markdown parsing, semantic search.
2. **NornWeave MCP server** (`nornweave mcp`) — Exposes email operations as MCP tools.
3. **This app** — Connects an OpenAI-backed agent (Agno) to those tools so you manage email via natural language.

### MCP tools used in the tutorial

| Tool | What it does | Tutorial steps |
|------|----------------|----------------|
| `create_inbox` | Provision a new email address for the agent | Step 3 |
| `send_email` | Send an email (Markdown → HTML); reply in a thread | Steps 4, 5, 9, 10 |
| `list_messages` | List messages in an inbox or thread | Steps 5, 6, 8, 9 |
| `search_email` | Find messages by keyword | Step 6 |
| `list_attachments` / `get_attachment_content` | List or download attachments | Step 7 |
| `send_email_with_attachments` | Send with file attachments | Step 7 |
| `wait_for_reply` | Block until a reply arrives (experimental) | Step 10 |
