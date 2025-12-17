import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from google.adk.agents import LlmAgent
from google.adk.agents.base_agent import BaseAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import InMemoryRunner
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from dotenv import load_dotenv

# Load environment variables (API key)
load_dotenv()

# ============================================================================
# PLUGIN DEFINITION
# ============================================================================
# Plugins extend BasePlugin and provide global callbacks across all agents/tools
class SimplePlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="simple_plugin")
        # Track usage statistics across all executions
        self.agent_count = 0
        self.tool_count = 0
        
    # Called when user sends a message - can modify the input
    async def on_user_message_callback(self, *, invocation_context, user_message: types.Content) -> Optional[types.Content]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"🔍 [Plugin] User message at {timestamp}")
        # Add timestamp to each message part for context
        modified_parts = [types.Part(text=f"[{timestamp}] {part.text}") for part in user_message.parts if hasattr(part, 'text')]
        return types.Content(role='user', parts=modified_parts)
    
    # Called before each agent execution - good for logging and setup
    async def before_agent_callback(self, *, agent: BaseAgent, callback_context: CallbackContext) -> None:
        self.agent_count += 1
        print(f"🤖 [Plugin] Agent {agent.name} starting (count: {self.agent_count})")
    
    # Called before each tool execution - track tool usage
    async def before_tool_callback(self, *, tool: BaseTool, tool_args: Dict[str, Any], tool_context: ToolContext) -> None:
        self.tool_count += 1
        print(f"🔧 [Plugin] Tool {tool.name} starting (count: {self.tool_count})")
    
    # Called after the entire run completes - generate final report
    async def after_run_callback(self, *, invocation_context) -> None:
        print(f"📊 [Plugin] Final Report: {self.agent_count} agents, {self.tool_count} tools")

# ============================================================================
# TOOL DEFINITION
# ============================================================================
# This tool can fail (division by zero) to demonstrate error handling
async def calculator_tool(tool_context: ToolContext, operation: str, a: float, b: float) -> Dict[str, Any]:
    print(f"🔧 [Tool] Calculator: {operation}({a}, {b})")
    if operation == "divide" and b == 0:
        raise ValueError("Division by zero is not allowed")
    # Dictionary of operations for cleaner code
    ops = {"add": lambda x, y: x + y, "subtract": lambda x, y: x - y, "multiply": lambda x, y: x * y, "divide": lambda x, y: x / y}
    if operation not in ops:
        raise ValueError(f"Unknown operation: {operation}")
    return {"operation": operation, "a": a, "b": b, "result": ops[operation](a, b)}

# ============================================================================
# AGENT AND RUNNER SETUP
# ============================================================================
# Create agent with the calculator tool
agent = LlmAgent(name="plugin_demo_agent", model="gemini-3-flash-preview", 
                instruction="You are a helpful assistant that can perform calculations. Use the calculator_tool when needed.",
                tools=[calculator_tool])

# Create runner and register the plugin - this makes the plugin global
runner = InMemoryRunner(agent=agent, app_name="plugin_demo_app", plugins=[SimplePlugin()])

# ============================================================================
# AGENT EXECUTION FUNCTION
# ============================================================================
async def run_agent(message: str) -> str:
    # Session management for conversation state
    user_id, session_id = "demo_user", "demo_session"
    session_service = runner.session_service
    
    # Get or create session (required for ADK)
    session = await session_service.get_session(app_name="plugin_demo_app", user_id=user_id, session_id=session_id)
    if not session:
        session = await session_service.create_session(app_name="plugin_demo_app", user_id=user_id, session_id=session_id)
    
    # Create user message content
    user_content = types.Content(role='user', parts=[types.Part(text=message)])
    
    # Run agent and collect response - plugin callbacks will fire automatically
    response_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=user_content):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_text += part.text
    return response_text if response_text else "No response received from agent."

# ============================================================================
# MAIN EXECUTION
# ============================================================================
if __name__ == "__main__":
    # Test the plugin functionality
    asyncio.run(run_agent("what is 2 + 2?"))
