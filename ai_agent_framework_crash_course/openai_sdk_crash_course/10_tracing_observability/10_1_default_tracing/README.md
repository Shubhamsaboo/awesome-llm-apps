# Default Tracing

Demonstrates the built-in automatic tracing system that captures all agent workflow events without any setup required.

## 🎯 What This Demonstrates

- **Automatic Tracing**: Built-in workflow monitoring (enabled by default)
- **Trace IDs**: Unique identifiers for each agent run
- **OpenAI Dashboard**: Free trace visualization platform
- **Tracing Configuration**: Enabling and disabling trace capture

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
   import asyncio
   from agent import main
   
   # Test default tracing (automatic)
   asyncio.run(main())
   ```

## 💡 Key Concepts

- **Zero Setup Required**: Tracing works automatically out of the box
- **Unique Run IDs**: Each `Runner.run()` gets a unique trace identifier
- **Automatic Capture**: LLM calls, tool executions, performance metrics
- **Free Dashboard**: View traces at platform.openai.com/traces

## 🧪 Automatic Capture

### What Gets Traced Automatically
- **LLM Generations**: Input prompts, model responses, token usage
- **Tool Calls**: Function executions, parameters, results
- **Handoffs**: Agent-to-agent delegations
- **Performance**: Execution time, latency metrics
- **Errors**: Exceptions and failure modes

### Trace Information
```python
result = await Runner.run(agent, "Hello")
print(f"Trace ID: {result.run_id}")
# Each run gets a unique identifier for dashboard lookup
```

### Separate Traces
- Each `Runner.run()` call = One trace
- Multiple runs = Multiple separate traces
- Independent workflow tracking

## 💻 Tracing Examples

### Basic Automatic Tracing
```python
# Tracing happens automatically - no setup required!
result = await Runner.run(agent, "Explain machine learning")
print(f"View trace: https://platform.openai.com/traces/{result.run_id}")
```

### Tracing Configuration
```python
# Disable tracing for specific runs
result = await Runner.run(
    agent,
    "Private conversation",
    run_config=RunConfig(tracing_disabled=True)
)
```

### Multiple Traces
```python
# Each run creates a separate trace
result1 = await Runner.run(agent, "Question 1")  # Trace 1
result2 = await Runner.run(agent, "Question 2")  # Trace 2
```

## 🔍 Dashboard Features

### OpenAI Traces Dashboard
- **Workflow Timeline**: Visual execution flow
- **Performance Metrics**: Response times, token usage
- **Error Tracking**: Exception details and stack traces
- **Content Inspection**: Input/output content review

### Free Access
- No additional setup required
- Accessible with OpenAI API key
- Real-time trace availability
- Historical trace retention

## 🔗 Next Steps

- [Custom Tracing](../10_2_custom_tracing/README.md) - Advanced tracing patterns
- [Tutorial 11: Production Patterns](../../11_production_patterns/README.md) - Real-world deployment
