# ⚡ Tutorial 7: In-Memory Caching

FigureOut includes a built-in in-memory cache. When the same natural language query is run again, FigureOut returns the cached response immediately — no LLM call, no latency, no token cost.

## 🎯 What You'll Learn

- How FigureOut's cache works
- How to observe cache hits vs cache misses
- How token usage drops to zero on a cache hit
- Real-world scenarios where caching is valuable

## 🧠 Core Concept: Query-Level Caching

FigureOut caches at the **natural language query** level. The full query string is used as the cache key. On a cache hit:

- The LLM is **not called**
- Token usage is **zero**
- Response time is **near-instant**

```
First call:  "Find me concerts in New York"  →  LLM called  →  response cached
Second call: "Find me concerts in New York"  →  cache hit   →  response returned instantly
Third call:  "Find concerts in New York"     →  cache miss  →  LLM called (different string)
```

> **Note:** The cache matches on the exact query string. Rephrased queries are treated as new queries.

## 🔧 How to Observe Cache Behaviour

Check `result["debug"]` to see whether a response came from the cache:

```python
result = asyncio.run(agent.run("What is machine learning?"))
debug = result.get("debug", {})

print(debug.get("cached"))        # True if served from cache
print(debug.get("input_tokens"))  # 0 on a cache hit
print(debug.get("output_tokens")) # 0 on a cache hit
```

## 📁 Project Structure

```
7_caching/
├── README.md         # This file
├── requirements.txt  # Dependencies
└── agent.py          # Cache demonstration with timing and token tracking
```

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key**:
   ```bash
   export OPENAI_API_KEY=sk-your_key_here
   ```

3. **Run the agent**:
   ```bash
   python agent.py
   ```

## 🧪 Sample Output

```
--- Run 1 (cold cache) ---
Query:         What is machine learning?
Cached:        False
Input tokens:  145
Output tokens: 52
Time:          1.83s

--- Run 2 (cache hit) ---
Query:         What is machine learning?
Cached:        True
Input tokens:  0
Output tokens: 0
Time:          0.001s

--- Run 3 (different query — cache miss) ---
Query:         What is deep learning?
Cached:        False
Input tokens:  147
Output tokens: 55
Time:          1.71s
```

## 💡 When Caching is Most Valuable

- **FAQ bots** — the same questions are asked repeatedly
- **Demo applications** — avoid burning tokens on identical test queries
- **High-traffic agents** — reduce LLM costs significantly at scale
- **Development** — iterate faster without hitting rate limits

## 🔗 What's Next?

**[Tutorial 8 — Hallucination Control](../8_hallucination_control/README.md)**: Learn how `inject_date` grounds the LLM to today's date so it can correctly resolve relative time expressions like "this weekend" or "end of this month".

Or explore the full resources:

- **[FigureOut GitHub](https://github.com/balajeekalyan/figureout)** — source code and full API reference
- **[Full Demo App](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/advanced_ai_agents/multi_agent_apps/figureout_multi_llm_orchestrator)** — a complete Events & Booking assistant using all FigureOut features
