from agents import Agent, Runner
import asyncio

# Create a simple agent for demonstrating execution methods
root_agent = Agent(
    name="Execution Demo Agent",
    instructions="""
    You are a helpful assistant demonstrating different execution patterns.
    
    Provide clear, informative responses that help users understand:
    - Synchronous execution (blocking)
    - Asynchronous execution (non-blocking)
    - Streaming execution (real-time)
    
    Keep responses appropriate for the execution method being demonstrated.
    """
)

# Example 1: Synchronous execution
def sync_execution_example():
    """Demonstrates Runner.run_sync() - blocking execution"""
    result = Runner.run_sync(root_agent, "Explain synchronous execution in simple terms")
    return result.final_output

# Example 2: Asynchronous execution  
async def async_execution_example():
    """Demonstrates Runner.run() - non-blocking execution"""
    result = await Runner.run(root_agent, "Explain asynchronous execution benefits")
    return result.final_output

# Example 3: Streaming execution
async def streaming_execution_example():
    """Demonstrates Runner.run_streamed() - real-time streaming"""
    full_response = ""
    
    async for event in Runner.run_streamed(root_agent, "Write a detailed explanation of streaming execution"):
        # Handle streaming events as they arrive
        if hasattr(event, 'content') and event.content:
            full_response += event.content
            print(event.content, end='', flush=True)  # Print in real-time
    
    print()  # New line after streaming
    return full_response
