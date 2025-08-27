# 🤝 Tutorial 8: Handoffs & Delegation

Master agent-to-agent task delegation! This tutorial teaches you how to use the OpenAI Agents SDK's handoff system to create specialized agents that can intelligently delegate tasks to each other, building powerful multi-agent workflows.

## 🎯 What You'll Learn

- **Agent Handoffs**: Delegating tasks between specialized agents
- **Handoff Configuration**: Custom tool names, descriptions, and callbacks
- **Input Filtering**: Controlling what context gets passed between agents
- **Triage Patterns**: Building intelligent routing and delegation systems

## 🧠 Core Concept: What Are Handoffs?

Handoffs enable **agent specialization and delegation** where agents can transfer tasks to other agents with specific expertise. Think of handoffs as a **smart routing system** that:

- Creates specialized agents for different domains (support, billing, technical)
- Allows intelligent task delegation based on user needs
- Maintains conversation context across agent transfers
- Provides custom routing logic and input filtering

```
┌─────────────────────────────────────────────────────────────┐
│                    HANDOFF WORKFLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  USER REQUEST                                               │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    1. ANALYZE REQUEST                      │
│  │   TRIAGE    │                                            │
│  │   AGENT     │    2. DECIDE DELEGATION                    │
│  └─────────────┘                                            │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    3. CALL HANDOFF TOOL                    │
│  │   HANDOFF   │    "transfer_to_billing_agent"             │
│  │    TOOL     │                                            │
│  └─────────────┘                                            │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    4. TRANSFER CONTEXT                     │
│  │  BILLING    │    (with optional filtering)               │
│  │   AGENT     │                                            │
│  └─────────────┘    5. PROCESS REQUEST                      │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    6. RETURN RESPONSE                      │
│  │  RESPONSE   │                                            │
│  │   TO USER   │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Tutorial Overview

This tutorial demonstrates **key handoff patterns**:

### **1. Basic Handoffs** (`basic_handoffs.py`)
- Simple agent-to-agent delegation
- Customer support triage example
- Automatic tool creation from handoff definitions

### **2. Advanced Handoffs** (`advanced_handoffs.py`)
- Custom handoff configuration with callbacks
- Input filtering and context management
- Handoff with structured input data

## 📁 Project Structure

```
8_handoffs_delegation/
├── README.md                # This file - concept explanation
├── requirements.txt         # Dependencies
├── basic_handoffs.py        # Simple agent handoffs (40 lines)
├── advanced_handoffs.py     # Advanced handoff patterns (50 lines)
├── app.py                  # Streamlit handoff demo (optional)
└── env.example             # Environment variables template
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to create agent handoffs for task delegation
- ✅ Configuring handoff tools with custom names and descriptions
- ✅ Using input filters to control context transfer
- ✅ Building intelligent triage systems with multiple agents
- ✅ When and how to use handoffs vs direct agent orchestration

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

3. **Test basic handoffs**:
   ```bash
   python basic_handoffs.py
   ```

4. **Try advanced patterns**:
   ```bash
   python advanced_handoffs.py
   ```

## 🔧 Key Handoff Patterns

### 1. **Basic Handoff Setup**
```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing Agent")
support_agent = Agent(name="Support Agent")

triage_agent = Agent(
    name="Triage Agent",
    handoffs=[billing_agent, support_agent]  # Creates tools automatically
)
```

### 2. **Custom Handoff Configuration**
```python
from agents import Agent, handoff

def on_handoff_callback(ctx):
    print(f"Handoff to {ctx.agent.name} initiated")

custom_handoff = handoff(
    agent=billing_agent,
    tool_name_override="escalate_to_billing",
    tool_description_override="Transfer complex billing issues",
    on_handoff=on_handoff_callback
)
```

### 3. **Input Filtering**
```python
from agents.extensions import handoff_filters

filtered_handoff = handoff(
    agent=support_agent,
    input_filter=handoff_filters.remove_all_tools  # Clean context
)
```

## 💡 Handoff Design Best Practices

1. **Clear Specialization**: Each agent should have a distinct area of expertise
2. **Intelligent Routing**: Use descriptive tool names and instructions for LLM
3. **Context Management**: Consider what context should transfer between agents
4. **Callback Integration**: Use callbacks for logging, metrics, and workflows
5. **Input Validation**: Structure inputs when passing specific data

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 9: Multi-Agent Orchestration](../9_multi_agent_orchestration/README.md)** - Complex multi-agent workflows with parallel execution
- **[Tutorial 10: Tracing & Observability](../10_tracing_observability/README.md)** - Monitoring and debugging
- **[Tutorial 11: Production Patterns](../11_production_patterns/README.md)** - Real-world deployment strategies

## 💡 Pro Tips

- **Start Simple**: Begin with basic handoffs, add complexity gradually
- **Clear Instructions**: Make agent roles and handoff triggers obvious
- **Test Routing**: Verify LLM chooses correct agents for different scenarios
- **Monitor Handoffs**: Use callbacks and tracing to track delegation patterns
- **Context Strategy**: Plan what information should transfer between agents