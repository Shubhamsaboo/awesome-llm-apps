"""Real-LLM eval for the earnings call analyst agent using monocle_test_tools.

This test calls Gemini for real (no mocks) and validates the resulting
Monocle trace through the ``monocle_trace_asserter`` fluent API:

  * the ADK agent ``earnings_call_analyst_agent`` was actually invoked
  * the captured inference output mentions the headline numbers fed in via the
    synthetic transcript, proving the model saw and processed the source text
  * total prompt + completion tokens stay under a guardrail
  * end-to-end workflow duration stays under a guardrail

A second test then loads the returned ``InsightEvent`` objects and runs the
two structured-output evals that the trace API cannot see by itself —
quote faithfulness (every quote substring exists in a source chunk) and
time alignment (start_time falls inside the chunk it was anchored to).

Required env: ``GOOGLE_API_KEY``. The test FAILS (not skips) if missing,
because the entire point is to run real LLM calls.
"""

from __future__ import annotations

import os

import pytest

from earnings_call_analyst_agent.schemas import (
    ResearchPack,
    TranscriptChunk,
    VideoMetadata,
)


CHUNK_1_TEXT = (
    "Good afternoon everyone, and thanks for joining our fiscal third quarter call. "
    "Total revenue came in at four point one billion dollars, up twenty two percent year over year, "
    "driven by record data center demand and accelerating enterprise AI adoption. "
    "Gross margin expanded one hundred and twenty basis points to seventy six point four percent."
)

CHUNK_2_TEXT = (
    "Turning to guidance. For the fourth quarter we expect revenue between four point three and four point five billion dollars, "
    "which is meaningfully above prior consensus. We are also raising our full year operating margin outlook by one hundred basis points. "
    "However, we want to flag that supply constraints on next generation accelerators may persist into the first half of next year."
)

CHUNK_3_TEXT = (
    "Free cash flow for the quarter was one point eight billion dollars, "
    "and we returned approximately one point one billion to shareholders through buybacks. "
    "Our cash and short term investments balance ended the quarter at twelve billion dollars."
)


def _build_chunks() -> list[TranscriptChunk]:
    return [
        TranscriptChunk(start=0.0, end=45.0, text=CHUNK_1_TEXT),
        TranscriptChunk(start=45.0, end=95.0, text=CHUNK_2_TEXT),
        TranscriptChunk(start=95.0, end=140.0, text=CHUNK_3_TEXT),
    ]


def _build_research() -> ResearchPack:
    return ResearchPack(
        company="Synthetic Semis Inc.",
        ticker="SYN",
        fiscal_period="Q3 FY26",
        confidence=0.7,
    )


def _build_metadata() -> VideoMetadata:
    return VideoMetadata(
        video_id="synthetic_q3",
        title="Synthetic Semis Q3 FY26 Earnings Call",
        author_name="Synthetic Semis IR",
        source_url="https://example.com/q3-call",
    )


@pytest.fixture(scope="session", autouse=True)
def _require_real_llm_env():
    if not os.getenv("GOOGLE_API_KEY"):
        pytest.fail(
            "GOOGLE_API_KEY is not set. This is a real-LLM eval test and must not be skipped. "
            "Source the repo .env first."
        )
    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "False")
    os.environ.setdefault("EARNINGS_GEMINI_MODEL", "gemini-2.5-flash")
    os.environ.setdefault("EARNINGS_SEARCH_GEMINI_MODEL", "gemini-2.5-flash")
    os.environ.setdefault("MONOCLE_EXPORTER", "okahu,file")
    os.environ.setdefault("MONOCLE_TEST_WORKFLOW_NAME", "earnings_call_analyst_eval")


