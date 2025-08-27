from agents import Agent, Runner, function_tool

# Define a specialized research agent
research_agent = Agent(
    name="Research Specialist",
    instructions="""
    You are a research specialist. Provide detailed, well-researched information
    on any topic with proper analysis and insights.
    """
)

# Define a writing agent
writing_agent = Agent(
    name="Writing Specialist", 
    instructions="""
    You are a professional writer. Take research information and create
    well-structured, engaging content with proper formatting.
    """
)

@function_tool
async def run_research_agent(topic: str) -> str:
    """Research a topic using the specialized research agent with custom configuration"""
    
    result = await Runner.run(
        research_agent,
        input=f"Research this topic thoroughly: {topic}",
        max_turns=3  # Custom configuration
    )
    
    return str(result.final_output)

@function_tool  
async def run_writing_agent(content: str, style: str = "professional") -> str:
    """Transform content using the specialized writing agent with custom style"""
    
    prompt = f"Rewrite this content in a {style} style: {content}"
    
    result = await Runner.run(
        writing_agent,
        input=prompt,
        max_turns=2  # Custom configuration
    )
    
    return str(result.final_output)

# Create orchestrator with custom agent tools
advanced_orchestrator = Agent(
    name="Content Creation Orchestrator",
    instructions="""
    You are a content creation orchestrator that combines research and writing expertise.
    
    You have access to:
    - Research agent: For in-depth topic research
    - Writing agent: For professional content creation
    
    When users request content:
    1. First use the research agent to gather information
    2. Then use the writing agent to create polished content
    3. You can specify writing styles (professional, casual, academic, etc.)
    
    Coordinate both agents to create comprehensive, well-written content.
    """,
    tools=[run_research_agent, run_writing_agent]
)
