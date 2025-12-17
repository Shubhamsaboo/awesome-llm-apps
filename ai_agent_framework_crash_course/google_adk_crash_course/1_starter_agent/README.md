# 🎯 Tutorial 1: Your First ADK Agent

Welcome to your first step in the Google ADK journey! This tutorial introduces you to the fundamental concept of creating a simple AI agent using Google's Agent Development Kit.

## 🎯 What You'll Learn

- **Basic Agent Creation**: How to create your first ADK agent
- **ADK Workflow**: Understanding the agent lifecycle
- **Simple Text Processing**: Basic input/output handling
- **Agent Configuration**: Essential parameters and settings

## 🧠 Core Concept: What is an ADK Agent?

An ADK agent is a **programmable AI assistant** that can:
- Process user inputs (text, images, etc.)
- Use AI models (like Gemini) to understand and respond
- Perform specific tasks based on your instructions
- Return structured or unstructured responses

Think of it as creating a **smart function** that uses AI to handle complex tasks.

## 🔧 Key Components

### 1. **LlmAgent Class**
The main building block for creating AI agents in ADK:
```python
from google.adk.agents import LlmAgent
```

### 2. **Essential Parameters**
- `name`: Unique identifier for your agent
- `model`: The AI model to use (e.g., "gemini-3-flash-preview")
- `description`: What your agent does
- `instruction`: How your agent should behave

### 3. **Basic Workflow**
1. **Input**: User sends a message
2. **Processing**: Agent uses AI model to understand and respond
3. **Output**: Agent returns a response

## 🚀 Tutorial Overview

In this tutorial, we'll create a **Creative Writing Agent** that:
- Helps users develop story ideas and characters
- Provides writing prompts and inspiration
- Assists with plot structure and pacing
- Demonstrates basic ADK functionality

## 📁 Project Structure

```
1_starter_agent/
├── README.md              # This file - concept explanation
├── requirements.txt       # Dependencies
└── creative_writing_agent/ # Agent implementation
    ├── __init__.py       # Makes it a Python package
    └── agent.py          # Main agent code
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to create a basic ADK agent
- ✅ Essential agent parameters and their purpose
- ✅ How to run and test your agent
- ✅ Basic ADK workflow and lifecycle

## 🚀 Getting Started

1. **Set up your environment**:
   ```bash
   # Make sure you have your Google AI API key
   # Get your API key from: https://aistudio.google.com/
   ```

2. **Install dependencies**:
   ```bash
   # Install required packages
   pip install -r requirements.txt
   ```

3. **Run the creative writing agent**:
   ```bash
   # Start the ADK web interface
   adk web
   
   # In the web interface, select: creative_writing_agent
   ```

4. **Test your agent**:
   - Try asking for story ideas: "I want to write a story about a magical forest"
   - Get character help: "Help me create a protagonist for my sci-fi story"
   - Request writing prompts: "Give me a creative writing prompt"
   - Ask for plot advice: "How can I structure my story's climax?"

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 2: Model agnostic Agent](../2_model_agnostic_agent/README.md)** - create agents that work with different AI models
- **[Tutorial 3: Structured Output Agent](../3_structured_output_agent/README.md)** - Learn to create type-safe, structured responses
- **[Tutorial 4: Tool Using Agent](../4_tool_using_agent/README.md)** - Add custom tools and functions to your agent

## 💡 Pro Tips

- **Start Simple**: Begin with basic functionality and add complexity gradually
- **Test Often**: Use the ADK web interface to test your agents
- **Read Instructions**: Clear instructions lead to better agent behavior
- **Experiment**: Try different models and parameters to see the differences