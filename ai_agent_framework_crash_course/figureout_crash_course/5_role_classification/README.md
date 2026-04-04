# 🗂️ Tutorial 5: Role Classification

FigureOut's classifier is what makes it an *orchestrator* rather than a simple agent. When you define multiple roles, FigureOut automatically reads the incoming query and routes it to the most relevant specialist — no `if/elif` chains required.

## 🎯 What You'll Learn

- How to define multiple specialist roles with distinct guidelines
- How the classifier picks a role based on the `guideline` field
- What happens when a query matches no role (`off_topic` fallback)
- How to inspect which role was selected via `debug`

## 🧠 Core Concept: The Classifier

When `agent.run(query)` is called:
1. FigureOut sends all role `guideline`s to the LLM classifier
2. The classifier returns the name of the best-matching role
3. That role's `prompt` and `schema` are used for the actual response

```
Query: "What's the capital of France?"
  → Classifier reads guidelines for all roles
  → Selects "geography" role
  → LLM uses geography prompt + schema to answer
```

### Writing Effective Guidelines

- Be **specific** — vague guidelines cause misclassification
- Cover **edge cases** — mention synonyms or related phrasings
- Avoid **overlap** — two roles with similar guidelines will compete

```python
# Too vague — will compete with many other roles
guideline="questions"

# Specific and clear
guideline="questions about world geography, countries, capitals, and maps"
```

### The `off_topic` Role

If no role matches, FigureOut selects `off_topic`. Always define it:

```python
"off_topic": RoleDefinition(
    prompt="Politely tell the user this is outside your scope.",
    schema='{"message": "str"}',
    guideline="anything not covered by the other roles",
)
```

## 📁 Project Structure

```
5_role_classification/
├── README.md         # This file
├── requirements.txt  # Dependencies
└── agent.py          # Customer support agent with 4 specialist roles
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
Query: "How do I reset my password?"
Role selected: account_support
Response: {"issue": "Password reset", "steps": [...], "escalate": false}

Query: "What's the price of the Pro plan?"
Role selected: billing_support
Response: {"topic": "Pro plan pricing", "answer": "...", "links": [...]}

Query: "What's the weather today?"
Role selected: off_topic
Response: {"message": "I can only help with account, billing, and technical issues."}
```

## 🔗 Next Steps

- **[Tutorial 6: Multi-Role Queries](../6_multi_role_queries/README.md)** — handle queries that span multiple roles in parallel
