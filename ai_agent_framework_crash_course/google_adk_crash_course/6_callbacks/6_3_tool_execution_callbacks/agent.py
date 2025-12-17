import os
import asyncio
import time
from datetime import datetime
from typing import Optional, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import BaseTool, FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def calculator_tool(operation: str, a: float, b: float) -> str:
    """Simple calculator tool with basic operations"""
    if operation == "add":
        return f"{a} + {b} = {a + b}"
    elif operation == "subtract":
        return f"{a} - {b} = {a - b}"
    elif operation == "multiply":
        return f"{a} × {b} = {a * b}"
    elif operation == "divide":
        if b == 0:
            return "Error: Division by zero"
        return f"{a} ÷ {b} = {a / b}"
    else:
        return f"Unknown operation: {operation}"

# Create FunctionTool from the calculator function
calculator_function_tool = FunctionTool(func=calculator_tool)

def before_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict[str, Any]]:
    """Callback before tool execution starts"""
    agent_name = tool_context.agent_name
    tool_name = tool.name
    start_time = time.time()
    
    print(f"🔧 Tool {tool_name} started")
    print(f"📝 Parameters: {args}")
    print(f"📋 Agent: {agent_name}")
    print()  # Add spacing
    
    # Store start time in tool_context state for after callback
    current_state = tool_context.state.to_dict()
    current_state["tool_start_time"] = start_time
    tool_context.state.update(current_state)
    
    # Return None to allow normal execution
    return None

def after_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Any) -> Optional[Any]:
    """Callback after tool execution completes"""
    agent_name = tool_context.agent_name
    tool_name = tool.name
    current_state = tool_context.state.to_dict()
    
    # Get start time from state and calculate duration
    start_time = current_state.get("tool_start_time")
    if start_time:
        end_time = time.time()
        duration_seconds = end_time - start_time
        
        print(f"✅ Tool {tool_name} completed")
        print(f"⏱️ Duration: {duration_seconds:.4f}s")
        print(f"📄 Result: {tool_response}")
        print()  # Add spacing
    else:
        print(f"✅ Tool {tool_name} completed")
        print(f"📄 Result: {tool_response}")
        print()  # Add spacing
    
    # Return None to use the original tool response
    return None

# --- 2. Setup Agent with Tool Callbacks ---
llm_agent_with_tool_callbacks = LlmAgent(
    name="tool_execution_demo_agent",
    model="gemini-3-flash-preview",
    instruction="You are a helpful assistant with calculator tools. When users ask for calculations, use the calculator_tool with appropriate parameters and provide clear explanations of the results.",
    description="An LLM agent demonstrating tool execution callbacks for monitoring",
    tools=[calculator_function_tool],
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback
)

# --- 3. Setup Runner and Sessions ---
runner = InMemoryRunner(agent=llm_agent_with_tool_callbacks, app_name="tool_execution_callback_demo")

async def run_agent(message: str) -> str:
    """Run the agent with the given message"""
    user_id = "demo_user"
    session_id = "demo_session"
    
    # Get the bundled session service
    session_service = runner.session_service
    
    # Get or create session
    session = await session_service.get_session(
        app_name="tool_execution_callback_demo", 
        user_id=user_id, 
        session_id=session_id
    )
    if not session:
        session = await session_service.create_session(
            app_name="tool_execution_callback_demo",
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
            # Don't break - let the loop complete naturally to ensure callbacks run
    
    return response_text

# --- 4. Execute ---
if __name__ == "__main__":
    print("\n" + "="*50 + " Tool Execution Callbacks Demo " + "="*50)
    
    # Test messages
    test_messages = [
        "Calculate 15 + 27",
        "What is 100 divided by 4?",
        "Multiply 8 by 12",
        "What is 50 minus 23?"
    ]
    
    async def test_agent():
        for i, message in enumerate(test_messages, 1):
            print(f"\n--- Test {i}: {message} ---")
            response = await run_agent(message)
            print(f"🤖 Response: {response}")
    
    asyncio.run(test_agent()) 