# 📋 Tutorial 6: Callbacks

## 🎯 What You'll Learn
- **Agent Lifecycle Callbacks**: Monitor agent creation, initialization, and cleanup
- **LLM Interaction Callbacks**: Track model requests, responses, and token usage
- **Tool Execution Callbacks**: Monitor tool calls, parameters, and results

## 💡 Core Concept: Callbacks

Callbacks are functions that get executed at specific points during agent execution, allowing you to monitor, log, and control the agent's behavior without modifying the core logic.

### **Callback Flow Diagram**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent Start   │───▶│  LLM Request    │───▶│  Tool Execution │
│   Callback      │    │   Callback      │    │   Callback      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Agent End      │    │  LLM Response   │    │  Tool Result    │
│  Callback       │    │   Callback      │    │   Callback      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Why Use Callbacks?**
- **Monitoring**: Track agent performance and behavior
- **Logging**: Record interactions for debugging and analysis
- **Control**: Modify behavior based on specific events
- **Integration**: Connect agents to external systems
- **Debugging**: Understand what's happening inside the agent

## 📖 Tutorial Overview

This tutorial covers three essential callback patterns in Google ADK:

1. **Agent Lifecycle Callbacks**: Monitor agent creation, initialization, and cleanup events
2. **LLM Interaction Callbacks**: Track model requests, responses, and token usage
3. **Tool Execution Callbacks**: Monitor tool calls, parameters, and execution results

Each sub-tutorial provides simple, focused examples that demonstrate specific callback patterns.

## 📁 Project Structure

```
6_callbacks/
├── README.md                           # This file - concept explanation
├── 6_1_agent_lifecycle_callbacks/      # Agent lifecycle monitoring
│   ├── README.md                       # Lifecycle callback patterns
│   ├── agent.py                        # Agent with lifecycle callbacks
│   ├── app.py                          # Streamlit interface
│   └── requirements.txt                # Dependencies
├── 6_2_llm_interaction_callbacks/      # LLM request/response tracking
│   ├── README.md                       # LLM callback patterns
│   ├── agent.py                        # Agent with LLM callbacks
│   ├── app.py                          # Streamlit interface
│   └── requirements.txt                # Dependencies
└── 6_3_tool_execution_callbacks/       # Tool execution monitoring
    ├── README.md                       # Tool callback patterns
    ├── agent.py                        # Agent with tool callbacks
    ├── app.py                          # Streamlit interface
    └── requirements.txt                # Dependencies
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:

- ✅ **Callback Fundamentals**: How callbacks work in Google ADK
- ✅ **Lifecycle Monitoring**: Track agent creation, initialization, and cleanup
- ✅ **LLM Tracking**: Monitor model requests, responses, and performance
- ✅ **Tool Monitoring**: Track tool execution and results
- ✅ **Practical Applications**: Real-world use cases for callbacks
- ✅ **Debugging Techniques**: Use callbacks for troubleshooting

## 🚀 Getting Started

### **Prerequisites**
- Python 3.11+
- Google AI Studio API key
- Basic understanding of Google ADK (Tutorials 1-5)

### **Setup**
1. **Get API Key**: Visit [Google AI Studio](https://aistudio.google.com/)
2. **Create .env file**: Add `GOOGLE_API_KEY=your_key_here`
3. **Install dependencies**: `pip install -r requirements.txt`

### **Run Tutorials**
```bash
# Agent Lifecycle Callbacks
cd 6_1_agent_lifecycle_callbacks
streamlit run app.py

# LLM Interaction Callbacks  
cd ../6_2_llm_interaction_callbacks
streamlit run app.py

# Tool Execution Callbacks
cd ../6_3_tool_execution_callbacks
streamlit run app.py
```

## ⚙️ Callback Patterns

### **1. Agent Lifecycle Callbacks**
```python
def on_agent_start(agent_name: str):
    print(f"▶️ Agent {agent_name} started")

def on_agent_end(agent_name: str, result: str):
    print(f"✅ Agent {agent_name} completed: {result}")

# Register callbacks
agent = LlmAgent(
    name="my_agent",
    model="gemini-3-flash-preview",
    on_start=on_agent_start,
    on_end=on_agent_end
)
```

### **2. LLM Interaction Callbacks**
```python
def on_llm_request(model: str, prompt: str):
    print(f"📤 LLM Request to {model}: {prompt[:50]}...")

def on_llm_response(model: str, response: str, tokens: int):
    print(f"📥 LLM Response from {model}: {tokens} tokens")

# Register callbacks
agent = LlmAgent(
    name="my_agent",
    model="gemini-3-flash-preview",
    on_llm_request=on_llm_request,
    on_llm_response=on_llm_response
)
```

### **3. Tool Execution Callbacks**
```python
def on_tool_start(tool_name: str, params: dict):
    print(f"🔧 Tool {tool_name} started with params: {params}")

def on_tool_end(tool_name: str, result: str):
    print(f"✅ Tool {tool_name} completed: {result}")

# Register callbacks
agent = LlmAgent(
    name="my_agent",
    model="gemini-3-flash-preview",
    tools=[my_tool],
    on_tool_start=on_tool_start,
    on_tool_end=on_tool_end
)
```

## 📊 Use Cases

### **Monitoring & Analytics**
- Track agent performance metrics
- Monitor token usage and costs
- Analyze tool usage patterns
- Debug agent behavior

### **Logging & Debugging**
- Log all agent interactions
- Debug tool execution issues
- Monitor LLM response quality
- Track error patterns

### **Integration & Control**
- Connect to external monitoring systems
- Implement custom error handling
- Add authentication and validation
- Control agent behavior dynamically

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:

- **[Advanced Agent Patterns](../6_callbacks/README.md)** - Complex agent architectures
- **[Production Deployment](../7_plugins/README.md)** - Deploying agents to production
- **[Custom Tools](../4_tool_using_agent/README.md)** - Building custom tools and integrations

## 📚 Additional Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Callback API Reference](https://google.github.io/adk-docs/api-reference/python/)
- [Best Practices Guide](https://google.github.io/adk-docs/best-practices/) 