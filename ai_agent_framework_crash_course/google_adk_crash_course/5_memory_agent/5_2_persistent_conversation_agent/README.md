# 🗄️ Tutorial 5.2: Persistent Conversation Agent

Welcome to persistent session management! This tutorial teaches you how to create an AI agent that can remember conversations across multiple sessions using `DatabaseSessionService` with SQLite.

## 🎯 What You'll Learn

- **DatabaseSessionService**: Persistent session storage with SQLite
- **Cross-Session Memory**: Remembering conversations across program restarts
- **Database Management**: Setting up and managing session databases
- **Data Persistence**: Long-term storage of conversation history
- **Session Recovery**: Retrieving previous conversations

## 🧠 Core Concept: Persistent Sessions

**DatabaseSessionService** stores session data in a SQLite database file. This means:
- ✅ **Persistent storage** - Data survives program restarts
- ✅ **Cross-session memory** - Remember conversations across sessions
- ✅ **Data integrity** - ACID compliance with SQLite
- ✅ **Scalable** - Can handle multiple users and sessions
- ❌ **Setup required** - Need to initialize database
- ❌ **File-based** - Limited to single machine

Perfect for:
- Production applications
- Multi-user systems
- Long-term conversation history
- Data analysis and insights

## 🔧 Key Components

### 1. **DatabaseSessionService**
```python
from google.adk.sessions import DatabaseSessionService
```

### 2. **Database Structure**
```
┌─────────────────────────────────────────────────────────────┐
│                    SQLITE DATABASE                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   SESSIONS  │  │    STATE    │  │   EVENTS    │         │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤         │
│  │ session_id  │  │ session_id  │  │ event_id    │         │
│  │ user_id     │  │ state_data  │  │ session_id  │         │
│  │ app_name    │  │ updated_at  │  │ event_type  │         │
│  │ created_at  │  └─────────────┘  │ content     │         │
│  └─────────────┘                   │ timestamp   │         │
│                                    └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 3. **Session Lifecycle with Persistence**
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   CREATE    │───▶│   USE       │───▶│   CLOSE     │
│  SESSION    │    │  SESSION    │    │  SESSION    │
│  (DB)       │    │  (DB)       │    │  (DB)       │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Database   │    │  Database   │    │  Database   │
│  Created    │    │  Updated    │    │  Archived   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🚀 Tutorial Overview

In this tutorial, we'll create a **Simple Persistent Agent** that:
- Remembers conversations across program restarts
- Uses SQLite database for persistent storage
- Demonstrates basic cross-session memory
- Shows the difference from in-memory sessions

## 📁 Project Structure

```
5_2_persistent_conversation/
├── README.md              # This file - concept explanation
├── requirements.txt       # Dependencies
├── agent.py              # Main agent with database session management
├── app.py                # Streamlit web interface
└── sessions.db           # SQLite database (created automatically)
```

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to set up DatabaseSessionService with SQLite
- ✅ How to create persistent sessions
- ✅ How to retrieve conversation history across sessions
- ✅ How to manage database connections and transactions
- ✅ How to build agents that remember long-term

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

4. **Test persistence**:
   - Have a conversation with the agent
   - Close the browser/app
   - Restart the app
   - Continue the conversation - it will remember!

## 🔍 Code Walkthrough

### Key Database Session Management Code:

```python
# 1. Create database session service
session_service = DatabaseSessionService(
    db_url="sqlite:///sessions.db"
)

# 2. Initialize database (creates tables)
await session_service.initialize()

# 3. Create or retrieve session
session = await session_service.get_session(
    app_name="demo",
    user_id="user123",
    session_id="session_user123"
)

# 4. Use with Runner for agent execution
async for event in runner.run_async(
    user_id=user_id,
    session_id=session_id,
    new_message=user_content
):
    # Handle response
```

## 🎯 Testing Your Agent

Try these persistence tests:

### Test 1: Cross-Session Memory
```
Session 1:
User: "My name is Bob"
Agent: "Nice to meet you, Bob!"

Session 2 (after restart):
User: "What's my name?"
Agent: "Your name is Bob!"
```

### Test 2: Interest Memory
```
Session 1:
User: "I love coding"
Agent: "That's great! Coding is a wonderful skill."

Session 2 (after restart):
User: "What do I love?"
Agent: "You love coding!"
```

### Test 3: Database Verification
```
1. Have a conversation
2. Check for sessions.db file in project directory
3. Restart the app
4. Continue conversation - it remembers!
```

## 🔗 Next Steps

After completing this tutorial, you'll be ready for:
- **[Tutorial 5.3: Cloud Memory](../README.md)** - Learn cloud-based session storage
- **Advanced Database Patterns** - Multi-user session management
- **Data Analytics** - Analyzing conversation patterns

## 💡 Pro Tips

- **Database Location**: The SQLite file is created in your project directory
- **Backup Strategy**: Consider backing up the sessions.db file
- **Performance**: SQLite is fast for small to medium applications
- **Scaling**: For large applications, consider PostgreSQL or cloud databases

## 🚨 Important Notes

- **Database File**: A `sessions.db` file will be created in your project directory
- **Data Persistence**: Conversations survive program restarts
- **File Permissions**: Ensure write permissions in the project directory
- **Backup**: The database file contains all conversation data - back it up! 