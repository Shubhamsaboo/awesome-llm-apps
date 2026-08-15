# 🎯 Tutorial 6.3: Tool Execution Callbacks

## 🎯 What You'll Learn
- **Before Tool Callbacks**: Monitor when tools begin execution
- **After Tool Callbacks**: Track tool completion and results
- **Tool Context**: Understand how tool execution is monitored

## 🧠 Core Concept: Tool Execution Monitoring

Tool execution callbacks allow you to monitor when agents use tools, track their execution lifecycle, and analyze the results. This provides visibility into how agents interact with external systems and APIs.

### **Tool Execution Flow**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tool Call     │───▶│  Before Tool    │───▶│  Tool Execution │
│   (Agent)       │    │   Callback      │    │   (External)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  After Tool     │    │  Tool Result    │
                       │   Callback      │    │   (Agent)       │
                       └─────────────────┘    └─────────────────┘
```

### **Callback Execution Timeline**
```
Time → 0ms    5ms    10ms   15ms   20ms   25ms
       │      │      │      │      │      │
       ▼      ▼      ▼      ▼      ▼      ▼
    [Tool] [Before] [Exec] [After] [Result]
    Call   Callback Start  Callback Return
```

### **Use Cases**
- **Execution Monitoring**: Track when tools start and complete
- **Parameter Validation**: Check tool inputs before execution
- **Result Logging**: Record tool outputs and errors
- **Debugging**: Understand tool execution patterns
- **Analytics**: Monitor which tools are used most

## 🚀 Tutorial Overview

In this tutorial, we'll create an agent with tool execution callbacks that:
- Uses a simple calculator tool
- Monitors tool execution start and end
- Tracks tool parameters and results
- Provides detailed tool usage visibility

## 📁 Project Structure

```
6_3_tool_execution_callbacks/
├── README.md              # This file
├── requirements.txt       # Dependencies
├── agent.py              # Agent with tool callbacks
└── app.py                # Streamlit interface
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:

- ✅ **Before Tool Callbacks**: How to monitor tool execution start
- ✅ **After Tool Callbacks**: How to track tool completion
- ✅ **Tool Context**: How to access tool and agent information
- ✅ **FunctionTool**: How to properly register tools with callbacks
- ✅ **Callback Integration**: How to integrate callbacks with agents

## 🚀 Getting Started

### **Setup**
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set up environment**: Create `.env` with `GOOGLE_API_KEY=your_key`
3. **Run the app**: `streamlit run app.py`

### **Test the Agent**
```bash
# Run the Streamlit app
streamlit run app.py

# Try these test messages:
- "Calculate 15 + 27"
- "What is 100 divided by 4?"
- "Multiply 8 by 12"
```

## 🔧 Key Concepts

### **1. Before Tool Callback**
- **Trigger**: When tool execution begins
- **Parameters**: `tool`, `args`, `tool_context`
- **Use Cases**: Log tool usage, validate parameters, record start

### **2. After Tool Callback**
- **Trigger**: When tool execution completes
- **Parameters**: `tool`, `args`, `tool_context`, `tool_response`
- **Use Cases**: Log results, handle errors, provide feedback

### **3. Tool Context**
- **Agent Information**: Access `tool_context.agent_name`
- **State Management**: Use `tool_context.state` for data sharing
- **Tool Details**: Access tool information via `tool.name`

## 🔍 Testing Examples

### **Basic Tool Usage**
```
User: "Calculate 15 + 27"

🔧 Tool calculator_tool started
📝 Parameters: {'operation': 'add', 'a': 15.0, 'b': 27.0}
📋 Agent: tool_execution_demo_agent

✅ Tool calculator_tool completed
⏱️ Duration: 0.0012s
📄 Result: 15 + 27 = 42
```

### **Error Handling**
```
User: "What is 10 divided by 0?"

🔧 Tool calculator_tool started
📝 Parameters: {'operation': 'divide', 'a': 10.0, 'b': 0.0}
📋 Agent: tool_execution_demo_agent

✅ Tool calculator_tool completed
⏱️ Duration: 0.0008s
📄 Result: Error: Division by zero
```

