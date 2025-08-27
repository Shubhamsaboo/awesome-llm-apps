from agents import Agent, Runner, SQLiteSession

# Create agent for memory operations demonstrations
root_agent = Agent(
    name="Memory Operations Agent", 
    instructions="""
    You are a helpful assistant demonstrating session memory operations.
    
    Remember previous conversation context and reference it when relevant.
    Reply concisely but show understanding of conversation history.
    """
)

# Example 1: Basic memory operations - get_items()
async def basic_memory_operations():
    """Demonstrates get_items, add_items, and session inspection from OpenAI SDK docs"""
    
    session = SQLiteSession("memory_demo", "operations.db")
    
    print("=== Basic Memory Operations ===")
    
    # Start conversation
    result = await Runner.run(root_agent, "Hello, my favorite color is blue.", session=session)
    print(f"Agent Response: {result.final_output}")
    
    # Demonstrate get_items() - retrieve conversation history
    items = await session.get_items()
    print(f"\n📋 Session Memory Inspection (get_items()):")
    print(f"   Total items in session: {len(items)}")
    for i, item in enumerate(items, 1):
        content_preview = item['content'][:50] + "..." if len(item['content']) > 50 else item['content']
        print(f"   {i}. [{item['role']}]: {content_preview}")
    
    # Demonstrate add_items() - manually add conversation items
    print(f"\n➕ Adding Custom Items (add_items()):")
    custom_items = [
        {"role": "user", "content": "I also love hiking and photography."},
        {"role": "assistant", "content": "Wonderful! Blue, hiking, and photography - I'll remember these interests."}
    ]
    await session.add_items(custom_items)
    
    updated_items = await session.get_items()
    print(f"   Items after manual addition: {len(updated_items)} (was {len(items)})")
    
    # Continue conversation with enriched context
    result = await Runner.run(root_agent, "What hobbies do I have?", session=session)
    print(f"\n🤖 Agent with enriched context: {result.final_output}")
    
    return session

# Example 2: Using pop_item() for corrections (from OpenAI SDK docs)
async def conversation_corrections():
    """Demonstrates using pop_item to correct or undo conversation turns"""
    
    session = SQLiteSession("correction_demo", "corrections.db")
    
    print("\n=== Conversation Corrections with pop_item() ===")
    
    # Initial question with wrong math
    result = await Runner.run(root_agent, "What's 2 + 2?", session=session)
    print(f"❓ Original Question: What's 2 + 2?")
    print(f"🤖 Agent Answer: {result.final_output}")
    
    print(f"\n📊 Items before correction: {len(await session.get_items())}")
    
    # User wants to correct their question using pop_item()
    print(f"\n🔄 Correcting conversation using pop_item()...")
    
    # Remove assistant's response using pop_item()
    assistant_item = await session.pop_item()
    if assistant_item:
        print(f"   ↩️  Removed assistant response: {assistant_item['content'][:50]}...")
    
    # Remove user's original question using pop_item()
    user_item = await session.pop_item()
    if user_item:
        print(f"   ↩️  Removed user question: {user_item['content']}")
    
    print(f"📊 Items after corrections: {len(await session.get_items())}")
    
    # Ask corrected question
    result = await Runner.run(root_agent, "What's 2 + 3?", session=session)
    print(f"\n✅ Corrected Question: What's 2 + 3?")
    print(f"🤖 New Answer: {result.final_output}")
    
    return session

# Example 3: clear_session() for session reset (from OpenAI SDK docs)
async def session_management():
    """Demonstrates clear_session() and session lifecycle management"""
    
    session = SQLiteSession("management_demo", "management.db")
    
    print("\n=== Session Management with clear_session() ===")
    
    # Build up conversation history
    print("🏗️  Building conversation history...")
    await Runner.run(root_agent, "I work as a teacher.", session=session)
    await Runner.run(root_agent, "I teach mathematics.", session=session) 
    await Runner.run(root_agent, "I love solving puzzles.", session=session)
    
    items_before = await session.get_items()
    print(f"📊 Session contains {len(items_before)} items before clearing")
    
    # Test agent memory before clearing
    result = await Runner.run(root_agent, "What do I do for work?", session=session)
    print(f"🤖 Agent remembers: {result.final_output}")
    
    # Demonstrate clear_session() - removes all conversation history
    print(f"\n🧹 Clearing session with clear_session()...")
    await session.clear_session()
    
    items_after = await session.get_items()
    print(f"📊 Session contains {len(items_after)} items after clearing")
    
    # Test fresh conversation after clearing
    result = await Runner.run(root_agent, "Do you know anything about me?", session=session)
    print(f"🤖 Fresh conversation (no memory): {result.final_output}")
    
    return session

# Example 4: Advanced memory inspection with get_items(limit)
async def memory_inspection():
    """Demonstrates get_items with limit parameter and detailed memory analysis"""
    
    session = SQLiteSession("inspection_demo", "inspection.db")
    
    print("\n=== Advanced Memory Inspection ===")
    
    # Build longer conversation for inspection
    conversation_items = [
        "Hello, I'm learning about AI.",
        "What is machine learning?",
        "How does deep learning work?", 
        "What's the difference between AI and ML?",
        "Can you explain neural networks?"
    ]
    
    print("🏗️  Building extended conversation...")
    for item in conversation_items:
        await Runner.run(root_agent, item, session=session)
    
    # Demonstrate get_items() with limit parameter (from SDK docs)
    print(f"\n🔍 Memory Inspection with get_items(limit=3):")
    recent_items = await session.get_items(limit=3)
    print(f"   Last 3 items (out of full conversation):")
    for i, item in enumerate(recent_items, 1):
        content_preview = item['content'][:60] + "..." if len(item['content']) > 60 else item['content']
        print(f"   {i}. [{item['role']}]: {content_preview}")
    
    # Compare with full conversation
    all_items = await session.get_items()
    print(f"\n📊 Full conversation analysis:")
    print(f"   Total items in session: {len(all_items)}")
    print(f"   Recent items retrieved: {len(recent_items)}")
    
    # Count items by role
    user_items = [item for item in all_items if item['role'] == 'user']
    assistant_items = [item for item in all_items if item['role'] == 'assistant']
    print(f"   User messages: {len(user_items)}")
    print(f"   Assistant responses: {len(assistant_items)}")
    
    return session

# Main execution function
async def main():
    """Run all memory operations examples"""
    import asyncio
    
    print("🧠 OpenAI Agents SDK - Memory Operations Examples")
    print("=" * 60)
    
    await basic_memory_operations()
    await conversation_corrections()
    await session_management()
    await memory_inspection()
    
    print("\n✅ All memory operations examples completed!")
    print("Key operations demonstrated:")
    print("  • get_items() - Retrieve conversation history")
    print("  • add_items() - Manually add conversation items")
    print("  • pop_item() - Remove last item for corrections")
    print("  • clear_session() - Reset conversation history")
    print("  • get_items(limit=N) - Retrieve recent items only")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
