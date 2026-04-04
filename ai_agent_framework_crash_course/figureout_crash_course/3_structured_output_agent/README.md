# 📐 Tutorial 3: Structured Output Agent

FigureOut enforces that every role returns a **schema-validated JSON response**. This tutorial shows how to design rich, multi-field schemas and build an agent that produces predictable, parseable output.

## 🎯 What You'll Learn

- How to write JSON schemas with nested fields and lists
- How schema design influences the LLM's output
- How to parse and use structured responses in your application

## 🧠 Core Concept: JSON Schemas in FigureOut

Every `RoleDefinition` includes a `schema` field — a string describing the expected JSON structure. FigureOut instructs the LLM to return output that matches this schema exactly.

### Simple Schema
```python
schema='{"answer": "str", "confidence": "str"}'
```

### Rich Schema with Lists and Nested Objects
```python
schema='''{
    "title": "str",
    "summary": "str",
    "pros": ["str"],
    "cons": ["str"],
    "verdict": "str",
    "score": "int (1-10)"
}'''
```

The richer your schema, the more structured and useful your responses become. Design schemas that match exactly what your application needs to render or process.

## 🔧 Schema Design Tips

- Use descriptive key names — the LLM uses them to understand what to fill in
- Add hints in parentheses: `"score": "int (1-10)"` tells the LLM the expected range
- Use lists (`["str"]`) for variable-length collections
- Keep schemas flat when possible — nested objects add complexity

## 📁 Project Structure

```
3_structured_output_agent/
├── README.md         # This file
├── requirements.txt  # Dependencies
└── agent.py          # Product review agent with rich schema
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

```json
{
  "response": {
    "title": "iPhone 15 Pro Review",
    "summary": "A powerful flagship with a titanium build and USB-C.",
    "pros": ["Titanium chassis", "USB-C finally", "Excellent camera system"],
    "cons": ["Expensive", "Battery life unchanged"],
    "verdict": "Best iPhone yet, but incremental over iPhone 14 Pro",
    "score": 8
  }
}
```

## 🔗 Next Steps

- **[Tutorial 4: Tool Using Agent](../4_tool_using_agent/README.md)** — add live MCP tools to your agent
- **[Tutorial 5: Role Classification](../5_role_classification/README.md)** — route queries to different schemas automatically
