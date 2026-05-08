from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any

from .adk_runtime import run_adk_agent_text
from .schemas import (
    Citation,
    InsightEvent,
    MiniVisualization,
    ResearchPack,
    TranscriptChunk,
    TranscriptSegment,
    VideoMetadata,
)

MODEL = os.getenv("EARNINGS_GEMINI_MODEL", "gemini-3-flash-preview")


try:
    from google.adk.agents import LlmAgent

    root_agent = LlmAgent(
        name="earnings_call_analyst_agent",
        model=MODEL,
        description="Creates playback-synced investor insight cards from an earnings-call transcript and research pack.",
        instruction=(
            "Act like a skeptical public-equities analyst. Read timestamped transcript chunks and research context. "
            "Create only high-signal investor cards. Use the agent field to classify the card as "
            "numbers_reconciler, cfo_tone, peer_context, surprise_detector, filing_grounder, or market_narrator. "
            "Return strict JSON only. Never invent filings, peers, consensus, or quote text."
        ),
    )
except Exception:
    root_agent = None


def generate_insights(
    metadata: VideoMetadata,
    research: ResearchPack,
    chunks: list[TranscriptChunk],
    max_chunks: int = 64,
) -> list[InsightEvent]:
    selected = select_signal_chunks(chunks, limit=max_chunks)
    if _has_gemini_key() and root_agent is not None:
        insights = _generate_with_adk(metadata, research, selected)
        if insights:
            return sorted(_realign_event_times(insights, selected))
    return sorted(_realign_event_times(_generate_local_insights(research, selected), selected))


def select_signal_chunks(chunks: list[TranscriptChunk], limit: int = 64) -> list[TranscriptChunk]:
    scored = []
    for index, chunk in enumerate(chunks):
        score = _chunk_signal_score(chunk.text)
        if index < 4:
            score += 3
        scored.append((score, index, chunk))
    chosen = sorted(scored, key=lambda item: (-item[0], item[1]))[:limit]
    return [chunk for _, _, chunk in sorted(chosen, key=lambda item: item[1])]


def _generate_with_adk(
    metadata: VideoMetadata, research: ResearchPack, chunks: list[TranscriptChunk]
) -> list[InsightEvent]:
    if root_agent is None:
        return []

    context = _research_context(research)
    chunk_payload = [
        {"start": round(chunk.start, 2), "end": round(chunk.end, 2), "text": chunk.text[:1600]}
        for chunk in chunks
    ]
    prompt = f"""
You are powering a playback-synced analyst cockpit for a YouTube earnings call.
Act like a skeptical public-equities analyst, not a generic summarizer.
Return strict JSON only, with this shape:
{{"insights":[{{"start_time": number, "end_time": number, "agent": one of
["numbers_reconciler","cfo_tone","peer_context","surprise_detector","filing_grounder","market_narrator"],
"severity": "high"|"medium"|"low", "headline": string, "quote": exact transcript quote,
"confidence": number 0-1, "explanation": string,
"mini_viz": {{"type": string, "title": string, "rows": [[string,string]], "points": [number], "labels": [string]}},
"citations": [{{"label": string, "source": string, "url": string}}]}}]}}

Rules:
- Create at most 24 insights.
- Every insight must be anchored to a supplied transcript chunk time.
- Use quote text copied from the transcript chunk.
- Do not invent filings, peers, or consensus data. If research context is thin, say so.
- Prefer high-signal cards: guidance changes, margins, capex, cash flow, demand, backlog, pricing, churn, macro, AI, layoffs, litigation, CFO hedging, and contradictions against prior context.
- Do not create cards for generic greetings, boilerplate safe-harbor language, or vague upbeat statements unless they reveal a concrete investor signal.
- Numbers Reconciler cards must identify the metric, current value, and baseline if available. If no baseline exists, say "baseline not found" in mini_viz rows.
- CFO Tone cards must cite the exact words that indicate confidence, caution, hedging, defensiveness, or unusual emphasis.
- Peer Context cards must distinguish "sector-wide" vs "company-specific" and name the evidence source when available.
- Surprise Detector cards must explain why the statement is novel, contradictory, unusually specific, or likely market-moving.
- The explanation field must answer "why this matters to an investor" in one concise sentence.
- Make mini_viz compact and useful. Use rows for direct comparisons. Use points only for a real time series, and include matching labels and a title with the unit, such as "Monthly Token Volume (Quadrillions)".
- If a finding is weak, omit it.
- If the transcript does not appear to be an earnings call, return at most one low-severity market_narrator card saying the source does not look like an earnings call.

Video: {metadata.title}
Research context:
{context}

Transcript chunks:
{json.dumps(chunk_payload)}
"""
    try:
        payload = _parse_json_object(run_adk_agent_text(root_agent, prompt))
    except Exception:
        return []

    raw_insights = payload.get("insights", [])
    if not isinstance(raw_insights, list):
        return []

    events: list[InsightEvent] = []
    for raw in raw_insights:
        if not isinstance(raw, dict):
            continue
        try:
            event_id = raw.get("id") or _event_id(raw)
            mini_raw = raw.get("mini_viz") if isinstance(raw.get("mini_viz"), dict) else {}
            citations_raw = raw.get("citations") if isinstance(raw.get("citations"), list) else []
            events.append(
                InsightEvent(
                    id=event_id,
                    start_time=float(raw.get("start_time", 0)),
                    end_time=float(raw.get("end_time", raw.get("start_time", 0))),
                    agent=str(raw.get("agent", "market_narrator")),
                    severity=raw.get("severity", "low"),
                    headline=str(raw.get("headline", "")).strip()[:180],
                    quote=str(raw.get("quote", "")).strip()[:500],
                    confidence=float(raw.get("confidence", 0.5)),
                    explanation=str(raw.get("explanation", "")).strip()[:600],
                    mini_viz=MiniVisualization(**mini_raw),
                    citations=[Citation(**item) for item in citations_raw if isinstance(item, dict)],
                )
            )
        except Exception:
            continue
    return _dedupe_events([event for event in events if event.headline and event.quote])


