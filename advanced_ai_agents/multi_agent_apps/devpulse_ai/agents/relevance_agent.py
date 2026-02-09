"""
Relevance Agent - Scores signals based on developer relevance.

This agent uses LLM reasoning to score each signal from 0-100
based on its relevance to AI/ML developers and engineers.
"""

from typing import Dict, Any, Optional
from agno.agent import Agent
from agno.models.google import Gemini


class RelevanceAgent:
    """
    Agent that scores signals based on relevance to developers.
    
    Responsibilities:
    - Score signals 0-100 based on developer relevance
    - Provide reasoning for each score
    - Prioritize actionable, timely content
    """
    
    def __init__(self, model_id: str = "gemini-1.5-flash"):
        """
        Initialize the Relevance Agent.
        
        Args:
            model_id: Model ID to use for scoring.
        """
        self.model_id = model_id
        self.agent = Agent(
            name="Relevance Scorer",
            model=Gemini(id=model_id),
            role="Scores technical signals based on developer relevance",
            instructions=[
                "Score each signal from 0-100 based on relevance.",
                "Consider: novelty, impact, actionability, and timeliness.",
                "Prioritize signals relevant to AI/ML engineers.",
                "Provide brief reasoning for each score."
            ],
            markdown=True
        )
    
    def score(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a signal for relevance.
        
        Args:
            signal: Signal dictionary to score.
            
        Returns:
            Dictionary with score and reasoning.
        """
        prompt = f"""
Rate the relevance of this signal for AI/ML developers.
Score from 0-100 where:
- 0-30: Low relevance (noise, off-topic)
- 31-60: Moderate relevance (interesting but not urgent)
- 61-80: High relevance (important for developers to know)
- 81-100: Critical relevance (must-know, actionable)

Signal:
- Source: {signal.get('source', 'unknown')}
- Title: {signal.get('title', 'Untitled')}
- Description: {signal.get('description', '')[:500]}

Respond with ONLY a JSON object:
{{"score": <number>, "reasoning": "<one sentence>"}}
"""
        
        try:
            response = self.agent.run(prompt, stream=False)
            # Parse response - in real use, would parse JSON
            return self._parse_response(response.content, signal)
        except Exception as e:
            return self._fallback_score(signal, str(e))
    
    def score_batch(self, signals: list) -> list:
        """
        Score multiple signals.
        
        Args:
            signals: List of signal dictionaries.
            
        Returns:
            List of signals with scores added.
        """
        scored = []
        for signal in signals:
            result = self.score(signal)
            signal_with_score = {**signal, "relevance": result}
            scored.append(signal_with_score)
        return scored
    
    def _parse_response(self, content: str, signal: Dict) -> Dict[str, Any]:
        """Parse LLM response into structured output."""
        import json
        try:
            # Try to extract JSON from response
            content = content.strip()
            if "```" in content:
                content = content.split("```")[1].replace("json", "").strip()
            return json.loads(content)
        except:
            return self._fallback_score(signal, "Parse error")
    
    def _fallback_score(self, signal: Dict, error: str) -> Dict[str, Any]:
        """Provide fallback score when LLM call fails."""
        # Simple heuristic based on metadata
        score = 50  # Default moderate score
        metadata = signal.get("metadata", {})
        
        if metadata.get("stars", 0) > 100:
            score += 20
        if metadata.get("points", 0) > 50:
            score += 15
            
        return {
            "score": min(score, 100),
            "reasoning": f"Heuristic score (LLM unavailable: {error})"
        }
