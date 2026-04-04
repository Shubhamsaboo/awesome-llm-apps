# 🔀 Tutorial 6: Multi-Role Queries

Some queries naturally span multiple domains — "Show me concerts and sports events this weekend" touches both a music role and a sports role. FigureOut supports **parallel multi-role execution** via the `max_roles` parameter.

## 🎯 What You'll Learn

- How to enable multi-role query handling with `max_roles`
- How FigureOut runs multiple roles in parallel
- How to read and merge responses from multiple roles
- When to use multi-role vs single-role mode

## 🧠 Core Concept: `max_roles`

By default, `max_roles=1` — only the best-matching role handles the query. Setting `max_roles > 1` allows the classifier to select up to N roles, each of which runs in parallel and contributes a response.

```python
agent = FigureOut(
    llm="openai",
    llm_version="gpt-4o-mini",
    roles=roles,
    max_roles=3,   # up to 3 roles can handle a single query simultaneously
)
```

### When to Use Multi-Role Mode

| Scenario | Recommended `max_roles` |
|---|---|
| Clearly focused queries | `1` (default) |
| Queries that mix 2-3 topics | `2` or `3` |
| Broad discovery queries | `3+` |
| You want the fastest response | `1` |

### Response Structure with Multiple Roles

When multiple roles fire, `result["response"]` contains a merged or primary response, and `result["debug"]["roles_selected"]` lists all roles that contributed:

```json
{
  "debug": {
    "roles_selected": ["news", "stock_price"],
    "tools_used": ["get_news", "get_stock_quote"]
  }
}
```

## 📁 Project Structure

```
6_multi_role_queries/
├── README.md         # This file
├── requirements.txt  # Dependencies
└── agent.py          # Financial assistant with multi-role queries
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
Query: "What's the latest news and stock price for Apple?"
Roles selected: ['stock_price', 'news']
Response: { ... combined financial + news context ... }

Query: "Give me the weather and news for New York"
Roles selected: ['weather', 'news']
Response: { ... }
```

## 💡 Pro Tips

- With `max_roles > 1`, write role guidelines that are **mutually exclusive** for single-topic queries — you don't want multiple roles firing when only one is needed
- Use `max_roles=1` in production for cost efficiency unless multi-domain queries are a core use case
- The debug output always shows which roles fired — use it to tune your guidelines

## 🎉 What's Next?

You've completed the FigureOut crash course! Here's what to explore next:

- **[FigureOut GitHub](https://github.com/balajeekalyan/figureout)** — source code, issues, and full API reference
- **[Full Demo App](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/advanced_ai_agents/multi_agent_apps/figureout_multi_llm_orchestrator)** — a complete Events & Booking assistant using all FigureOut features
