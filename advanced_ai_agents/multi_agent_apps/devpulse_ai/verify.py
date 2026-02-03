"""
DevPulseAI Verification Script

This script verifies the pipeline works correctly using MOCK DATA ONLY.
No network calls or API keys are required.

Usage:
    python verify.py

Expected output:
    [OK] DevPulseAI reference pipeline executed successfully
"""

from typing import List, Dict, Any

# Mock signal data for verification
MOCK_SIGNALS = [
    {
        "id": "mock-gh-001",
        "source": "github",
        "title": "awesome-llm-apps",
        "description": "A curated collection of awesome LLM apps built with RAG and AI agents.",
        "url": "https://github.com/Shubhamsaboo/awesome-llm-apps",
        "metadata": {"stars": 5000, "language": "Python", "topics": ["llm", "ai"]}
    },
    {
        "id": "mock-arxiv-001",
        "source": "arxiv",
        "title": "Attention Is All You Need: Revisited",
        "description": "A comprehensive analysis of transformer architectures and their evolution over the past years.",
        "url": "https://arxiv.org/abs/2401.00001",
        "metadata": {"pdf": "https://arxiv.org/pdf/2401.00001", "published": "2024-01-15"}
    },
    {
        "id": "mock-hn-001",
        "source": "hackernews",
        "title": "GPT-5 Breaking Changes in API",
        "description": "OpenAI announces breaking changes to the Chat Completions API.",
        "url": "https://news.ycombinator.com/item?id=12345",
        "metadata": {"points": 500, "comments": 200, "author": "techwriter"}
    },
    {
        "id": "mock-medium-001",
        "source": "medium",
        "title": "Building Production RAG Systems",
        "description": "A deep dive into building scalable retrieval-augmented generation pipelines.",
        "url": "https://medium.com/@techblog/building-rag",
        "metadata": {"author": "TechBlog", "published": "2024-01-20"}
    },
    {
        "id": "mock-hf-001",
        "source": "huggingface",
        "title": "HF Model: meta-llama/Llama-3-8B",
        "description": "Pipeline: text-generation | Downloads: 1,000,000 | Likes: 5,000",
        "url": "https://huggingface.co/meta-llama/Llama-3-8B",
        "metadata": {"downloads": 1000000, "likes": 5000, "pipeline_tag": "text-generation"}
    }
]


def verify_imports():
    """Verify all modules can be imported."""
    print("[1/5] Verifying imports...")
    
    try:
        from agents import (
            SignalCollectorAgent,
            RelevanceAgent,
            RiskAgent,
            SynthesisAgent
        )
        from adapters.github import fetch_github_trending
        from adapters.arxiv import fetch_arxiv_papers
        from adapters.hackernews import fetch_hackernews_stories
        from adapters.medium import fetch_medium_blogs
        from adapters.huggingface import fetch_huggingface_models
        print("  ✓ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def verify_signal_collector():
    """Verify SignalCollectorAgent works with mock data."""
    print("[2/5] Verifying Signal Collector...")
    
    from agents import SignalCollectorAgent
    
    collector = SignalCollectorAgent()
    normalized = collector.collect(MOCK_SIGNALS)
    
    assert len(normalized) == len(MOCK_SIGNALS), "Signal count mismatch"
    assert all("collected_at" in s for s in normalized), "Missing timestamp"
    
    summary = collector.summarize_collection(normalized)
    print(f"  ✓ {summary}")
    return normalized


def verify_relevance_agent(signals: List[Dict]):
    """Verify RelevanceAgent works with mock data."""
    print("[3/5] Verifying Relevance Agent...")
    
    from agents import RelevanceAgent
    
    # Use fallback mode (no API key needed)
    agent = RelevanceAgent()
    
    scored = []
    for signal in signals:
        # Use fallback scoring directly
        result = agent._fallback_score(signal, "Mock mode")
        signal_with_score = {**signal, "relevance": result}
        scored.append(signal_with_score)
    
    assert all("relevance" in s for s in scored), "Missing relevance scores"
    print(f"  ✓ Scored {len(scored)} signals")
    return scored


def verify_risk_agent(signals: List[Dict]):
    """Verify RiskAgent works with mock data."""
    print("[4/5] Verifying Risk Agent...")
    
    from agents import RiskAgent
    
    agent = RiskAgent()
    
    assessed = []
    for signal in signals:
        # Use fallback assessment directly
        result = agent._fallback_assessment(signal, "Mock mode")
        signal_with_risk = {**signal, "risk": result}
        assessed.append(signal_with_risk)
    
    assert all("risk" in s for s in assessed), "Missing risk assessments"
    
    # Check that breaking change detection works
    breaking = [s for s in assessed if s.get("risk", {}).get("breaking_changes")]
    print(f"  ✓ Assessed {len(assessed)} signals ({len(breaking)} with breaking changes)")
    return assessed


def verify_synthesis_agent(signals: List[Dict]):
    """Verify SynthesisAgent produces valid digest."""
    print("[5/5] Verifying Synthesis Agent...")
    
    from agents import SynthesisAgent
    
    agent = SynthesisAgent()
    digest = agent.synthesize(signals)
    
    assert "generated_at" in digest, "Missing timestamp"
    assert "executive_summary" in digest, "Missing summary"
    assert "recommendations" in digest, "Missing recommendations"
    assert digest["total_signals"] == len(signals), "Signal count mismatch"
    
    print(f"  ✓ Generated digest with {len(digest['recommendations'])} recommendations")
    return digest


def run_verification():
    """Run complete verification suite."""
    print("=" * 60)
    print("🔍 DevPulseAI Verification Suite")
    print("=" * 60)
    print("\nUsing MOCK DATA - No network calls or API keys required.\n")
    
    try:
        # Step 1: Import verification
        if not verify_imports():
            raise AssertionError("Import verification failed")
        
        # Step 2: Signal collection
        normalized = verify_signal_collector()
        
        # Step 3: Relevance scoring
        scored = verify_relevance_agent(normalized)
        
        # Step 4: Risk assessment
        assessed = verify_risk_agent(scored)
        
        # Step 5: Synthesis
        digest = verify_synthesis_agent(assessed)
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 Verification Summary")
        print("=" * 60)
        print(f"  • Signals processed: {digest['total_signals']}")
        print(f"  • Summary: {digest['executive_summary']}")
        print(f"  • Recommendations: {len(digest['recommendations'])}")
        
        print("\n" + "=" * 60)
        print("[OK] DevPulseAI reference pipeline executed successfully")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Verification failed: {e}")
        return False


if __name__ == "__main__":
    success = run_verification()
    exit(0 if success else 1)
