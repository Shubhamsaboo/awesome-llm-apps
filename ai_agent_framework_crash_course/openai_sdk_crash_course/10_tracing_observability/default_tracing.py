from agents import Agent, Runner
import asyncio

# Create agent for tracing demonstrations
root_agent = Agent(
    name="Tracing Demo Agent",
    instructions="""
    You are a helpful assistant demonstrating tracing capabilities.
    
    Respond concisely but perform actions that generate interesting trace data.
    """
)

# Example 1: Basic automatic tracing
async def basic_automatic_tracing():
    """Demonstrates default tracing that happens automatically"""
    
    print("=== Basic Automatic Tracing ===")
    print("Tracing is enabled by default - no setup required!")
    print("View traces at: https://platform.openai.com/traces")
    
    # Single agent run - creates one trace automatically
    result = await Runner.run(
        root_agent,
        "Explain what tracing means in software development."
    )
    
    print(f"Response: {result.final_output}")
    print(f"Trace ID: {result.run_id}")  # Each run gets a unique ID
    print("Check the OpenAI Traces dashboard to see this execution!")
    
    return result

# Example 2: Multiple runs create separate traces
async def multiple_separate_traces():
    """Shows how separate runs create individual traces"""
    
    print("\n=== Multiple Separate Traces ===")
    print("Each Runner.run() call creates a separate trace")
    
    # First trace
    result1 = await Runner.run(
        root_agent,
        "What are the benefits of monitoring software?"
    )
    print(f"Trace 1 ID: {result1.run_id}")
    
    # Second trace (separate from first)
    result2 = await Runner.run(
        root_agent,
        "How do you debug performance issues?"
    )
    print(f"Trace 2 ID: {result2.run_id}")
    
    print("Two separate traces created - each with its own workflow view")
    
    return result1, result2

# Example 3: Understanding trace structure
async def trace_structure_demo():
    """Demonstrates what gets captured in traces"""
    
    print("\n=== Trace Structure Demo ===")
    print("Each trace automatically captures:")
    print("• LLM generations (input/output)")
    print("• Execution time and performance")
    print("• Any errors or exceptions")
    print("• Metadata and context")
    
    # Create a run that will generate rich trace data
    result = await Runner.run(
        root_agent,
        "List 3 key components of observability and explain each briefly."
    )
    
    print(f"Response generated: {len(result.final_output)} characters")
    print(f"Trace contains rich data for run: {result.run_id}")
    
    # Show what type of information is captured
    print("\nIn the trace dashboard, you'll see:")
    print("1. Workflow timeline with duration")
    print("2. LLM generation details (model, tokens, etc.)")
    print("3. Input/output content and metadata")
    print("4. Performance metrics and execution flow")
    
    return result

# Example 4: Tracing configuration options
async def tracing_configuration():
    """Shows how to configure tracing behavior"""
    
    print("\n=== Tracing Configuration ===")
    
    # Example of disabling tracing for specific run
    from agents.run import RunConfig
    
    print("Running with tracing disabled...")
    result_no_trace = await Runner.run(
        root_agent,
        "This run won't be traced.",
        run_config=RunConfig(tracing_disabled=True)
    )
    
    print(f"Run completed without tracing: {result_no_trace.run_id}")
    print("(This run won't appear in traces dashboard)")
    
    print("\nRunning with normal tracing...")
    result_with_trace = await Runner.run(
        root_agent,
        "This run will be traced normally."
    )
    
    print(f"Run completed with tracing: {result_with_trace.run_id}")
    print("(This run will appear in traces dashboard)")
    
    return result_no_trace, result_with_trace

# Main execution
async def main():
    print("🔍 OpenAI Agents SDK - Tracing Basics")
    print("=" * 50)
    
    await basic_automatic_tracing()
    await multiple_separate_traces()
    await trace_structure_demo()
    await tracing_configuration()
    
    print("\n✅ Tracing tutorial complete!")
    print("Visit https://platform.openai.com/traces to explore your traces")

if __name__ == "__main__":
    asyncio.run(main())
