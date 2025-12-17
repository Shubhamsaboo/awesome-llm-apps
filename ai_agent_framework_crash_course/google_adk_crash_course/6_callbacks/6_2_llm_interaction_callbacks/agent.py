#!/usr/bin/env python3
"""
LLM Interaction Callbacks Demo
Simple agent that demonstrates LLM request/response monitoring
"""

import os
from datetime import datetime
from typing import Optional
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.runners import InMemoryRunner
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def before_model_callback(callback_context: CallbackContext, llm_request) -> Optional[types.Content]:
    """Callback before LLM request is made"""
    agent_name = callback_context.agent_name
    request_time = datetime.now()
    
    # Extract model and prompt from llm_request
    model = getattr(llm_request, 'model', 'unknown')
    
    # Extract full prompt text from llm_request contents
    prompt_text = "unknown"
    if hasattr(llm_request, 'contents') and llm_request.contents:
        for content in llm_request.contents:
            if hasattr(content, 'parts') and content.parts:
                for part in content.parts:
                    if hasattr(part, 'text') and part.text:
                        prompt_text = part.text
                        break
                if prompt_text != "unknown":
                    break
    
    print(f"🤖 LLM Request to {model}")
    print(f"⏰ Request time: {request_time.strftime('%H:%M:%S')}")
    print(f"📋 Agent: {agent_name}")
    print()  # Add spacing
    
    # Store request info in state for after callback
    current_state = callback_context.state.to_dict()
    current_state["llm_request_time"] = request_time.isoformat()
    current_state["llm_model"] = model
    current_state["llm_prompt_length"] = len(prompt_text)
    callback_context.state.update(current_state)
    
    # Return None to allow normal execution
    return None

def after_model_callback(callback_context: CallbackContext, llm_response) -> Optional[types.Content]:
    """Callback after LLM response is received"""
    agent_name = callback_context.agent_name
    current_state = callback_context.state.to_dict()
    
    # Extract response info
    response_text = str(llm_response) if llm_response else 'unknown'
    model = current_state.get("llm_model", "unknown")
    
    # Extract token count from usage_metadata
    tokens = 0
    if llm_response and hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
        tokens = getattr(llm_response.usage_metadata, 'total_token_count', 0)
    
    # Get request time from state
    request_time_str = current_state.get("llm_request_time")
    if request_time_str:
        request_time = datetime.fromisoformat(request_time_str)
        duration = datetime.now() - request_time
        duration_seconds = duration.total_seconds()
    else:
        duration_seconds = 0
    
    print(f"📝 LLM Response from {model}")
    print(f"⏱️ Duration: {duration_seconds:.2f}s")
    print(f"🔢 Tokens: {tokens}")
    
    # Calculate estimated cost for Gemini 3 Flash
    # Pricing: $2.50 per 1M output tokens (including thinking tokens)
    cost_per_1k_output = 0.0025  # $2.50 per 1M = $0.0025 per 1K
    estimated_cost = (tokens / 1000) * cost_per_1k_output
    print(f"💰 Estimated cost: ${estimated_cost:.4f}")
    print()  # Add spacing
    
    # Return None to use the original response
    return None

# Create agent with LLM callbacks
root_agent = LlmAgent(
    name="llm_monitor_agent",
    model="gemini-3-flash-preview",
    description="Agent with LLM interaction monitoring",
    instruction="""
    You are a helpful assistant with LLM monitoring.
    
    Your role is to:
    - Provide clear, informative responses
    - Keep responses concise but comprehensive
    - Demonstrate the LLM callback system
    
    The system will automatically track:
    - Your requests to the LLM model
    - Response times and token usage
    - Estimated API costs
    
    Focus on being helpful while showing the monitoring capabilities.
    """,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback
)

# Create runner for agent execution
runner = InMemoryRunner(agent=root_agent, app_name="llm_monitor_app")

async def run_agent(message: str) -> str:
    """Run the agent with the given message"""
    user_id = "demo_user"
    session_id = "demo_session"
    
    # Get the bundled session service
    session_service = runner.session_service
    
    # Get or create session
    session = await session_service.get_session(
        app_name="llm_monitor_app", 
        user_id=user_id, 
        session_id=session_id
    )
    if not session:
        session = await session_service.create_session(
            app_name="llm_monitor_app",
            user_id=user_id,
            session_id=session_id,
            state={"conversation_history": []}
        )
    
    # Create user content
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=message)]
    )
    
    # Run agent and get response
    response_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content
    ):
        if event.is_final_response() and event.content:
            response_text = event.content.parts[0].text.strip()
            # Don't break here - let the loop complete naturally to ensure callbacks run
    
    return response_text

if __name__ == "__main__":
    import asyncio
    
    # Test the agent
    print("🧪 Testing LLM Interaction Callbacks")
    print("=" * 50)
    
    test_messages = [
        "Explain quantum computing in simple terms",
        "Write a short poem about AI",
        "What are the benefits of renewable energy?"
    ]
    
    async def test_agent():
        for message in test_messages:
            print(f"\n🤖 User: {message}")
            response = await run_agent(message)
            print(f"🤖 Agent: {response}")
            print("-" * 50)
    
    asyncio.run(test_agent()) 