# Support Ticket Agent

A structured output agent demonstrating Pydantic schema-based responses for customer support ticket creation.

## 🎯 What This Demonstrates

- **Structured Output**: Using Pydantic models to define response schemas
- **Enum Types**: Priority levels with controlled values
- **Optional Fields**: Flexible schema with required and optional properties
- **Field Validation**: Input validation and description metadata

## 🚀 Quick Start

1. **Install OpenAI Agents SDK**:
   ```bash
   pip install openai-agents
   ```

2. **Set up environment**:
   ```bash
   cp ../env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the agent**:
   ```python
   from agents import Runner
   from agent import root_agent
   
   result = Runner.run_sync(root_agent, "I can't log into my account and it's urgent!")
   print(result.final_output)  # Returns SupportTicket object
   ```

## 💡 Key Concepts

- **Pydantic Models**: Defining structured response schemas
- **Enum Validation**: Priority levels (low, medium, high, critical)
- **Field Descriptions**: Helping the LLM understand field requirements
- **Optional Fields**: Handling optional vs required data

## 🧪 Example Usage

```python
# The agent will return a SupportTicket object like:
{
    "title": "Account Login Issue",
    "description": "User unable to access account",
    "priority": "high",
    "category": "account_access",
    "steps_to_reproduce": ["Go to login page", "Enter credentials", "Error occurs"],
    "estimated_resolution_time": "2-4 hours"
}
```

## 🔗 Next Steps

- [Product Review Agent](../2_2_product_review_agent/README.md) - Complex structured output
- [Email Generator Agent](../2_3_email_generator_agent/README.md) - Simple structured output
- [Tutorial 3: Tool Using Agent](../../3_tool_using_agent/README.md) - Adding tools to agents
