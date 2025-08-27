from agents import Agent, Runner, function_tool
import asyncio

# Define specialized research agent
research_agent = Agent(
    name="Research Specialist",
    instructions="""
    You are a research specialist. Provide detailed, well-researched information
    on any topic with proper analysis and insights. Focus on factual accuracy
    and comprehensive coverage.
    """
)

# Define specialized writing agent
writing_agent = Agent(
    name="Writing Specialist", 
    instructions="""
    You are a professional writer. Take research information and create
    well-structured, engaging content with proper formatting and flow.
    Make content accessible and compelling for readers.
    """
)

# Define editing agent
editing_agent = Agent(
    name="Editing Specialist",
    instructions="""
    You are a professional editor. Review written content for:
    - Grammar and spelling errors
    - Clarity and readability
    - Structure and flow
    - Consistency and tone
    
    Provide the improved version of the content.
    """
)

# Create function tools from agents
@function_tool
async def research_tool(topic: str) -> str:
    """Research a topic using the specialized research agent with custom configuration"""
    
    result = await Runner.run(
        research_agent,
        input=f"Research this topic thoroughly and provide key insights: {topic}",
        max_turns=3  # Allow deeper research
    )
    
    return str(result.final_output)

@function_tool  
async def writing_tool(content: str, style: str = "professional") -> str:
    """Transform content using the specialized writing agent with custom style"""
    
    prompt = f"Write engaging {style} content based on this research: {content}"
    
    result = await Runner.run(
        writing_agent,
        input=prompt,
        max_turns=2
    )
    
    return str(result.final_output)

@function_tool
async def editing_tool(content: str) -> str:
    """Edit and improve content using the specialized editing agent"""
    
    result = await Runner.run(
        editing_agent,
        input=f"Edit and improve this content for clarity, grammar, and engagement: {content}"
    )
    
    return str(result.final_output)

# Create orchestrator agent that uses other agents as tools
content_orchestrator = Agent(
    name="Content Creation Orchestrator",
    instructions="""
    You are a content creation orchestrator that coordinates research, writing, and editing.
    
    You have access to:
    - research_tool: For in-depth topic research and insights
    - writing_tool: For professional content creation (specify style: professional, casual, academic, etc.)
    - editing_tool: For content review and improvement
    
    When users request content:
    1. First use research_tool to gather comprehensive information
    2. Then use writing_tool to create well-structured content
    3. Finally use editing_tool to polish and improve the final piece
    
    Coordinate all three tools to create high-quality, well-researched content.
    """,
    tools=[research_tool, writing_tool, editing_tool]
)

# Example 1: Basic content creation workflow
async def basic_content_workflow():
    """Demonstrates basic orchestration using agents as tools"""
    
    print("=== Basic Content Creation Workflow ===")
    
    result = await Runner.run(
        content_orchestrator,
        """Create a comprehensive article about the benefits of renewable energy. 
        I need it to be professional and well-researched, suitable for a business audience."""
    )
    
    print(f"Final article: {result.final_output}")
    
    return result

# Example 2: Custom workflow with specific requirements
async def custom_workflow_example():
    """Shows orchestrator handling specific workflow requirements"""
    
    print("\n=== Custom Workflow with Specific Requirements ===")
    
    result = await Runner.run(
        content_orchestrator,
        """I need content about artificial intelligence in healthcare for a technical blog.
        Make sure to:
        1. Research current AI applications in medical diagnosis
        2. Write in an accessible but technical style
        3. Include both benefits and challenges
        4. Keep it under 500 words
        
        Please go through the full research -> write -> edit process."""
    )
    
    print(f"Technical blog post: {result.final_output}")
    
    return result

# Example 3: Comparison with direct agent orchestration
async def direct_orchestration_comparison():
    """Compares agents-as-tools vs direct orchestration"""
    
    print("\n=== Direct Orchestration (Manual) ===")
    topic = "The future of remote work"
    
    # Manual orchestration - calling agents directly
    print("Step 1: Research...")
    research_result = await Runner.run(
        research_agent,
        f"Research trends and predictions about: {topic}"
    )
    
    print("Step 2: Writing...")
    writing_result = await Runner.run(
        writing_agent,
        f"Write a professional article based on this research: {research_result.final_output}"
    )
    
    print("Step 3: Editing...")
    editing_result = await Runner.run(
        editing_agent,
        f"Edit and improve this article: {writing_result.final_output}"
    )
    
    print(f"Manual orchestration result: {editing_result.final_output}")
    
    print("\n=== Agents-as-Tools Orchestration (Automatic) ===")
    
    # Automatic orchestration using orchestrator agent
    orchestrated_result = await Runner.run(
        content_orchestrator,
        f"Create a professional article about: {topic}. Go through research, writing, and editing."
    )
    
    print(f"Automatic orchestration result: {orchestrated_result.final_output}")
    
    return editing_result, orchestrated_result

# Example 4: Advanced orchestrator with conditional logic
async def advanced_orchestrator_example():
    """Shows more sophisticated orchestration logic"""
    
    print("\n=== Advanced Orchestrator with Conditional Logic ===")
    
    # Create advanced orchestrator with conditional workflows
    advanced_orchestrator = Agent(
        name="Advanced Content Orchestrator",
        instructions="""
        You are an intelligent content orchestrator that adapts workflows based on requirements.
        
        Available tools:
        - research_tool: For topic research
        - writing_tool: For content creation (styles: professional, casual, academic, creative)
        - editing_tool: For content improvement
        
        Workflow decisions:
        - For complex/technical topics: Do extra research first
        - For creative content: Use creative writing style
        - For short content: Skip detailed research
        - For business content: Always edit for professionalism
        - Always explain your workflow decisions
        
        Adapt your approach based on the specific request.
        """,
        tools=[research_tool, writing_tool, editing_tool]
    )
    
    # Test with different content types
    requests = [
        "Write a quick social media post about coffee benefits",
        "Create a detailed technical whitepaper on blockchain security",
        "Write a creative story about a robot learning to paint"
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"\nRequest {i}: {request}")
        result = await Runner.run(advanced_orchestrator, request)
        print(f"Result: {result.final_output}")
        print("-" * 50)
    
    return requests

# Main execution
async def main():
    print("🔧 OpenAI Agents SDK - Agents as Tools Orchestration")
    print("=" * 60)
    
    await basic_content_workflow()
    await custom_workflow_example()
    await direct_orchestration_comparison()
    await advanced_orchestrator_example()
    
    print("\n✅ Agents as tools tutorial complete!")
    print("Agents as tools enable sophisticated workflow orchestration with intelligent coordination")

if __name__ == "__main__":
    asyncio.run(main())
