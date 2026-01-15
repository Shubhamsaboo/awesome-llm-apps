import logging
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass, asdict
import base64
import requests
import os
import time
import hashlib
import json
from functools import lru_cache, wraps
from datetime import datetime, timedelta

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

# Configure logging with more detail
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Simple in-memory cache for API responses
class SimpleCache:
    """Simple cache with TTL support"""
    def __init__(self, ttl_seconds: int = 3600):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                logger.info(f"Cache hit for key: {key[:50]}...")
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        self.cache[key] = (value, time.time())
        logger.info(f"Cached result for key: {key[:50]}...")
    
    def clear(self):
        self.cache.clear()
        logger.info("Cache cleared")


# Global cache instance
api_cache = SimpleCache(ttl_seconds=1800)  # 30 minutes TTL


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function calls on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} retries failed for {func.__name__}: {str(e)}")
            
            # Return error dict instead of raising
            return {
                "error": f"Failed after {max_retries} retries: {str(last_exception)}",
                "function": func.__name__,
                "status": "error"
            }
        return wrapper
    return decorator


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
            return obj.decode('utf-8')
        except UnicodeDecodeError:
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
    
    wrapped_tool.__name__ = tool_func.__name__
    wrapped_tool.__doc__ = tool_func.__doc__
    return wrapped_tool


@dataclass
class MarketInsight:
    """Structure for market research insights with enhanced metadata"""
    category: str
    finding: str
    confidence: float
    source: str
    timestamp: str = None
    priority: str = "medium"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def analyze_market_data(research_query: str, industry: str = "") -> Dict[str, Any]:
    """
    Analyze market data and generate insights with enhanced structure.
    
    Args:
        research_query: The business query to analyze
        industry: Optional industry context
        
    Returns:
        Market analysis insights and recommendations
    """
    insights = []
    
    if "startup" in research_query.lower() or "launch" in research_query.lower():
        insights.extend([
            MarketInsight(
                "Market Opportunity", 
                "Growing market with moderate competition", 
                0.8, 
                "Market Research",
                priority="high"
            ),
            MarketInsight(
                "Risk Assessment", 
                "Standard startup risks apply - funding, competition", 
                0.7, 
                "Analysis",
                priority="high"
            ),
            MarketInsight(
                "Recommendation", 
                "Conduct MVP testing before full launch", 
                0.9, 
                "Strategic Planning",
                priority="critical"
            )
        ])
    
    if "saas" in research_query.lower() or "software" in research_query.lower():
        insights.extend([
            MarketInsight(
                "Technology Trend", 
                "Cloud-based solutions gaining adoption", 
                0.9, 
                "Tech Analysis",
                priority="medium"
            ),
            MarketInsight(
                "Customer Behavior", 
                "Businesses prefer subscription models", 
                0.8, 
                "Market Study",
                priority="medium"
            )
        ])
    
    if industry:
        insights.append(
            MarketInsight(
                "Industry Specific", 
                f"{industry} sector shows growth potential", 
                0.7, 
                "Industry Report",
                priority="medium"
            )
        )
    
    # Enhanced response structure
    return {
        "query": research_query,
        "industry": industry,
        "insights": [insight.to_dict() for insight in insights],
        "summary": f"Analysis completed for: {research_query}",
        "total_insights": len(insights),
        "high_confidence_count": sum(1 for i in insights if i.confidence >= 0.8),
        "critical_items": [i.to_dict() for i in insights if i.priority == "critical"],
        "generated_at": datetime.now().isoformat(),
        "status": "success"
    }


