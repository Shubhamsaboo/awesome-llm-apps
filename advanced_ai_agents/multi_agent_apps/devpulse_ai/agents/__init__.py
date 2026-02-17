"""
DevPulseAI Agents Package

This package contains the intelligence pipeline components:

- SignalCollector: Pure utility (NOT an agent) — normalizes and deduplicates signals.
  Signal collection is deterministic and intentionally not agent-driven.

- RelevanceAgent: LLM agent — scores signals 0-100 for developer relevance.
  Uses fast model (gpt-4.1-mini) for high-throughput classification.

- RiskAgent: LLM agent — assesses security risks and breaking changes.
  Uses structured-reasoning model (gpt-4.1-mini) for careful analysis.

- SynthesisAgent: LLM agent — produces final intelligence digest.
  Uses strongest model (gpt-4.1) for cross-referencing and summarization.

Design Principle:
    Agents are used ONLY where reasoning is required.
    Deterministic operations (collection, normalization, dedup) are utilities.
"""

from .signal_collector import SignalCollector
from .relevance_agent import RelevanceAgent
from .risk_agent import RiskAgent
from .synthesis_agent import SynthesisAgent

__all__ = [
    "SignalCollector",
    "RelevanceAgent",
    "RiskAgent",
    "SynthesisAgent",
]
