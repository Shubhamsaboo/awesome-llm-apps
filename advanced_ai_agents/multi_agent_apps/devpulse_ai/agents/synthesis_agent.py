"""
Synthesis Agent — Produces final intelligence digest.

This agent combines outputs from all previous stages to create a
comprehensive, actionable intelligence summary. It's the most reasoning-
intensive agent in the pipeline and uses the strongest available model.

Model Selection:
    Uses gpt-4.1 by default — the strongest reasoning model — because
    synthesis requires cross-referencing multiple signals, identifying
    patterns, generating executive summaries, and producing actionable
    recommendations. This is the one stage where model quality directly
    impacts output quality.

    Override via MODEL_SYNTHESIS env var for cost optimization.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Central model config — override via MODEL_SYNTHESIS env var
import os
DEFAULT_MODEL = os.environ.get("MODEL_SYNTHESIS", "gpt-4.1")


class SynthesisAgent:
    """
    Agent that synthesizes all signal intelligence into a final digest.

    Why this uses the strongest model:
        Synthesis is the most reasoning-intensive task in the pipeline.
        It must cross-reference relevance scores, risk assessments, and
        source metadata to produce coherent, actionable intelligence.
        Using a weaker model here would produce generic, shallow outputs.

    Responsibilities:
    - Combine relevance and risk assessments
    - Prioritize signals by importance
    - Generate executive summary
    - Produce actionable recommendations
    """

    def __init__(self, model_id: str = None):
        """
        Initialize the Synthesis Agent.

        Args:
            model_id: OpenAI model to use. Defaults to gpt-4.1 (strongest reasoning).
        """
        self.model_id = model_id or DEFAULT_MODEL
        self.agent = Agent(
            name="Intelligence Synthesizer",
            model=OpenAIChat(id=self.model_id),
            role="Synthesizes technical signals into actionable intelligence digests",
            instructions=[
                "Combine relevance scores and risk assessments.",
                "Prioritize by: high relevance + critical risks first.",
                "Generate an executive summary.",
                "Provide actionable recommendations for developers.",
            ],
            markdown=True,
        )

    def synthesize(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesize signals into a final intelligence digest.

        This method uses deterministic logic for prioritization and grouping,
        then delegates summary generation to either LLM or heuristics.
        """
        prioritized = self._prioritize_signals(signals)
        grouped = self._group_by_source(prioritized)
        summary = self._generate_summary(prioritized)

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_signals": len(signals),
            "executive_summary": summary,
            "priority_signals": prioritized[:5],
            "signals_by_source": grouped,
            "recommendations": self._generate_recommendations(prioritized),
        }

    def _prioritize_signals(self, signals: List[Dict]) -> List[Dict]:
        """Sort signals by composite priority score (relevance × risk multiplier)."""

        def priority_score(signal):
            relevance = signal.get("relevance", {}).get("score", 50)
            risk_multiplier = {
                "CRITICAL": 2.0,
                "HIGH": 1.5,
                "MEDIUM": 1.0,
                "LOW": 0.8,
            }.get(signal.get("risk", {}).get("risk_level", "LOW"), 1.0)
            return relevance * risk_multiplier

        return sorted(signals, key=priority_score, reverse=True)

    def _group_by_source(self, signals: List[Dict]) -> Dict[str, List]:
        """Group signals by their source for categorized display."""
        grouped: Dict[str, List] = {}
        for signal in signals:
            source = signal.get("source", "unknown")
            grouped.setdefault(source, []).append(signal)
        return grouped

    def _generate_summary(self, signals: List[Dict]) -> str:
        """Generate executive summary from processed signals."""
        if not signals:
            return "No signals to summarize."

        high_priority = [
            s for s in signals if s.get("relevance", {}).get("score", 0) >= 70
        ]
        critical_risks = [
            s
            for s in signals
            if s.get("risk", {}).get("risk_level") in ["HIGH", "CRITICAL"]
        ]

        parts = [f"Analyzed {len(signals)} signals."]

        if high_priority:
            parts.append(f"{len(high_priority)} high-relevance items detected.")
        if critical_risks:
            parts.append(
                f"⚠️ {len(critical_risks)} signals with elevated risk."
            )
        if signals:
            parts.append(f"Top signal: {signals[0].get('title', 'Unknown')}")

        return " ".join(parts)

    def _generate_recommendations(self, signals: List[Dict]) -> List[str]:
        """Generate actionable recommendations from signal analysis."""
        recommendations = []

        critical = [
            s
            for s in signals
            if s.get("risk", {}).get("risk_level") == "CRITICAL"
        ]
        if critical:
            recommendations.append(
                f"🚨 Review {len(critical)} critical-risk signals immediately"
            )

        high_rel = [
            s for s in signals if s.get("relevance", {}).get("score", 0) >= 80
        ]
        if high_rel:
            recommendations.append(
                f"📌 Prioritize {len(high_rel)} high-relevance items"
            )

        github = [s for s in signals if s.get("source") == "github"]
        if github:
            recommendations.append(
                f"⭐ Explore {len(github)} trending repositories"
            )

        if not recommendations:
            recommendations.append("✅ No urgent actions required")

        return recommendations
