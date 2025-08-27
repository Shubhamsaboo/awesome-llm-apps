# Conversation Management

Demonstrates manual conversation threading with `to_input_list()` and automatic management with Sessions.

## 🎯 What This Demonstrates

- **Manual Threading**: Using `result.to_input_list()` for conversation history
- **Automatic Sessions**: Using `SQLiteSession` for memory management
- **Conversation Context**: Maintaining state across multiple turns
- **Thread Management**: Different approaches to conversation flow

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
   from agent import manual_conversation_example, session_conversation_example
   
   # Test manual conversation management
   asyncio.run(manual_conversation_example())
   ```

## 💡 Key Concepts

- **to_input_list()**: Manual conversation history management
- **SQLiteSession**: Automatic conversation persistence
- **Context Preservation**: Maintaining conversation state
- **Session Storage**: In-memory vs persistent storage

## 🔗 Next Steps

- [Execution Methods](../4_1_execution_methods/README.md) - Basic execution patterns
- [Streaming Events](../4_4_streaming_events/README.md) - Real-time processing
