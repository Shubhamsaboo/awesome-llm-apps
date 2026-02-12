"""
DevPulseAI - Multi-Agent Signal Intelligence Pipeline

This script demonstrates a complete multi-agent workflow for
aggregating and analyzing technical signals from multiple sources.

Usage:
    python main.py

Requirements:
    - OpenAI API key set as OPENAI_API_KEY environment variable
    - Internet connection for fetching live data
"""

import os
from typing import List, Dict, Any, Optional

# Reduced default signal count for faster demo execution
DEFAULT_SIGNAL_LIMIT = 8

# Import adapters
from adapters.github import fetch_github_trending
from adapters.arxiv import fetch_arxiv_papers
from adapters.hackernews import fetch_hackernews_stories
from adapters.medium import fetch_medium_blogs
from adapters.huggingface import fetch_huggingface_models

# Import agents
from agents import (
    SignalCollectorAgent,
    RelevanceAgent,
    RiskAgent,
    SynthesisAgent
)


def collect_signals(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Collect signals from all configured sources.
    
    Args:
        limit: Maximum signals to fetch per source. Defaults to DEFAULT_SIGNAL_LIMIT.
        
    Returns:
        Combined list of signals from all adapters.
    """
    fetch_limit = limit if limit is not None else DEFAULT_SIGNAL_LIMIT
    print(f"\n📡 [1/4] Collecting Signals (limit: {fetch_limit} per source)...")
    
    signals = []
    
    # Fetch from each source
    print("  → Fetching GitHub trending repos...")
    signals.extend(fetch_github_trending(limit=fetch_limit))
    
    print("  → Fetching ArXiv papers...")
    signals.extend(fetch_arxiv_papers(limit=fetch_limit))
    
    print("  → Fetching HackerNews stories...")
    signals.extend(fetch_hackernews_stories(limit=fetch_limit))
    
    print("  → Fetching Medium blogs...")
    signals.extend(fetch_medium_blogs(limit=min(fetch_limit, 3))) # Medium feeds are usually denser
    
    print("  → Fetching HuggingFace models...")
    signals.extend(fetch_huggingface_models(limit=fetch_limit))
    
    print(f"  ✓ Collected {len(signals)} raw signals")
    return signals


def run_pipeline():
    """
    Execute the full signal intelligence pipeline.
    
    Pipeline stages:
    1. Signal Collection - Aggregate from multiple sources
    2. Relevance Scoring - Rate signals 0-100
    3. Risk Assessment - Identify security/breaking changes
    4. Synthesis - Produce final intelligence digest
    """
    print("=" * 60)
    print("🧠 DevPulseAI - Signal Intelligence Pipeline")
    print("=" * 60)
    
    # Check for API key
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("\n⚠️  Warning: GOOGLE_API_KEY not set.")
        print("   LLM-based agents will use fallback heuristics.\n")
    
    # Stage 1: Collection
    raw_signals = collect_signals()
    
    # Initialize agents
    collector = SignalCollectorAgent()
    relevance = RelevanceAgent()
    risk = RiskAgent()
    synthesis = SynthesisAgent()
    
    # Stage 2: Normalize
    print("\n🔄 [2/4] Normalizing Signals...")
    normalized = collector.collect(raw_signals)
    print(f"  ✓ {collector.summarize_collection(normalized)}")
    
    # Stage 3: Score for relevance
    print("\n📊 [3/4] Scoring Relevance...")
    scored = relevance.score_batch(normalized)
    high_relevance = sum(1 for s in scored 
                         if s.get("relevance", {}).get("score", 0) >= 70)
    print(f"  ✓ {high_relevance}/{len(scored)} signals rated high-relevance")
    
    # Stage 4: Assess risks
    print("\n⚠️  [4/4] Assessing Risks...")
    assessed = risk.assess_batch(scored)
    critical = sum(1 for s in assessed 
                   if s.get("risk", {}).get("risk_level") in ["HIGH", "CRITICAL"])
    print(f"  ✓ {critical}/{len(assessed)} signals with elevated risk")
    
    # Stage 5: Synthesize
    print("\n📋 Generating Intelligence Digest...")
    digest = synthesis.synthesize(assessed)
    
    # Output results
    print("\n" + "=" * 60)
    print("📄 INTELLIGENCE DIGEST")
    print("=" * 60)
    print(f"\n🕐 Generated: {digest['generated_at']}")
    print(f"📦 Total Signals: {digest['total_signals']}")
    print(f"\n📝 Summary: {digest['executive_summary']}")
    
    print("\n🎯 Top Priority Signals:")
    for i, signal in enumerate(digest.get("priority_signals", [])[:3], 1):
        score = signal.get("relevance", {}).get("score", "?")
        risk_level = signal.get("risk", {}).get("risk_level", "?")
        print(f"   {i}. [{signal['source']}] {signal['title'][:50]}...")
        print(f"      Relevance: {score} | Risk: {risk_level}")
    
    print("\n💡 Recommendations:")
    for rec in digest.get("recommendations", []):
        print(f"   • {rec}")
    
    print("\n" + "=" * 60)
    print("✅ Pipeline completed successfully!")
    print("=" * 60)
    
    return digest


if __name__ == "__main__":
    run_pipeline()
