"""
DevPulseAI Verification Script

Verifies the complete pipeline using MOCK DATA ONLY.
No network calls, no API keys, no external dependencies required.

Usage:
    python verify.py

Expected output:
    [OK] DevPulseAI reference pipeline executed successfully

Runs in <1s on any machine.
"""

import sys
import time
from typing import List, Dict, Any

# ────────────────────────────────────────────────
# Mock signal data — representative of real adapter output
# ────────────────────────────────────────────────
MOCK_SIGNALS = [
    {
        "id": "mock-gh-001",
        "source": "github",
        "title": "awesome-llm-apps",
        "description": "A curated collection of awesome LLM apps built with RAG and AI agents.",
        "url": "https://github.com/Shubhamsaboo/awesome-llm-apps",
        "metadata": {"stars": 5000, "language": "Python", "topics": ["llm", "ai"]},
    },
    {
        "id": "mock-arxiv-001",
        "source": "arxiv",
        "title": "Attention Is All You Need: Revisited",
        "description": "A comprehensive analysis of transformer architectures.",
        "url": "https://arxiv.org/abs/2401.00001",
        "metadata": {"pdf": "https://arxiv.org/pdf/2401.00001", "published": "2024-01-15"},
    },
    {
        "id": "mock-hn-001",
        "source": "hackernews",
        "title": "GPT-5 Breaking Changes in API",
        "description": "OpenAI announces breaking changes to the Chat Completions API.",
        "url": "https://news.ycombinator.com/item?id=12345",
        "metadata": {"points": 500, "comments": 200, "author": "techwriter"},
    },
    {
        "id": "mock-medium-001",
        "source": "medium",
        "title": "Building Production RAG Systems",
        "description": "A deep dive into building scalable retrieval-augmented generation.",
        "url": "https://medium.com/@techblog/building-rag",
        "metadata": {"author": "TechBlog", "published": "2024-01-20"},
    },
    {
        "id": "mock-hf-001",
        "source": "huggingface",
        "title": "HF Model: meta-llama/Llama-3-8B",
        "description": "Pipeline: text-generation | Downloads: 1,000,000 | Likes: 5,000",
        "url": "https://huggingface.co/meta-llama/Llama-3-8B",
        "metadata": {"downloads": 1000000, "likes": 5000, "pipeline_tag": "text-generation"},
    },
]


# ────────────────────────────────────────────────
# Verification steps
# ────────────────────────────────────────────────

def verify_imports():
    """Verify all modules can be imported without errors."""
    print("[1/5] Verifying imports...")

    from agents import SignalCollector, RelevanceAgent, RiskAgent, SynthesisAgent
    from adapters.github import fetch_github_trending
    from adapters.arxiv import fetch_arxiv_papers
    from adapters.hackernews import fetch_hackernews_stories
    from adapters.medium import fetch_medium_blogs
    from adapters.huggingface import fetch_huggingface_models

    # Verify SignalCollector is NOT an agent (no .agent attribute)
    collector = SignalCollector()
    assert not hasattr(collector, "agent"), (
        "SignalCollector should NOT have an .agent attribute — "
        "it's a utility, not an agent"
    )

    print("  ✓ All modules imported successfully")
    print("  ✓ SignalCollector confirmed as utility (no LLM)")
    return True


def verify_signal_collector():
    """Verify SignalCollector normalizes and deduplicates correctly."""
    print("[2/5] Verifying Signal Collector (utility)...")

    from agents import SignalCollector

    collector = SignalCollector()

    # Test normalization
    normalized = collector.collect(MOCK_SIGNALS)
    assert len(normalized) == len(MOCK_SIGNALS), "Signal count mismatch"
    assert all("collected_at" in s for s in normalized), "Missing timestamp"

    # Test deduplication — adding duplicates should not increase count
    duped = MOCK_SIGNALS + [MOCK_SIGNALS[0]]  # One duplicate
    deduped = collector.collect(duped)
    assert len(deduped) == len(MOCK_SIGNALS), "Deduplication failed"

    summary = collector.summarize_collection(normalized)
    print(f"  ✓ {summary}")
    print("  ✓ Deduplication works correctly")
    return normalized


def verify_relevance_agent(signals: List[Dict]):
    """Verify RelevanceAgent fallback scoring works without API key."""
    print("[3/5] Verifying Relevance Agent (fallback mode)...")

    from agents import RelevanceAgent

    agent = RelevanceAgent()

    # Use fallback scoring directly (no API key needed)
    scored = []
    for signal in signals:
        result = agent._fallback_score(signal, "Mock mode")
        scored.append({**signal, "relevance": result})

    assert all("relevance" in s for s in scored), "Missing relevance scores"
    assert all(
        0 <= s["relevance"]["score"] <= 100 for s in scored
    ), "Scores out of range"

    print(f"  ✓ Scored {len(scored)} signals (heuristic fallback)")
    return scored


def verify_risk_agent(signals: List[Dict]):
    """Verify RiskAgent fallback assessment works without API key."""
    print("[4/5] Verifying Risk Agent (fallback mode)...")

    from agents import RiskAgent

    agent = RiskAgent()

    assessed = []
    for signal in signals:
        result = agent._fallback_assessment(signal, "Mock mode")
        assessed.append({**signal, "risk": result})

    assert all("risk" in s for s in assessed), "Missing risk assessments"

    # Verify keyword detection: "GPT-5 Breaking Changes" should flag
    breaking = [s for s in assessed if s.get("risk", {}).get("breaking_changes")]
    assert len(breaking) >= 1, "Breaking change detection failed"

    print(f"  ✓ Assessed {len(assessed)} signals ({len(breaking)} with breaking changes)")
    return assessed


def verify_synthesis_agent(signals: List[Dict]):
    """Verify SynthesisAgent produces valid digest structure."""
    print("[5/5] Verifying Synthesis Agent...")

    from agents import SynthesisAgent

    agent = SynthesisAgent()
    digest = agent.synthesize(signals)

    assert "generated_at" in digest, "Missing timestamp"
    assert "executive_summary" in digest, "Missing summary"
    assert "recommendations" in digest, "Missing recommendations"
    assert "priority_signals" in digest, "Missing priority signals"
    assert digest["total_signals"] == len(signals), "Signal count mismatch"

    print(f"  ✓ Generated digest with {len(digest['recommendations'])} recommendations")
    return digest


# ────────────────────────────────────────────────
# Main verification runner
# ────────────────────────────────────────────────

def run_verification():
    """Run the complete verification suite with timing."""
    print("=" * 60)
    print("🔍 DevPulseAI Verification Suite")
    print("=" * 60)
    print("\nUsing MOCK DATA — No network calls or API keys required.\n")

    start = time.time()

    try:
        if not verify_imports():
            raise AssertionError("Import verification failed")

        normalized = verify_signal_collector()
        scored = verify_relevance_agent(normalized)
        assessed = verify_risk_agent(scored)
        digest = verify_synthesis_agent(assessed)

        elapsed = time.time() - start

        # Final summary
        print("\n" + "=" * 60)
        print("📊 Verification Summary")
        print("=" * 60)
        print(f"  • Signals processed:  {digest['total_signals']}")
        print(f"  • Summary:            {digest['executive_summary']}")
        print(f"  • Recommendations:    {len(digest['recommendations'])}")
        print(f"  • Time elapsed:       {elapsed:.3f}s")

        print("\n" + "=" * 60)
        print("[OK] DevPulseAI reference pipeline executed successfully")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[FAIL] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
