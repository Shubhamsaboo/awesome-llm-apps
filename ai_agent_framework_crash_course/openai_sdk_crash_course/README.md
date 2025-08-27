# 🚀 OpenAI Agents SDK Crash Course

A comprehensive tutorial series for learning OpenAI's Agents SDK from basics to advanced concepts. This crash course is designed to take you from zero to hero in building AI agents with the OpenAI Agents SDK.

## 📚 What is OpenAI Agents SDK?

OpenAI Agents SDK is a powerful framework for **developing and deploying AI agents**. It provides:

### Key Features:
- **Agent Orchestration**: Create and manage intelligent AI agents
- **Tool Integration**: Extend agents with custom and built-in tools
- **Structured Outputs**: Type-safe responses using Pydantic models
- **Multi-Agent Workflows**: Coordinate multiple agents with handoffs
- **Real-time Execution**: Sync, async, and streaming execution methods
- **Voice Integration**: Static, streaming, and realtime voice capabilities
- **Session Management**: Automatic conversation memory and history
- **Production Ready**: Built-in tracing, guardrails, and monitoring

## 🎯 Learning Path

This crash course covers the essential concepts of OpenAI Agents SDK through hands-on tutorials:

### 📚 **Tutorials**

#### **🌱 Foundation Layer**

1. **[1_starter_agent](./1_starter_agent/README.md)** - Your first OpenAI agent
   - Basic agent creation and configuration
   - Understanding different execution methods
   - Simple text processing and responses

2. **[2_structured_output_agent](./2_structured_output_agent/README.md)** - Type-safe responses
   - **Support Ticket Agent** - Convert complaints to structured tickets
   - **Product Review Agent** - Extract structured data from reviews
   - Pydantic models and validation

#### **🔧 Core Capabilities Layer**

3. **[3_tool_using_agent](./3_tool_using_agent/README.md)** - Agent tools & functions
   - Custom function tools with `@function_tool`
   - Built-in tools (WebSearch, CodeInterpreter, FileSearch)
   - Tool integration and execution patterns

4. **[4_running_agents](./4_running_agents/README.md)** - Running & execution mastery
   - The agent loop: LLM calls, tool execution, handoffs
   - Sync, async, and streaming execution methods  
   - Advanced streaming events and exception handling
   - Run configuration and conversation management

5. **[5_context_management](./5_context_management/README.md)** - State & context handling
   - Context passing between runs
   - State persistence and management
   - Conversation flow control

#### **🧠 Advanced Features Layer**

6. **[6_guardrails_validation](./6_guardrails_validation/README.md)** - Safety & validation
   - Input guardrails for user validation
   - Output guardrails for response filtering
   - Custom business rule validation

7. **[7_sessions](./7_sessions/README.md)** - Sessions & memory management
   - Automatic conversation history with SQLiteSession
   - Memory operations and conversation corrections
   - Multiple session management and organization

#### **🤝 Multi-Agent Layer**

8. **[8_handoffs_delegation](./8_handoffs_delegation/README.md)** - Agent handoffs & delegation
   - Agent-to-agent task delegation
   - Triage systems and smart routing
   - Advanced handoff configuration with callbacks

9. **[9_multi_agent_orchestration](./9_multi_agent_orchestration/README.md)** - Complex workflows
   - Parallel agent execution with `asyncio.gather()`
   - Agents as tools orchestration patterns
   - Multi-stage workflow coordination

#### **🔍 Production Layer**

10. **[10_tracing_observability](./10_tracing_observability/README.md)** - Monitoring & debugging
    - Built-in tracing and execution visualization
    - Custom traces and spans for complex workflows
    - Performance monitoring and optimization

#### **🎙️ Voice & Advanced Features**

11. **[11_voice](./11_voice/README.md)** - Voice agents & real-time conversation
    - Static voice processing (turn-based interaction)
    - Streaming voice processing (real-time conversation)
    - Realtime voice agents (ultra-low latency with WebSocket)
    - Speech-to-text, text-to-speech, and voice pipelines

