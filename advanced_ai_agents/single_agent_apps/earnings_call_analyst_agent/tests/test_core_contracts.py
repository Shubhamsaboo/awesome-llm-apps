import pytest

from earnings_call_analyst_agent.schemas import (
    InsightEvent,
    ResearchDocument,
    ResearchPack,
    TranscriptSegment,
    VideoMetadata,
)
from earnings_call_analyst_agent.adk_runtime import (
    _ensure_google_api_key_alias,
    adk_auth_mode,
    has_adk_credentials,
    parse_json_object,
)
from earnings_call_analyst_agent.agent import (
    _chunk_signal_score,
    _realign_event_times,
    generate_insights,
)
from earnings_call_analyst_agent.research import build_research_pack, fetch_market_news
from earnings_call_analyst_agent.youtube_ingest import (
    chunk_transcript,
    extract_video_id,
    load_transcript,
    parse_transcribed_segments,
)


@pytest.mark.parametrize(
    ("url", "video_id"),
    [
        ("https://www.youtube.com/watch?v=abcDEF12345", "abcDEF12345"),
        ("https://youtu.be/abcDEF12345?t=120", "abcDEF12345"),
        ("https://www.youtube.com/live/abcDEF12345?si=x", "abcDEF12345"),
        ("abcDEF12345", "abcDEF12345"),
    ],
)
def test_extract_video_id_handles_common_youtube_urls(url, video_id):
    assert extract_video_id(url) == video_id


def test_extract_video_id_rejects_invalid_values():
    with pytest.raises(ValueError):
        extract_video_id("https://example.com/not-youtube")


def test_chunk_transcript_combines_segments_until_window_limit():
    segments = [
        TranscriptSegment(start=0, duration=3, text="Good afternoon everyone."),
        TranscriptSegment(start=3, duration=3, text="Revenue grew twelve percent."),
        TranscriptSegment(start=9, duration=3, text="Margins expanded by 80 basis points."),
    ]

    chunks = chunk_transcript(segments, window_seconds=7)

    assert len(chunks) == 2
    assert chunks[0].start == 0
    assert chunks[0].end == 6
    assert "Revenue grew" in chunks[0].text
    assert chunks[1].start == 9
    assert chunks[1].end == 12


def test_insight_event_reveal_order_uses_start_time_then_severity():
    events = [
        InsightEvent(
            id="later",
            start_time=20,
            end_time=25,
            agent="cfo_tone",
            severity="low",
            headline="Later",
            quote="Later quote",
            confidence=0.6,
        ),
        InsightEvent(
            id="high",
            start_time=10,
            end_time=13,
            agent="surprise_detector",
            severity="high",
            headline="High",
            quote="High quote",
            confidence=0.9,
        ),
        InsightEvent(
            id="medium",
            start_time=10,
            end_time=14,
            agent="numbers_reconciler",
            severity="medium",
            headline="Medium",
            quote="Medium quote",
            confidence=0.8,
        ),
    ]

    assert [event.id for event in sorted(events)] == ["high", "medium", "later"]


def test_realign_event_times_snaps_quote_to_caption_segment():
    chunks = chunk_transcript(
        [
            TranscriptSegment(start=0, duration=4, text="Welcome to the earnings call."),
            TranscriptSegment(start=12, duration=5, text="Revenue grew twelve percent in the quarter."),
            TranscriptSegment(start=21, duration=4, text="Operating margin also improved."),
        ],
        window_seconds=60,
    )
    event = InsightEvent(
        id="metric",
        start_time=0,
        end_time=4,
        agent="numbers_reconciler",
        severity="medium",
        headline="Revenue growth called out",
        quote="Revenue grew twelve percent",
        confidence=0.8,
    )

    [realigned] = _realign_event_times([event], chunks)

    assert realigned.start_time == pytest.approx(11.65)
    assert realigned.end_time == 17


def test_realign_event_times_prefers_where_quote_begins_for_spanning_quotes():
    chunks = chunk_transcript(
        [
            TranscriptSegment(start=18, duration=4, text="We're no strangers to love."),
            TranscriptSegment(start=22, duration=4, text="You know the rules and so do I."),
        ],
        window_seconds=60,
    )
    event = InsightEvent(
        id="context",
        start_time=22,
        end_time=26,
        agent="market_narrator",
        severity="low",
        headline="Not an earnings call",
        quote="We're no strangers to love You know the rules and so do I",
        confidence=0.8,
    )

    [realigned] = _realign_event_times([event], chunks)

    assert realigned.start_time == pytest.approx(17.65)


def test_research_pack_handles_null_ticker_from_identity(monkeypatch):
    monkeypatch.setattr(
        "earnings_call_analyst_agent.research.infer_company_identity",
        lambda *_: {
            "company": "Example Co",
            "ticker": None,
            "fiscal_period": None,
            "peers": None,
            "confidence": 0.2,
        },
    )

    pack = build_research_pack(
        metadata=type(
            "Metadata",
            (),
            {"title": "Example Q4 earnings call", "author_name": "Example IR"},
        )(),
        transcript=[TranscriptSegment(start=0, duration=1, text="Welcome to the call.")],
    )

    assert pack.company == "Example Co"
    assert pack.ticker == ""
    assert pack.peers == []


