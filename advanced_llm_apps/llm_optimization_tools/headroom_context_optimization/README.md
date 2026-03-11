# 🧠 Headroom - Context Optimization Layer

Reduce LLM API costs by 50-90% through intelligent context compression. Tool outputs are 70-95% redundant boilerplate—Headroom compresses that away while preserving accuracy.

## 📋 Overview

This app demonstrates how to use [Headroom](https://github.com/chopratejas/headroom) to dramatically reduce token usage when working with AI agents and tool-heavy LLM applications. Unlike simple truncation, Headroom uses statistical analysis to keep what matters and compress what doesn't.

### Key Benefits

- **💰 47-92% token reduction** verified across real workloads
- **🎯 Zero code changes** - works as a transparent proxy
- **🔄 Reversible compression** - LLM can retrieve original data via CCR
- **🧠 Content-aware** - handles code, logs, JSON optimally
- **⚡ Provider caching** - automatic prefix optimization for cache hits
- **🔌 Framework native** - LangChain, Agno, MCP, any OpenAI client

## 🚀 Features

- **SmartCrusher**: Statistical compression of JSON tool outputs—keeps first items, last items, anomalies, and query-relevant matches
- **CacheAligner**: Stabilizes prefixes for better provider-side caching (OpenAI, Anthropic, Google)
- **RollingWindow**: Manages context limits without breaking tool call/response pairing
- **Code-Aware Compression**: AST-based compression using tree-sitter
- **LLMLingua-2 Integration**: Optional ML-based 20x compression
- **Memory System**: Persistent, LLM-driven memory with zero-latency inline extraction
- **CCR (Compress-Cache-Retrieve)**: Reversible compression—LLM requests original data when needed

## 📦 Installation

### Basic Installation

```bash
pip install headroom-ai
```

### With Framework Integrations

```bash
pip install "headroom-ai[proxy]"      # Proxy server (zero code changes)
pip install "headroom-ai[langchain]"  # LangChain integration
pip install "headroom-ai[agno]"       # Agno agent framework
pip install "headroom-ai[code]"       # AST-based code compression
pip install "headroom-ai[llmlingua]"  # ML-based compression
pip install "headroom-ai[all]"        # Everything
```

## 💻 Usage

### Option 1: Proxy (Zero Code Changes)

```bash
headroom proxy --port 8787
```

Point your existing tools at the proxy:

```bash
# Claude Code
ANTHROPIC_BASE_URL=http://localhost:8787 claude

# Cursor or any OpenAI-compatible client
OPENAI_BASE_URL=http://localhost:8787/v1 cursor
```

### Option 2: LangChain Integration

```python
from langchain_openai import ChatOpenAI
from headroom.integrations import HeadroomChatModel

# Wrap your model - that's it!
llm = HeadroomChatModel(ChatOpenAI(model="gpt-4o"))
response = llm.invoke("Analyze these logs and find the error")
```

### Option 3: Agno Agent Framework

```python
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from headroom.integrations.agno import HeadroomAgnoModel

# Wrap your model
model = HeadroomAgnoModel(OpenAIChat(id="gpt-4o"))
agent = Agent(model=model, tools=[search_github, search_code, query_db])

response = agent.run("Investigate the memory leak")
print(f"Tokens saved: {model.total_tokens_saved}")
```

## 📊 Real-World Performance

These numbers are from actual API calls, not estimates:

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| Code search (100 results) | 17,765 tokens | 1,408 tokens | **92%** |
| SRE incident debugging | 65,694 tokens | 5,118 tokens | **92%** |
| Codebase exploration | 78,502 tokens | 41,254 tokens | **47%** |
| GitHub issue triage | 54,174 tokens | 14,761 tokens | **73%** |
| Multi-tool agent | 15,662 tokens | 6,100 tokens | **76%** |

## 🔬 Proof: Needle in Haystack Test

**Setup:** 100 production log entries. One critical FATAL error buried at position 67.

**Before Headroom:** 10,144 tokens
**After Headroom:** 1,260 tokens (**87.6% reduction**)

**The question:** "What caused the outage? What's the error code? What's the fix?"

**Both responses (baseline and Headroom):** *"payment-gateway service, error PG-5523, fix: Increase max_connections to 500, 1,847 transactions affected"*

**Same answer. 87.6% fewer tokens.**

```bash
# Run it yourself
python headroom_demo.py
```

## 🎯 Best Use Cases

**Use Headroom when:**
- ✅ Building AI agents with multiple tools (search, database, APIs)
- ✅ Processing large tool outputs (logs, code search results, API responses)
- ✅ Context window is filling up with redundant data
- ✅ Reducing LLM API costs at scale

**Headroom shines with:**
- 🔍 Code search results
- 📋 Log analysis
- 🗄️ Database query results
- 🔗 API response processing
- 🤖 Multi-tool agent workflows

## 🛡️ Safety Guarantees

- **Never removes human content** - user/assistant messages preserved
- **Never breaks tool ordering** - tool calls and responses stay paired
- **Parse failures are no-ops** - malformed content passes through unchanged
- **Compression is reversible** - LLM retrieves original via CCR

## 🔗 Resources

- **GitHub**: https://github.com/chopratejas/headroom
- **PyPI**: https://pypi.org/project/headroom-ai/
- **Documentation**: https://github.com/chopratejas/headroom/tree/main/docs
- **Demo Video**: https://github.com/chopratejas/headroom/releases

## 🔌 Provider Support

| Provider | Token Counting | Cache Optimization |
|----------|----------------|-------------------|
| OpenAI | tiktoken (exact) | Automatic prefix caching |
| Anthropic | Official API | cache_control blocks |
| Google | Official API | Context caching |
| Cohere | Official API | - |
| Mistral | Official tokenizer | - |

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new compression strategies
- Add benchmarks
- Improve documentation

## 📄 License

Apache License 2.0 - see [LICENSE](https://github.com/chopratejas/headroom/blob/main/LICENSE).

## 🙏 Credits

Built by [Tejas Chopra](https://github.com/chopratejas) for the AI developer community.
