import logging
from typing import Dict, Any, List, Union
from dataclasses import dataclass
import base64
import requests
import os

# Google ADK imports
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner


# Define constants for the agent configuration
MODEL_ID = "gemini-2.5-flash"
APP_NAME = "ai_consultant_agent"
USER_ID = "consultant-user"
SESSION_ID = "consultant-session"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_bytes_for_json(obj: Any) -> Any:
    """
    Recursively convert bytes objects to strings to ensure JSON serializability.
    
    Args:
        obj: Any object that might contain bytes
        
    Returns:
        Object with all bytes converted to strings
    """
    if isinstance(obj, bytes):
        try:
            # Try to decode as UTF-8 text first
            return obj.decode('utf-8')
        except UnicodeDecodeError:
            # If not valid UTF-8, encode as base64 string
            return base64.b64encode(obj).decode('ascii')
    elif isinstance(obj, dict):
        return {key: sanitize_bytes_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_bytes_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_bytes_for_json(item) for item in obj)
    else:
        return obj

def safe_tool_wrapper(tool_func):
    """
    Wrapper to ensure tool functions never return bytes objects.
    
    Args:
        tool_func: The original tool function
        
    Returns:
        Wrapped function that sanitizes output
    """
    def wrapped_tool(*args, **kwargs):
        try:
            result = tool_func(*args, **kwargs)
            return sanitize_bytes_for_json(result)
        except Exception as e:
            logger.error(f"Error in tool {tool_func.__name__}: {e}")
            return {
                "error": f"Tool execution failed: {str(e)}",
                "tool": tool_func.__name__,
                "status": "error"
            }
    
    # Preserve function metadata
    wrapped_tool.__name__ = tool_func.__name__
    wrapped_tool.__doc__ = tool_func.__doc__
    return wrapped_tool

@dataclass
class MarketInsight:
    """Structure for market research insights"""
    category: str
    finding: str
    confidence: float
    source: str

def analyze_market_data(research_query: str, industry: str = "") -> Dict[str, Any]:
    """
    Analyze market data and generate insights
    
    Args:
        research_query: The business query to analyze
        industry: Optional industry context
        
    Returns:
        Market analysis insights and recommendations
    """
    # Simulate market analysis - in real implementation this would process actual search results
    insights = []
    
    if "startup" in research_query.lower() or "launch" in research_query.lower():
        insights.extend([
            MarketInsight("Market Opportunity", "Growing market with moderate competition", 0.8, "Market Research"),
            MarketInsight("Risk Assessment", "Standard startup risks apply - funding, competition", 0.7, "Analysis"),
            MarketInsight("Recommendation", "Conduct MVP testing before full launch", 0.9, "Strategic Planning")
        ])
    
    if "saas" in research_query.lower() or "software" in research_query.lower():
        insights.extend([
            MarketInsight("Technology Trend", "Cloud-based solutions gaining adoption", 0.9, "Tech Analysis"),
            MarketInsight("Customer Behavior", "Businesses prefer subscription models", 0.8, "Market Study")
        ])
    
    if industry:
        insights.append(
            MarketInsight("Industry Specific", f"{industry} sector shows growth potential", 0.7, "Industry Report")
        )
    
    return {
        "query": research_query,
        "industry": industry,
        "insights": [
            {
                "category": insight.category,
                "finding": insight.finding,
                "confidence": insight.confidence,
                "source": insight.source
            }
            for insight in insights
        ],
        "summary": f"Analysis completed for: {research_query}",
        "total_insights": len(insights)
    }

