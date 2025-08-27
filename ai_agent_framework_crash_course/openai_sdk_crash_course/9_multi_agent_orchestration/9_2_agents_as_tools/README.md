# Agents as Tools

Demonstrates advanced orchestration patterns where specialized agents are used as function tools by orchestrator agents.

## 🎯 What This Demonstrates

- **@function_tool with Agents**: Converting agents to reusable tools
- **Content Creation Pipeline**: Research → Writing → Editing workflow
- **Custom Configuration**: Per-agent settings and parameters
- **Intelligent Orchestration**: LLM-driven workflow coordination

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
   
   # Test agent orchestration patterns
   asyncio.run(main())
   ```

## 💡 Key Concepts

- **Agent Tool Creation**: Using `@function_tool` with `Runner.run()`
- **Workflow Orchestration**: Coordinating multiple specialized agents
- **Custom Configuration**: Per-tool settings (max_turns, temperature)
- **Intelligent Coordination**: LLM decides when and how to use tools

## 🧪 Available Tools

### Research Tool
```python
@function_tool
async def research_tool(topic: str) -> str:
    result = await Runner.run(
        research_agent,
        input=f"Research this topic thoroughly: {topic}",
        max_turns=3
    )
    return str(result.final_output)
```

### Writing Tool
```python
@function_tool  
async def writing_tool(content: str, style: str = "professional") -> str:
    prompt = f"Write engaging {style} content based on this research: {content}"
    result = await Runner.run(writing_agent, input=prompt, max_turns=2)
    return str(result.final_output)
```

### Editing Tool
```python
@function_tool
async def editing_tool(content: str) -> str:
    result = await Runner.run(
        editing_agent,
        input=f"Edit and improve this content: {content}"
    )
    return str(result.final_output)
```

## 💻 Orchestration Patterns

### Basic Content Workflow
1. **Research**: Gather comprehensive information
2. **Write**: Create well-structured content
3. **Edit**: Polish and improve final output

### Advanced Orchestration
- **Conditional Logic**: Adapt workflow based on requirements
- **Style Selection**: Choose appropriate writing approach
- **Quality Control**: Multi-stage review and improvement

### Manual vs Automatic Comparison
- **Direct Agent Calls**: Manual orchestration
- **Tool-Based**: Automatic LLM coordination
- **Performance**: Compare execution patterns

## 🔗 Next Steps

- [Parallel Execution](../9_1_parallel_execution/README.md) - Concurrent agent patterns
- [Tutorial 10: Tracing & Observability](../../10_tracing_observability/README.md) - Monitoring workflows
