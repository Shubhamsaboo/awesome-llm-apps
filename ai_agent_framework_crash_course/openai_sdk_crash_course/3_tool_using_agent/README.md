# 🎯 Tutorial 3: Tool Using Agent

Welcome to the world of tools! This tutorial teaches you how to create agents that can use **custom functions and built-in tools** to perform specific tasks. This is where your agents become truly powerful and capable of real-world actions.

## 🎯 What You'll Learn

- **Function Tools**: Creating custom Python functions as agent tools
- **Built-in Tools**: Using OpenAI's pre-built capabilities
- **Tool Integration**: Adding tools to agents effectively
- **Tool Execution**: Understanding how agents decide when to use tools

## 🧠 Core Concept: Tools in OpenAI Agents SDK

Tools are **functions that your agent can call** to perform specific tasks. Think of them as the agent's "hands" - they allow the agent to:
- Perform calculations and data processing
- Search the web and access real-time information
- Execute code and analyze data
- Call external APIs and services
- Access databases and file systems

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT WITH TOOLS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   INPUT     │───▶│    AGENT    │───▶│   OUTPUT    │     │
│  │ "Calculate  │    │  Reasoning  │    │ "Using the  │     │
│  │  compound   │    │ + Tool Use  │    │ calculator  │     │
│  │  interest"  │    │             │    │ tool: $..."│     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                             │                               │
│                             ▼                               │
│                      ┌─────────────┐                       │
│                      │    TOOLS    │                       │
│                      │ ┌─────────┐ │                       │
│                      │ │Calculator│ │                       │
│                      │ ├─────────┤ │                       │
│                      │ │Web Search│ │                       │
│                      │ ├─────────┤ │                       │
│                      │ │File I/O │ │                       │
│                      │ └─────────┘ │                       │
│                      └─────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Types of Tools

### 1. **Function Tools**
Custom Python functions you create:
```python
@function_tool
def calculate_compound_interest(principal: float, rate: float, time: int) -> float:
    """Calculate compound interest"""
    return principal * (1 + rate) ** time
```

### 2. **Built-in Tools**
OpenAI provides powerful pre-built tools:
- **WebSearchTool**: Search the web for current information
- **CodeInterpreterTool**: Execute Python code safely
- **FileSearchTool**: Search through uploaded files

## 🚀 Tutorial Overview

This tutorial includes **three focused tool integration examples**:

### **1. Function Tools** (`3_1_function_tools/`)
- Custom Python functions as tools
- `@function_tool` decorator usage
- Basic mathematical and utility functions

### **2. Built-in Tools** (`3_2_builtin_tools/`)
- OpenAI's WebSearchTool integration
- CodeInterpreterTool for computations
- Pre-built tool capabilities

### **3. Agents as Tools** (`3_3_agents_as_tools/`)
- Using agents as tools for orchestration
- Specialized agent coordination
- Advanced agent composition patterns

## 📁 Project Structure

```
3_tool_using_agent/
├── README.md                    # This file - concept explanation
├── requirements.txt             # Dependencies
├── 3_1_function_tools/          # Custom function tools
│   ├── __init__.py
│   ├── tools.py                # Custom tool definitions
│   └── agent.py                # Agent with function tools (25 lines)
├── 3_2_builtin_tools/           # Built-in tools integration
│   ├── __init__.py
│   └── agent.py                # Agent with built-in tools (30 lines)
├── 3_3_agents_as_tools/         # Agents as tools pattern
│   ├── __init__.py
│   ├── agent.py                # Basic agent orchestration (40 lines)
│   └── advanced_agent.py       # Custom agent tools with Runner config
├── app.py                      # Streamlit web interface (optional)
└── env.example                 # Environment variables template
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to create custom function tools with `@function_tool`
- ✅ How to integrate built-in tools like WebSearch and CodeInterpreter
- ✅ How agents decide when and how to use tools
- ✅ Best practices for tool design and integration
- ✅ Error handling and tool validation

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

3. **Test the calculator agent**:
   ```bash
   python calculator_agent.py
   ```

4. **Test the research agent**:
   ```bash
   python research_agent.py
   ```

5. **Test the data analysis agent**:
   ```bash
   python data_analysis_agent.py
   ```

6. **Run the interactive web interface**:
   ```bash
   streamlit run app.py
   ```

## 🧪 Sample Use Cases

### Agents as Tools
Try these orchestration requests:
- "Translate 'Hello, how are you?' to Spanish and French"
- "Say 'Good morning' in all available languages"
- "Research artificial intelligence and write a professional summary"

### Research Agent
Try these information requests:
- "What's the latest news about artificial intelligence?"
- "Find information about renewable energy trends in 2024"
- "Search for Python programming best practices"

### Data Analysis Agent
Try these data requests:
- "Analyze this CSV data: [paste some data]"
- "Create a simple bar chart of sales data"
- "Calculate statistical measures for this dataset"

## 🔧 Key Tool Patterns

### 1. **Simple Function Tool**
```python
@function_tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together"""
    return a + b
```

### 2. **Complex Function Tool with Validation**
```python
@function_tool
def get_weather(city: str, units: str = "metric") -> str:
    """Get current weather for a city"""
    if not city.strip():
        return "Error: City name cannot be empty"
    
    # API call logic here
    return f"Weather data for {city}"
```

### 3. **Agents as Tools Integration**
```python
from agents import Agent

# Define specialized agents
translator = Agent(name="Translator", instructions="Translate text")

# Use agent as a tool
orchestrator = Agent(
    name="Orchestrator",
    instructions="Coordinate translation tasks",
    tools=[
        translator.as_tool(
            tool_name="translate_text",
            tool_description="Translate user's message"
        )
    ]
)
```

## 💡 Tool Design Best Practices

1. **Clear Docstrings**: Tools need descriptive docstrings for the agent to understand their purpose
2. **Type Hints**: Always use proper type hints for parameters and return values
3. **Error Handling**: Handle errors gracefully and return meaningful messages
4. **Simple Parameters**: Keep tool parameters simple and well-defined
5. **Single Purpose**: Each tool should do one thing well

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 4: Runner Execution Methods](../4_running_agents/README.md)** - Master different execution patterns
- **[Tutorial 5: Context Management](../5_context_management/README.md)** - Manage state across interactions
- **[Tutorial 6: Guardrails & Validation](../6_guardrails_validation/README.md)** - Add safety and validation

## 🚨 Troubleshooting

- **Tool Not Called**: Check that your tool docstring clearly describes its purpose
- **Type Errors**: Verify that parameter types match the function signature
- **Import Issues**: Make sure you've imported the `function_tool` decorator
- **API Errors**: For built-in tools, check your OpenAI API key and permissions
