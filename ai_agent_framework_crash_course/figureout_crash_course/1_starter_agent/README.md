# 🎯 Tutorial 1: Your First FigureOut Agent

Welcome to FigureOut! This tutorial introduces the core building blocks: creating a single-role agent and running your first query.

## 🎯 What You'll Learn

- How to define a `RoleDefinition`
- How to create a `FigureOut` agent
- How to run a query with `agent.run()`
- How to read the structured JSON response

## 🧠 Core Concept: How FigureOut Works

FigureOut is built around **roles**. Each role is a specialist that:
1. Has a system `prompt` describing its expertise
2. Defines a JSON `schema` for its response
3. Uses a `guideline` to tell the classifier when to pick it

When you call `agent.run("some query")`, FigureOut:
1. Classifies the query against all role guidelines
2. Picks the best-matching role
3. Calls the LLM with that role's prompt
4. Returns a JSON response matching the role's schema

## 🔧 Key Components

### `RoleDefinition`
```python
from figureout import RoleDefinition

RoleDefinition(
    prompt="You are a helpful assistant...",   # system prompt for the LLM
    schema='{"answer": "str"}',                # JSON schema for the response
    guideline="general questions",             # used by the classifier
)
```

### `FigureOut`
```python
from figureout import FigureOut

agent = FigureOut(
    llm="openai",            # provider: openai, gemini, claude, groq, mistral, meta
    llm_version="gpt-4o-mini",
    roles={"my_role": role_definition},
    api_key="sk-...",        # or set via env var OPENAI_API_KEY
)
```

### `agent.run()`
```python
import asyncio

result = asyncio.run(agent.run("What is the speed of light?"))
print(result)
# {"response": {"answer": "299,792,458 m/s", ...}, "debug": {...}}
```

## 📁 Project Structure

```
1_starter_agent/
├── README.md         # This file
├── requirements.txt  # Dependencies
└── agent.py          # Starter agent implementation
```

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key** (choose one):
   ```bash
   export OPENAI_API_KEY=sk-your_key_here   # Linux/Mac
   set OPENAI_API_KEY=sk-your_key_here      # Windows
   ```
   Or create a `.env` file:
   ```
   OPENAI_API_KEY=sk-your_key_here
   ```

3. **Run the agent**:
   ```bash
   python agent.py
   ```

## 🧪 Sample Output

```json
{
  "response": {
    "answer": "The speed of light in a vacuum is approximately 299,792,458 metres per second.",
    "confidence": "high"
  },
  "debug": {
    "roles_selected": ["qa"],
    "input_tokens": 120,
    "output_tokens": 35,
    "tools_used": []
  }
}
```

## 🔗 Next Steps

- **[Tutorial 2: Multi-Provider Agent](../2_multi_provider_agent/README.md)** — swap OpenAI for Claude or Gemini
- **[Tutorial 3: Structured Output Agent](../3_structured_output_agent/README.md)** — design richer JSON schemas
