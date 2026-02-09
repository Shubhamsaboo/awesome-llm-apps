"""
Risk Agent - Assesses security risks and breaking changes.

This agent analyzes signals for potential risks including:
- Security vulnerabilities
- Breaking changes in dependencies
- Deprecation notices
"""

from typing import Dict, Any, List
from agno.agent import Agent
from agno.models.google import Gemini


class RiskAgent:
    """
    Agent that assesses risk levels in technical signals.
    
    Responsibilities:
    - Identify security vulnerabilities
    - Flag breaking changes
    - Detect deprecation notices
    - Rate overall risk level
    """
    
    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    
    def __init__(self, model_id: str = "gemini-1.5-flash"):
        """
        Initialize the Risk Agent.
        
        Args:
            model_id: Model ID to use for risk assessment.
        """
        self.model_id = model_id
        self.agent = Agent(
            name="Risk Assessor",
            model=Gemini(id=model_id),
            role="Assesses security and breaking change risks in technical signals",
            instructions=[
                "Analyze signals for security vulnerabilities.",
                "Identify breaking changes that may affect developers.",
                "Flag deprecation notices and migration requirements.",
                "Rate risk level: LOW, MEDIUM, HIGH, or CRITICAL."
            ],
            markdown=True
        )
    
    def assess(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk level of a signal.
        
        Args:
            signal: Signal dictionary to assess.
            
        Returns:
            Dictionary with risk assessment.
        """
        prompt = f"""
Analyze this technical signal for risks:

Signal:
- Source: {signal.get('source', 'unknown')}
- Title: {signal.get('title', 'Untitled')}
- Description: {signal.get('description', '')[:500]}

Assess for:
1. Security vulnerabilities
2. Breaking changes
3. Deprecations

Respond with ONLY a JSON object:
{{"risk_level": "LOW|MEDIUM|HIGH|CRITICAL", "concerns": ["<list of concerns>"], "breaking_changes": true|false}}
"""
        
        try:
            response = self.agent.run(prompt, stream=False)
            return self._parse_response(response.content, signal)
        except Exception as e:
            return self._fallback_assessment(signal, str(e))
    
    def assess_batch(self, signals: list) -> list:
        """
        Assess multiple signals for risk.
        
        Args:
            signals: List of signal dictionaries.
            
        Returns:
            List of signals with risk assessments added.
        """
        assessed = []
        for signal in signals:
            result = self.assess(signal)
            signal_with_risk = {**signal, "risk": result}
            assessed.append(signal_with_risk)
        return assessed
    
    def _parse_response(self, content: str, signal: Dict) -> Dict[str, Any]:
        """Parse LLM response into structured output."""
        import json
        try:
            content = content.strip()
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
            return json.loads(content)
        except:
            return self._fallback_assessment(signal, "Parse error")
    
    def _fallback_assessment(self, signal: Dict, error: str) -> Dict[str, Any]:
        """Provide fallback assessment when LLM call fails."""
        title = signal.get("title", "").lower()
        
        # Simple keyword-based heuristics
        risk_level = "LOW"
        concerns = []
        
        risk_keywords = {
            "HIGH": ["vulnerability", "exploit", "CVE", "critical", "breach"],
            "MEDIUM": ["breaking", "deprecated", "removed", "migration"],
        }
        
        for level, keywords in risk_keywords.items():
            if any(kw.lower() in title for kw in keywords):
                risk_level = level
                concerns.append(f"Keyword match: {level}")
                break
        
        return {
            "risk_level": risk_level,
            "concerns": concerns if concerns else [f"Heuristic (LLM unavailable: {error})"],
            "breaking_changes": "breaking" in title.lower()
        }
