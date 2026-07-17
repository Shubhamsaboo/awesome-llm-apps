# Streaming AI Chatbot

A streaming, multi-turn AI chatbot built on the [iii engine](https://iii.dev) in one file of business logic. Token-by-token streaming, conversation state, durable turns, model routing, and REST endpoints are not implemented in this app: they come from reusable workers on the engine's bus, and the app just sends messages and listens to triggers.

The core is genuinely a few lines. Sending a message with full multi-turn context is one function call:

```javascript
const send = await iii.trigger({
  function_id: 'harness::send',
  payload: {
    message,
    model,
    session_id: conversationId,
    options: { system_prompt: SYSTEM_PROMPT },
  },
})
```

And live token streaming is one trigger binding: `session::message-updated` fires on every revision of the streaming assistant message, the handler prints the new suffix.

| Capability | Who provides it |
|---|---|
| Turn loop, streaming generation, durability (crash resumes mid-turn) | `harness` worker |
| Conversation state, transcript, live message-update triggers | `session-manager` worker |
| Token budgeting when conversations get long | `context-manager` worker |
| Model catalog and routing, any provider, key storage | `llm-router` + `provider-*` workers |
| Web access for the bot (optional, one env var) | `web` worker |
| REST endpoints (optional) | `http` worker |

## What the rewrite adds

The previous version of this tutorial hand-rolled the pipeline against a single provider. Rebuilt on the engine, the same app is smaller and does more:

- **Multi-turn conversations.** Every message carries the full session context automatically. The old version sent each message in isolation.
- **Any model, no key in the app.** The model comes from `router::models::list` at runtime; credentials live in the `llm-router` worker. Nothing is hardcoded.
- **An agent, not just a chatbot.** `CHAT_FUNCTIONS=web::fetch` turns it into a chatbot that can read the web mid-answer. Any function on the bus can be granted the same way.
- **Durable turns.** A crash or restart resumes mid-turn instead of dropping the response.
- **Observability.** Every turn is a correlated trace in the iii console, including per-call token usage.

## Installation

**Step 1: Install the iii engine**

```bash
curl -fsSL https://install.iii.dev/iii/main/install.sh | sh
```

**Step 2: Start the engine**

```bash
mkdir iii-app && cd iii-app
touch config.yaml
iii -c config.yaml
```

**Step 3: Add the workers this app depends on**

From a second terminal in the same folder:

```bash
cd iii-app
iii worker add harness console
```

One command: `harness` installs the whole loop (session-manager, context-manager, llm-router with the Anthropic and OpenAI providers, web, state, queue, and siblings). `console` adds the UI at `http://localhost:3113`.

**Step 4: Configure a model provider**

Open `http://localhost:3113`, click the model picker, and paste a provider key. It is stored in the `llm-router` worker config, not in this app.

**Step 5 (optional): REST endpoints**

```bash
iii worker add http
```

**Step 6: Install and run the app**

```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/chat_with_X_tutorials/streaming_ai_chatbot
npm install
node chatbot.js
```

## Usage

Interactive terminal chat with live token streaming:

```text
you > hi! what can you do?
ai  > Hi! I can answer questions, help you write and debug code, summarize
text, brainstorm ideas...

you > shorter please
ai  > I answer questions and help with writing, code, and ideas.
```

The second turn already proves the state management: "shorter please" only makes sense because the session carried the history.

Give the bot the web and it becomes an agent:

```bash
CHAT_FUNCTIONS=web::fetch node chatbot.js
```

Run it as a resident worker (`chat::send` / `chat::history` callable by any other worker or agent on the bus):

```bash
node chatbot.js --serve
```

With the `http` worker installed, the same surface over REST:

```bash
curl -X POST http://localhost:3111/chat \
  -H 'content-type: application/json' \
  -d '{"message": "Hello, how are you?"}'
# { "conversation_id": "s_...", "turn_id": "t_...", "history": "GET /chat/s_..." }

curl http://localhost:3111/chat/<conversation_id>
```

`GET /chat/:conversation_id` during generation returns the partial assistant text: the transcript is the stream, so polling it is already live. Pass `conversation_id` back into `POST /chat` to continue the conversation.

## Configuration

| Env var | Default | Meaning |
|---|---|---|
| `III_URL` | `ws://localhost:49134` | Engine WebSocket address |
| `CHAT_MODEL` | none | Model id; required only when several models are available |
| `CHAT_SYSTEM_PROMPT` | concise friendly assistant | System prompt (enriches the harness identity prompt) |
| `CHAT_FUNCTIONS` | none | Comma-separated function allow-list for the bot, e.g. `web::fetch` |
