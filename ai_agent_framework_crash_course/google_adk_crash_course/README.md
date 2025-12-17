# 🚀 Google ADK Crash Course

A comprehensive tutorial series for learning Google's Agent Development Kit (ADK) from basics to advanced concepts. This crash course is designed to take you from zero to hero in building AI agents with Google ADK.

> **📌 Note: This course has been updated for the new Gemini 3 Flash model!**  
> All tutorials in this course use the **Gemini 3 Flash** model (e.g., `gemini-3-flash-preview`). 

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
   - **[2.1 OpenAI Agent](./2_model_agnostic_agent/2_1_openai_adk_agent/README.md)** - OpenAI integration
   - **[2.2 Anthropic Claude Agent](./2_model_agnostic_agent/2_2_anthropic_adk_agent/README.md)** - Claude integration

3. **[3_structured_output_agent](./3_structured_output_agent/README.md)** - Type-safe responses
   - **[3.1 Customer Support Ticket Agent](./3_structured_output_agent/3_1_customer_support_ticket_agent/README.md)** - Pydantic schemas
   - **[3.2 Email Agent](./3_structured_output_agent/3_2_email_agent/README.md)** - Structured data validation

4. **[4_tool_using_agent](./4_tool_using_agent/README.md)** - Agent with tools
   - **[4.1 Built-in Tools](./4_tool_using_agent/4_1_builtin_tools/README.md)** - Search, Code Execution
   - **[4.2 Function Tools](./4_tool_using_agent/4_2_function_tools/README.md)** - Custom Python functions
   - **[4.3 Third-party Tools](./4_tool_using_agent/4_3_thirdparty_tools/README.md)** - LangChain, CrewAI
   - **[4.4 MCP Tools](./4_tool_using_agent/4_4_mcp_tools/README.md)** - MCP tools integration

5. **[5_memory_agent](./5_memory_agent/README.md)** - Memory and session management
   - **[5.1 In-Memory Conversation](./5_memory_agent/5_1_in_memory_conversation/README.md)** - Basic session management
   - **[5.2 Persistent Conversation](./5_memory_agent/5_2_persistent_conversation/README.md)** - Database storage with SQLite

6. **[6_callbacks](./6_callbacks/README.md)** - Callback patterns and monitoring
   - **[6.1 Agent Lifecycle Callbacks](./6_callbacks/6_1_agent_lifecycle_callbacks/README.md)** - Monitor agent creation and cleanup
   - **[6.2 LLM Interaction Callbacks](./6_callbacks/6_2_llm_interaction_callbacks/README.md)** - Track model requests and responses
   - **[6.3 Tool Execution Callbacks](./6_callbacks/6_3_tool_execution_callbacks/README.md)** - Monitor tool calls and results

7. **[7_plugins](./7_plugins/README.md)** - Plugin system for cross-cutting concerns
   - Global callback management
   - Request/response modification
   - Error handling and logging
   - Usage analytics and monitoring

8. **[8_simple_multi_agent](./8_simple_multi_agent/README.md)** - Multi-agent orchestration
   - **[8.1 Multi-Agent Researcher](./8_simple_multi_agent/multi_agent_researcher/README.md)** - Research pipeline with specialized agents
   - Coordinator agent with sub-agents
   - Sequential workflow: Research → Summarize → Critique
   - Web search integration and comprehensive analysis

9. **[9_multi_agent_patterns](./9_multi_agent_patterns/README.md)** - Multi-Agent Patterns
   - **[9.1 Sequential Agent](./9_multi_agent_patterns/9_1_sequential_agent/README.md)** — Deterministic pipeline of sub-agents (e.g., Draft → Critique → Improve)
   - **[9.2 Loop Agent](./9_multi_agent_patterns/9_2_loop_agent/README.md)** — Iterative refinement with an explicit stop condition (max iterations or an exit tool). A tweet crafting loop demonstrates the pattern. 
   - **[9.3 Parallel Agent](./9_multi_agent_patterns/9_3_parallel_agent/README.md)** — Execute multiple sub-agents concurrently and merge results.

## 🛠️ Prerequisites

Before starting this crash course, ensure you have:

- **Python 3.11+** installed
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