## 🎯 What Each Metric Tells You

### **Before Tool Callback Output**
- **🔧 Tool Name**: Which tool is being executed
- **📝 Parameters**: Input parameters passed to the tool
- **📋 Agent**: Which agent is using the tool

### **After Tool Callback Output**
- **✅ Completion Status**: Tool execution completed successfully
- **⏱️ Duration**: How long the tool took to execute
- **📄 Result**: The output or result from the tool

## 🎯 Critical Implementation Notes

### **FunctionTool Requirement**
Tools must be wrapped with `FunctionTool` for callbacks to work:

```python
# ✅ Correct - Use FunctionTool
calculator_function_tool = FunctionTool(func=calculator_tool)
agent = LlmAgent(tools=[calculator_function_tool], ...)

# ❌ Incorrect - Raw function won't trigger callbacks
agent = LlmAgent(tools=[calculator_tool], ...)
```

### **Callback Signatures**
Use the correct parameter order for tool callbacks:

```python
# ✅ Correct signatures
def before_tool_callback(tool: BaseTool, args: dict, tool_context: ToolContext):
    pass

def after_tool_callback(tool: BaseTool, args: dict, tool_context: ToolContext, tool_response: any):
    pass
```

### **Event Loop Completion**
Don't break the event loop immediately after `is_final_response()`:

```python
# ✅ Do this - allows callbacks to complete
if event.is_final_response() and event.content:
    response_text = event.content.parts[0].text.strip()
    # Don't break - let the loop complete naturally
```

## 🎯 Advanced Patterns

### **Multiple Tools**
Register multiple tools with the same callbacks:

```python
def weather_tool(city: str) -> str:
    return f"Weather in {city}: Sunny, 25°C"

def calculator_tool(operation: str, a: float, b: float) -> str:
    # ... implementation

# Register multiple tools
weather_function_tool = FunctionTool(func=weather_tool)
calculator_function_tool = FunctionTool(func=calculator_tool)

agent = LlmAgent(
    name="multi_tool_agent",
    model="gemini-3-flash-preview",
    tools=[calculator_function_tool, weather_function_tool],
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback
)
```

### **Parameter Validation**
Implement validation in before_tool_callback:

```python
def before_tool_callback(tool: BaseTool, args: dict, tool_context: ToolContext):
    tool_name = tool.name
    
    # Validate calculator tool parameters
    if tool_name == "calculator_tool":
        if "operation" not in args:
            print("⚠️ Warning: Missing operation parameter")
        if "a" not in args or "b" not in args:
            print("⚠️ Warning: Missing numeric parameters")
    
    print(f"🔧 Tool {tool_name} started")
    print(f"📝 Parameters: {args}")
    return None
```

### **Result Modification**
Modify tool results in after_tool_callback:

```python
def after_tool_callback(tool: BaseTool, args: dict, tool_context: ToolContext, tool_response: any):
    tool_name = tool.name
    
    # Add context to calculator results
    if tool_name == "calculator_tool" and "result" in tool_response:
        operation = args.get("operation", "unknown")
        tool_response["context"] = f"Performed {operation} operation"
    
    print(f"✅ Tool {tool_name} completed")
    print(f"📄 Result: {tool_response}")
    return tool_response  # Return modified response
```

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:

- **[Advanced Tool Patterns](../../4_tool_using_agent/README.md)** - Complex tool architectures
- **[Custom Tool Development](../../4_tool_using_agent/README.md)** - Building custom tools
- **[Tool Integration](../../4_tool_using_agent/README.md)** - Integrating external APIs

## 📚 Additional Resources

- [Google ADK Tool Callbacks](https://google.github.io/adk-docs/callbacks/types-of-callbacks/#tool-execution-callbacks)
- [Tool Development Guide](https://google.github.io/adk-docs/tools/)
- [FunctionTool Documentation](https://google.github.io/adk-docs/tools/function-tools/) 