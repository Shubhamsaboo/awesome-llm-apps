# 🧩 FigureOut Crash Course

A hands-on tutorial series for learning [FigureOut](https://github.com/balajeekalyan/figureout) — a lightweight, modular multi-LLM orchestrator with automatic role classification and MCP tool calling.

## 📚 What is FigureOut?

FigureOut is a framework for building LLM workflows without framework bloat. It:

- **Classifies** incoming queries and dispatches them to the right specialist role automatically
- **Supports 6 LLM providers**: OpenAI, Google Gemini, Anthropic Claude, Meta (Llama), Mistral, and Groq — swap with one parameter
- **Returns structured JSON** responses validated against a schema you define per role
- **Integrates MCP tools** via FastMCP — tools are called automatically based on the query

### Key Features:
- **Automatic Role Classification**: No manual routing logic required
- **Multi-Provider**: One codebase, any LLM backend
- **Structured JSON Output**: Predictable, schema-validated responses
- **MCP Tool Calling**: Native FastMCP integration
- **Multi-Role Queries**: Up to N roles can handle a single query in parallel
- **Debug Panel**: See which role was selected, tools called, and token usage

## 🎯 Learning Path

### 📚 Tutorials

1. **[1_starter_agent](./1_starter_agent/README.md)** — Your first FigureOut agent
   - Basic agent creation with a single role
   - Running a query and reading the response

2. **[2_multi_provider_agent](./2_multi_provider_agent/README.md)** — Swap LLM providers
   - Using OpenAI, Claude, and Gemini with the same agent
   - Understanding the `llm` and `llm_version` parameters

3. **[3_structured_output_agent](./3_structured_output_agent/README.md)** — Schema-validated responses
   - Defining JSON schemas per role
   - Building a multi-field structured output agent

4. **[4_tool_using_agent](./4_tool_using_agent/README.md)** — MCP tool calling with FastMCP
   - Defining tools with `@mcp.tool()`
   - Attaching an MCP server to FigureOut
   - Automatic tool dispatch based on query

5. **[5_role_classification](./5_role_classification/README.md)** — Multi-role routing
   - Defining multiple specialist roles
   - How FigureOut classifies and routes queries
   - Using guidelines to steer classification

6. **[6_multi_role_queries](./6_multi_role_queries/README.md)** — Parallel multi-role handling
   - Handling queries that span multiple domains
   - Using `max_roles` to enable parallel role execution

7. **[7_caching](./7_caching/README.md)** — In-memory query caching
   - How FigureOut caches query-response pairs
   - Cache hits: zero tokens, near-instant response
   - Observing cache behaviour via debug output

8. **[8_hallucination_control](./8_hallucination_control/README.md)** — Grounding the LLM to today's date
   - Why relative time expressions ("this weekend", "next Monday") cause hallucinations
   - How `inject_date` appends the current date to every system prompt
   - Side-by-side comparison: grounded vs ungrounded responses

## 🛠️ Prerequisites

- **Python 3.8+** installed
- API key for at least one supported LLM provider
- Basic understanding of Python and async/await

## 📦 Installation

Install only the provider you need:

```bash
pip install figureout[openai]   # OpenAI
pip install figureout[gemini]   # Google Gemini
pip install figureout[claude]   # Anthropic Claude
pip install figureout[all]      # All providers
```

## 📖 How to Use This Course

Each tutorial folder contains:

- **README.md**: Concept explanation and learning objectives
- **agent.py**: Minimal, working implementation
- **requirements.txt**: Dependencies for that tutorial

### Learning Approach:
1. Read the README to understand the concept
2. Examine the code before running it
3. Run the example and observe the output
4. Experiment by modifying roles, schemas, or queries
5. Move to the next tutorial when ready

## 🎯 Tutorial Features

Each tutorial includes:
- ✅ Clear concept explanation
- ✅ Minimal, working code examples
- ✅ Real-world use cases
- ✅ Step-by-step instructions
- ✅ Best practices and tips

## 📚 Additional Resources

- [FigureOut GitHub Repository](https://github.com/balajeekalyan/figureout)
- [FastMCP Documentation](https://gofastmcp.com/)
- [FigureOut Demo App](https://github.com/Shubhamsaboo/awesome-llm-apps/tree/main/advanced_ai_agents/multi_agent_apps/figureout_multi_llm_orchestrator)
