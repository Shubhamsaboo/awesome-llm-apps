## 🎧 ADK Multi-Agent Customer Support with Memory
This Streamlit app implements a multi-agent customer support assistant built with Google's Agent Development Kit (ADK). A **triage agent** delegates each request to the right **specialist sub-agent** (billing, technical, or account), while **Mem0 + Qdrant** remember each customer's history across sessions.

Unlike the other tutorials in this folder, which use a single agent with mem0 bolted onto its prompt, this example splits the two concerns explicitly:
- **ADK** handles orchestration and the current conversation — deciding which specialist should answer, running tools, keeping short-term turn state.
- **Mem0 + Qdrant** handle long-term memory — what this specific customer has raised before, their plan, their preferences — pulled in *before* routing and written back *after* every reply.

### Features
- Root `triage_agent` (Google ADK `LlmAgent`) that automatically delegates to `billing_agent`, `technical_agent`, or `account_agent` sub-agents based on the request
- Each specialist has its own focused tool (`look_up_invoice`, `reset_password`, `check_subscription_status`) backed by mock data — swap these for real API/DB calls
- Mem0 + Qdrant recall relevant past interactions for the current customer before the triage agent routes the message
- Every exchange is written back to Mem0 so the next session (even with a brand-new ADK session) starts with full context
- Sidebar "View customer memory" to inspect what's been remembered for a given customer email
- Runs on a **single Google API key** — no Docker, no Qdrant server, no OpenAI key. Mem0 is configured to use Gemini for both its internal LLM (fact extraction) and its embeddings, and Qdrant runs in embedded on-disk mode (`./qdrant_storage/`), not as a separate service.

### How it works
1. Customer sends a message.
2. The app queries Mem0 for memories relevant to that message, for that `user_id`.
3. The message plus the retrieved memory context is handed to the ADK `triage_agent`.
4. The triage agent's LLM decides which specialist sub-agent should handle it and transfers control.
5. The specialist calls its tool if needed and replies.
6. The customer's message and the final answer are both written back into Mem0.

### How to get Started?

1. Clone the GitHub repository
```bash
git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
cd awesome-llm-apps/advanced_llm_apps/llm_apps_with_memory_tutorials/adk_customer_support_agent_memory
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

3. Get a Google API key for Gemini from [Google AI Studio](https://aistudio.google.com/apikey) — you'll paste it into the app's UI at runtime. That's the only credential this app needs.

4. Run the Streamlit App
```bash
streamlit run adk_customer_support_agent_memory.py
```

The first run creates a `qdrant_storage/` folder next to the script — that's Mem0's embedded, on-disk vector store. Delete it if you want to wipe all remembered customer history.

### Using a real Qdrant server instead
The embedded mode above is the default because it needs nothing beyond the one API key. If you'd rather point at a real Qdrant instance (shared across machines, or just persistent/inspectable via Qdrant's dashboard), swap the `vector_store` block in `MEM0_CONFIG` for:
```python
"vector_store": {
    "provider": "qdrant",
    "config": {
        "collection_name": "adk_customer_support",
        "host": "localhost",  # or use "url"/"api_key" for Qdrant Cloud
        "port": 6333,
        "embedding_model_dims": 768,
    },
},
```
and start a server first, either via Docker (`docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z qdrant/qdrant`) or the standalone Windows `qdrant.exe` binary from the [Qdrant releases page](https://github.com/qdrant/qdrant/releases).

### Notes / next steps
- This is a sketch: `MOCK_INVOICES` / `MOCK_ACCOUNTS` and the three tools are stand-ins for a real billing/auth/subscription backend.
- `google-adk`'s API is young and moves fast — if something doesn't match your installed version, check the [ADK docs](https://google.github.io/adk-docs/) for the current `LlmAgent` / `Runner` / `sub_agents` signatures.
- Natural extensions: add a 4th "escalation" sub-agent for anything the specialists can't resolve, or log every tool call to Mem0 as structured metadata instead of just the chat text.
