# 🧠 Tutorial 5.1: In-Memory Conversation Agent

Welcome to your first step into session management! This tutorial teaches you how to create an AI agent that can remember conversations within a single session using `InMemorySessionService`.

## 🎯 What You'll Learn

- **InMemorySessionService**: Basic session management for temporary conversations
- **Session Creation**: How to create and manage conversation sessions
- **State Management**: Storing and retrieving conversation context
- **Event Tracking**: Recording conversation history
- **Multi-turn Conversations**: Building agents that remember context

## 🧠 Core Concept: In-Memory Sessions

**InMemorySessionService** stores session data in your computer's RAM (memory). This means:
- ✅ **Fast access** - No database queries needed
- ✅ **Simple setup** - No external dependencies
- ❌ **Temporary storage** - Data is lost when the program stops
- ❌ **No persistence** - Can't remember across program restarts

Perfect for:
- Development and testing
- Temporary conversations
- Prototyping memory features
- Single-session applications

## 🔧 Key Components

### 1. **InMemorySessionService**
```python
from google.adk.sessions import InMemorySessionService
```

### 2. **Session Lifecycle**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CREATE    │───▶│   USE       │───▶│   CLOSE     │
│  SESSION    │    │  SESSION    │    │  SESSION    │
└─────────────┘    └─────────────┘    └─────────────┘
```

### 3. **Session Data Structure**
```python
{
    "session_id": "unique_session_id",
    "user_id": "user_identifier", 
    "state": {
        "conversation_history": [...],
        "user_preferences": {...},
        "current_context": "..."
    },
    "events": [
        {"type": "user_input", "content": "...", "timestamp": "..."},
        {"type": "agent_response", "content": "...", "timestamp": "..."}
    ]
}
```

## 🚀 Tutorial Overview

In this tutorial, we'll create a **Personal Assistant Agent** that:
- Remembers your name and preferences
- Tracks conversation history
- Provides personalized responses
- Demonstrates basic session management

## 📁 Project Structure

```
5_1_in_memory_conversation/
├── README.md              # This file - concept explanation
├── requirements.txt       # Dependencies
├── agent.py              # Main agent with session management
└── app.py                # Streamlit web interface
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to create and manage sessions
- ✅ How to store and retrieve conversation state
- ✅ How to track conversation events
- ✅ How to build multi-turn conversations
- ✅ Basic session lifecycle management

## 🚀 Getting Started

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up your environment**:
   ```bash
   # Create a .env file with your Google AI API key
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   ```

3. **Run the agent**:
   ```bash
   # Start the Streamlit app
   streamlit run app.py
   ```

4. **Test the memory**:
   - Tell the agent your name: "My name is John"
   - Ask about your preferences: "What do you know about me?"
   - Have a conversation and see how it remembers context

## 🔍 Code Walkthrough

### Key Session Management Code:

```python
# 1. Create session service
session_service = InMemorySessionService()

# 2. Create a new session
session = await session_service.create_session(
    app_name="personal_assistant",
    user_id="user123"
)

# 3. Update session state
await session_service.update_session_state(
    session_id=session.session_id,
    state={"user_name": "John", "preferences": ["travel", "music"]}
)

# 4. Add events to track conversation
await session_service.add_event(
    session_id=session.session_id,
    event_type="user_input",
    content="My name is John"
)
```

## 🎯 Testing Your Agent

Try these conversation flows to test memory:

### Flow 1: Personal Information
```
User: "My name is Alice"
Agent: "Nice to meet you, Alice! How can I help you today?"

User: "What's my name?"
Agent: "Your name is Alice! I remember you told me that."
```

### Flow 2: Preferences
```
User: "I love pizza and hiking"
Agent: "Great! I'll remember that you love pizza and hiking."

User: "What are my interests?"
Agent: "Based on our conversation, you love pizza and hiking!"
```

### Flow 3: Context Continuity
```
User: "I'm planning a trip"
Agent: "That sounds exciting! Since you mentioned hiking, would you like recommendations for hiking destinations?"

User: "Yes, where should I go?"
Agent: "Given your love for hiking, I'd recommend..."
```

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 5.2: Persistent Conversation](../5_2_persistent_conversation/README.md)** - Learn database-based session storage
- **[Tutorial 5.3: Cloud Memory](../5_3_cloud_memory/README.md)** - Explore cloud-based memory solutions

## 💡 Pro Tips

- **Test Multi-turn Conversations**: Have extended conversations to see memory in action
- **Monitor Session State**: Use the web interface to inspect what the agent remembers
- **Experiment with State**: Try storing different types of data in the session state
- **Understand Limitations**: Remember that in-memory sessions are temporary

## 🚨 Important Notes

- **Data Loss**: In-memory sessions are lost when you restart the application
- **Single Process**: Sessions only work within the same Python process
- **Memory Usage**: Large conversation histories will consume RAM
- **Development Only**: Use in-memory sessions for development, not production 