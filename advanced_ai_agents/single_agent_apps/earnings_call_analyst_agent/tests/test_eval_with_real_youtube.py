"""Real-LLM, real-YouTube eval driven by monocle_test_tools.

Counterpart to ``test_eval_with_real_llm.py``: that test seeds a synthetic
transcript so it can assert against known facts; this test runs the live
agent against an actual public earnings call so the Okahu evaluation
templates score against a real transcript that the model has not seen
prepared into it.

Default video: Google (Alphabet) earnings call —
``https://www.youtube.com/watch?v=LPJoiDiVkTI``. Override with
``YOUTUBE_EVAL_URL`` env var. Skip the test by exporting
``SKIP_YOUTUBE_EVAL=true``.

Required env: ``GOOGLE_API_KEY``, ``OKAHU_API_KEY``,
``OKAHU_INGESTION_ENDPOINT``, ``OKAHU_EVALUATION_ENDPOINT``. See the
README "Run the eval suite" section for the full prerequisite list.
"""

from __future__ import annotations

import os

import pytest

from earnings_call_analyst_agent.schemas import ResearchPack


DEFAULT_YOUTUBE_URL = "https://www.youtube.com/watch?v=LPJoiDiVkTI"

# Cap the chunks we hand the model so a 45-minute earnings call does not
# balloon the prompt past Gemini's input window. 40 chunks at the 45s
# default window covers ~30 minutes of call — enough material for the
# Okahu evaluation templates to score against.
MAX_CHUNKS = 40


@pytest.fixture(scope="session", autouse=True)
def _require_real_llm_env():
    if os.getenv("SKIP_YOUTUBE_EVAL", "").lower() in {"1", "true", "yes"}:
        pytest.skip("SKIP_YOUTUBE_EVAL set — skipping real-YouTube eval suite")
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.fail(
            "GOOGLE_API_KEY is not set. This is a real-LLM eval test and must not be skipped. "
            "Source the repo .env first."
        )
    if not os.getenv("OKAHU_API_KEY"):
        pytest.fail(
            "OKAHU_API_KEY is not set. The Okahu evaluation checks below need a valid key "
            "for the same tenant the project .mcp.json queries."
        )
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")
    os.environ.setdefault("EARNINGS_GEMINI_MODEL", "gemini-2.5-flash")
    os.environ.setdefault("EARNINGS_SEARCH_GEMINI_MODEL", "gemini-2.5-flash")
    os.environ.setdefault("MONOCLE_EXPORTER", "okahu,file")
    os.environ.setdefault("MONOCLE_TEST_WORKFLOW_NAME", "earnings_call_analyst_eval")


def test_real_youtube_call_with_okahu_evaluations(monocle_trace_asserter):
    """End-to-end run against a real public earnings call YouTube video.

    Pulls the transcript through the same ``youtube_ingest`` pipeline the
    FastAPI demo uses, runs the agent on the first ``MAX_CHUNKS`` of
    transcript, and validates the resulting Monocle trace through the
    ``monocle_test_tools`` fluent API.

    The four Okahu evaluation templates each score the model's output
    against the **actual transcript chunks** the agent received on this
    run (captured in the trace's ``data.input`` event), so the checks
    are content-aware to whichever video URL was supplied — no facts
    are pre-seeded into the test code.
    """
    from earnings_call_analyst_agent.telemetry import setup_telemetry
    setup_telemetry(workflow_name="earnings_call_analyst_eval")

    from earnings_call_analyst_agent.youtube_ingest import (
        chunk_transcript,
        extract_video_id,
        fetch_video_metadata,
        load_transcript,
    )
    from earnings_call_analyst_agent.agent import generate_insights

    url = os.getenv("YOUTUBE_EVAL_URL", DEFAULT_YOUTUBE_URL)
    video_id = extract_video_id(url)
    metadata = fetch_video_metadata(url, video_id)
    segments, _source = load_transcript(video_id)
    assert segments, (
        f"No transcript segments returned for {url}. Either the video has no "
        "captions and ADK audio transcription failed, or the video is unavailable."
    )

    chunks = chunk_transcript(segments)[:MAX_CHUNKS]
    assert chunks, f"chunk_transcript returned no chunks for {url}"

    research = ResearchPack(
        company=metadata.author_name or "Unknown company",
        ticker="",
        fiscal_period="",
        confidence=0.0,
    )

    events = generate_insights(metadata, research, chunks)
    assert events, (
        "Expected at least one InsightEvent from the real Gemini call against "
        f"{url}. Got an empty list."
    )

    # Structural trace checks via monocle_test_tools.
    monocle_trace_asserter.called_agent(
        "earnings_call_analyst_agent",
        message="No agentic.invocation span captured for the earnings analyst agent",
    )
    monocle_trace_asserter.under_token_limit(
        100000,
        message=(
            "Per-call token usage above the 100k guardrail — real-call transcripts "
            "are large but should not be unbounded"
        ),
    )
    monocle_trace_asserter.under_duration(
        300.0,
        units="seconds",
        span_type="workflow",
        message=(
            "End-to-end workflow exceeded 300s — real-call processing should "
            "stay under five minutes excluding Okahu evaluation submissions"
        ),
    )

    # Okahu cloud-side quality checks. Each one grades the model's output
    # against the actual transcript captured in this trace.
    monocle_trace_asserter.validator._trace_source = ""
    monocle_trace_asserter.with_evaluation("okahu") \
        .check_eval(
            "hallucination",
            expected="no_hallucination",
            fact_name="traces",
            message="Okahu flagged hallucination in the analyst output against real transcript",
        ) \
        .check_eval(
            "contextual_relevancy",
            expected="highly_relevant",
            fact_name="traces",
            message="Okahu flagged generated insights as not contextually relevant to the real transcript",
        ) \
        .check_eval(
            "summarization",
            expected=["excellent", "good"],
            fact_name="traces",
            message="Okahu rated the structured summarization below the 'good' bar",
        ) \
        .check_eval(
            "pii_leakage",
            not_expected="pii_leakage",
            fact_name="traces",
            message="Okahu flagged PII in the analyst output",
        )
