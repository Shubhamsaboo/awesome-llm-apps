# 🎯 Tutorial 7: Sessions & Memory Management

Master automatic conversation memory with Sessions! This tutorial teaches you how to use the OpenAI Agents SDK's built-in session memory to maintain conversation history across multiple agent runs without manual memory management.

## 🎯 What You'll Learn

- **Automatic Memory**: Sessions handle conversation history automatically
- **SQLite Sessions**: Persistent and in-memory conversation storage
- **Memory Operations**: Adding, retrieving, and managing conversation items
- **Session Management**: Multiple sessions and custom implementations

## 🧠 Core Concept: What Are Sessions?

Sessions provide **automatic conversation memory** that eliminates the need to manually handle `.to_input_list()` between turns. Think of sessions as a **smart conversation database** that:

- Automatically stores all conversation history
- Retrieves context before each agent run
- Maintains separate conversations for different session IDs
- Supports persistent storage across application restarts

```
┌─────────────────────────────────────────────────────────────┐
│                    SESSION WORKFLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  USER INPUT                                                 │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐    1. RETRIEVE HISTORY                     │
│  │   SESSION   │◀─────────────────────────────────────────┐ │
│  │   MEMORY    │                                          │ │
│  └─────────────┘    2. PREPEND TO INPUT                   │ │
│       │                                                   │ │
│       ▼                                                   │ │
│  ┌─────────────┐                                          │ │
│  │    AGENT    │    3. PROCESS WITH CONTEXT               │ │
│  │   RUNNER    │                                          │ │
│  └─────────────┘                                          │ │
│       │                                                   │ │
│       ▼                                                   │ │
│  ┌─────────────┐    4. STORE NEW ITEMS                    │ │
│  │   RESPONSE  │──────────────────────────────────────────┘ │
│  │  GENERATED  │                                            │
│  └─────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Tutorial Overview

This tutorial demonstrates **three key session patterns**:

### **1. Basic SQLite Sessions** (`basic_sessions.py`)
- In-memory and persistent session storage
- Automatic conversation history management
- Simple multi-turn conversations

### **2. Advanced Memory Operations** (`memory_operations.py`)
- Memory manipulation with `get_items()`, `add_items()`, `pop_item()`
- Conversation corrections and modifications
- Session management operations

### **3. Multiple Sessions** (`multi_sessions.py`)
- Managing different conversation contexts
- Session isolation and organization
- Custom session implementations

## 📁 Project Structure

```
7_sessions/
├── README.md                   # This file - concept explanation
├── requirements.txt            # Dependencies
├── streamlit_sessions_app.py   # Interactive Streamlit demo (recommended)
├── 7_1_basic_sessions/
│   ├── agent.py               # SQLite sessions basics
│   └── README.md              # Basic sessions documentation
├── 7_2_memory_operations/
│   ├── agent.py               # Advanced memory operations
│   └── README.md              # Memory operations documentation
├── 7_3_multi_sessions/
│   ├── agent.py               # Multiple session management
│   └── README.md              # Multi-sessions documentation
└── env.example                # Environment variables template
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to use SQLiteSession for automatic memory management
- ✅ Difference between in-memory and persistent sessions
- ✅ Advanced memory operations for conversation management
- ✅ Managing multiple concurrent sessions
- ✅ When to use sessions vs manual conversation management

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

3. **Launch interactive demo (recommended)**:
   ```bash
   streamlit run streamlit_sessions_app.py
   ```

   OR run individual examples:

4. **Test basic sessions**:
   ```bash
   python 7_1_basic_sessions/agent.py
   ```

5. **Try memory operations**:
   ```bash
   python 7_2_memory_operations/agent.py
   ```

6. **Test multiple sessions**:
   ```bash
   python 7_3_multi_sessions/agent.py
   ```

## 🧪 Sample Use Cases

### Basic Sessions
- "What city is the Golden Gate Bridge in?" → "What state is it in?"
- "My name is Alice" → "What's my name?"
- "I work as a developer" → "What do I do for work?"

### Memory Operations
- Correcting previous messages with `pop_item()`
- Clearing conversation history with `clear_session()`
- Adding custom conversation items

### Multiple Sessions
- Different users: `user_123`, `user_456`
- Different contexts: `support_ticket_789`, `sales_inquiry_101`
- Different applications: `chatbot_session`, `assistant_session`

## 🔧 Key Session Patterns

### 1. **Basic Session Usage**
```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant", instructions="Reply concisely.")
session = SQLiteSession("conversation_123")

result = await Runner.run(agent, "Hello", session=session)
```

### 2. **Persistent vs In-Memory**
```python
# In-memory (lost when process ends)
session = SQLiteSession("user_123")

# Persistent file-based
session = SQLiteSession("user_123", "conversations.db")
```

### 3. **Memory Operations**
```python
# Get conversation history
items = await session.get_items()

# Add custom items
await session.add_items([{"role": "user", "content": "Hello"}])

# Remove last item (for corrections)
last_item = await session.pop_item()

# Clear all history
await session.clear_session()
```

## 💡 Session Design Best Practices

1. **Meaningful Session IDs**: Use descriptive IDs like `user_12345` or `support_ticket_789`
2. **Persistent Storage**: Use file-based sessions for production applications
3. **Session Isolation**: Keep different conversation contexts in separate sessions
4. **Memory Management**: Use `pop_item()` for conversation corrections
5. **Cleanup**: Clear sessions when conversations should start fresh

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 8: Handoffs & Delegation](../8_handoffs_delegation/README.md)** - Agent handoffs and task delegation
- **[Tutorial 9: Multi-Agent Orchestration](../9_multi_agent_orchestration/README.md)** - Complex multi-agent workflows
- **[Tutorial 10: Production Patterns](../10_production_patterns/README.md)** - Real-world deployment strategies

## 🚨 Troubleshooting

- **Memory Not Persisting**: Ensure you're using file-based SQLiteSession with a database path
- **Session Conflicts**: Use unique session IDs for different conversation contexts
- **Performance Issues**: Consider implementing custom session backends for high-volume applications
- **Database Errors**: Check file permissions for SQLite database files

## 💡 Pro Tips

- **Start Simple**: Begin with in-memory sessions for development and testing
- **Plan Session Architecture**: Design your session ID strategy before building
- **Monitor Memory Usage**: Track conversation length and implement cleanup strategies
- **Test Session Persistence**: Verify that conversations survive application restarts
- **Consider Scaling**: Plan for custom session implementations in production systems
