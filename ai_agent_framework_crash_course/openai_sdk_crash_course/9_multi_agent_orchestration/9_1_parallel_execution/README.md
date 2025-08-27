# Parallel Execution

Demonstrates running multiple agents simultaneously using `asyncio.gather()` for improved performance and quality through diversity.

## 🎯 What This Demonstrates

- **Parallel Agent Execution**: Running multiple agents simultaneously
- **Quality Selection**: Choosing the best result from multiple attempts
- **Translation Orchestration**: Multiple language approaches
- **Content Generation Diversity**: Different writing styles in parallel

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
   
   # Test parallel execution patterns
   asyncio.run(main())
   ```

## 💡 Key Concepts

- **asyncio.gather()**: Running multiple agents concurrently
- **ItemHelpers**: Extracting text outputs from results
- **Quality Assessment**: Using picker agents to select best results
- **Trace Grouping**: Organizing parallel workflows in single traces

## 🧪 Available Examples

### Parallel Translation with Quality Selection
```python
with trace("Parallel translation"):
    res_1, res_2, res_3 = await asyncio.gather(
        Runner.run(spanish_agent, msg),
        Runner.run(spanish_agent, msg),
        Runner.run(spanish_agent, msg),
    )
    
    best_translation = await Runner.run(
        translation_picker,
        f"Input: {msg}\n\nTranslations:\n{translations}"
    )
```

### Multi-Style Translation
- **Formal Spanish**: Using 'usted' forms
- **Casual Spanish**: Using 'tú' forms  
- **Regional Spanish**: Mexican expressions

### Content Generation Diversity
- **Creative Writing**: Vivid imagery and storytelling
- **Informative Writing**: Clear, factual content
- **Persuasive Writing**: Compelling, action-oriented

## 💻 Parallel Patterns

### Quality Through Repetition
- Run same agent multiple times
- Compare results for consistency
- Select highest quality output

### Quality Through Specialization
- Different agents for different approaches
- Specialized expertise areas
- Diverse perspective synthesis

### Performance Optimization
- Concurrent execution vs sequential
- Reduced total response time
- Better resource utilization

## 🔗 Next Steps

- [Agents as Tools](../9_2_agents_as_tools/README.md) - Agent orchestration patterns
- [Tutorial 10: Tracing & Observability](../../10_tracing_observability/README.md) - Monitoring workflows
