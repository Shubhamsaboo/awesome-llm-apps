# 🧠 Tutorial 5: Memory Agents - Sessions, State & Events

Welcome to the memory and session management tutorial! This tutorial teaches you how to create AI agents that can remember conversations, maintain context, and provide personalized experiences across multiple interactions.

## 🎯 What You'll Learn

- **Session Management**: How agents maintain conversation context
- **State Persistence**: Storing and retrieving conversation data
- **Event Tracking**: Understanding conversation flow and history
- **Memory Types**: In-memory, database, and cloud-based memory solutions
- **Personalization**: Creating agents that remember user preferences

## 🧠 Core Concepts

### 1. **Sessions** - The Conversation Container

A **Session** is like a conversation thread that keeps track of all interactions between a user and an agent.

```
┌─────────────────────────────────────────────────────────────┐
│                    SESSION LIFECYCLE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   CREATE    │───▶│   ACTIVE    │───▶│   CLOSED    │     │
│  │  SESSION    │    │ CONVERSATION│    │   SESSION   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  User ID    │    │   Events    │    │   Memory    │     │
│  │  Created    │    │   State     │    │   Stored    │     │
│  │  Timestamp  │    │   History   │    │   Archived  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

**Example**: When you start chatting with a travel agent, a session is created. All your questions about flights, hotels, and preferences are stored in that session.

### 2. **State** - The Current Context

**State** represents the current context and data that the agent needs to remember during a conversation.

```
┌─────────────────────────────────────────────────────────────┐
│                        SESSION STATE                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   USER STATE    │  │  AGENT STATE    │  │  APP STATE  │ │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────┤ │
│  │ • User ID       │  │ • Agent Name    │  │ • Session ID│ │
│  │ • Preferences   │  │ • Current Task  │  │ • Timestamp │ │
│  │ • History       │  │ • Tools Used    │  │ • Status    │ │
│  │ • Context       │  │ • Memory        │  │ • Metadata  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Example**: A travel agent's state might include:
- User's preferred destinations
- Budget constraints
- Travel dates
- Previous recommendations

### 3. **Events** - The Conversation History

**Events** are individual interactions that make up the conversation history.

```
┌─────────────────────────────────────────────────────────────┐
│                      EVENT FLOW                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   USER      │───▶│   AGENT     │───▶│   RESPONSE  │     │
│  │  MESSAGE    │    │  PROCESSING │    │  GENERATED  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Event Type: │    │ Event Type: │    │ Event Type: │     │
│  │ user_input  │    │ processing  │    │ response    │     │
│  │ Timestamp   │    │ Timestamp   │    │ Timestamp   │     │
│  │ Content     │    │ Duration    │    │ Content     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

**Example Event Sequence**:
1. **User Event**: "I want to go to Paris"
2. **Agent Event**: Processing request, checking preferences
3. **Response Event**: "Great! I see you prefer luxury hotels. Here are some options..."

### 4. **Session Runtime Flow**

```
┌─────────────────────────────────────────────────────────────┐
│                    SESSION RUNTIME FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. SESSION CREATION                                        │
│  ┌─────────────┐                                            │
│  │ User starts │───▶ Create Session with User ID            │
│  │ conversation│    Initialize State & Memory               │
│  └─────────────┘                                            │
│                                                             │
│  2. CONVERSATION LOOP                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   User      │───▶│   Agent     │───▶│   Update    │     │
│  │  Input      │    │  Processes  │    │   State     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Record      │    │ Use Context │    │ Store       │     │
│  │ Event       │    │ & Memory    │    │ Response    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│  3. SESSION CLOSURE                                         │
│  ┌─────────────┐                                            │
│  │ User ends   │───▶ Save Final State                       │
│  │ conversation│    Archive Session                         │
│  └─────────────┘    Store in Memory Bank                    │
└─────────────────────────────────────────────────────────────┘
```

## 📚 Tutorial Structure

This tutorial is divided into three progressive levels:

1. **[5_1_in_memory_conversation](./5_1_in_memory_conversation/README.md)** - Basic session management
   - InMemorySessionService for temporary conversations
   - Simple state management
   - Event tracking basics

2. **[5_2_persistent_conversation](./5_2_persistent_conversation/README.md)** - Database persistence
   - DatabaseSessionService with SQLite
   - Persistent state storage
   - Conversation history across sessions

## 🛠️ Prerequisites

Before starting this tutorial, ensure you have:

- **Python 3.11+** installed
- **Google AI API Key** from [Google AI Studio](https://aistudio.google.com/)
- **SQLite** (usually comes with Python)
- Basic understanding of databases (for tutorial 5_2)

## 📖 How to Use This Course

Each tutorial follows a consistent structure:

- **README.md**: Concept explanation and learning objectives
- **agent.py**: Contains the agent implementation
- **requirements.txt**: Dependencies for the tutorial
- **app.py**: Streamlit web interface (where applicable)

### Learning Approach:
1. **Read the README** to understand the memory concept
2. **Examine the code** to see session management implementation
3. **Run the example** to see memory in action
4. **Experiment** by having multi-turn conversations
5. **Move to the next tutorial** when ready

## 🎯 Tutorial Features

Each tutorial includes:
- ✅ **Clear concept explanation**
- ✅ **Minimal, working code examples**
- ✅ **Real-world use cases**
- ✅ **Step-by-step instructions**
- ✅ **Memory persistence demonstration**

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **Advanced Agent Patterns** - Multi-agent systems
- **Custom Memory Implementations** - Building your own memory services
- **Production Deployment** - Scaling memory agents

## 💡 Pro Tips

- **Start Simple**: Begin with in-memory sessions before moving to persistence
- **Test Conversations**: Have multi-turn conversations to see memory in action
- **Monitor State**: Use the ADK web interface to inspect session state
- **Plan Memory Strategy**: Choose the right memory service for your use case 