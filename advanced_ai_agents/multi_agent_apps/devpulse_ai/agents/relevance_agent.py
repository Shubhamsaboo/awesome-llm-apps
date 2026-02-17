"""
Relevance Agent — Scores signals by developer relevance (0–100).

This agent uses LLM reasoning to evaluate each signal's importance to
AI/ML developers. It's a legitimate agent because relevance scoring
requires judgment, context understanding, and nuanced assessment that
pure heuristics cannot capture.

Model Selection:
    Uses a fast, cost-efficient model (gpt-4.1-mini by default) because
    relevance scoring is high-volume and doesn't require deep reasoning —
    it's a classification task, not a synthesis task.
"""

import json
from typing import Dict, Any, List
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Central model config — override via MODEL_RELEVANCE env var
import os
DEFAULT_MODEL = os.environ.get("MODEL_RELEVANCE", "gpt-4.1-mini")


class RelevanceAgent:
    """
    Agent that scores signals based on relevance to developers.

    Why this IS an agent (unlike SignalCollector):
        Relevance scoring requires understanding context, assessing novelty,
        and making judgment calls about what matters to developers. This is
        inherently a reasoning task that benefits from LLM capabilities.

    Responsibilities:
    - Score signals 0–100 based on developer relevance
    - Provide reasoning for each score
    - Gracefully fall back to heuristics when LLM unavailable
    """

    def __init__(self, model_id: str = None):
        """
        Initialize the Relevance Agent.

        Args:
            model_id: OpenAI model to use. Defaults to gpt-4.1-mini (fast, cheap).
        """
        self.model_id = model_id or DEFAULT_MODEL
        self.agent = Agent(
            name="Relevance Scorer",
            model=OpenAIChat(id=self.model_id),
            role="Scores technical signals based on developer relevance",
            instructions=[
                "Score each signal from 0-100 based on relevance.",
                "Consider: novelty, impact, actionability, and timeliness.",
                "Prioritize signals relevant to AI/ML engineers.",
                "Provide brief reasoning for each score.",
            ],
            markdown=True,
        )

    def score(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single signal for developer relevance.

        Attempts LLM scoring first, falls back to heuristics on failure.
        """
        prompt = f"""Rate the relevance of this signal for AI/ML developers.
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
{{"score": <number>, "reasoning": "<one sentence>"}}"""

        try:
            response = self.agent.run(prompt, stream=False)
            return self._parse_response(response.content, signal)
        except Exception as e:
            return self._fallback_score(signal, str(e))

    def score_batch(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Score multiple signals, returning each with a 'relevance' key."""
        scored = []
        for signal in signals:
            result = self.score(signal)
            scored.append({**signal, "relevance": result})
        return scored

    def _parse_response(self, content: str, signal: Dict) -> Dict[str, Any]:
        """Parse LLM JSON response into structured output."""
        try:
            text = content.strip()
            if "```" in text:
                text = text.split("```")[1].replace("json", "").strip()
            return json.loads(text)
        except (json.JSONDecodeError, IndexError):
            return self._fallback_score(signal, "Parse error")

    def _fallback_score(self, signal: Dict, error: str) -> Dict[str, Any]:
        """
        Heuristic fallback when LLM is unavailable.

        Uses metadata signals (stars, points) as rough relevance proxies.
        This is intentionally simple — the LLM path is the real logic.
        """
        score = 50  # Default: moderate
        metadata = signal.get("metadata", {})

        if metadata.get("stars", 0) > 100:
            score += 20
        if metadata.get("points", 0) > 50:
            score += 15

        return {
            "score": min(score, 100),
            "reasoning": f"Heuristic score (LLM unavailable: {error})",
        }
