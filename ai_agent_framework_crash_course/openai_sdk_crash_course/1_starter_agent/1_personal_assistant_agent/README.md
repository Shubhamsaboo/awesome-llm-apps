# Personal Assistant Agent

A basic personal assistant agent demonstrating the fundamental concepts of agent creation with the OpenAI Agents SDK.

## 🎯 What This Demonstrates

- **Basic Agent Definition**: Creating a simple agent with name and instructions
- **Model Configuration**: Using the default GPT-4o model
- **Simple Instructions**: Basic conversational capabilities

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

2. **Run the agent**:
   ```python
   from agents import Runner
   from agent import root_agent
   
   result = Runner.run_sync(root_agent, "Hello, introduce yourself!")
   print(result.final_output)
   ```

## 💡 Key Concepts

- **Agent Definition**: The `Agent()` class with basic parameters
- **Instructions**: Natural language instructions that guide agent behavior
- **Model Selection**: Default model usage (gpt-4o)

## 🔗 Next Steps

This agent demonstrates the absolute basics. For more advanced features, see:
- [Execution Demo Agent](../execution_demo_agent/README.md) - Different execution methods
- [Tutorial 2: Structured Output](../../2_structured_output_agent/README.md) - Pydantic schema outputs
- [Tutorial 3: Tool Using Agent](../../3_tool_using_agent/README.md) - Adding tools and functions
