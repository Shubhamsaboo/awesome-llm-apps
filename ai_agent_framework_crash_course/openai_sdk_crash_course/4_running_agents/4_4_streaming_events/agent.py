from agents import Agent, Runner
import asyncio
import time

# Create agents for demonstrating streaming events
root_agent = Agent(
    name="Streaming Demo Agent",
    instructions="""
    You are a helpful assistant that demonstrates streaming capabilities.
    
    When asked to write long content, be comprehensive and detailed.
    When asked technical questions, provide thorough explanations.
    """
)

# Example 1: Basic streaming with event processing
async def basic_streaming_example():
    """Demonstrates basic streaming event handling"""
    
    print("=== Basic Streaming Events ===")
    print("Requesting a detailed explanation...")
    
    full_response = ""
    start_time = time.time()
    
    # Use run_streamed to get real-time events
    async for event in Runner.run_streamed(
        root_agent, 
        "Write a comprehensive explanation of how machine learning works, including examples."
    ):
        # Process different types of streaming events
        if hasattr(event, 'content') and event.content:
            # This is a text content event
            full_response += event.content
            print(event.content, end='', flush=True)
        
        if hasattr(event, 'type'):
            # Handle different event types
            if event.type == "response_start":
                print(f"\n[EVENT] Response started")
            elif event.type == "response_complete":
                print(f"\n[EVENT] Response completed")
                
    elapsed_time = time.time() - start_time
    print(f"\n\nStreaming completed in {elapsed_time:.2f} seconds")
    print(f"Total response length: {len(full_response)} characters")
    
    return full_response

# Example 2: Advanced streaming with RunResultStreaming
async def advanced_streaming_example():
    """Shows how to work with RunResultStreaming object"""
    
    print("\n=== Advanced Streaming with RunResultStreaming ===")
    print("Generating a long story with progress tracking...")
    
    # Track streaming progress
    events_count = 0
    chunks_received = []
    
    # Get the streaming result generator
    streaming_result = Runner.run_streamed(
        root_agent,
        "Write a creative short story about a robot who discovers emotions. Make it at least 500 words."
    )
    
    print("Processing streaming events:")
    
    async for event in streaming_result:
        events_count += 1
        
        # Collect content chunks
        if hasattr(event, 'content') and event.content:
            chunks_received.append(event.content)
            # Show progress every 10 chunks
            if len(chunks_received) % 10 == 0:
                print(f"\n[PROGRESS] Received {len(chunks_received)} chunks...")
            print(event.content, end='', flush=True)
        
        # Handle specific event types
        if hasattr(event, 'type'):
            if event.type == "tool_call_start":
                print(f"\n[EVENT] Tool call started")
            elif event.type == "tool_call_complete":
                print(f"\n[EVENT] Tool call completed")
    
    print(f"\n\nStreaming summary:")
    print(f"- Total events processed: {events_count}")
    print(f"- Content chunks received: {len(chunks_received)}")
    print(f"- Final story length: {sum(len(chunk) for chunk in chunks_received)} characters")
    
    # Access the final result
    final_result = "".join(chunks_received)
    return final_result

# Example 3: Streaming with custom processing
async def custom_streaming_processing():
    """Demonstrates custom streaming event processing"""
    
    print("\n=== Custom Streaming Processing ===")
    print("Analyzing streaming patterns...")
    
    # Custom streaming analytics
    analytics = {
        "words_per_second": [],
        "chunk_sizes": [],
        "response_time": None,
        "total_words": 0
    }
    
    start_time = time.time()
    last_update = start_time
    current_content = ""
    
    async for event in Runner.run_streamed(
        root_agent,
        "Explain the benefits and challenges of renewable energy in detail."
    ):
        current_time = time.time()
        
        if hasattr(event, 'content') and event.content:
            # Track chunk size
            chunk_size = len(event.content)
            analytics["chunk_sizes"].append(chunk_size)
            
            # Update content
            current_content += event.content
            
            # Calculate words per second every few chunks
            if len(analytics["chunk_sizes"]) % 5 == 0:
                time_diff = current_time - last_update
                if time_diff > 0:
                    words_in_chunk = len(event.content.split())
                    wps = words_in_chunk / time_diff
                    analytics["words_per_second"].append(wps)
                    last_update = current_time
            
            print(event.content, end='', flush=True)
    
    # Final analytics
    analytics["response_time"] = time.time() - start_time
    analytics["total_words"] = len(current_content.split())
    
    print(f"\n\nStreaming Analytics:")
    print(f"- Total response time: {analytics['response_time']:.2f} seconds")
    print(f"- Total words: {analytics['total_words']}")
    print(f"- Average chunk size: {sum(analytics['chunk_sizes'])/len(analytics['chunk_sizes']):.1f} chars")
    
    if analytics["words_per_second"]:
        avg_wps = sum(analytics["words_per_second"]) / len(analytics["words_per_second"])
        print(f"- Average words per second: {avg_wps:.1f}")
    
    return analytics

# Example 4: Streaming with error handling
async def streaming_with_error_handling():
    """Shows proper error handling for streaming operations"""
    
    print("\n=== Streaming with Error Handling ===")
    
    try:
        response_parts = []
        
        async for event in Runner.run_streamed(
            root_agent,
            "What are the top 3 programming languages and why?"
        ):
            try:
                if hasattr(event, 'content') and event.content:
                    response_parts.append(event.content)
                    print(event.content, end='', flush=True)
                    
            except Exception as chunk_error:
                print(f"\n[ERROR] Error processing chunk: {chunk_error}")
                continue  # Continue with next chunk
                
        print(f"\n\nStreaming completed successfully!")
        print(f"Collected {len(response_parts)} response parts")
        
        return "".join(response_parts)
        
    except Exception as streaming_error:
        print(f"\n[ERROR] Streaming failed: {streaming_error}")
        return None

# Main execution
async def main():
    print("🚀 OpenAI Agents SDK - Streaming Events")
    print("=" * 60)
    
    await basic_streaming_example()
    await advanced_streaming_example()
    await custom_streaming_processing()
    await streaming_with_error_handling()
    
    print("\n✅ Streaming events tutorial complete!")
    print("Streaming enables real-time response processing for better user experience")

if __name__ == "__main__":
    asyncio.run(main())
