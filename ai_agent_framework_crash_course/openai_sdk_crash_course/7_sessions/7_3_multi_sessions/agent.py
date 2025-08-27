from agents import Agent, Runner, SQLiteSession

# Create agents for multi-session demonstrations
support_agent = Agent(
    name="Support Agent",
    instructions="You are a customer support representative. Help with account and technical issues."
)

sales_agent = Agent(
    name="Sales Agent", 
    instructions="You are a sales representative. Help with product information and purchases."
)

# Example 1: Different users with separate sessions
async def multi_user_sessions():
    """Demonstrates separate sessions for different users"""
    
    print("=== Multi-User Sessions ===")
    
    # Create separate sessions for different users
    alice_session = SQLiteSession("user_alice", "multi_user.db")
    bob_session = SQLiteSession("user_bob", "multi_user.db")
    
    # Alice's conversation
    print("Alice's conversation:")
    result = await Runner.run(support_agent, "I forgot my password", session=alice_session)
    print(f"Alice: I forgot my password")
    print(f"Support: {result.final_output}")
    
    result = await Runner.run(support_agent, "My email is alice@example.com", session=alice_session)
    print(f"Alice: My email is alice@example.com")
    print(f"Support: {result.final_output}")
    
    # Bob's separate conversation
    print("\nBob's conversation:")
    result = await Runner.run(support_agent, "My app keeps crashing", session=bob_session)
    print(f"Bob: My app keeps crashing") 
    print(f"Support: {result.final_output}")
    
    # Alice continues her conversation (agent remembers her context)
    print("\nAlice continues:")
    result = await Runner.run(support_agent, "Did you find my account?", session=alice_session)
    print(f"Alice: Did you find my account?")
    print(f"Support: {result.final_output}")
    
    return alice_session, bob_session

# Example 2: Different conversation contexts
async def context_based_sessions():
    """Demonstrates sessions for different conversation contexts"""
    
    print("\n=== Context-Based Sessions ===")
    
    # Different conversation contexts
    support_session = SQLiteSession("support_ticket_123", "contexts.db")
    sales_session = SQLiteSession("sales_inquiry_456", "contexts.db")
    
    # Support conversation
    print("Support context:")
    result = await Runner.run(support_agent, "I can't access my premium features", session=support_session)
    print(f"Customer: I can't access my premium features")
    print(f"Support: {result.final_output}")
    
    # Sales conversation
    print("\nSales context:")
    result = await Runner.run(sales_agent, "What premium features do you offer?", session=sales_session)
    print(f"Prospect: What premium features do you offer?")
    print(f"Sales: {result.final_output}")
    
    # Continue support conversation
    print("\nBack to support:")
    result = await Runner.run(support_agent, "I'm on the premium plan", session=support_session)
    print(f"Customer: I'm on the premium plan")
    print(f"Support: {result.final_output}")
    
    return support_session, sales_session

# Example 3: Shared session across different agents
async def shared_session_agents():
    """Demonstrates how different agents can share the same session"""
    
    print("\n=== Shared Session Across Agents ===")
    
    # Shared session for customer handoff scenario
    shared_session = SQLiteSession("customer_handoff", "shared.db")
    
    # Start with sales agent
    print("Starting with Sales Agent:")
    result = await Runner.run(
        sales_agent, 
        "I'm interested in your premium plan but have technical questions.",
        session=shared_session
    )
    print(f"Customer: I'm interested in your premium plan but have technical questions.")
    print(f"Sales: {result.final_output}")
    
    # Handoff to support agent (same session, so context is preserved)
    print("\nHandoff to Support Agent:")
    result = await Runner.run(
        support_agent,
        "Can you help me understand the technical requirements?", 
        session=shared_session
    )
    print(f"Customer: Can you help me understand the technical requirements?")
    print(f"Support: {result.final_output}")
    
    # Back to sales for closing
    print("\nBack to Sales Agent:")
    result = await Runner.run(
        sales_agent,
        "Thanks for the technical info. How do I upgrade?",
        session=shared_session
    )
    print(f"Customer: Thanks for the technical info. How do I upgrade?")
    print(f"Sales: {result.final_output}")
    
    return shared_session

# Example 4: Session organization strategies
async def session_organization():
    """Demonstrates different session organization strategies"""
    
    print("\n=== Session Organization Strategies ===")
    
    # Strategy 1: User-based with timestamps
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    user_daily_session = SQLiteSession(f"user_123_{timestamp}", "daily_sessions.db")
    
    # Strategy 2: Feature-based sessions
    chat_session = SQLiteSession("chat_feature_user_123", "feature_sessions.db")
    support_session = SQLiteSession("support_feature_user_123", "feature_sessions.db")
    
    # Strategy 3: Thread-based sessions
    thread_session = SQLiteSession("thread_abc123", "thread_sessions.db")
    
    # Demonstrate different approaches
    print("Daily user session:")
    result = await Runner.run(support_agent, "Daily check-in", session=user_daily_session)
    print(f"Response: {result.final_output}")
    
    print("\nFeature-specific chat:")
    result = await Runner.run(support_agent, "Chat feature question", session=chat_session)
    print(f"Response: {result.final_output}")
    
    print("\nThread-based conversation:")
    result = await Runner.run(support_agent, "Thread conversation", session=thread_session)
    print(f"Response: {result.final_output}")
    
    return user_daily_session, chat_session, thread_session