def _generate_local_insights(
    research: ResearchPack, chunks: list[TranscriptChunk]
) -> list[InsightEvent]:
    events: list[InsightEvent] = []
    tone_points: list[float] = []
    for chunk in chunks[:80]:
        text = chunk.text
        lower = text.lower()
        numbers = re.findall(r"(?:\$?\d+(?:\.\d+)?\s*(?:%|percent|million|billion|basis points|bps)?)", text)
        if numbers and any(term in lower for term in ["revenue", "margin", "guidance", "cash", "eps", "growth"]):
            quote = _quote(text, numbers[0])
            events.append(
                InsightEvent(
                    id=_stable_id("numbers", chunk.start, quote),
                    start_time=chunk.start,
                    end_time=chunk.end,
                    agent="numbers_reconciler",
                    severity="medium",
                    headline=f"Numeric claim detected: {numbers[0]}",
                    quote=quote,
                    confidence=0.62,
                    explanation="Gemini analysis was unavailable, so this local pass flagged a financial metric for review.",
                    mini_viz=MiniVisualization(
                        type="metric_table",
                        title="Detected metric",
                        rows=[["Metric", numbers[0]], ["Context", _compact_context(lower)]],
                    ),
                    citations=_default_citations(research),
                )
            )
        hedge_count = sum(lower.count(term) for term in ["uncertain", "challenging", "headwind", "pressure", "cautious", "volatile"])
        confident_count = sum(lower.count(term) for term in ["confident", "strong", "record", "accelerat", "robust"])
        tone = max(0, min(100, 50 + confident_count * 10 - hedge_count * 12))
        tone_points.append(tone)
        if hedge_count >= 2:
            quote = _quote(text, "headwind" if "headwind" in lower else text.split()[0])
            events.append(
                InsightEvent(
                    id=_stable_id("tone", chunk.start, quote),
                    start_time=chunk.start,
                    end_time=chunk.end,
                    agent="cfo_tone",
                    severity="low",
                    headline="Tone shifted toward caution",
                    quote=quote,
                    confidence=0.58,
                    explanation="Local tone scan found clustered caution language in this segment.",
                    mini_viz=MiniVisualization(
                        type="tone_sparkline",
                        title="Tone score",
                        points=tone_points[-12:],
                    ),
                    citations=[Citation(label="Transcript segment", source="YouTube captions")],
                )
            )
    return _dedupe_events(events)[:30]


