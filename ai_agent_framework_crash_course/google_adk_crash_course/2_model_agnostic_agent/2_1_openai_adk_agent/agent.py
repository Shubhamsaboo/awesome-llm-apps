import os
import random
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

def get_fun_fact():
    """Return a random fun fact"""
    facts = [
        "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly edible.",
        "Octopuses have three hearts and blue blood.",
        "A group of flamingos is called a 'flamboyance'.",
        "Bananas are berries, but strawberries aren't.",
        "A day on Venus is longer than its year.",
        "Wombat poop is cube-shaped.",
        "There are more possible games of chess than atoms in the observable universe.",
        "Dolphins have names for each other.",
    ]
    return random.choice(facts)

# OpenAI model via OpenRouter
model = LiteLlm(
    model="openrouter/openai/gpt-4o",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

root_agent = Agent(
    name="openai_adk_agent",
    model=model,
    description="Fun fact agent using OpenAI GPT-4 via OpenRouter",
    instruction="""
    You are a helpful assistant powered by OpenAI GPT-4 that shares interesting fun facts. 
    Use the `get_fun_fact` tool when users ask for a fun fact or interesting information.
    Be enthusiastic and friendly in your responses.
    Always mention that you're powered by OpenAI GPT-4 when introducing yourself.
    """,
    tools=[get_fun_fact],
) 