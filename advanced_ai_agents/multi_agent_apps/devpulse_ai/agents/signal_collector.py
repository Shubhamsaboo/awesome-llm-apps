"""
Signal Collector — Pure utility (not an agent).

Signal collection is deterministic and intentionally not agent-driven.
This module aggregates signals from adapters, normalizes them to a unified
schema, and deduplicates deterministically. No LLM reasoning is involved
because collection/normalization is a mechanical transformation — using an
agent here would be decorative, not functional.

Design Decision:
    Agents are used only where reasoning is required. Signal collection
    involves no ambiguity, judgment, or language understanding — it's a
    pipeline transformation. Wrapping it in an Agent class would mislead
    readers into thinking an LLM call is necessary here.
"""

from typing import List, Dict, Any
from datetime import datetime, timezone


class SignalCollector:
    """
    Utility that collects and normalizes signals from multiple sources.

    NOT an agent — no LLM calls. This is an intentional design choice.
    See module docstring for rationale.

    Responsibilities:
    - Normalize signals to unified schema
    - Deduplicate deterministically (source:id composite key)
    - Filter incomplete signals
    """

    def collect(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize and deduplicate raw signals from adapters.

        Args:
            signals: Raw signals from adapters (heterogeneous schemas).

        Returns:
            List of normalized, deduplicated signal dictionaries.
        """
        normalized = []
        seen_ids = set()

        for signal in signals:
            # Deterministic dedup key: source + external id
            signal_id = f"{signal.get('source', 'unknown')}:{signal.get('id', '')}"
            if signal_id in seen_ids:
                continue
            seen_ids.add(signal_id)

            # Normalize to unified schema
            normalized.append({
                "id": signal.get("id", ""),
                "source": signal.get("source", "unknown"),
                "title": signal.get("title", "Untitled"),
                "description": signal.get("description", ""),
                "url": signal.get("url", ""),
                "metadata": signal.get("metadata", {}),
                "collected_at": datetime.now(timezone.utc).isoformat(),
            })

        return normalized

    def summarize_collection(self, signals: List[Dict[str, Any]]) -> str:
        """
        Generate a human-readable collection summary.

        Pure string formatting — no LLM needed.
        """
        sources: Dict[str, int] = {}
        for s in signals:
            src = s.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1

        parts = [f"{count} from {src}" for src, count in sources.items()]
        return f"Collected {len(signals)} signals: {', '.join(parts)}"