def _chunk_signal_score(text: str) -> int:
    lower = text.lower()
    terms = [
        "revenue",
        "guidance",
        "margin",
        "eps",
        "earnings",
        "cash flow",
        "free cash",
        "capex",
        "demand",
        "backlog",
        "pricing",
        "churn",
        "headwind",
        "tailwind",
        "uncertain",
        "confident",
        "ai",
        "layoff",
        "restructuring",
        "litigation",
    ]
    score = sum(lower.count(term) for term in terms)
    score += min(6, len(re.findall(r"\d", text)) // 8)
    return score


def _research_context(research: ResearchPack) -> str:
    docs = "\n".join(
        f"- {doc.kind}: {doc.title} {doc.url}" for doc in research.documents[:5]
    )
    news = "\n".join(f"- {item.title}: {item.summary}" for item in research.news[:8])
    peers = ", ".join(research.peers) or "Not resolved"
    notes = "; ".join(research.notes)
    return (
        f"Company: {research.company}\nTicker: {research.ticker}\n"
        f"Fiscal period: {research.fiscal_period}\nPeers: {peers}\n"
        f"Documents:\n{docs or '- None'}\nRecent news:\n{news or '- None'}\nNotes: {notes}"
    )


def _parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _dedupe_events(events: list[InsightEvent]) -> list[InsightEvent]:
    seen: set[tuple[str, int, str]] = set()
    deduped: list[InsightEvent] = []
    for event in sorted(events):
        key = (str(event.agent), round(event.start_time), event.headline.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)
    return deduped


def _event_id(raw: dict[str, Any]) -> str:
    return _stable_id(
        str(raw.get("agent", "")),
        raw.get("start_time", ""),
        str(raw.get("headline", "")),
    )


def _stable_id(*parts: object) -> str:
    digest = hashlib.sha1("|".join(str(part) for part in parts).encode()).hexdigest()
    return digest[:12]


def _has_gemini_key() -> bool:
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    return bool(os.getenv("GOOGLE_API_KEY"))


def _quote(text: str, needle: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sentence in sentences:
        if needle.lower() in sentence.lower():
            return sentence.strip()[:420]
    return text.strip()[:420]


def _compact_context(text: str) -> str:
    for term in ["revenue", "margin", "guidance", "cash", "eps", "growth"]:
        if term in text:
            return term
    return "financial statement"


def _default_citations(research: ResearchPack) -> list[Citation]:
    citations = [Citation(label="Transcript segment", source="YouTube captions")]
    if research.documents:
        doc = research.documents[0]
        citations.append(Citation(label=doc.kind, source=doc.title, url=doc.url))
    return citations


def _realign_event_times(
    events: list[InsightEvent], chunks: list[TranscriptChunk]
) -> list[InsightEvent]:
    segments = [
        segment
        for chunk in chunks
        for segment in chunk.segments
        if segment.text.strip()
    ]
    if not segments:
        return events

    realigned: list[InsightEvent] = []
    for event in events:
        segment = _best_quote_segment(event.quote, event.start_time, segments)
        if not segment:
            realigned.append(event)
            continue
        realigned.append(
            event.model_copy(
                update={
                    "start_time": max(0, segment.start - 0.35),
                    "end_time": max(segment.end, segment.start + 0.75),
                }
            )
        )
    return realigned


def _best_quote_segment(
    quote: str, fallback_time: float, segments: list[TranscriptSegment]
) -> TranscriptSegment | None:
    quote_tokens = _token_set(quote)
    if not quote_tokens:
        return min(segments, key=lambda segment: abs(segment.start - fallback_time), default=None)

    best: tuple[float, TranscriptSegment] | None = None
    normalized_quote = _normalize_text(quote)
    ordered_quote_tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", quote.lower())
        if len(token) > 2
    ]
    prefix_tokens = set(ordered_quote_tokens[: min(6, len(ordered_quote_tokens))])
    first_token = ordered_quote_tokens[0] if ordered_quote_tokens else ""
    second_token = ordered_quote_tokens[1] if len(ordered_quote_tokens) > 1 else ""
    for segment in segments:
        normalized_segment = _normalize_text(segment.text)
        segment_tokens = _token_set(segment.text)
        overlap = len(quote_tokens & segment_tokens) / max(1, len(quote_tokens))
        prefix_overlap = len(prefix_tokens & segment_tokens) / max(1, len(prefix_tokens))
        substring_bonus = 0.75 if normalized_quote and normalized_quote in normalized_segment else 0
        start_bonus = 0.9 if first_token and first_token in segment_tokens else 0
        start_bonus += 0.45 if second_token and second_token in segment_tokens else 0
        time_penalty = min(0.35, abs(segment.start - fallback_time) / 900)
        score = overlap + (prefix_overlap * 0.8) + substring_bonus + start_bonus - time_penalty
        if best is None or score > best[0]:
            best = (score, segment)

    if not best or best[0] < 0.22:
        return min(segments, key=lambda segment: abs(segment.start - fallback_time), default=None)
    return best[1]


def _token_set(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2
    }


def _normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))
