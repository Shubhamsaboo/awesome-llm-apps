from agents import Agent

# Define specialized translation agents
spanish_agent = Agent(
    name="Spanish Agent",
    instructions="You translate the user's message to Spanish"
)

french_agent = Agent(
    name="French Agent", 
    instructions="You translate the user's message to French"
)

german_agent = Agent(
    name="German Agent",
    instructions="You translate the user's message to German"
)

# Create orchestrator agent that uses other agents as tools
root_agent = Agent(
    name="Translation Orchestrator",
    instructions="""
    You are a translation orchestrator agent. You coordinate specialized translation agents.
    
    You have access to translation agents for:
    - Spanish translations
    - French translations  
    - German translations
    
    When users request translations:
    1. Use the appropriate translation agent tool
    2. You can use multiple agents if asked for multiple translations
    3. Present the results clearly with language labels
    
    If asked for multiple translations, call the relevant tools for each language.
    """,
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish"
        ),
        french_agent.as_tool(
            tool_name="translate_to_french", 
            tool_description="Translate the user's message to French"
        ),
        german_agent.as_tool(
            tool_name="translate_to_german",
            tool_description="Translate the user's message to German"
        )
    ]
)