def generate_strategic_recommendations(analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate strategic business recommendations based on analysis
    
    Args:
        analysis_data: Market analysis results
        
    Returns:
        List of strategic recommendations
    """
    recommendations = []
    
    # Generate recommendations based on insights
    insights = analysis_data.get("insights", [])
    
    if any("startup" in insight["finding"].lower() for insight in insights):
        recommendations.append({
            "category": "Market Entry Strategy",
            "priority": "High",
            "recommendation": "Implement phased market entry with MVP testing",
            "rationale": "Reduces risk and validates market fit before major investment",
            "timeline": "3-6 months",
            "action_items": [
                "Develop minimum viable product",
                "Identify target customer segment",
                "Conduct market validation tests"
            ]
        })
    
    if any("saas" in insight["finding"].lower() for insight in insights):
        recommendations.append({
            "category": "Technology Strategy", 
            "priority": "Medium",
            "recommendation": "Focus on cloud-native architecture and subscription model",
            "rationale": "Aligns with market trends and customer preferences",
            "timeline": "2-4 months",
            "action_items": [
                "Design scalable cloud infrastructure",
                "Implement subscription billing system",
                "Plan for multi-tenant architecture"
            ]
        })
    
    # Always include risk management
    recommendations.append({
        "category": "Risk Management",
        "priority": "High", 
        "recommendation": "Establish comprehensive risk monitoring framework",
        "rationale": "Proactive risk management is essential for business success",
        "timeline": "1-2 months",
        "action_items": [
            "Identify key business risks",
            "Develop mitigation strategies",
            "Implement monitoring systems"
        ]
    })
    
    return recommendations

def perplexity_search(query: str, system_prompt: str = "Be precise and concise. Focus on business insights and market data.") -> Dict[str, Any]:
    """Search the web using Perplexity AI for real-time information and insights."""
    try:
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if not api_key:
            return {"error": "Perplexity API key not found. Please set PERPLEXITY_API_KEY environment variable.", "query": query, "status": "error"}
        
        response = requests.post("https://api.perplexity.ai/chat/completions", 
            json={"model": "sonar", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]},
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if "choices" in result and result["choices"]:
            return {"query": query, "content": result["choices"][0]["message"]["content"], "citations": result.get("citations", []), 
                   "search_results": result.get("search_results", []), "status": "success", "source": "Perplexity AI", 
                   "model": result.get("model", "sonar"), "usage": result.get("usage", {}), "response_id": result.get("id", ""), "created": result.get("created", 0)}
        return {"error": "No response content found", "query": query, "status": "error", "raw_response": result}
    except Exception as e:
        return {"error": f"Error: {str(e)}", "query": query, "status": "error"}

# Define the consultant tools with safety wrappers
consultant_tools = [
    safe_tool_wrapper(analyze_market_data),
    safe_tool_wrapper(generate_strategic_recommendations),
    safe_tool_wrapper(perplexity_search)
]

INSTRUCTIONS = """You are a senior AI business consultant specializing in market analysis and strategic planning.

Your expertise includes:
- Business strategy development and recommendations
- Risk assessment and mitigation planning
- Implementation planning with timelines
- Market analysis using your knowledge and available tools
- Real-time web research using Perplexity AI search capabilities

When consulting with clients:
1. Use Perplexity search to gather current market data, competitor information, and industry trends from the web
2. Use the market analysis tool to process business queries and generate insights
3. Use the strategic recommendations tool to create actionable business advice
4. Provide clear, specific recommendations with implementation timelines
5. Focus on practical solutions that drive measurable business outcomes

**Core Responsibilities:**
- Conduct real-time web research using Perplexity AI for current market data and trends
- Analyze competitive landscapes and market opportunities using search results and your knowledge
- Provide strategic guidance with clear action items based on up-to-date information
- Assess risks and suggest mitigation strategies using current market conditions
- Create implementation roadmaps with realistic timelines
- Generate comprehensive business insights combining web research with analysis tools

**Critical Rules:**
- Always search for current market data, trends, and competitor information when relevant using Perplexity search
- Base recommendations on sound business principles, current market insights, and real-time web data
- Provide specific, actionable advice rather than generic guidance
- Include timelines and success metrics in recommendations
- Prioritize recommendations by business impact and feasibility
- Use Perplexity search to validate assumptions and gather supporting evidence with citations
- Combine search results with your analysis tools for comprehensive consultation

**Search Strategy:**
- Use Perplexity search for competitor analysis, market size, industry trends, and regulatory changes
- Look up recent news, funding rounds, and market developments in relevant sectors
- Verify market assumptions with current web data before making recommendations
- Research best practices and case studies from similar businesses
- Always include citations and sources when referencing search results

Always maintain a professional, analytical approach while being results-oriented.
Use all available tools including Perplexity search to provide comprehensive, well-researched consultation backed by current web data and citations."""

# Define the agent instance
root_agent = LlmAgent(
    model=MODEL_ID,
    name=APP_NAME,
    description="An AI business consultant that provides market research, strategic analysis, and actionable recommendations.",
    instruction=INSTRUCTIONS,
    tools=consultant_tools,
    output_key="consultation_response"
)

# Setup Runner and Session Service
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service
)

if __name__ == "__main__":
    print("🤖 AI Consultant Agent with Google ADK")
    print("=====================================")
    print()
    print("This agent provides comprehensive business consultation including:")
    print("• Market research and analysis")
    print("• Strategic recommendations") 
    print("• Implementation planning")
    print("• Risk assessment")
    print()
    print("To use this agent:")
    print("1. Run: adk web .")
    print("2. Open the web interface")
    print("3. Select 'AI Business Consultant' agent")
    print("4. Start your consultation")
    print()
    print("Example queries:")
    print('• "I want to launch a SaaS startup for small businesses"')
    print('• "Should I expand my retail business to e-commerce?"')
    print('• "What are the market opportunities in the healthcare tech space?"')
    print()
    print("📊 Use the Eval tab in ADK web to save and evaluate consultation sessions!")
    print()
    print(f"✅ Agent '{APP_NAME}' initialized successfully!")
    print(f"   Model: {MODEL_ID}")
    print(f"   Tools: {len(consultant_tools)} available")
    print(f"   Session Service: {type(session_service).__name__}")
    print(f"   Runner: {type(runner).__name__}") 