# 🤖 Multi-Tenant RAG App with LongTrainer

A fully runnable tutorial that shows how to build a **production-ready, multi-tenant RAG application** using [LongTrainer](https://github.com/ENDEVSOLS/Long-Trainer) — a framework built on top of LangChain that handles multi-bot isolation, persistent memory, and agentic retrieval out of the box.

## What You'll Build

A Streamlit app where you can:
- **Create isolated bots** for different tenants (e.g. different companies / users)
- **Upload documents or URLs** to each bot's private knowledge base
- **Chat** with each bot — responses are grounded in *that tenant's* knowledge only
- See clearly that **no data leaks** between tenants

## Features

- **Multi-Bot Isolation** — Each tenant gets its own `bot_id` and vector store namespace
- **Document Ingestion** — Feed PDFs, DOCX, TXT files, or any URL into a bot
- **Persistent Chat History** — Every conversation thread is tracked per bot
- **One-line Setup** — LongTrainer abstracts all LangChain plumbing into simple API calls

## Prerequisites

You'll need:

1. **OpenAI API Key**
   - Sign up at [platform.openai.com](https://platform.openai.com/)
   - Navigate to **API Keys** and generate a new key

## How to Run

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shubhamsaboo/awesome-llm-apps.git
   cd awesome-llm-apps/rag_tutorials/longtrainer_multi_tenant_rag
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

4. **Use the app**
   - Enter your OpenAI API Key in the field at the top
   - Create a tenant bot in the sidebar (e.g. "Acme Corp")
   - Add URLs or upload documents to that bot's knowledge base
   - Switch to the **Chat** tab and ask questions
   - Create a second tenant bot and verify that documents from the first are **not accessible**

## How It Works

```
┌──────────────────────────────────────────────┐
│               LongTrainer                    │
│                                              │
│  Tenant A  ──►  Bot-ID-A  ──►  VectorStore-A │
│  Tenant B  ──►  Bot-ID-B  ──►  VectorStore-B │
│  Tenant C  ──►  Bot-ID-C  ──►  VectorStore-C │
└──────────────────────────────────────────────┘
```

| LongTrainer API | What it does |
|-----------------|--------------|
| `LongTrainer(openai_api_key=...)` | Initialises the framework |
| `initialize_bot_id()` | Provisions an isolated RAG namespace for a tenant |
| `add_url_to_bot(bot_id, url)` | Fetches, chunks & embeds a URL into the bot's vector store |
| `add_document_to_bot(bot_id, path)` | Parses & ingests PDF / DOCX / TXT |
| `get_new_chat(bot_id)` | Creates a fresh conversation thread |
| `chat(query, bot_id, chat_id)` | Retrieves context and returns a grounded answer |

LongTrainer wraps the full LangChain RAG pipeline — vector store management, embedding, retrieval-augmented generation, and conversation memory — into these five calls, making multi-tenant production deployment dramatically simpler.

## Learn More

- 📦 [LongTrainer on PyPI](https://pypi.org/project/longtrainer/)
- 📖 [LongTrainer GitHub](https://github.com/ENDEVSOLS/Long-Trainer)
- 📚 [LangChain Documentation](https://python.langchain.com/)
