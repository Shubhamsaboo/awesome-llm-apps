import pytest

from earnings_call_analyst_agent.schemas import InsightEvent, ResearchDocument, TranscriptSegment
from earnings_call_analyst_agent.adk_runtime import _ensure_google_api_key_alias
from earnings_call_analyst_agent.agent import _realign_event_times
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
    monkeypatch.setattr("earnings_call_analyst_agent.research.fetch_yahoo_news", lambda *_args, **_kwargs: pytest.fail("Yahoo fallback should not run when ADK search resolves news"))

    assert fetch_market_news("TSLA", "Tesla") == grounded


def test_fetch_market_news_falls_back_when_adk_search_is_empty(monkeypatch):
    fallback = [
        ResearchDocument(
            title="Tesla stock update - MarketWatch",
            kind="news",
            url="https://www.marketwatch.com/example",
        )
    ]
    monkeypatch.setattr("earnings_call_analyst_agent.research.fetch_adk_grounded_news", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("earnings_call_analyst_agent.research.fetch_yahoo_news", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("earnings_call_analyst_agent.research.fetch_google_news", lambda *_args, **_kwargs: fallback)

    assert fetch_market_news("TSLA", "Tesla") == fallback


def test_gemini_key_is_aliased_for_adk(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    _ensure_google_api_key_alias()

    assert __import__("os").environ["GOOGLE_API_KEY"] == "test-key"


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
