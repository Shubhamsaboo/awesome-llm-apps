# 🧠 Tutorial 5: Context Management

Master context-aware agent development with the OpenAI Agents SDK! This tutorial teaches you how to use `RunContextWrapper` to pass custom context objects that enable agents to access user data, session information, and state throughout their execution.

## 🎯 What You'll Learn

- **RunContextWrapper**: Pass custom context objects to agents
- **Context-Aware Tools**: Build tools that access user state and preferences
- **Type-Safe Context**: Use generic types for compile-time safety
- **Context Manipulation**: Update and modify context during agent execution
- **Production Patterns**: Real-world context management strategies

## 🧠 Core Concept: What is Context Management?

Context management allows you to pass **custom data structures** to your agents that persist throughout the entire agent execution. Think of context as a **shared state container** that:

- Stores user information, preferences, and session data
- Provides access to external systems and databases
- Maintains state across multiple tool calls
- Enables personalized agent behavior
- Supports type-safe data access

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTEXT WORKFLOW                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  USER CONTEXT                                               │
│  ┌─────────────┐                                            │
│  │  UserInfo   │    1. PASS TO RUNNER                       │
│  │  - name     │ ────────────────────────────────────────┐  │
│  │  - uid      │                                         │  │
│  │  - prefs    │                                         ▼  │
│  └─────────────┘                                            │
│                   ┌─────────────┐                           │
│                   │   AGENT     │    2. CONTEXT AVAILABLE   │
│                   │   RUNNER    │       TO ALL TOOLS        │
│                   └─────────────┘                           │
│                         │                                   │
│                         ▼                                   │
│                   ┌─────────────┐    3. TOOLS ACCESS        │
│                   │ TOOL CALLS  │       CONTEXT VIA         │
│                   │ WITH        │       RunContextWrapper   │
│                   │ CONTEXT     │                           │
│                   └─────────────┘                           │
│                         │                                   │
│                         ▼                                   │
│                   ┌─────────────┐    4. CONTEXT CAN BE      │
│                   │  CONTEXT    │       MODIFIED AND        │
│                   │ UPDATED     │       PERSISTS            │
│                   └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Key Context Management Concepts

### **Context Objects**
Custom data classes that hold state and user information:

```python
@dataclass
class UserInfo:
    name: str
    uid: int
    preferences: dict = None
```

### **RunContextWrapper**
Type-safe wrapper that provides access to context in tools:

```python
@function_tool
async def my_tool(wrapper: RunContextWrapper[UserInfo]) -> str:
    user = wrapper.context  # Access the UserInfo object
    return f"Hello {user.name}"
```

### **Context-Aware Agents**
Agents that use generic typing for context safety:

```python
agent = Agent[UserInfo](
    name="Context Agent",
    tools=[context_aware_tool]
)
```

## 🧪 What This Demonstrates

### **1. User Information Context**
- Storing user profile data (name, ID, preferences)
- Personalizing agent responses based on user context
- Updating user preferences during conversation

### **2. Context-Aware Tools**
- `fetch_user_profile()`: Retrieve user information from context
- `update_user_preference()`: Modify user settings in context
- `get_personalized_greeting()`: Generate custom greetings

### **3. Type Safety**
- Generic typing with `Agent[UserInfo]` for compile-time checks
- Typed context access with `RunContextWrapper[UserInfo]`
- IDE support and autocompletion for context objects

### **4. Context Persistence**
- Context modifications persist across tool calls
- State changes are maintained throughout agent execution
- Updated context is available to subsequent operations

## 🎯 Learning Objectives

By the end of this tutorial, you'll understand:
- ✅ How to create custom context objects with dataclasses
- ✅ Using RunContextWrapper for type-safe context access
- ✅ Building context-aware tools that read and modify state
- ✅ Implementing personalized agent behavior with context
- ✅ Production patterns for context management at scale

## 🚀 Getting Started

1. **Install OpenAI Agents SDK**:
   ```bash
   pip install openai-agents
   ```

2. **Set up environment**:
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the context example**:
   ```python
   import asyncio
   from agent import context_example
   
   # Test context management
   asyncio.run(context_example())
   ```

## 🧪 Sample Use Cases

### Basic Context Usage
- "Hello! I'd like to know about my profile and prefer casual greetings."
- "Update my greeting style to friendly"
- "What are my current preferences?"

### Personalization Examples
- Customized greetings based on user preferences
- Tailored responses using user profile information
- Dynamic behavior modification through context updates

### Production Applications
- User session management in web applications
- Customer support with account context
- E-commerce with shopping preferences and history

## 🔧 Key Context Patterns

### 1. **Basic Context Creation**
```python
from dataclasses import dataclass

@dataclass
class UserInfo:
    name: str
    uid: int
    preferences: dict = None
```

### 2. **Context-Aware Tool**
```python
@function_tool
async def my_tool(wrapper: RunContextWrapper[UserInfo]) -> str:
    user = wrapper.context
    return f"Processing for {user.name}"
```

### 3. **Running with Context**
```python
user_context = UserInfo(name="Alice", uid=123)
result = await Runner.run(agent, "message", context=user_context)
```

### 4. **Context Updates**
```python
@function_tool
async def update_preference(wrapper: RunContextWrapper[UserInfo], key: str, value: str) -> str:
    wrapper.context.preferences[key] = value
    return f"Updated {key} to {value}"
```

## 💡 Context Management Best Practices

1. **Use Dataclasses**: Leverage Python dataclasses for clean context objects
2. **Type Safety**: Always use generic typing for compile-time validation
3. **Immutable Where Possible**: Consider frozen dataclasses for read-only context
4. **Validation**: Add validation to context object initialization
5. **Documentation**: Document context fields and their purposes clearly

## 🔗 Related Concepts

- **Sessions**: Context works alongside session memory for comprehensive state
- **Guardrails**: Context can be used in guardrail validation logic
- **Tool Calling**: Context enables sophisticated tool behavior

## 🚨 Common Pitfalls

- **Missing Generic Types**: Always specify context type in Agent[YourContextType]
- **Context Mutations**: Be careful about unintended context modifications
- **Memory Leaks**: Clean up large context objects when no longer needed
- **Thread Safety**: Consider concurrent access in multi-threaded applications

## 💡 Pro Tips

- **Start Simple**: Begin with basic user info, expand to complex state objects
- **Validate Early**: Add validation to context object constructors
- **Use Type Hints**: Leverage Python type hints for better IDE support
- **Consider Immutability**: Use frozen dataclasses for read-only context when appropriate
- **Document Context**: Clear documentation helps team members understand context structure

## 🔗 Next Steps

After mastering context management, you'll be ready for:
- **[Tutorial 6: Guardrails & Validation](../6_guardrails_validation/README.md)** - Input/output safety with context
- **[Tutorial 7: Sessions](../7_sessions/README.md)** - Combining context with conversation memory
- **[Tutorial 8: Production Patterns](../8_handoffs_delegation/README.md)** - Scaling context in real applications
