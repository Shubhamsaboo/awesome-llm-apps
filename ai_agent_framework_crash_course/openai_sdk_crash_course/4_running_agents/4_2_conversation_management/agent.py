from agents import Agent, Runner, SQLiteSession

# Create an agent for demonstrating conversation management
root_agent = Agent(
    name="Conversation Agent",
    instructions="You are a helpful assistant that remembers conversation context. Reply concisely but reference previous context when relevant."
)

# Example 1: Manual conversation management
async def manual_conversation_example():
    """Demonstrates manual conversation management using result.to_input_list()"""
    
    # First turn
    result = await Runner.run(root_agent, "My name is Alice and I live in San Francisco.")
    print(f"Turn 1: {result.final_output}")
    
    # Second turn - manually pass conversation history
    new_input = result.to_input_list() + [{"role": "user", "content": "What city do I live in?"}]
    result = await Runner.run(root_agent, new_input)
    print(f"Turn 2: {result.final_output}")
    
    return result

# Example 2: Automatic conversation management with Sessions
async def session_conversation_example():
    """Demonstrates automatic conversation management using SQLiteSession"""
    
    # Create session instance
    session = SQLiteSession("conversation_123")
    
    # First turn
    result = await Runner.run(root_agent, "I'm a software developer working on AI projects.", session=session)
    print(f"Session Turn 1: {result.final_output}")
    
    # Second turn - session automatically remembers context
    result = await Runner.run(root_agent, "What kind of work do I do?", session=session)
    print(f"Session Turn 2: {result.final_output}")
    
    return result
