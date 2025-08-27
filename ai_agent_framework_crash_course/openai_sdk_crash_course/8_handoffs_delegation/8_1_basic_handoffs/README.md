# Basic Handoffs

Demonstrates fundamental agent-to-agent task delegation using the OpenAI Agents SDK handoff system.

## 🎯 What This Demonstrates

- **Agent Handoffs**: Simple task delegation between specialized agents
- **Automatic Tool Creation**: Handoffs automatically create transfer tools
- **Triage Patterns**: Intelligent routing based on request type
- **Specialized Agents**: Different agents for billing and technical support

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
   
   # Test basic handoffs
   asyncio.run(main())
   ```

## 💡 Key Concepts

- **Handoff Definition**: Adding agents to the `handoffs` parameter
- **Tool Generation**: Automatic creation of `transfer_to_*` tools
- **Agent Specialization**: Different expertise areas for different agents
- **Intelligent Routing**: LLM decides which agent to transfer to

## 🧪 Available Examples

### Billing Agent Handoff
- "I was charged twice for my subscription"
- "Can you help me get a refund?"
- "What are my payment options?"

### Technical Support Handoff
- "My app keeps crashing"
- "I can't upload photos"
- "The app won't load"

### No Handoff Needed
- "What are your customer service hours?"
- "How do I contact support?"
- "What services do you offer?"

## 💻 Agent Architecture

```python
# Specialized agents
billing_agent = Agent(name="Billing Agent", instructions="Handle billing issues")
technical_agent = Agent(name="Technical Support Agent", instructions="Handle technical issues")

# Triage agent with handoffs
triage_agent = Agent(
    name="Customer Service Triage Agent",
    handoffs=[billing_agent, technical_agent]  # Creates tools automatically
)
```

## 🔗 Next Steps

- [Advanced Handoffs](../8_2_advanced_handoffs/README.md) - Custom configuration and callbacks
- [Tutorial 9: Multi-Agent Orchestration](../../9_multi_agent_orchestration/README.md) - Complex workflows