## 🛠️ Prerequisites

Before starting this crash course, ensure you have:

- **Python 3.8+** installed (Python 3.9+ required for voice features)
- **OpenAI API Key** from [OpenAI Platform](https://platform.openai.com/api-keys)
- Basic understanding of Python and APIs
- Familiarity with async/await concepts (helpful but not required)
- **For voice tutorials**: Microphone and speakers/headphones

## 📖 How to Use This Course

Each tutorial follows a consistent structure:

- **README.md**: Concept explanation and learning objectives
- **Python files**: Contains the agent implementations and examples
- **Interactive interfaces**: Streamlit web apps for hands-on testing
- **Submodules**: Organized examples for different concepts
- **requirements.txt**: Dependencies for the tutorial
- **env.example**: Environment variable template

### Learning Approach:
1. **Read the README** to understand the concept
2. **Examine the code** to see the implementation
3. **Run the examples** to see agents in action
4. **Experiment** by modifying the code
5. **Use interactive interfaces** for hands-on testing
6. **Try voice features** (tutorial 11) with your microphone
7. **Move to the next tutorial** when ready

## 🎯 Tutorial Features

Each tutorial includes:
- ✅ **Clear concept explanation**
- ✅ **Minimal, working code examples**
- ✅ **Real-world use cases**
- ✅ **Step-by-step instructions**
- ✅ **Interactive web interfaces**
- ✅ **Best practices and tips**

## 🚀 Quick Start

1. **Clone the repository** and navigate to this directory
2. **Choose a tutorial** from the list above
3. **Follow the README** instructions for that tutorial
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Set up environment**: Copy `env.example` to `.env` and add your API key
6. **Run the examples** and start learning!

## 🔧 Environment Setup

Each tutorial requires an OpenAI API key. Create a `.env` file in each tutorial directory:

```bash
OPENAI_API_KEY=sk-your_openai_key_here
```

Get your API key from: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

## 💡 Learning Tips

- **Start Sequential**: Follow tutorials in order for best learning experience
- **Experiment Freely**: Modify code and see what happens
- **Use Web Interfaces**: Interactive apps make learning more engaging
- **Read Error Messages**: They often contain helpful guidance
- **Join Community**: Engage with other learners and share experiences

## 🚨 Common Issues

### API Key Problems
- Make sure your `.env` file is in the tutorial directory
- Verify your API key is valid and has sufficient credits
- Check for typos in the environment variable name

### Import Errors
- Ensure you've installed requirements: `pip install -r requirements.txt`
- Check that you're using Python 3.8 or higher
- Try creating a virtual environment if you have conflicts

### Rate Limiting
- OpenAI has rate limits based on your plan
- If you hit limits, wait a moment before trying again
- Consider upgrading your OpenAI plan for higher limits

## 📚 Additional Resources

- [OpenAI Agents SDK Documentation](https://openai.github.io/openai-agents-python/)
- [OpenAI Platform](https://platform.openai.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## 🤝 Contributing

Feel free to contribute improvements, bug fixes, or additional tutorials. Each tutorial should:
- Be self-contained and runnable
- Include clear documentation
- Follow the established structure
- Use minimal, understandable code

## 📊 Progress Tracking

Track your progress through the course:

- [ ] **Tutorial 1**: Basic agent creation ✨
- [ ] **Tutorial 2**: Structured outputs with Pydantic
- [ ] **Tutorial 3**: Tool integration and custom functions
- [ ] **Tutorial 4**: Execution methods mastery
- [ ] **Tutorial 5**: Context and state management
- [ ] **Tutorial 6**: Guardrails and validation
- [ ] **Tutorial 7**: Sessions and memory management
- [ ] **Tutorial 8**: Agent handoffs and delegation
- [ ] **Tutorial 9**: Multi-agent orchestration
- [ ] **Tutorial 10**: Tracing and observability
- [ ] **Tutorial 11**: Voice agents and real-time conversation 🎯

Happy learning! 🚀
