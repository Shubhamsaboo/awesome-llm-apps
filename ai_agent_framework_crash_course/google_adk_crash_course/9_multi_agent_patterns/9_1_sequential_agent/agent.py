import os
import asyncio
import inspect
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Load environment variables
load_dotenv()

# --- Search Agent (Wrapped as AgentTool) ---
search_agent = LlmAgent(
    name="search_agent",
    model="gemini-3-flash-preview",
    description="Conducts web search for current market information and competitive analysis",
    instruction=(
        "You are a web search specialist. When given a business topic:\n"
        "1. Use web search to find current market information\n"
        "2. Identify key competitors and their market position\n"
        "3. Gather recent industry trends and market data\n"
        "4. Find market size estimates and growth projections\n"
        "5. Provide comprehensive, up-to-date market analysis\n\n"
        "Always use web search to get the most current information available."
    ),
    tools=[google_search]
)

# --- Simple Sub-agents ---
market_researcher = LlmAgent(
    name="market_researcher",
    model="gemini-3-flash-preview",
    description="Conducts market research and competitive analysis using search capabilities",
    instruction=(
        "You are a market research specialist. Given a business topic:\n"
        "1. Use the search_agent to gather current market information\n"
        "2. Identify key competitors and their market position\n"
        "3. Analyze current market trends and opportunities\n"
        "4. Provide industry insights and market size estimates\n"
        "5. Synthesize search results into comprehensive market analysis\n\n"
        "Provide a comprehensive analysis in clear, structured format based on current web research."
    ),
    tools=[AgentTool(search_agent)]
)

swot_analyzer = LlmAgent(
    name="swot_analyzer",
    model="gemini-3-flash-preview",
    description="Performs SWOT analysis based on market research",
    instruction=(
        "You are a strategic analyst. Given market research findings:\n"
        "1. Identify internal strengths and competitive advantages\n"
        "2. Assess internal weaknesses and limitations\n"
        "3. Identify external opportunities in the market\n"
        "4. Evaluate external threats and challenges\n\n"
        "Provide a clear SWOT analysis with actionable insights."
    )
)

strategy_formulator = LlmAgent(
    name="strategy_formulator",
    model="gemini-3-flash-preview",
    description="Develops strategic objectives and action plans",
    instruction=(
        "You are a strategic planner. Given SWOT analysis results:\n"
        "1. Define 3-5 key strategic objectives\n"
        "2. Create specific action items for each objective\n"
        "3. Recommend realistic timeline for implementation\n"
        "4. Define success metrics and KPIs to track\n\n"
        "Provide a clear strategic plan with actionable steps."
    )
)

implementation_planner = LlmAgent(
    name="implementation_planner",
    model="gemini-3-flash-preview",
    description="Creates detailed implementation roadmap",
    instruction=(
        "You are an implementation specialist. Given the strategy plan:\n"
        "1. Identify required resources (human, financial, technical)\n"
        "2. Define key milestones and checkpoints\n"
        "3. Develop risk mitigation strategies\n"
        "4. Provide final recommendations with confidence level\n\n"
        "Create a practical implementation roadmap."
    )
)

# --- Sequential Agent (Pure Sequential Pattern) ---
business_intelligence_team = SequentialAgent(
    name="business_intelligence_team",
    description="Sequentially processes business intelligence through research, analysis, strategy, and planning",
    sub_agents=[
        market_researcher,      # Step 1: Market research (with search capabilities)
        swot_analyzer,          # Step 2: SWOT analysis
        strategy_formulator,    # Step 3: Strategy development
        implementation_planner  # Step 4: Implementation planning
    ]
)

# --- Runner Setup for Execution ---
session_service = InMemorySessionService()
runner = Runner(
    agent=business_intelligence_team,
    app_name="business_intelligence",
    session_service=session_service
)

# --- Simple Execution Function ---
async def analyze_business_intelligence(user_id: str, business_topic: str) -> str:
    """Process business intelligence through the sequential pipeline"""
    session_id = f"bi_session_{user_id}"
    
    # Support both sync and async session service
    async def _maybe_await(value):
        return await value if inspect.isawaitable(value) else value

    session = await _maybe_await(session_service.get_session(
        app_name="business_intelligence",
        user_id=user_id,
        session_id=session_id
    ))
    if not session:
        session = await _maybe_await(session_service.create_session(
            app_name="business_intelligence",
            user_id=user_id,
            session_id=session_id,
            state={"business_topic": business_topic, "conversation_history": []}
        ))
    
    # Create user content
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=f"Please analyze this business topic: {business_topic}")]
    )
    
    # Run the sequential pipeline (support async or sync stream)
    response_text = ""
    stream = runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_content
    )
    if inspect.isasyncgen(stream):
        async for event in stream:
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
    else:
        for event in stream:
            if getattr(event, "is_final_response", lambda: False)():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
    
    return response_text