def test_load_transcript_falls_back_to_audio_transcription(monkeypatch):
    def captions_fail(_video_id):
        raise RuntimeError("Subtitles are disabled for this video")

    monkeypatch.setattr("earnings_call_analyst_agent.youtube_ingest.fetch_transcript", captions_fail)
    monkeypatch.setattr(
        "earnings_call_analyst_agent.youtube_ingest.transcribe_audio_with_adk",
        lambda video_id: [TranscriptSegment(start=0, duration=5, text="Fallback transcript")],
    )

    segments, source = load_transcript("abcDEF12345")

    assert source == "adk_audio"
    assert segments[0].text == "Fallback transcript"


def test_fetch_market_news_prefers_adk_grounded_search(monkeypatch):
    grounded = [
        ResearchDocument(
            title="Tesla shares rise after delivery update - Reuters",
            kind="news",
            url="https://www.reuters.com/example",
        )
    ]
    monkeypatch.setattr("earnings_call_analyst_agent.research.fetch_adk_grounded_news", lambda *_args, **_kwargs: grounded)

    assert fetch_market_news("TSLA", "Tesla") == grounded


def test_fetch_market_news_does_not_use_non_adk_fallbacks(monkeypatch):
    monkeypatch.setattr("earnings_call_analyst_agent.research.fetch_adk_grounded_news", lambda *_args, **_kwargs: [])

    assert fetch_market_news("TSLA", "Tesla") == []


def test_generate_insights_does_not_emit_local_heuristic_cards_without_adk(monkeypatch):
    monkeypatch.setattr("earnings_call_analyst_agent.agent.has_adk_credentials", lambda: False)
    chunks = chunk_transcript(
        [TranscriptSegment(start=0, duration=5, text="Revenue grew 12 percent and margin expanded.")],
        window_seconds=60,
    )

    insights = generate_insights(
        VideoMetadata(video_id="abcDEF12345", title="Example Q4 earnings call"),
        ResearchPack(company="Example Co", ticker="EXM"),
        chunks,
    )

    assert insights == []


def test_generate_insights_uses_adk_agent_path(monkeypatch):
    monkeypatch.setattr("earnings_call_analyst_agent.agent.has_adk_credentials", lambda: True)
    monkeypatch.setattr("earnings_call_analyst_agent.agent.root_agent", object())
    monkeypatch.setattr(
        "earnings_call_analyst_agent.agent.run_adk_agent_text",
        lambda *_args, **_kwargs: """
        {"insights": [{
          "start_time": 0,
          "end_time": 5,
          "agent": "numbers_reconciler",
          "severity": "medium",
          "headline": "Revenue growth called out",
          "quote": "Revenue grew 12 percent",
          "confidence": 0.82,
          "explanation": "Revenue acceleration matters for investor expectations.",
          "mini_viz": {"type": "metric_table", "title": "Revenue", "rows": [["Current", "12%"]]},
          "citations": [{"label": "Transcript segment", "source": "YouTube captions"}]
        }]}
        """,
    )
    chunks = chunk_transcript(
        [TranscriptSegment(start=0, duration=5, text="Revenue grew 12 percent and margin expanded.")],
        window_seconds=60,
    )

    insights = generate_insights(
        VideoMetadata(video_id="abcDEF12345", title="Example Q4 earnings call"),
        ResearchPack(company="Example Co", ticker="EXM"),
        chunks,
    )

    assert [insight.headline for insight in insights] == ["Revenue growth called out"]


def test_gemini_key_is_aliased_for_adk(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    _ensure_google_api_key_alias()

    assert __import__("os").environ["GOOGLE_API_KEY"] == "test-key"


def test_vertex_ai_env_counts_as_adk_credentials(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "True")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo-project")

    assert has_adk_credentials() is True
    assert adk_auth_mode() == "vertex_ai"


def test_missing_vertex_project_does_not_count_as_adk_credentials(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "True")

    assert has_adk_credentials() is False
    assert adk_auth_mode() == "missing"


def test_parse_transcribed_segments_accepts_json_with_code_fences():
    text = """
    ```json
    {"segments": [
      {"start": 0, "duration": 4.5, "text": "Welcome to the call."},
      {"start": 4.5, "end": 9, "text": "Revenue grew this quarter."}
    ]}
    ```
    """

    segments = parse_transcribed_segments(text)

    assert [segment.text for segment in segments] == [
        "Welcome to the call.",
        "Revenue grew this quarter.",
    ]
    assert segments[1].duration == 4.5


def test_shared_json_parser_accepts_fenced_json():
    assert parse_json_object('```json\n{"ok": true}\n```') == {"ok": True}


def test_signal_score_ignores_short_terms_inside_other_words():
    # "said", "remain", "maintain" contain "ai"; "steps" and "keeps" contain "eps".
    boilerplate = "As I said, we remain focused and maintain our steps. It keeps going."

    assert _chunk_signal_score(boilerplate) == 0


def test_signal_score_counts_short_terms_as_whole_words():
    assert _chunk_signal_score("AI demand lifted EPS. AI-driven margins.") == 5
