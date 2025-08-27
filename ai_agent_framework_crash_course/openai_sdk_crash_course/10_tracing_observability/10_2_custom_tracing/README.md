# Custom Tracing

Demonstrates advanced tracing patterns including custom traces, spans, and workflow organization for complex multi-agent systems.

## 🎯 What This Demonstrates

- **Custom Traces**: Grouping multiple agent runs in single workflows
- **Custom Spans**: Adding business logic monitoring points
- **Hierarchical Tracking**: Nested spans for complex operations
- **Trace Metadata**: Organizing traces with groups and metadata

## 🚀 Quick Start

1. **Install OpenAI Agents SDK**:
   ```bash
   pip install openai-agents
   ```

2. **Set up environment**:
   ```bash
   cp ../env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Run the agent**:
   ```python
   import asyncio
   from agent import main
   
   # Test custom tracing patterns
   asyncio.run(main())
   ```

## 💡 Key Concepts

- **trace() Context Manager**: Creating custom workflow groupings
- **custom_span()**: Adding business logic monitoring
- **Trace Metadata**: Workflow naming and organization
- **Hierarchical Structure**: Nested spans for complex operations

## 🧪 Custom Tracing Patterns

### Multi-Step Workflow Traces
```python
with trace("Research and Analysis Workflow") as workflow_trace:
    # Step 1: Research
    research_result = await Runner.run(research_agent, "Research AI in healthcare")
    
    # Step 2: Analysis  
    analysis_result = await Runner.run(analysis_agent, f"Analyze: {research_result.final_output}")
    
    # Step 3: Summary
    summary_result = await Runner.run(analysis_agent, f"Summarize: {analysis_result.final_output}")
```

### Custom Business Logic Spans
```python
with trace("Document Processing Workflow") as doc_trace:
    
    with custom_span("Data Preparation") as prep_span:
        # Your business logic here
        data = prepare_data()
        prep_span.add_event("Data loaded", {"records": 100})
        prep_span.add_event("Data validated", {"errors": 0})
        
    with custom_span("AI Processing") as ai_span:
        result = await Runner.run(agent, "Process the data")
        ai_span.add_event("Processing complete", {
            "output_length": len(result.final_output)
        })
```

### Hierarchical Spans
```python
with trace("E-commerce Order Processing") as order_trace:
    
    with custom_span("Order Validation") as validation_span:
        
        # Nested span for inventory check
        with custom_span("Inventory Check") as inventory_span:
            inventory_span.add_event("Stock verified", {"available": True})
        
        # Nested span for payment validation
        with custom_span("Payment Validation") as payment_span:
            payment_span.add_event("Payment authorized", {"amount": 99.99})
```

## 💻 Advanced Features

### Trace Metadata and Grouping
```python
conversation_id = "conv_12345"

# First interaction in conversation
with trace(
    "Customer Support - Initial Inquiry",
    group_id=conversation_id,
    metadata={"customer_id": "cust_789", "priority": "high"}
) as trace1:
    result1 = await Runner.run(support_agent, "How do I reset my password?")

# Follow-up interaction in same conversation
with trace(
    "Customer Support - Follow-up",
    group_id=conversation_id,
    metadata={"customer_id": "cust_789", "interaction": 2}
) as trace2:
    result2 = await Runner.run(support_agent, f"Based on this context: {result1.final_output}")
```

### Event Tracking
```python
with custom_span("Business Process") as span:
    span.add_event("Process started", {"timestamp": datetime.now()})
    # Business logic here
    span.add_event("Milestone reached", {"progress": "50%"})
    # More business logic
    span.add_event("Process completed", {"status": "success"})
```

## 🔍 Benefits of Custom Tracing

### Workflow Organization
- **Group Related Operations**: Multiple agent runs in single trace
- **Business Logic Visibility**: Monitor custom processes alongside AI
- **Performance Analysis**: Track end-to-end workflow performance

### Production Monitoring
- **Error Correlation**: Link failures across multiple components
- **Performance Optimization**: Identify bottlenecks in complex workflows
- **User Journey Tracking**: Follow conversations across interactions

### Debugging and Analysis
- **Complex Workflow Understanding**: Visualize multi-step processes
- **Context Preservation**: Maintain relationship between related operations
- **Metadata Organization**: Filter and search traces by business criteria

## 🔗 Next Steps

- [Default Tracing](../10_1_default_tracing/README.md) - Basic tracing fundamentals
- [Tutorial 11: Production Patterns](../../11_production_patterns/README.md) - Real-world deployment
