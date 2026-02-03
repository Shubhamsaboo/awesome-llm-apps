"""
Synthesis Agent - Produces final intelligence digest.

This agent combines outputs from all previous agents to create
a comprehensive, actionable intelligence summary for developers.
"""

from typing import Dict, Any, List
from agno.agent import Agent
from agno.models.openai import OpenAIChat


class SynthesisAgent:
    """
    Agent that synthesizes all signal intelligence into a final digest.
    
    Responsibilities:
    - Combine relevance and risk assessments
    - Prioritize signals by importance
    - Generate executive summary
    - Produce actionable recommendations
    """
    
    def __init__(self, model_id: str = "gpt-4o-mini"):
        """
        Initialize the Synthesis Agent.
        
        Args:
            model_id: OpenAI model to use for synthesis.
        """
        self.model_id = model_id
        self.agent = Agent(
            name="Intelligence Synthesizer",
            model=OpenAIChat(id=model_id),
            role="Synthesizes technical signals into actionable intelligence digests",
            instructions=[
                "Combine relevance scores and risk assessments.",
                "Prioritize by: high relevance + critical risks first.",
                "Generate an executive summary.",
                "Provide actionable recommendations for developers."
            ],
            markdown=True
        )
    
    def synthesize(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize signals into a final intelligence digest.
        
        Args:
            signals: List of signals with relevance and risk data.
            
        Returns:
            Complete intelligence digest.
        """
        # Sort by priority (high relevance + high risk first)
        prioritized = self._prioritize_signals(signals)
        
        # Group by category
        grouped = self._group_by_source(prioritized)
        
        # Generate summary
        summary = self._generate_summary(prioritized)
        
        return {
            "generated_at": self._get_timestamp(),
            "total_signals": len(signals),
            "executive_summary": summary,
            "priority_signals": prioritized[:5],  # Top 5
            "signals_by_source": grouped,
            "recommendations": self._generate_recommendations(prioritized)
        }
    
    def _prioritize_signals(self, signals: List[Dict]) -> List[Dict]:
        """Sort signals by priority score."""
        def priority_score(signal):
            relevance = signal.get("relevance", {}).get("score", 50)
            risk = signal.get("risk", {})
            risk_multiplier = {
                "CRITICAL": 2.0,
                "HIGH": 1.5,
                "MEDIUM": 1.0,
                "LOW": 0.8
            }.get(risk.get("risk_level", "LOW"), 1.0)
            return relevance * risk_multiplier
        
        return sorted(signals, key=priority_score, reverse=True)
    
    def _group_by_source(self, signals: List[Dict]) -> Dict[str, List]:
        """Group signals by their source."""
        grouped = {}
        for signal in signals:
            source = signal.get("source", "unknown")
            if source not in grouped:
                grouped[source] = []
            grouped[source].append(signal)
        return grouped
    
    def _generate_summary(self, signals: List[Dict]) -> str:
        """Generate executive summary."""
        if not signals:
            return "No signals to summarize."
        
        high_priority = [s for s in signals 
                        if s.get("relevance", {}).get("score", 0) >= 70]
        critical_risks = [s for s in signals 
                         if s.get("risk", {}).get("risk_level") in ["HIGH", "CRITICAL"]]
        
        parts = [f"Analyzed {len(signals)} signals."]
        
        if high_priority:
            parts.append(f"{len(high_priority)} high-relevance items detected.")
        
        if critical_risks:
            parts.append(f"⚠️ {len(critical_risks)} signals with elevated risk.")
        
        if signals:
            top = signals[0]
            parts.append(f"Top signal: {top.get('title', 'Unknown')}")
        
        return " ".join(parts)
    
    def _generate_recommendations(self, signals: List[Dict]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        critical_risks = [s for s in signals 
                         if s.get("risk", {}).get("risk_level") == "CRITICAL"]
        if critical_risks:
            recommendations.append(
                f"🚨 Review {len(critical_risks)} critical-risk signals immediately"
            )
        
        high_relevance = [s for s in signals 
                         if s.get("relevance", {}).get("score", 0) >= 80]
        if high_relevance:
            recommendations.append(
                f"📌 Prioritize {len(high_relevance)} high-relevance items"
            )
        
        github_signals = [s for s in signals if s.get("source") == "github"]
        if github_signals:
            recommendations.append(
                f"⭐ Explore {len(github_signals)} trending repositories"
            )
        
        if not recommendations:
            recommendations.append("✅ No urgent actions required")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current UTC timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
