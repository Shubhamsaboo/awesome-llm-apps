import asyncio
import os
import uuid
from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types
from dotenv import load_dotenv

# Load environment variables (for API key)
load_dotenv()

# Create session service and agent
session_service = InMemorySessionService()
agent = LlmAgent(
    name="memory_agent",
    model="gemini-3-flash-preview",
    description="A simple agent that remembers conversations",
    instruction="You are a helpful assistant. Remember what users tell you and reference it in future conversations."
)

# Create runner with session service
runner = Runner(
    agent=agent,
    app_name="demo",
    session_service=session_service
)

async def chat(user_id: str, message: str) -> str:
    """Simple chat function with memory using Runner"""
    session_id = f"session_{user_id}"
    
    # Create or get session
    session = await session_service.get_session(app_name="demo", user_id=user_id, session_id=session_id)
    if not session:
        # Create new session with initial state
        session = await session_service.create_session(
            app_name="demo",
            user_id=user_id,
            session_id=session_id,
            state={"conversation_history": []}
        )
    
    # Create user content
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=message)]
    )
    
    # Run the agent with session
    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response_text = event.content.parts[0].text
            break
    
    return response_text

# Test the memory
if __name__ == "__main__":
    async def test():
        user_id = "test_user"
        messages = ["My name is Alice", "What's my name?", "I love pizza", "What do I love?"]
        
        for msg in messages:
            print(f"\nUser: {msg}")
            response = await chat(user_id, msg)
            print(f"Assistant: {response}")
    
    asyncio.run(test()) 