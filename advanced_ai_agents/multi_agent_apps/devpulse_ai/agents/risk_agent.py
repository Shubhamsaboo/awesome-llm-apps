"""
Risk Agent — Assesses security risks and breaking changes.

This agent uses LLM reasoning to analyze signals for potential risks
including security vulnerabilities, breaking API changes, and deprecation
notices. It's a legitimate agent because risk assessment requires
contextual understanding of technical implications.

Model Selection:
    Uses a structured-reasoning model (gpt-4.1-mini by default) because
    risk assessment benefits from careful, step-by-step analysis. For
    production workloads with high-stakes decisions, consider upgrading
    to gpt-4.1 or o4-mini via the MODEL_RISK environment variable.
"""

import json
from typing import Dict, Any, List
from agno.agent import Agent
from agno.models.openai import OpenAIChat

# Central model config — override via MODEL_RISK env var
import os
DEFAULT_MODEL = os.environ.get("MODEL_RISK", "gpt-4.1-mini")


class RiskAgent:
    """
    Agent that assesses risk levels in technical signals.

    Why this IS an agent:
        Risk assessment requires reasoning about technical implications,
        understanding security contexts, and making judgment calls about
        severity. This is inherently a reasoning task.

    Responsibilities:
    - Identify security vulnerabilities
    - Flag breaking changes
    - Detect deprecation notices
    - Rate overall risk level (LOW / MEDIUM / HIGH / CRITICAL)
    """

    RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def __init__(self, model_id: str = None):
        """
        Initialize the Risk Agent.

        Args:
            model_id: OpenAI model to use. Defaults to gpt-4.1-mini.
        """
        self.model_id = model_id or DEFAULT_MODEL
        self.agent = Agent(
            name="Risk Assessor",
            model=OpenAIChat(id=self.model_id),
            role="Assesses security and breaking change risks in technical signals",
            instructions=[
                "Analyze signals for security vulnerabilities.",
                "Identify breaking changes that may affect developers.",
                "Flag deprecation notices and migration requirements.",
                "Rate risk level: LOW, MEDIUM, HIGH, or CRITICAL.",
            ],
            markdown=True,
        )

    def assess(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk level of a signal.

        Attempts LLM assessment first, falls back to keyword heuristics.
        """
        prompt = f"""Analyze this technical signal for risks:

Signal:
- Source: {signal.get('source', 'unknown')}
- Title: {signal.get('title', 'Untitled')}
- Description: {signal.get('description', '')[:500]}

Assess for:
1. Security vulnerabilities
2. Breaking changes
3. Deprecations

Respond with ONLY a JSON object:
{{"risk_level": "LOW|MEDIUM|HIGH|CRITICAL", "concerns": ["<list of concerns>"], "breaking_changes": true|false}}"""

        try:
            response = self.agent.run(prompt, stream=False)
            return self._parse_response(response.content, signal)
        except Exception as e:
            return self._fallback_assessment(signal, str(e))

    def assess_batch(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assess multiple signals, returning each with a 'risk' key."""
        assessed = []
        for signal in signals:
            result = self.assess(signal)
            assessed.append({**signal, "risk": result})
        return assessed

    def _parse_response(self, content: str, signal: Dict) -> Dict[str, Any]:
        """Parse LLM JSON response into structured output."""
        try:
            text = content.strip()
            if "```" in text:
                text = text.split("```")[1].replace("json", "").strip()
            return json.loads(text)
        except (json.JSONDecodeError, IndexError):
            return self._fallback_assessment(signal, "Parse error")

    def _fallback_assessment(self, signal: Dict, error: str) -> Dict[str, Any]:
        """
        Keyword-based fallback when LLM is unavailable.

        Simple heuristic: scan title for risk-indicating keywords.
        This is intentionally conservative — better to over-flag than miss.
        """
        title = signal.get("title", "").lower()

        risk_level = "LOW"
        concerns = []

        risk_keywords = {
            "HIGH": ["vulnerability", "exploit", "cve", "critical", "breach"],
            "MEDIUM": ["breaking", "deprecated", "removed", "migration"],
        }

        for level, keywords in risk_keywords.items():
            if any(kw in title for kw in keywords):
                risk_level = level
                concerns.append(f"Keyword match: {level}")
                break

        return {
            "risk_level": risk_level,
            "concerns": concerns or [f"Heuristic (LLM unavailable: {error})"],
            "breaking_changes": "breaking" in title,
        }
