# 🔗 Third-party Tools

Third-party tools allow you to integrate **existing tool ecosystems** from frameworks like LangChain, CrewAI, and others. This dramatically expands your agent's capabilities by leveraging battle-tested tools from the broader AI community.

## 🎯 What You'll Learn

- **LangChain Integration**: Using LangChain's extensive tool library
- **CrewAI Tools**: Leveraging CrewAI's specialized agent tools
- **Tool Adapters**: How ADK wraps external tools
- **Ecosystem Benefits**: Advantages of using established tool libraries
- **Best Practices**: When and how to use third-party tools

## 🧠 Core Concept: Third-party Tools

Third-party tools are **external libraries wrapped for ADK**:
- **LangChain Tools**: Web scraping, document loaders, APIs
- **CrewAI Tools**: Web scraping, file operations, specialized functions
- **Custom Integrations**: Any external service or library
- **Wrapper Classes**: ADK provides adapters for seamless integration

### Key Advantages
- ✅ **Rich Ecosystem**: Access to hundreds of pre-built tools
- ✅ **Battle-tested**: Proven tools used by thousands of developers
- ✅ **Community Support**: Active communities and documentation
- ✅ **Rapid Development**: Don't reinvent the wheel

## 🔧 Available Third-party Integrations

### 1. **LangChain Tools**
- **Purpose**: Comprehensive tool ecosystem
- **Examples**: Web scraping, file operations, APIs
- **Benefits**: Mature, well-documented tools

### 2. **CrewAI Tools**
- **Purpose**: Specialized agent tools
- **Examples**: Web scraping, file operations, content processing
- **Benefits**: Optimized for agent workflows

### 3. **Custom Integrations**
- **Purpose**: Any external service or library
- **Examples**: Database connectors, API clients
- **Benefits**: Unlimited extensibility

## 🚀 Tutorial Examples

This sub-example includes two practical implementations:

### 📍 **LangChain Agent**
**Location**: `./langchain_agent/`
- **Web Search**: DuckDuckGo search integration for real-time information
- **Wikipedia Integration**: Access to encyclopedic knowledge and articles
- **Research Capabilities**: Comprehensive research combining multiple sources
- **Content Analysis**: Information synthesis and source citation

### 📍 **CrewAI Agent**
**Location**: `./crewai_agent/`
- **Website Operations**: Website content search and scraping capabilities
- **File System Tools**: Directory search and file reading operations
- **Content Extraction**: Advanced web scraping and data extraction
- **Document Processing**: Local file analysis and content processing

## 📁 Project Structure

```
4_3_thirdparty_tools/
├── README.md                    # This file - third-party tools guide
├── requirements.txt             # Dependencies for third-party tools
├── ../env.example              # Environment variables template (shared)
├── langchain_agent/            # LangChain integration
│   ├── __init__.py
│   └── agent.py               # Agent with LangChain tools
└── crewai_agent/               # CrewAI integration
    ├── __init__.py
    └── agent.py               # Agent with CrewAI tools
```

## 🎯 Learning Objectives

By the end of this sub-example, you'll understand:
- ✅ How to integrate LangChain tools with ADK
- ✅ How to use CrewAI tools in ADK agents
- ✅ Best practices for third-party tool integration
- ✅ When to choose third-party vs custom tools
- ✅ How to handle tool compatibility issues

## 🔗 Getting Started

1. **Set up environment**:
   ```bash
   cd 4_3_thirdparty_tools
   
   # Copy the environment template
   cp ../env.example .env
   
   # Edit .env and add your Google AI API key
   # Get your API key from: https://aistudio.google.com/
   ```

2. **Install Dependencies**: Install required packages
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the agents**:
   ```bash
   # Start the ADK web interface
   adk web
   
   # In the web interface, select:
   # - langchain_agent: For web search and Wikipedia research
   # - crewai_agent: For website scraping and file operations
   ```

4. **Try the agents**:
   - **LangChain Agent**: "Search for latest AI news", "Tell me about machine learning"
   - **CrewAI Agent**: "Scrape content from example.com", "Search for Python files in current directory"

5. **Compare Approaches**: See the differences and benefits of each tool ecosystem

## 💡 Pro Tips

- **Choose Established Tools**: Use well-maintained libraries
- **Read Documentation**: Understand tool limitations and requirements
- **Handle Dependencies**: Manage external library versions carefully
- **Test Integration**: Verify tool compatibility with ADK
- **Monitor Performance**: Some tools may be slower than custom implementations

## 🔧 Integration Patterns

### 1. **LangChain Tool Wrapper**
```python
from google.adk.tools.langchain_tool import LangchainTool
from langchain_community.tools import DuckDuckGoSearchRun

# Wrap LangChain tool for ADK
search_tool = LangchainTool(DuckDuckGoSearchRun())
```

