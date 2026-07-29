# Idea / Blueprint

Not runnable code — just the wiring diagram. This walks through every moving piece of the ADK multi-agent customer support bot, what each is responsible for, and exactly what gets passed to what.

```
                                                 ┌────────────────────────┐
                                                 │        Mem0            │
                                                 │  (backed by Qdrant)    │
                                                 │  long-term, cross-     │
                                                 │  session memory        │
                                                 └───────┬────────┬──────┘
                                                          │        │
                                                (1) search│        │(5) add
                                                 before    │        │  after
                                                 routing   ▼        │
  user ──(chat_input)──► [Streamlit UI] ───────► "augmented message"
                              ▲                          │
                              │ (6) render answer         │ (2) new_message
                              │                           ▼
                              │                  ┌───────────────────┐
                              │                  │   ADK Runner       │
                              │                  │ (+ SessionService) │
                              │                  └─────────┬──────────┘
                              │                            │ (3) routes via
                              │                            │  sub-agent description
                              │                  ┌─────────▼──────────┐
                              │                  │   triage_agent      │
                              │                  │  (root LlmAgent)    │
                              │                  └───┬─────┬─────┬────┘
                              │                      │     │     │
                              │              billing_│ tech│ acct│_agent
                              │                agent │agent│agent│
                              │                      ▼     ▼     ▼
                              │                 [tool call]  [tool call]  [tool call]
                              │                      │     │     │
                              └──────(4) final_text◄─┴─────┴─────┘
```

Five numbered steps above = the five things that "wire up" the whole app. Everything below is that diagram spelled out per component.

## 1. Config — the constants everything else depends on

- `APP_NAME` — namespace ADK uses to key sessions in `SessionService`
- `MODEL` — which Gemini model every `LlmAgent` uses (root + specialists can each use a different model if you want a cheaper/faster model for routing vs. answering — start with one model everywhere, split later if latency/cost matters)

### Where each credential actually lives

There are three separate secrets here, not one — easy to conflate because only #1 is "the LLM key":