def generate_strategic_recommendations(analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate strategic business recommendations based on analysis with enhanced formatting.
    
    Args:
        analysis_data: Market analysis results
        
    Returns:
        List of strategic recommendations with rich metadata
    """
    recommendations = []
    insights = analysis_data.get("insights", [])
    
    if any("startup" in insight.get("finding", "").lower() for insight in insights):
        recommendations.append({
            "id": "rec_001",
            "category": "Market Entry Strategy",
            "priority": "High",
            "recommendation": "Implement phased market entry with MVP testing",
            "rationale": "Reduces risk and validates market fit before major investment",
            "timeline": "3-6 months",
            "estimated_effort": "High",
            "expected_impact": "Critical",
            "action_items": [
                {"step": 1, "action": "Develop minimum viable product", "duration": "2-3 months"},
                {"step": 2, "action": "Identify target customer segment", "duration": "2-4 weeks"},
                {"step": 3, "action": "Conduct market validation tests", "duration": "4-6 weeks"}
            ],
            "success_metrics": [
                "Customer acquisition rate",
                "Product-market fit score",
                "User feedback quality"
            ],
            "risks": ["Timeline delays", "Budget overruns", "Market changes"],
            "generated_at": datetime.now().isoformat()
        })
    
    if any("saas" in insight.get("finding", "").lower() for insight in insights):
        recommendations.append({
            "id": "rec_002",
            "category": "Technology Strategy", 
            "priority": "Medium",
            "recommendation": "Focus on cloud-native architecture and subscription model",
            "rationale": "Aligns with market trends and customer preferences",
            "timeline": "2-4 months",
            "estimated_effort": "Medium",
            "expected_impact": "High",
            "action_items": [
                {"step": 1, "action": "Design scalable cloud infrastructure", "duration": "3-4 weeks"},
                {"step": 2, "action": "Implement subscription billing system", "duration": "2-3 weeks"},
                {"step": 3, "action": "Plan for multi-tenant architecture", "duration": "3-5 weeks"}
            ],
            "success_metrics": [
                "System uptime (99.9%+)",
                "Subscription conversion rate",
                "Infrastructure cost per user"
            ],
            "risks": ["Technical complexity", "Integration challenges", "Scalability issues"],
            "generated_at": datetime.now().isoformat()
        })
    
    recommendations.append({
        "id": "rec_003",
        "category": "Risk Management",
        "priority": "High", 
        "recommendation": "Establish comprehensive risk monitoring framework",
        "rationale": "Proactive risk management is essential for business success",
        "timeline": "1-2 months",
        "estimated_effort": "Low",
        "expected_impact": "Critical",
        "action_items": [
            {"step": 1, "action": "Identify key business risks", "duration": "1-2 weeks"},
            {"step": 2, "action": "Develop mitigation strategies", "duration": "2-3 weeks"},
            {"step": 3, "action": "Implement monitoring systems", "duration": "2-3 weeks"}
        ],
        "success_metrics": [
            "Risk detection rate",
            "Response time to incidents",
            "Mitigation effectiveness"
        ],
        "risks": ["Incomplete risk coverage", "Resource constraints", "Process compliance"],
        "generated_at": datetime.now().isoformat()
    })
    
    return {
        "recommendations": recommendations,
        "total_count": len(recommendations),
        "high_priority_count": sum(1 for r in recommendations if r["priority"] == "High"),
        "estimated_total_timeline": "3-6 months for full implementation",
        "status": "success",
        "generated_at": datetime.now().isoformat()
    }


@retry_on_failure(max_retries=3, delay=1.0, backoff=2.0)
def perplexity_search(query: str, system_prompt: str = "Be precise and concise. Focus on business insights and market data.") -> Dict[str, Any]:
    """
    Search the web using Perplexity AI with caching and retry logic.
    
    Args:
        query: Search query
        system_prompt: System instructions for the AI
        
    Returns:
        Search results with citations and metadata
    """
    # Create cache key from query
    cache_key = hashlib.md5(f"{query}:{system_prompt}".encode()).hexdigest()
    
    # Check cache first
    cached_result = api_cache.get(cache_key)
    if cached_result is not None:
        cached_result["cache_hit"] = True
        return cached_result
    
    # Validate API key
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return {
            "error": "Perplexity API key not found. Please set PERPLEXITY_API_KEY environment variable.",
            "query": query,
            "status": "error",
            "cache_hit": False
        }
    
    # Make API request
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        json={
            "model": "sonar",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        timeout=30
    )
    response.raise_for_status()
    result = response.json()
    
    if "choices" in result and result["choices"]:
        formatted_result = {
            "query": query,
            "content": result["choices"][0]["message"]["content"],
            "citations": result.get("citations", []),
            "search_results": result.get("search_results", []),
            "status": "success",
            "source": "Perplexity AI",
            "model": result.get("model", "sonar"),
            "usage": result.get("usage", {}),
            "response_id": result.get("id", ""),
            "created": result.get("created", 0),
            "timestamp": datetime.now().isoformat(),
            "cache_hit": False
        }
        
        # Cache the successful result
        api_cache.set(cache_key, formatted_result)
        
        return formatted_result
    
    return {
        "error": "No response content found",
        "query": query,
        "status": "error",
        "raw_response": result,
        "cache_hit": False
    }


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
    print("AI Consultant Agent with Google ADK (Enhanced)")
    print("=" * 50)
    print()
    print("✨ New Features:")
    print("  • Intelligent caching for faster responses")
    print("  • Automatic retry logic for API reliability")
    print("  • Enhanced structured outputs with metadata")
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
    print("Use the Eval tab in ADK web to save and evaluate consultation sessions!")
    print()
    print(f"✓ Agent '{APP_NAME}' initialized successfully!")
    print(f"  Model: {MODEL_ID}")
    print(f"  Tools: {len(consultant_tools)} available")
    print(f"  Session Service: {type(session_service).__name__}")
    print(f"  Runner: {type(runner).__name__}")
    print(f"  Cache: Enabled (30 min TTL)")
    print(f"  Retry Logic: Enabled (3 attempts, exponential backoff)")
