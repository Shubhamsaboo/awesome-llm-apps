# 🔄 Tutorial 2: Multi-Provider Agent

One of FigureOut's core strengths is provider-agnosticism. The same agent definition runs on OpenAI, Claude, Gemini, Groq, Mistral, or Meta Llama — just change two parameters.

## 🎯 What You'll Learn

- How to switch LLM providers with `llm` and `llm_version`
- Which API key each provider requires
- How to run the same query across multiple providers and compare responses

## 🧠 Core Concept: Provider Swapping

FigureOut abstracts away provider differences. The same `roles`, `schema`, and `guideline` work identically regardless of the backend:

```python
# OpenAI
agent = FigureOut(llm="openai", llm_version="gpt-4o-mini", roles=roles, api_key="sk-...")

# Claude
agent = FigureOut(llm="claude", llm_version="claude-haiku-4-5-20251001", roles=roles, api_key="sk-ant-...")

# Gemini
agent = FigureOut(llm="gemini", llm_version="gemini-2.0-flash", roles=roles, api_key="AI...")
```

## 🔧 Supported Providers

| `llm` value | Model example | Env var |
|---|---|---|
| `openai` | `gpt-4o-mini` | `OPENAI_API_KEY` |
| `claude` | `claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` |
| `gemini` | `gemini-2.0-flash` | `GEMINI_API_KEY` |
| `groq` | `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| `mistral` | `mistral-small-latest` | `MISTRAL_API_KEY` |
| `meta` | `Llama-4-Scout-17B-16E-Instruct` | `META_API_KEY` |

## 📁 Project Structure

```
2_multi_provider_agent/
├── README.md         # This file
├── requirements.txt  # Dependencies
└── agent.py          # Multi-provider comparison agent
```

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API keys** for the providers you want to test:
   ```bash
   export OPENAI_API_KEY=sk-...
   export ANTHROPIC_API_KEY=sk-ant-...
   export GEMINI_API_KEY=AI...
   ```

3. **Run the agent**:
   ```bash
   python agent.py
   ```

## 💡 Pro Tips

- You only need **one** provider's API key to get started
- Groq is free-tier friendly for experimenting
- Model versions change — check the provider's docs for the latest model IDs

## 🔗 Next Steps

- **[Tutorial 3: Structured Output Agent](../3_structured_output_agent/README.md)** — design richer JSON schemas
- **[Tutorial 4: Tool Using Agent](../4_tool_using_agent/README.md)** — add MCP tools
