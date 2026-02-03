"""
Signal Collector Agent - Aggregates signals from multiple data sources.

This agent is responsible for the ingestion phase of the pipeline.
It collects signals from GitHub, ArXiv, and HackerNews, then normalizes
them into a unified schema for downstream processing.
"""

from typing import List, Dict, Any
from agno.agent import Agent
from agno.models.openai import OpenAIChat


class SignalCollectorAgent:
    """
    Agent that collects and normalizes signals from multiple sources.
    
    Responsibilities:
    - Fetch data from configured adapters
    - Normalize signals to unified schema
    - Deduplicate and filter low-quality signals
    """
    
    def __init__(self, model_id: str = "gpt-4o-mini"):
        """
        Initialize the Signal Collector Agent.
        
        Args:
            model_id: OpenAI model to use for signal processing.
        """
        self.model_id = model_id
        self.agent = Agent(
            name="Signal Collector",
            model=OpenAIChat(id=model_id),
            role="Collects and normalizes technical signals from multiple sources",
            instructions=[
                "You aggregate signals from GitHub, ArXiv, and HackerNews.",
                "Normalize all signals to a consistent format.",
                "Filter out low-quality or duplicate signals.",
                "Prioritize signals relevant to AI/ML developers."
            ],
            markdown=True
        )
    
    def collect(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process and normalize collected signals.
        
        Args:
            signals: Raw signals from adapters.
            
        Returns:
            List of normalized signal dictionaries.
        """
        normalized = []
        seen_ids = set()
        
        for signal in signals:
            # Deduplicate
            signal_id = f"{signal.get('source', 'unknown')}:{signal.get('id', '')}"
            if signal_id in seen_ids:
                continue
            seen_ids.add(signal_id)
            
            # Ensure required fields
            normalized_signal = {
                "id": signal.get("id", ""),
                "source": signal.get("source", "unknown"),
                "title": signal.get("title", "Untitled"),
                "description": signal.get("description", ""),
                "url": signal.get("url", ""),
                "metadata": signal.get("metadata", {}),
                "collected_at": self._get_timestamp()
            }
            normalized.append(normalized_signal)
        
        return normalized
    
    def _get_timestamp(self) -> str:
        """Get current UTC timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def summarize_collection(self, signals: List[Dict[str, Any]]) -> str:
        """
        Generate a summary of collected signals.
        
        Args:
            signals: List of collected signals.
            
        Returns:
            Summary string.
        """
        sources = {}
        for s in signals:
            src = s.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        
        summary_parts = [f"{count} from {src}" for src, count in sources.items()]
        return f"Collected {len(signals)} signals: {', '.join(summary_parts)}"
