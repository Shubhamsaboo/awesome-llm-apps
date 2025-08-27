from agents import Agent, Runner, trace, custom_span
import asyncio

# Create agents for custom tracing demonstrations
research_agent = Agent(
    name="Research Agent",
    instructions="You are a research assistant. Provide concise, factual information."
)

analysis_agent = Agent(
    name="Analysis Agent", 
    instructions="You analyze information and provide insights."
)

# Example 1: Custom trace for multi-step workflow
async def multi_step_workflow_trace():
    """Demonstrates grouping multiple agent runs in a single trace"""
    
    print("=== Multi-Step Workflow Trace ===")
    
    # Create custom trace that groups multiple operations
    with trace("Research and Analysis Workflow") as workflow_trace:
        print("Starting research phase...")
        
        # Step 1: Research
        research_result = await Runner.run(
            research_agent,
            "What are the key benefits of artificial intelligence in healthcare?"
        )
        print(f"Research complete: {len(research_result.final_output)} characters")
        
        # Step 2: Analysis  
        analysis_result = await Runner.run(
            analysis_agent,
            f"Analyze this research and identify the top 3 benefits: {research_result.final_output}"
        )
        print(f"Analysis complete: {len(analysis_result.final_output)} characters")
        
        # Step 3: Summary
        summary_result = await Runner.run(
            analysis_agent,
            f"Create a brief executive summary of these findings: {analysis_result.final_output}"
        )
        print(f"Summary complete: {len(summary_result.final_output)} characters")
    
    print(f"Workflow trace created: {workflow_trace.trace_id}")
    print("All three agent runs are grouped in a single trace!")
    
    return research_result, analysis_result, summary_result

# Example 2: Custom spans for business logic
async def custom_spans_demo():
    """Shows how to add custom spans for monitoring business logic"""
    
    print("\n=== Custom Spans Demo ===")
    
    with trace("Document Processing Workflow") as doc_trace:
        
        # Custom span for data preparation
        with custom_span("Data Preparation") as prep_span:
            print("Preparing data...")
            # Simulate data processing
            await asyncio.sleep(0.1)
            prep_span.add_event("Data loaded", {"records": 100})
            prep_span.add_event("Data validated", {"errors": 0})
            
        # Custom span for agent processing
        with custom_span("AI Processing") as ai_span:
            print("Processing with AI...")
            result = await Runner.run(
                research_agent,
                "Summarize the importance of data quality in AI systems."
            )
            ai_span.add_event("Processing complete", {
                "output_length": len(result.final_output),
                "model_used": "gpt-4o"
            })
            
        # Custom span for post-processing
        with custom_span("Post Processing") as post_span:
            print("Post-processing results...")
            await asyncio.sleep(0.1)
            post_span.add_event("Results formatted", {"format": "text"})
            post_span.add_event("Quality check passed", {"score": 0.95})
    
    print(f"Document processing trace: {doc_trace.trace_id}")
    print("Custom spans provide detailed workflow visibility!")
    
    return result

# Example 3: Hierarchical spans
async def hierarchical_spans():
    """Demonstrates nested spans for complex workflows"""
    
    print("\n=== Hierarchical Spans ===")
    
    with trace("E-commerce Order Processing") as order_trace:
        
        with custom_span("Order Validation") as validation_span:
            print("Validating order...")
            
            # Nested span for inventory check
            with custom_span("Inventory Check") as inventory_span:
                await asyncio.sleep(0.05)
                inventory_span.add_event("Stock verified", {"available": True})
            
            # Nested span for payment validation
            with custom_span("Payment Validation") as payment_span:
                await asyncio.sleep(0.05)
                payment_span.add_event("Payment authorized", {"amount": 99.99})
            
            validation_span.add_event("Order validated", {"order_id": "ORD-12345"})
        
        with custom_span("AI Recommendation Generation") as rec_span:
            print("Generating recommendations...")
            result = await Runner.run(
                research_agent,
                "What are good complementary products for a wireless headset purchase?"
            )
            rec_span.add_event("Recommendations generated", {
                "count": 3,
                "confidence": 0.89
            })
        
        with custom_span("Order Completion") as completion_span:
            print("Completing order...")
            completion_span.add_event("Shipping scheduled", {"tracking": "TRK-789"})
            completion_span.add_event("Email sent", {"type": "confirmation"})
    
    print(f"E-commerce order trace: {order_trace.trace_id}")
    print("Hierarchical spans show detailed operation breakdown!")
    
    return result

# Example 4: Trace metadata and grouping
async def trace_metadata_demo():
    """Shows how to use trace metadata and grouping"""
    
    print("\n=== Trace Metadata and Grouping ===")
    
    # Create multiple traces with shared group ID
    conversation_id = "conv_12345"
    
    # First interaction in conversation
    with trace(
        "Customer Support - Initial Inquiry",
        group_id=conversation_id,
        metadata={"customer_id": "cust_789", "priority": "high"}
    ) as trace1:
        result1 = await Runner.run(
            research_agent,
            "How do I reset my password?"
        )
        trace1.add_event("Initial inquiry processed", {"category": "password_reset"})
    
    # Follow-up interaction in same conversation
    with trace(
        "Customer Support - Follow-up",
        group_id=conversation_id,
        metadata={"customer_id": "cust_789", "interaction": 2}
    ) as trace2:
        result2 = await Runner.run(
            analysis_agent,
            f"Based on this password reset request, what additional security measures should we recommend? Context: {result1.final_output}"
        )
        trace2.add_event("Follow-up completed", {"recommendations_provided": True})
    
    print(f"Conversation traces: {trace1.trace_id}, {trace2.trace_id}")
    print(f"Grouped under conversation: {conversation_id}")
    print("Metadata helps organize and filter traces in dashboard!")
    
    return result1, result2

# Main execution
async def main():
    print("🎨 OpenAI Agents SDK - Custom Tracing")
    print("=" * 50)
    
    await multi_step_workflow_trace()
    await custom_spans_demo()
    await hierarchical_spans()
    await trace_metadata_demo()
    
    print("\n✅ Custom tracing tutorial complete!")
    print("Check the OpenAI Traces dashboard to see your custom workflow visualizations")

if __name__ == "__main__":
    asyncio.run(main())