### 2. **CrewAI Tool Wrapper**
```python
from google.adk.tools.crewai_tool import CrewaiTool
from crewai_tools import ScrapeWebsiteTool, DirectorySearchTool, FileReadTool

# Basic tool - minimal configuration
scrape_tool = CrewaiTool(
    name="scrape_website",
    description="Scrape and extract content from websites",
    tool=ScrapeWebsiteTool(
        config=dict(
            llm=dict(
                provider="google",  # Use Google instead of default OpenAI
                config=dict(model="gemini-3-flash-preview"),
            ),
        )
    )
)

# Search tool - needs embeddings for semantic search
search_tool = CrewaiTool(
    name="website_search",
    description="Search for content within websites",
    tool=WebsiteSearchTool(
        config=dict(
            llm=dict(
                provider="google",
                config=dict(model="gemini-3-flash-preview"),
            ),
            embedder=dict(
                provider="google",
                config=dict(
                    model="gemini-embedding-001",
                    task_type="retrieval_document",
                ),
            ),
        )
    )
)
```

### 3. **Custom Integration Pattern**
```python
from google.adk.tools import FunctionTool
import external_library

def custom_integration(query: str) -> dict:
    """Integrate with external library."""
    result = external_library.process(query)
    return {"result": result, "status": "success"}

# Use as function tool
tool = FunctionTool(custom_integration)
```

## 🔧 Common Third-party Tools

### LangChain Tools
- **DuckDuckGoSearchRun**: Web search
- **WebBaseLoader**: Web scraping
- **WikipediaQueryRun**: Wikipedia search
- **PythonREPLTool**: Python code execution
- **ShellTool**: Shell command execution

### CrewAI Tools
- **ScrapeWebsiteTool**: Web scraping and content extraction
- **DirectorySearchTool**: File system search and exploration
- **FileReadTool**: File reading and content analysis

### Custom Integrations
- **Database connectors**: SQLAlchemy, MongoDB
- **API clients**: REST, GraphQL
- **File processors**: PDF, Excel, CSV
- **Cloud services**: AWS, GCP, Azure

## 🚨 Important Considerations

- **Dependencies**: Third-party tools add external dependencies
- **Compatibility**: Ensure tool versions work with ADK
- **Performance**: Some tools may be slower than custom implementations
- **Maintenance**: External tools may change or become deprecated
- **Security**: Validate external tool safety and permissions

### 🔧 **CrewAI Model Configuration**
⚠️ **Important**: CrewAI tools use OpenAI models by default. When using Google ADK, configure them to use Google models for consistency:

```python
# ❌ Default - Uses OpenAI models
tool = WebsiteSearchTool()

# ✅ Correct configuration - All tools need both LLM and embeddings
tool = ScrapeWebsiteTool(
    config=dict(
        llm=dict(
            provider="google",
            config=dict(model="gemini-3-flash-preview"),
        ),
        embedder=dict(
            provider="google",
            config=dict(
                model="gemini-embedding-001",
                task_type="retrieval_document",
            ),
        ),
    )
)

# ✅ Same configuration pattern for all tools
tool = DirectorySearchTool(
    config=dict(
        llm=dict(
            provider="google",
            config=dict(model="gemini-3-flash-preview"),
        ),
        embedder=dict(
            provider="google",
            config=dict(
                model="gemini-embedding-001",
                task_type="retrieval_document",
            ),
        ),
    )
)
```

**Key Points:**
- **LLM Config**: Always set `provider="google"` to avoid OpenAI defaults
- **Embeddings**: Required for all CrewAI tools to prevent OpenAI fallback
- **Available providers**: `google`, `openai`, `anthropic`, `ollama`, `llama2`, etc.

## 🔧 Common Use Cases

### Web and Research
- Web scraping and content extraction
- Website content analysis
- Document processing
- Content research and analysis

### File Operations
- File system search and exploration
- File reading and content analysis
- Directory navigation
- Local file processing

### Development Tools
- Code execution
- Documentation search
- Version control operations
- Testing utilities

### Cloud and Services
- Cloud storage operations
- Email and messaging
- Authentication services
- Monitoring and logging

## 📊 Comparison: Third-party vs Custom vs Built-in

| Aspect | Third-party | Custom | Built-in |
|--------|-------------|--------|----------|
| **Development Time** | Fast | Slow | Instant |
| **Flexibility** | Medium | High | Low |
| **Performance** | Variable | High | Highest |
| **Maintenance** | External | Internal | None |
| **Features** | Rich | Tailored | Basic |
| **Dependencies** | Many | Few | None |
