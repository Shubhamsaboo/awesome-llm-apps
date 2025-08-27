# 🔍 Tutorial 8: Tracing & Observability

Master monitoring and debugging with built-in tracing! This tutorial teaches you how to use the OpenAI Agents SDK's comprehensive tracing system to visualize, debug, and monitor your agent workflows during development and production.

## 🎯 What You'll Learn

- **Built-in Tracing**: Automatic capture of LLM generations, tool calls, handoffs
- **Traces & Spans**: Understanding workflow structure and execution flow
- **Custom Tracing**: Creating custom traces and spans for complex workflows
- **Production Monitoring**: Debugging and performance optimization

## 🧠 Core Concept: What Is Tracing?

Tracing provides **comprehensive workflow monitoring** that automatically captures every event during agent execution:

- **LLM Generations**: Model calls, inputs, outputs, and performance
- **Tool Calls**: Function executions, parameters, and results  
- **Handoffs**: Agent-to-agent delegations and context transfer
- **Guardrails**: Input/output validation events
- **Custom Events**: Your own monitoring points

```
┌─────────────────────────────────────────────────────────────┐
│                    TRACING ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  AGENT WORKFLOW                                             │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    AUTOMATIC CAPTURE                       │
│  │    TRACE    │◀─────────────────────────────────────────┐ │
│  │ (Workflow)  │                                          │ │
│  └─────────────┘                                          │ │
│       │                                                   │ │
│       ▼                                                   │ │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │ │
│  │    SPAN     │    │    SPAN     │    │    SPAN     │    │ │
│  │ (LLM Call)  │    │ (Tool Call) │    │ (Handoff)   │    │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    │ │
│       │                    │                    │         │ │
│       ▼                    ▼                    ▼         │ │
│  ┌─────────────────────────────────────────────────────┐  │ │
│  │         OPENAI TRACES DASHBOARD                     │  │ │
│  │    • Execution Visualization                        │  │ │
│  │    • Performance Metrics                            │__| │ 
│  │    • Debug Information                              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Tutorial Overview

This tutorial demonstrates **three key tracing patterns**:

### **1. Default Tracing** (`default_tracing.py`)
- Built-in automatic tracing (enabled by default)
- Understanding traces and spans structure
- Basic workflow monitoring

### **2. Custom Tracing** (`custom_tracing.py`)
- Creating custom traces for multi-step workflows
- Adding custom spans for monitoring points
- Grouping multiple agent runs in single trace

### **3. Advanced Observability** (`advanced_observability.py`)
- Sensitive data handling and configuration
- Custom trace processors for external systems
- Production monitoring patterns

## 📁 Project Structure

```
8_tracing_observability/
├── README.md                    # This file - concept explanation
├── requirements.txt             # Dependencies  
├── default_tracing.py           # Built-in tracing basics (35 lines)
├── custom_tracing.py            # Custom traces and spans (45 lines)
├── advanced_observability.py    # Production tracing patterns (40 lines)
├── app.py                      # Streamlit tracing dashboard (optional)
└── env.example                 # Environment variables template
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How built-in tracing captures agent workflow events
- ✅ Difference between traces (workflows) and spans (operations)
- ✅ Creating custom traces for complex multi-step workflows
- ✅ Monitoring and debugging agent performance in production
- ✅ Integrating with external observability systems

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

3. **Test default tracing**:
   ```bash
   python default_tracing.py
   ```

4. **Try custom tracing**:
   ```bash
   python custom_tracing.py
   ```

5. **Explore advanced patterns**:
   ```bash
   python advanced_observability.py
   ```

## 🧪 Sample Use Cases

### Default Tracing
- Monitor basic agent workflows automatically
- Debug tool call failures and LLM generation issues
- Track performance metrics for optimization

### Custom Tracing
- Group related agent runs in complex workflows
- Add custom monitoring points in business logic
- Create hierarchical span structures for debugging

### Advanced Observability
- Configure sensitive data handling for compliance
- Export traces to external monitoring systems
- Set up production alerting and dashboards

## 🔧 Key Tracing Patterns

### 1. **Default Tracing (Automatic)**
```python
from agents import Agent, Runner

agent = Agent(name="Assistant")
# Tracing happens automatically - no setup required!
result = await Runner.run(agent, "Hello")
# View traces at: https://platform.openai.com/traces
```

### 2. **Custom Trace Creation**
```python
from agents import Agent, Runner, trace

with trace("Multi-step Workflow") as my_trace:
    result1 = await Runner.run(agent, "Step 1")
    result2 = await Runner.run(agent, "Step 2")
    # Both runs are part of the same trace
```

### 3. **Custom Spans**
```python
from agents import custom_span

with custom_span("Data Processing") as span:
    # Your custom logic here
    data = process_data()
    span.add_event("Processing complete", {"records": len(data)})
```

## 💡 Tracing Design Best Practices

1. **Meaningful Names**: Use descriptive trace and span names
2. **Logical Grouping**: Group related operations in single traces  
3. **Custom Events**: Add key business events as custom spans
4. **Sensitive Data**: Configure data handling for compliance
5. **Performance Monitoring**: Track execution time and resource usage

## 🚨 Important Notes

- **Enabled by Default**: Tracing is automatically enabled
- **Zero Data Retention**: Tracing unavailable for ZDR policy organizations
- **Free Dashboard**: View traces at OpenAI Traces dashboard
- **Disable if Needed**: Set `OPENAI_AGENTS_DISABLE_TRACING=1` to disable

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 9: Handoffs & Delegation](../9_handoffs_delegation/README.md)** - Agent handoffs and task delegation
- **[Tutorial 10: Multi-Agent Orchestration](../10_multi_agent_orchestration/README.md)** - Complex multi-agent workflows
- **[Tutorial 11: Production Patterns](../11_production_patterns/README.md)** - Real-world deployment strategies

## 🚨 Troubleshooting

- **No Traces Visible**: Check OpenAI API key and internet connectivity
- **Missing Spans**: Ensure operations are within trace context
- **Performance Issues**: Configure sensitive data filtering
- **ZDR Policy**: Tracing unavailable - disable or use custom processors

## 💡 Pro Tips

- **Start Simple**: Use default tracing first, add custom traces as needed
- **Strategic Naming**: Use consistent naming conventions for traces/spans
- **Monitor Performance**: Track execution time trends over time
- **External Integration**: Consider custom processors for your monitoring stack
- **Development vs Production**: Different tracing strategies for each environment
