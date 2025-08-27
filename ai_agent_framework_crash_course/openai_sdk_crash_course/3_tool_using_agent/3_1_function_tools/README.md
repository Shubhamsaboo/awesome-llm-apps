# Function Tools Agent

Demonstrates custom function tools creation using the `@function_tool` decorator.

## 🎯 What This Demonstrates

- **Custom Function Tools**: Creating tools with `@function_tool` decorator
- **Tool Descriptions**: Providing clear docstrings for LLM understanding
- **Parameter Handling**: Type hints and default parameters
- **Error Handling**: Graceful tool failure management

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
   
   result = Runner.run_sync(root_agent, "What time is it in New York?")
   print(result.final_output)
   ```

## 💡 Key Concepts

- **@function_tool Decorator**: Converting Python functions to agent tools
- **Tool Docstrings**: How LLM understands when to use tools
- **Type Hints**: Parameter validation and documentation
- **Tool Registration**: Adding tools to agent configuration

## 🧪 Available Tools

### `get_current_time(timezone: str = "UTC")`
- Returns current time in specified timezone
- Handles timezone validation and error cases

### `greet_user(name: str)`
- Simple greeting tool demonstrating basic tool usage
- Shows parameter passing from LLM to tool

## 🔗 Next Steps

- [Built-in Tools](../3_2_builtin_tools/README.md) - Using WebSearch, CodeInterpreter
- [Agents as Tools](../3_3_agents_as_tools/README.md) - Advanced agent orchestration
