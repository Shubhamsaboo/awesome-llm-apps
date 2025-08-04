# 🎯 Tutorial 4: Tool Using Agent

Welcome to the world of tools! This tutorial teaches you how to create agents that can use **different types of tools** to perform specific tasks. This is where your agents become truly powerful and capable of real-world actions.

## 🎯 What You'll Learn

- **Built-in Tools**: Using Google ADK's pre-built capabilities
- **Function Tools**: Creating custom Python functions as tools
- **Third-party Tools**: Integrating with LangChain, CrewAI, and other frameworks
- **MCP Tools**: Integration with Model Context Protocol

## 🧠 Core Concept: Tools in ADK

Tools are **functions that your agent can call** to perform specific tasks. Think of them as the agent's "hands" - they allow the agent to:
- Search the web and access real-time information
- Execute code and perform calculations
- Call external APIs and services
- Access databases and file systems
- Interact with other AI frameworks

## 🔧 Types of Tools in ADK

### 1. **Built-in Tools**
Google ADK provides powerful pre-built tools:
- **Search Tool**: Web search capabilities
- **Code Execution Tool**: Run Python code safely
- **RAG Tools**: Retrieval-augmented generation
- **Cloud Tools**: Google Cloud integrations

*Note: Built-in tools work only with Gemini models*

### 2. **Function Tools**
Custom Python functions you create:
- Mathematical calculations
- Data processing
- API calls
- File operations
- Business logic

### 3. **Third-party Tools**
Integration with other frameworks:
- **LangChain Tools**: Web scraping, document loaders, etc.
- **CrewAI Tools**: Specialized agent tools
- **Custom Integrations**: Any external service

### 4. **MCP Tools**
Integration with Model Context Protocol:
- **External MCP Servers**: Connect to existing MCP servers
- **Custom MCP Servers**: Create your own MCP server
- **Protocol Communication**: SSE and Streamable HTTP support

## 🚀 Tutorial Structure

This tutorial contains **four comprehensive examples**:

### 📍 **Example 1: Built-in Tools**
**Location**: `./4_1_builtin_tools/`
- Learn to use Google ADK's pre-built tools
- Implement web search capabilities
- Explore code execution tools

### 📍 **Example 2: Function Tools**
**Location**: `./4_2_function_tools/`
- Create custom Python functions as tools
- Build mathematical and utility tools
- Implement API integration tools

### 📍 **Example 3: Third-party Tools**
**Location**: `./4_3_thirdparty_tools/`
- Integrate LangChain tools
- Use CrewAI specialized tools
- Create custom integrations

### 📍 **Example 4: MCP Tools**
**Location**: `./4_4_mcp_tools/`
- Connect to Model Context Protocol servers
- Use filesystem and Wikipedia MCP tools
- Create custom MCP servers

## 📁 Project Structure

```
4_tool_using_agent/
├── README.md                    # This tutorial overview
├── 4_1_builtin_tools/          # Built-in tools examples
├── 4_2_function_tools/         # Function tools examples  
├── 4_3_thirdparty_tools/       # Third-party tools examples
└── 4_4_mcp_tools/              # MCP tools examples
```

Each example directory follows the standard structure:
- **Python file**: Contains the agent implementation and Streamlit app
- **README.md**: Setup and usage documentation
- **requirements.txt**: Dependencies list

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to use Google ADK's built-in tools effectively
- ✅ How to create and integrate custom function tools
- ✅ How to leverage third-party tool ecosystems
- ✅ How to connect to and create MCP servers
- ✅ When to use each type of tool
- ✅ Best practices for tool design and integration

## 💡 Pro Tips

- **Start with Built-ins**: Use Google's tools when possible - they're optimized
- **Clear Descriptions**: Write detailed docstrings for your tools
- **Error Handling**: Always handle potential errors in your tools
- **Tool Selection**: Help the AI understand when to use each tool
- **Testing**: Test each tool independently before combining

## 🎯 Real-World Applications

Tool-using agents are essential for:
- **Information Retrieval**: Search engines, knowledge bases
- **Data Analysis**: Processing and analyzing data
- **API Integration**: Connecting to external services
- **Automation**: Performing repetitive tasks
- **Decision Making**: Using external data for decisions

## 🚨 Important Notes

- **Model Compatibility**: Built-in tools only work with Gemini models
- **Tool Mixing**: Cannot mix built-in and custom tools in same agent
- **Performance**: Built-in tools are optimized for speed
- **Security**: Custom tools require proper validation
