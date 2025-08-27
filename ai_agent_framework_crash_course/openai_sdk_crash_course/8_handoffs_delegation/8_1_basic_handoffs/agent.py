from agents import Agent, Runner, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
import asyncio

# Create specialized agents
billing_agent = Agent(
    name="Billing Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a billing specialist. Help customers with:
    - Payment issues and billing questions
    - Subscription management and upgrades
    - Invoice and receipt requests
    - Refund processing
    
    Be helpful and provide specific billing assistance.
    """
)

technical_agent = Agent(
    name="Technical Support Agent", 
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a technical support specialist. Help customers with:
    - App crashes and technical issues
    - Account access problems
    - Feature usage and troubleshooting
    - Bug reports and technical questions
    
    Provide clear technical guidance and solutions.
    """
)

# Create triage agent with handoffs
root_agent = Agent(
    name="Customer Service Triage Agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    You are a customer service triage agent. Your job is to:
    
    1. Understand the customer's issue
    2. Determine which specialist can best help them
    3. Transfer them to the appropriate agent using handoff tools
    
    Available specialists:
    - Billing Agent: For payment, subscription, billing, and refund issues
    - Technical Support Agent: For app problems, technical issues, and troubleshooting
    
    If the issue is clearly billing-related, transfer to Billing Agent.
    If the issue is clearly technical, transfer to Technical Support Agent.
    If you can handle it yourself (general questions), do so.
    """,
    handoffs=[billing_agent, technical_agent]  # Creates handoff tools automatically
)

# Example usage
async def main():
    print("🤝 OpenAI Agents SDK - Basic Handoffs")
    print("=" * 50)
    
    # Test billing handoff
    print("=== Billing Handoff Example ===")
    result = await Runner.run(
        root_agent,
        "Hi, I was charged twice for my subscription this month. Can you help me get a refund?"
    )
    print(f"Response: {result.final_output}")
    
    # Test technical handoff
    print("\n=== Technical Support Handoff Example ===")
    result = await Runner.run(
        root_agent,
        "My app keeps crashing when I try to upload photos. This has been happening for 3 days."
    )
    print(f"Response: {result.final_output}")
    
    print("\n✅ Basic handoffs tutorial complete!")

if __name__ == "__main__":
    asyncio.run(main())
