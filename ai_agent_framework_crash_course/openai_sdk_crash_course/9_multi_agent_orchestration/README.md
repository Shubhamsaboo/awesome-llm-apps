# 🎼 Tutorial 9: Multi-Agent Orchestration

Master complex multi-agent workflows! This tutorial teaches you how to coordinate multiple agents using parallel execution, agents-as-tools patterns, and advanced orchestration techniques for building sophisticated AI systems.

## 🎯 What You'll Learn

- **Parallel Execution**: Running multiple agents simultaneously with `asyncio.gather()`
- **Agents as Tools**: Using agents as function tools for complex orchestration
- **Workflow Coordination**: Sequential and parallel agent processing patterns
- **Result Synthesis**: Combining outputs from multiple agents intelligently

## 🧠 Core Concept: What Is Multi-Agent Orchestration?

Multi-agent orchestration enables **coordinated AI workflows** where multiple specialized agents work together to solve complex problems. Think of orchestration as a **conductor leading an orchestra** where:

- Different agents have specialized roles and expertise
- Agents can work in parallel or sequence based on workflow needs
- Results from multiple agents are synthesized intelligently
- Complex tasks are broken down across multiple AI capabilities

```
┌─────────────────────────────────────────────────────────────-┐
│                MULTI-AGENT ORCHESTRATION                     │
├─────────────────────────────────────────────────────────────-┤
│                                                              │
│  COMPLEX TASK                                                │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────┐    1. TASK DECOMPOSITION                    │
│  │ORCHESTRATOR │                                             │
│  │   AGENT     │    2. AGENT COORDINATION                    │
│  └─────────────┘                                             │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              PARALLEL EXECUTION                         │ │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │ │ |
│  │  │RESEARCH │  │WRITING  │  │ANALYSIS │  │REVIEW   │   │ │ |
│  │  │ AGENT   │  │ AGENT   │  │ AGENT   │  │ AGENT   │   │ │ |
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │ │ |
│  └─────────────────────────────────────────────────────────┘ │
│       │              │              │              │         │
│       ▼              ▼              ▼              ▼         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              RESULT SYNTHESIS                           │ │
│  │        • Combine outputs intelligently                  │ │
│  │        • Quality assessment and selection               │ │
│  │        • Final coordinated response                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────-┘
```

## 🚀 Tutorial Overview

This tutorial demonstrates **three key orchestration patterns**:

### **1. Parallel Agent Execution** (`parallel_execution.py`)
- Running multiple agents simultaneously with `asyncio.gather()`
- Quality assessment and best result selection
- Translation example with multiple attempts

### **2. Agents as Tools Orchestration** (`agents_as_tools.py`)
- Using specialized agents as function tools
- Content creation workflow with research and writing agents
- Custom agent tool configuration and coordination

### **3. Complex Workflow Orchestration** (`complex_orchestration.py`)
- Multi-stage workflows combining parallel and sequential execution
- Content pipeline with research, writing, review, and optimization
- Advanced result synthesis and quality control

## 📁 Project Structure

```
9_multi_agent_orchestration/
├── README.md                    # This file - concept explanation
├── requirements.txt             # Dependencies
├── parallel_execution.py        # Parallel agent patterns (45 lines)
├── agents_as_tools.py           # Agents as tools orchestration (55 lines)
├── complex_orchestration.py     # Advanced workflow patterns (70 lines)
├── app.py                      # Streamlit orchestration demo (optional)
└── env.example                 # Environment variables template
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to run multiple agents in parallel for improved performance
- ✅ Using agents as function tools for complex orchestration
- ✅ Combining sequential and parallel execution patterns
- ✅ Synthesizing results from multiple agents intelligently
- ✅ When to use different orchestration patterns for various use cases

## 🚀 Getting Started

1. **Install OpenAI Agents SDK**:
   ```bash
   pip install openai-agents
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Test parallel execution**:
   ```bash
   python parallel_execution.py
   ```

4. **Try agents as tools**:
   ```bash
   python agents_as_tools.py
   ```

5. **Explore complex workflows**:
   ```bash
   python complex_orchestration.py
   ```

## 🧪 Sample Use Cases

### Parallel Execution
- Multiple translation attempts with quality selection
- Content generation with diversity and choice
- Research from multiple perspectives simultaneously

### Agents as Tools
- Content creation: research → writing → editing pipeline
- Analysis workflows: data processing → insights → recommendations
- Customer service: triage → specialist → quality assurance

### Complex Orchestration
- Multi-stage content production with feedback loops
- Research and development workflows with validation
- Educational content creation with multiple review stages

## 🔧 Key Orchestration Patterns

### 1. **Parallel Execution with Quality Selection**
```python
import asyncio
from agents import Agent, Runner, trace

# Run multiple agents in parallel
with trace("Parallel translation"):
    results = await asyncio.gather(
        Runner.run(translator_agent, message),
        Runner.run(translator_agent, message),
        Runner.run(translator_agent, message)
    )
    
    # Select best result
    best = await Runner.run(selector_agent, combined_results)
```

### 2. **Agents as Function Tools**
```python
from agents import Agent, function_tool

@function_tool
async def research_tool(topic: str) -> str:
    result = await Runner.run(research_agent, f"Research: {topic}")
    return str(result.final_output)

orchestrator = Agent(
    name="Content Orchestrator",
    tools=[research_tool, writing_tool]
)
```

### 3. **Sequential + Parallel Hybrid**
```python
# Sequential stages with parallel execution within stages
with trace("Content Creation Pipeline"):
    # Stage 1: Parallel research
    research_results = await asyncio.gather(
        research_agent_1.run(topic),
        research_agent_2.run(topic)
    )
    
    # Stage 2: Sequential writing
    content = await writing_agent.run(combined_research)
    
    # Stage 3: Parallel review
    reviews = await asyncio.gather(
        quality_agent.run(content),
        style_agent.run(content)
    )
```

## 💡 Orchestration Design Best Practices

1. **Task Decomposition**: Break complex tasks into agent-sized pieces
2. **Parallel Optimization**: Use parallel execution where agents are independent
3. **Quality Control**: Include review and selection mechanisms
4. **Error Handling**: Plan for agent failures and provide fallbacks
5. **Result Synthesis**: Design intelligent combination of multiple outputs

## 🚨 Important Notes

- **Tracing Integration**: Use `trace()` to group multi-agent workflows
- **Resource Management**: Consider API rate limits with parallel execution
- **Quality vs Speed**: Balance parallelization with result quality
- **Error Propagation**: Handle failures gracefully in complex workflows

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 10: Tracing & Observability](../10_tracing_observability/README.md)** - Monitoring complex workflows
- **[Tutorial 11: Production Patterns](../11_voice/README.md)** - Real-world deployment strategies

## 🚨 Troubleshooting

- **Performance Issues**: Check for unnecessary sequential execution
- **Quality Problems**: Improve result synthesis and selection logic
- **Rate Limiting**: Implement backoff and retry for parallel calls
- **Memory Usage**: Monitor resource consumption with many parallel agents

## 💡 Pro Tips

- **Start Simple**: Begin with basic parallel execution, add complexity gradually
- **Measure Performance**: Compare parallel vs sequential execution times
- **Quality Metrics**: Develop criteria for selecting best results from multiple agents
- **Workflow Visualization**: Use tracing to understand complex execution flows
- **Agent Specialization**: Design agents with clear, focused responsibilities