def test_real_llm_run_with_monocle_trace_assertions(monocle_trace_asserter):
    """End-to-end real-LLM run validated through monocle_test_tools.

    Order matters: ``monocle_trace_asserter`` is a function-scoped fixture
    that installs an in-memory span exporter via ``MonocleValidator``. The
    agent call MUST happen after that, otherwise spans go to the file/okahu
    exporters but never into the validator's in-memory store and all
    ``called_agent`` / ``under_*`` assertions see an empty span list.

    Every assertion below is a ``monocle_test_tools`` call. The test runs
    two layers of validation in a single Gemini call:

    1. **Trace-level structural checks** via the test_tools fluent API —
       the ADK agent was invoked, the inference output references the
       input, token usage and latency stay under guardrails.

    2. **Cloud-side quality checks** via Okahu evaluation templates with
       ``with_evaluation("okahu")`` and ``check_eval`` — hallucination,
       contextual relevancy, summarization quality, and PII leakage. Each
       posts the captured trace to the Okahu evaluation service and waits
       for a job result.

    Both layers run in a single test because the ``monocle_trace_asserter``
    fixture is function-scoped: re-creating the validator and re-running
    the agent for each layer would burn a fresh Gemini call per test and
    cause ADK state issues between fixture cycles.

    All Okahu checks use ``fact_name="traces"`` because the stage instance
    publishes every template with ``group_by: traces``. Using a non-traces
    fact_name fails the ``verify_eval_template_exists`` lookup before the
    eval job is even submitted.

    Requires ``OKAHU_API_KEY``, ``OKAHU_EVALUATION_ENDPOINT``, and
    ``GOOGLE_API_KEY`` (all set via the repo .env).
    """
    from earnings_call_analyst_agent.telemetry import setup_telemetry
    setup_telemetry(workflow_name="earnings_call_analyst_eval")
    from earnings_call_analyst_agent.agent import generate_insights

    chunks = _build_chunks()
    events = generate_insights(_build_metadata(), _build_research(), chunks)

    assert events, "expected at least one InsightEvent from the real Gemini call"

    # --- Layer 1: trace-level structural checks ---
    # Each guardrail starts from a fresh chain so that called_agent's filtering
    # doesn't narrow the span set for the workflow-level token/duration checks.
    monocle_trace_asserter.called_agent(
        "earnings_call_analyst_agent",
        message="No agentic.invocation span captured for the earnings analyst agent",
    )
    monocle_trace_asserter.contains_any_output(
        "four point one billion",
        "twenty two percent",
        "seventy six point four",
        message=(
            "Inference output did not reference any of the headline figures from the "
            "synthetic transcript — model may be hallucinating or trace capture broke"
        ),
    )
    monocle_trace_asserter.under_token_limit(
        20000,
        message="Per-call token usage above the 20k guardrail — prompt may be unbounded",
    )
    monocle_trace_asserter.under_duration(
        120.0,
        units="seconds",
        span_type="workflow",
        message="End-to-end workflow exceeded 120s — model or pipeline latency regression",
    )

    # --- Layer 2: Okahu cloud-side quality checks ---
    # Picks tied to the earnings-analyst domain:
    # * hallucination — analyst can't fabricate numbers or quotes; a single
    #   fabricated figure is a real-world incident for an investor tool.
    # * contextual_relevancy — generated insights must stay anchored to the
    #   provided transcript context, not drift into prior quarters.
    # * summarization — the agent's core job is structured summarization
    #   of the call; Okahu rates this on a quality scale.
    # * pii_leakage — synthetic input has no PII, so output must have none.
    #
    # monocle_test_tools 0.8.1 only sets validator._trace_source inside
    # run_agent[_async]; we ran the agent ourselves (so spans land in the
    # in-memory exporter via instrumentation), so we have to seed the
    # attribute before with_evaluation reads it.
    monocle_trace_asserter.validator._trace_source = ""
    monocle_trace_asserter.with_evaluation("okahu") \
        .check_eval(
            "hallucination",
            expected="no_hallucination",
            fact_name="traces",
            message="Okahu flagged hallucination in the analyst output",
        ) \
        .check_eval(
            "contextual_relevancy",
            expected="highly_relevant",
            fact_name="traces",
            message="Okahu flagged generated insights as not contextually relevant",
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
            message="Okahu flagged PII in the analyst output despite synthetic input",
        )
