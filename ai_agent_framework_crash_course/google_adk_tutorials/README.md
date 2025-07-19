# 🚀 Google ADK Crash Course

A comprehensive tutorial series for learning Google's Agent Development Kit (ADK) from basics to advanced concepts. This crash course is designed to take you from zero to hero in building AI agents with Google ADK.

## 📚 What is Google ADK?

Google ADK (Agent Development Kit) is a flexible and modular framework for **developing and deploying AI agents**. It's optimized for Gemini and the Google ecosystem but is **model-agnostic** and **deployment-agnostic**, making it compatible with other frameworks.

### Key Features:
- **Flexible Orchestration**: Define workflows using workflow agents or LLM-driven dynamic routing
- **Multi-Agent Architecture**: Build modular applications with multiple specialized agents
- **Rich Tool Ecosystem**: Use pre-built tools, create custom functions, or integrate 3rd-party libraries
- **Deployment Ready**: Containerize and deploy agents anywhere
- **Built-in Evaluation**: Assess agent performance systematically
- **Safety and Security**: Built-in patterns for trustworthy agents

## 🎯 Learning Path

This crash course covers the essential concepts of Google ADK through hands-on tutorials:

### 📚 **Tutorials**

1. **[1_starter_agent](./1_starter_agent/README.md)** - Your first ADK agent
   - Basic agent creation
   - Understanding the ADK workflow
   - Simple text processing

2. **[2_model_agnostic_agent](./2_model_agnostic_agent/README.md)** - Model-agnostic agent development
   - Google Gemini models (AI Studio & Vertex AI)
   - Anthropic Claude integration
   - Local models with Ollama
   - LiteLLM integration for multiple providers

3. **[3_structured_output_agent](./3_structured_output_agent/README.md)** - Type-safe responses
   - Pydantic schemas
   - Structured data validation
   - Business logic implementation

4. **[4_tool_using_agent](./4_tool_using_agent/README.md)** - Agent with tools
   - Built-in tools (Search, Code Execution)
   - Function tools (Custom Python functions)
   - Third-party tools (LangChain, CrewAI)
   - MCP tools integration

5. **More tutorials coming soon!**

## 🛠️ Prerequisites

Before starting this crash course, ensure you have:

- **Python 3.8+** installed
- **Google AI API Key** from [Google AI Studio](https://aistudio.google.com/)
- Basic understanding of Python and APIs

## 📖 How to Use This Course

Each tutorial follows a consistent structure:

- **README.md**: Concept explanation and learning objectives
- **Python file**: Contains the agent implementation and Streamlit app
- **requirements.txt**: Dependencies for the tutorial

### Learning Approach:
1. **Read the README** to understand the concept
2. **Examine the code** to see the implementation
3. **Run the example** to see it in action
4. **Experiment** by modifying the code
5. **Move to the next tutorial** when ready

## 🎯 Tutorial Features

Each tutorial includes:
- ✅ **Clear concept explanation**
- ✅ **Minimal, working code examples**
- ✅ **Real-world use cases**
- ✅ **Step-by-step instructions**
- ✅ **Best practices and tips**

## 📚 Additional Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Google AI Studio](https://aistudio.google.com/)
- [Gemini API Reference](https://ai.google.dev/docs)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 🤝 Contributing

Feel free to contribute improvements, bug fixes, or additional tutorials. Each tutorial should:
- Be self-contained and runnable
- Include clear documentation
- Follow the established structure
- Use minimal, understandable code
