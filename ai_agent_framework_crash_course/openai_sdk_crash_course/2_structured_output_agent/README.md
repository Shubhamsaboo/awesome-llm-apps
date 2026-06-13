# 🎯 Tutorial 2: Structured Output Agent

Learn how to create agents that return **type-safe, structured data** using Pydantic models. This tutorial teaches you how to ensure your agents return consistent, validated JSON responses that your applications can reliably process.

## 🎯 What You'll Learn

- **Structured Outputs**: Using Pydantic models to define response schemas
- **Type Safety**: Ensuring consistent data types and validation
- **JSON Schema Generation**: Automatic schema creation from Python classes
- **Output Validation**: Built-in validation and error handling

## 🧠 Core Concept: Why Structured Outputs?

Traditional AI responses are unstructured text, making them difficult to process programmatically. Structured outputs solve this by:

- **Consistency**: Always return the same data structure
- **Validation**: Automatic type checking and data validation
- **Integration**: Easy to integrate with databases, APIs, and applications
- **Reliability**: Reduce parsing errors and improve application stability

```
┌─────────────────────────────────────────────────────────────┐
│                    UNSTRUCTURED vs STRUCTURED               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  UNSTRUCTURED OUTPUT:                                       │
│  "The customer John Doe submitted a high priority           │
│   billing issue about charges on January 15th..."           │
│                                                             │
│  STRUCTURED OUTPUT:                                         │
│  {                                                          │
│    "customer_name": "John Doe",                             │
│    "issue_type": "billing",                                 │
│    "priority": "high",                                      │
│    "date_submitted": "2024-01-15",                          │
│    "description": "Incorrect charges on account"            │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Tutorial Overview

This tutorial includes **three focused structured output examples**:

### **1. Support Ticket Agent** (`2_1_support_ticket_agent/`)
- Basic structured output with enums
- Required and optional fields
- Business validation patterns

### **2. Product Review Agent** (`2_2_product_review_agent/`)
- Complex sentiment analysis schema
- List fields and nested validation
- Rating classification logic

### **3. Email Generator Agent** (`2_3_email_generator_agent/`)
- Simple two-field structure
- Enum validation for tone
- Content formatting patterns

## 📁 Project Structure

```
2_structured_output_agent/
├── README.md                    # This file - concept explanation
├── requirements.txt             # Dependencies
├── 2_1_support_ticket_agent/    # Basic structured output
│   ├── __init__.py
│   └── agent.py                # Support ticket schema (35 lines)
├── 2_2_product_review_agent/    # Complex structured output
│   ├── __init__.py
│   └── agent.py                # Product review analysis (45 lines)
├── 2_3_email_generator_agent/   # Simple structured output
│   ├── __init__.py
│   └── agent.py                # Email content generation (30 lines)
├── app.py                      # Streamlit web interface (optional)
└── env.example                 # Environment variables template
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to define Pydantic models for agent outputs
- ✅ Using the `output_type` parameter in agents
- ✅ Complex data structures with nested models
- ✅ Enum validation for controlled vocabularies
- ✅ Optional fields and default values
- ✅ Custom validation methods

## 🚀 Getting Started

1. **Install OpenAI Agents SDK**:
   ```bash
   pip install openai-agents
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Test the support ticket agent**:
   ```bash
   python support_ticket_agent.py
   ```

4. **Test the product review agent**:
   ```bash
   python product_review_agent.py
   ```

5. **Run the interactive web interface**:
   ```bash
   streamlit run app.py
   ```

## 🧪 Sample Use Cases

### Support Ticket Agent
Try these customer complaints:
- "My billing statement shows duplicate charges for last month's subscription"
- "I can't log into my account and need immediate help"
- "The app keeps crashing when I try to upload files"

### Product Review Agent  
Try these product reviews:
- "This laptop is amazing! Great battery life and super fast. Would definitely recommend. 5 stars!"
- "The phone camera quality is poor and battery drains quickly. Not worth the price."
- "Decent product but shipping took forever. Customer service was helpful though."

## 🔧 Key Pydantic Patterns

### 1. **Basic Model with Enums**
```python
class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SupportTicket(BaseModel):
    priority: Priority
    category: str
```

### 2. **Optional Fields with Defaults**
```python
class Review(BaseModel):
    rating: int = Field(ge=1, le=5)
    sentiment: str
    recommend: Optional[bool] = None
```

### 3. **Complex Nested Structures**
```python
class ProductReview(BaseModel):
    product_info: ProductInfo
    review_data: ReviewData
    analysis: ReviewAnalysis
```

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 3: Tool Using Agent](../3_tool_using_agent/README.md)** - Add custom tools and functions
- **[Tutorial 4: Runner Execution Methods](../4_running_agents/README.md)** - Master different execution patterns
- **[Tutorial 5: Context Management](../5_context_management/README.md)** - Manage state across interactions

## 💡 Pro Tips

- **Design Schemas First**: Plan your data structure before implementing
- **Use Descriptive Fields**: Clear field descriptions improve agent accuracy
- **Validate Constraints**: Use Pydantic validators for business rules
- **Handle Optionals**: Plan for missing or uncertain data
- **Test Edge Cases**: Try incomplete or ambiguous inputs

## 🚨 Troubleshooting

- **Validation Errors**: Check that your Pydantic model matches expected output
- **Missing Fields**: Ensure all required fields are included in the schema
- **Type Mismatches**: Verify field types match the data being returned
- **Enum Errors**: Make sure enum values match exactly (case-sensitive)