1. **`GOOGLE_API_KEY`** (Gemini, used by ADK and by Mem0's own LLM + embedder)
   → `st.text_input(type="password")` in the UI, then `os.environ["GOOGLE_API_KEY"] = value`.
   ADK's Gemini client reads it from the environment, not from a constructor arg, so setting `os.environ` is the actual wiring step, not just bookkeeping. Mem0 reads the same env var for its `"gemini"` provider, so one key covers everything — no separate OpenAI key needed (see §7).

2. **Qdrant connection info** — only relevant if you move off the default embedded mode. Lives inside the Mem0 config dict, under `"vector_store"`:
   - local server (Docker or `qdrant.exe`, no auth): `{"host": "localhost", "port": 6333}`
   - Qdrant Cloud (needs credentials): `{"url": "https://xxx.cloud.qdrant.io", "api_key": QDRANT_API_KEY}`
   Never hardcode `QDRANT_API_KEY` — read it from `os.environ`.

3. **Mem0's embedder key** — the one that's easy to miss. `Memory.from_config()` embeds every stored memory with a model of its own; if left at Mem0's default (OpenAI), it's a totally separate credential from the Gemini key used for chat. This build avoids that by explicitly setting `embedder.provider = "gemini"`, so it reuses `GOOGLE_API_KEY` too. If you ever swap the embedder provider, remember the failure mode is an auth error that looks unrelated to Gemini or Qdrant.

### Local dev vs. deployed

- **Local dev:** put any extra secrets (`QDRANT_API_KEY`, etc.) in a `.env` file (gitignored), loaded with `python-dotenv` — keeps them out of the UI entirely except the one key a user is meant to paste in (`GOOGLE_API_KEY`, matching the sibling tutorials' pattern).
- **Deployed** (Streamlit Community Cloud etc.): use `st.secrets[...]` backed by `secrets.toml` — never commit that file.
- Either way: never put a real key as a string literal in this repo.

## 2. Mock data layer — stand-in for the real backend

In the real version these become API calls (Stripe for invoices, an internal auth service for password reset, a subscriptions DB for plan status). Keeping them as dicts means the wiring can be built and tested before any real backend integration exists.

```python
MOCK_INVOICES = {invoice_id: {amount, status, date}, ...}
MOCK_ACCOUNTS = {email: {plan, renewal_date}, ...}
```

## 3. Tools — one per specialist, plain Python functions

ADK auto-wraps a plain function into a callable tool from its signature + docstring, so the contract that matters is:
- type-hinted args (the LLM fills these in from the conversation)
- a docstring describing exactly when to call it (the LLM reads this to decide *if* to call it)
- a small dict return (status + payload) that the calling agent then turns into natural language

```python
def look_up_invoice(invoice_id: str) -> dict: ...             # used by billing_agent
def reset_password(account_email: str) -> dict: ...           # used by technical_agent
def check_subscription_status(account_email: str) -> dict: ...  # used by account_agent
```

**Wiring point:** each tool is passed into exactly one specialist's `tools=[...]` list. A tool is never shared between specialists — that's what keeps each sub-agent's responsibility narrow.

**Wiring point (learned while testing):** the sidebar's "Customer email" is the identity used for Mem0/session, but the chat *message text* is all the LLM actually sees. Unless the email is explicitly included in the message (see §7), `reset_password`/`check_subscription_status` have no way to know it and will just ask the customer to repeat it.

## 4. Specialist sub-agents — narrow, tool-carrying LlmAgents

Each specialist is an `LlmAgent` with:
- **name** — unique id ADK uses internally for delegation/logging
- **model** — `MODEL`
- **description** — this is the routing signal. The root agent's LLM reads every sub-agent's description to decide who should handle a given message. Write these like a job posting, not a summary.
- **instruction** — the specialist's own system prompt: how it should behave once a message has already been routed to it, including telling it to use the account email already present in the message context instead of re-asking
- **tools** — the one tool it's allowed to call

```python
billing_agent   = LlmAgent(name="billing_agent",   description="...invoices, payment disputes...", tools=[look_up_invoice])
technical_agent = LlmAgent(name="technical_agent", description="...login, password reset...",       tools=[reset_password])
account_agent   = LlmAgent(name="account_agent",   description="...subscription plan, renewal...",  tools=[check_subscription_status])
```

## 5. Root agent — triage_agent, wires the specialists together

```python
triage_agent = LlmAgent(
    name="triage_agent",
    model=MODEL,
    instruction="read the message + any memory context, pick a specialist, "
                "delegate; ask a clarifying question if unsure",
    sub_agents=[billing_agent, technical_agent, account_agent],
)
```

**Wiring point:** passing `sub_agents=[...]` is all that's needed for ADK to enable automatic transfer — no manual if/else routing logic. The root agent's LLM call effectively does: "given these 3 descriptions and this message, which one (if any) should I hand off to?"

## 6. ADK session layer — short-term, per-conversation state

```python
session_service = InMemorySessionService()
runner = Runner(agent=triage_agent, app_name=APP_NAME, session_service=session_service)
```

**Key idea:** `session_id` is scoped to "this browser session talking about this stuff right now." It resets if the Streamlit process restarts. That's intentional — ADK's session is not the thing responsible for remembering the customer across days/weeks. That job belongs to §7. Conflating the two is the mistake this design deliberately avoids.

```python
await session_service.create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
```
Called once per `user_id`, guarded by a flag in `st.session_state` so it isn't re-created on every Streamlit rerun.

**Wiring point (learned while testing):** `session_service`/`runner` (and `memory`, in §7) must be built once per *process*, not once per browser session — use `st.cache_resource`, not `st.session_state`. Embedded/on-disk Qdrant takes a file lock; caching `Memory.from_config(...)` per-session would crash the second concurrent user with "Storage folder ... already accessed by another instance."

## 7. Mem0 + Qdrant — long-term, cross-session memory

```python
memory = Memory.from_config({
    "llm":       {"provider": "gemini", "config": {"model": MODEL}},
    "embedder":  {"provider": "gemini", "config": {"model": "models/gemini-embedding-001", "embedding_dims": 768}},
    "vector_store": {"provider": "qdrant", "config": {"path": "./qdrant_storage", "embedding_model_dims": 768, "on_disk": True}},
})
```
Embedded on-disk Qdrant by default — no Docker, no separate server, no OpenAI key, since both the LLM and embedder are pinned to Gemini and read the same `GOOGLE_API_KEY`.

Two wiring points, one on each side of the agent call:

**Before routing** (step 1 in the diagram):
```python
relevant = memory.search(query=user_message, filters={"user_id": customer_email}, top_k=5)
augmented_message = f"Customer account email: {customer_email}\nRelevant past information:\n{relevant}\n\nCustomer says: {user_message}"
```
This is what actually gets sent to the ADK runner, not the raw user message — the triage agent's routing decision and the specialist's answer both benefit from this context, and the email line is what lets tools skip re-asking (see §3/§4).

**After answering** (step 5 in the diagram):
```python
memory.add(user_message, user_id=customer_email, metadata={"role": "user"})
memory.add(final_answer, user_id=customer_email, metadata={"role": "assistant"})
```
Next time this customer writes in — even a brand-new ADK session — the search step above surfaces this exchange.

> Note on API shape: Mem0 2.x rejects top-level `user_id=`/`limit=` on `search()`/`get_all()` — it wants `filters={"user_id": ...}` and `top_k=`. `add()` is the exception; it still takes `user_id` directly. Check the version actually installed (`pip show mem0ai`) before assuming which shape applies.

## 8. Runner call — the actual agent invocation, async under the hood

ADK's `Runner` is async-native (`run_async` yields a stream of events — tool calls, intermediate agent transfers, the final response). Streamlit is sync, so the wiring needs a small bridge:

```python
async def call_agent(user_id, session_id, message_text) -> str:
    content = types.Content(role="user", parts=[types.Part(text=message_text)])
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response():
            return event.content.parts[0].text

def run_agent_sync(...) -> str:
    return asyncio.run(call_agent(...))   # bridges async ADK -> sync Streamlit
```

**Wiring point:** `event.is_final_response()` is what filters out the noisy intermediate events (tool calls, sub-agent transfer events) so only the specialist's actual reply gets shown to the customer.

## 9. Streamlit UI — glues 1–8 into a chat loop

Sequence per user turn (mirrors the numbered diagram at the top):
1. `prompt = st.chat_input(...)`
2. `relevant_memories = memory.search(...)` — Mem0
3. `full_message = augment(prompt, relevant_memories, user_id)`
4. `answer = run_agent_sync(user_id, session_id, full_message)` — ADK
5. `memory.add(prompt, ...); memory.add(answer, ...)` — Mem0
6. `st.chat_message("assistant").markdown(answer)`

Sidebar wiring:
- customer email input → becomes both the Mem0 `user_id` **and** the ADK `session_id` seed (`f"session-{user_id}"`) → one identity threads through both memory systems
- "View customer memory" button → `memory.get_all(filters={"user_id": ...})` → lets you *see* the thing that step 2/5 are reading from and writing to, which is the best way to sanity-check the memory loop is actually working

## Extension points (once this wiring is validated end-to-end)

- `escalation_agent`: a 4th sub-agent for anything the 3 specialists can't resolve, `description="...anything not billing/technical/account, or requests to speak to a human..."`
- swap `MOCK_*` dicts for real API clients — tool function bodies change, tool signatures/docstrings (the LLM-facing contract) stay the same
- store tool call results as structured Mem0 metadata (not just chat text) so future searches can filter by e.g. `metadata["invoice_id"]`
- if routing quality matters, give `triage_agent` a cheaper/faster model than the specialists (it only ever makes a routing decision)
