# 🎯 Tutorial 1: Your First OpenAI Agent

Welcome to your first step in the OpenAI Agents SDK journey! This tutorial introduces you to the fundamental concept of creating a simple AI agent using OpenAI's Agents SDK.

## 🎯 What You'll Learn

- **Basic Agent Creation**: How to create your first OpenAI agent
- **OpenAI SDK Workflow**: Understanding the agent lifecycle
- **Simple Text Processing**: Basic input/output handling
- **Agent Configuration**: Essential parameters and settings

## 🧠 Core Concept: What is an OpenAI Agent?

An OpenAI agent is a **programmable AI assistant** that can:
- Process user inputs (text, voice, etc.)
- Use AI models (like GPT-4o) to understand and respond
- Perform specific tasks based on your instructions
- Return structured or unstructured responses

Think of it as creating a **smart function** that uses AI to handle complex tasks.

## 🔧 Key Components

### 1. **Agent Class**
The main building block for creating AI agents in OpenAI SDK:
```python
from agents import Agent
```

### 2. **Essential Parameters**
- `name`: Unique identifier for your agent
- `instructions`: How your agent should behave
- `model`: The AI model to use (defaults to "gpt-4o")

### 3. **Basic Workflow**
1. **Input**: User sends a message
2. **Processing**: Agent uses AI model to understand and respond
3. **Output**: Agent returns a response

## 🚀 Tutorial Overview

This tutorial includes **two focused agent examples**:

### **1. Personal Assistant Agent** (`personal_assistant_agent/`)
- Basic agent creation and configuration
- Simple instructions and role definition
- Core Agent class usage

### **2. Execution Demo Agent** (`execution_demo_agent/`)  
- Demonstrates different execution methods
- Sync, async, and streaming patterns
- Runner class usage examples

## 📁 Project Structure

```
1_starter_agent/
├── README.md                    # This file - concept explanation
├── requirements.txt             # Dependencies
├── personal_assistant_agent/    # Basic agent creation
│   ├── __init__.py
│   └── agent.py                # Simple agent definition (20 lines)
├── execution_demo_agent/        # Execution methods demonstration
│   ├── __init__.py
│   └── agent.py                # Sync, async, streaming examples
├── app.py                      # Streamlit web interface (optional)
└── env.example                 # Environment variables template
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to create a basic OpenAI agent
- ✅ Essential agent parameters and their purpose
- ✅ How to run agents synchronously and asynchronously
- ✅ Basic OpenAI SDK workflow and lifecycle
- ✅ How to use streaming responses

## 🚀 Getting Started

1. **Set up your environment**:
   ```bash
   # Make sure you have your OpenAI API key
   # Get your API key from: https://platform.openai.com/api-keys
   ```

2. **Install OpenAI Agents SDK**:
   ```bash
   pip install openai-agents
   ```

3. **Install dependencies**:
   ```bash
   # Install required packages
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=sk-your_openai_key_here
   ```

4. **Test the agent**:
   ```bash
   # Run the agent directly
   python agent.py
   
   # Or run the Streamlit web interface
   streamlit run app.py
   ```

6. **Try different execution methods**:
   - Test synchronous execution: "What's the weather like today?"
   - Test asynchronous execution: "Tell me a story about AI"
   - Test streaming responses: "Explain machine learning in detail"

## 🧪 Sample Prompts to Try

- **General Questions**: "What's the capital of France?"
- **Creative Tasks**: "Write a short poem about technology"
- **Problem Solving**: "How can I improve my productivity?"
- **Explanations**: "Explain quantum computing in simple terms"

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 2: Structured Output Agent](../2_structured_output_agent/README.md)** - Learn to create type-safe, structured responses
- **[Tutorial 3: Tool Using Agent](../3_tool_using_agent/README.md)** - Add custom tools and functions to your agent
- **[Tutorial 4: Runner Execution Methods](../4_runner_execution/README.md)** - Master different execution patterns

## 💡 Pro Tips

- **Start Simple**: Begin with basic functionality and add complexity gradually
- **Test Often**: Try different prompts to understand agent behavior
- **Read Instructions**: Clear instructions lead to better agent behavior
- **Experiment**: Try different execution methods to see the differences

## 🚨 Troubleshooting

- **API Key Issues**: Make sure your `.env` file contains a valid `OPENAI_API_KEY`
- **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **Rate Limits**: If you hit rate limits, wait a moment before trying again
