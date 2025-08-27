# Multi Sessions

Demonstrates managing multiple concurrent sessions for different users, contexts, and conversation types.

## 🎯 What This Demonstrates

- **Multi-User Sessions**: Separate conversations for different users
- **Context-Based Sessions**: Different session types (support, sales, etc.)
- **Shared Sessions**: Multiple agents using the same conversation
- **Session Organization**: Naming strategies and management patterns

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
   from agent import multi_user_sessions, context_based_sessions
   
   # Test multi-user sessions
   asyncio.run(multi_user_sessions())
   
   # Test context-based sessions
   asyncio.run(context_based_sessions())
   ```

## 💡 Key Concepts

- **Session Isolation**: Keeping conversations separate
- **User-Based Sessions**: Individual user conversation histories
- **Context Switching**: Different conversation types and purposes
- **Agent Handoffs**: Sharing sessions between specialized agents

## 🧪 Available Patterns

### Multi-User Sessions
- Separate sessions for Alice and Bob
- Isolated conversation histories
- User-specific context preservation

### Context-Based Sessions
- Support ticket conversations
- Sales inquiry conversations
- Feature-specific sessions

### Shared Session Agents
- Customer handoff scenarios
- Multiple agents, single conversation
- Context preservation across agent switches

### Session Organization
- User-based naming: `user_123`
- Feature-based naming: `chat_feature_user_123`
- Thread-based naming: `thread_abc123`
- Timestamp-based naming: `user_123_20241215`

## 🔗 Next Steps

- [Basic Sessions](../7_1_basic_sessions/README.md) - Session fundamentals
- [Memory Operations](../7_2_memory_operations/README.md) - Advanced memory manipulation
- [Tutorial 8: Handoffs & Delegation](../../8_handoffs_delegation/README.md) - Agent handoffs
