from dataclasses import dataclass
from agents import Agent, RunContextWrapper, Runner, function_tool

@dataclass
class UserInfo:
    """Context object containing user information and session data"""
    name: str
    uid: int
    preferences: dict = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}

@function_tool
async def fetch_user_profile(wrapper: RunContextWrapper[UserInfo]) -> str:
    """Fetch detailed user profile information from the context"""
    user = wrapper.context
    return f"User Profile: {user.name} (ID: {user.uid}), Preferences: {user.preferences}"

@function_tool
async def update_user_preference(wrapper: RunContextWrapper[UserInfo], key: str, value: str) -> str:
    """Update a user preference in the context"""
    user = wrapper.context
    user.preferences[key] = value
    return f"Updated {user.name}'s preference: {key} = {value}"

@function_tool
async def get_personalized_greeting(wrapper: RunContextWrapper[UserInfo]) -> str:
    """Generate a personalized greeting based on user context"""
    user = wrapper.context
    preferred_style = user.preferences.get('greeting_style', 'formal')
    
    if preferred_style == 'casual':
        return f"Hey {user.name}! What's up?"
    elif preferred_style == 'friendly':
        return f"Hi there, {user.name}! How can I help you today?"
    else:
        return f"Good day, {user.name}. How may I assist you?"

# Create agent with context-aware tools
root_agent = Agent[UserInfo](
    name="Context-Aware Assistant",
    instructions="""
    You are a personalized assistant that uses user context to provide tailored responses.
    
    You have access to:
    - User profile information (name, ID, preferences)
    - Ability to update user preferences
    - Personalized greeting generation
    
    Use the context tools to:
    1. Fetch user information when needed
    2. Update preferences when users express them
    3. Provide personalized greetings and responses
    
    Always consider the user's context when responding.
    """,
    tools=[fetch_user_profile, update_user_preference, get_personalized_greeting]
)

# Example usage with context
async def context_example():
    """Demonstrates context management with user information"""
    
    # Create user context
    user_context = UserInfo(
        name="Alice Johnson",
        uid=12345,
        preferences={"greeting_style": "friendly", "topic_interest": "technology"}
    )
    
    # Run agent with context
    result = await Runner.run(
        root_agent,
        "Hello! I'd like to know about my profile and prefer casual greetings.",
        context=user_context
    )
    
    print(f"Response: {result.final_output}")
    print(f"Updated context: {user_context}")
    
    return result
