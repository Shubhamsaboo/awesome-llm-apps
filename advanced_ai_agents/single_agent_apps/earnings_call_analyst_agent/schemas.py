from __future__ import annotations

from functools import total_ordering
from typing import Any, Literal, Union

from pydantic import BaseModel, Field


Severity = Literal["high", "medium", "low"]
AgentName = Literal[
    "numbers_reconciler",
    "cfo_tone",
    "peer_context",
    "surprise_detector",
    "filing_grounder",
    "market_narrator",
]


class TranscriptSegment(BaseModel):
    start: float
    duration: float = 0
    text: str

    @property
    def end(self) -> float:
        return self.start + self.duration


class TranscriptChunk(BaseModel):
    start: float
    end: float
    text: str
    segments: list[TranscriptSegment] = Field(default_factory=list)


class MiniVisualization(BaseModel):
    type: str = "note"
    title: str = ""
    rows: list[list[str]] = Field(default_factory=list)
    points: list[float] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    label: str
    source: str = ""
    url: str = ""


@total_ordering
class InsightEvent(BaseModel):
    id: str
    start_time: float
    end_time: float
    agent: Union[AgentName, str]
    severity: Severity
    headline: str
    quote: str
    confidence: float = Field(ge=0, le=1)
    explanation: str = ""
    mini_viz: MiniVisualization = Field(default_factory=MiniVisualization)
    citations: list[Citation] = Field(default_factory=list)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, InsightEvent):
            return NotImplemented
        severity_rank = {"high": 0, "medium": 1, "low": 2}
        return (
            self.start_time,
            severity_rank.get(self.severity, 9),
            self.id,
        ) < (
            other.start_time,
            severity_rank.get(other.severity, 9),
            other.id,
        )


class VideoMetadata(BaseModel):
    video_id: str
    title: str = "Untitled earnings call"
    author_name: str = ""
    thumbnail_url: str = ""
    source_url: str = ""


class ResearchDocument(BaseModel):
    title: str
    kind: str
    url: str = ""
    summary: str = ""


class ResearchPack(BaseModel):
    company: str = "Unknown company"
    ticker: str = ""
    fiscal_period: str = ""
    confidence: float = 0
    documents: list[ResearchDocument] = Field(default_factory=list)
    peers: list[str] = Field(default_factory=list)
    news: list[ResearchDocument] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AnalysisSession(BaseModel):
    session_id: str
    video: VideoMetadata
    transcript: list[TranscriptSegment]
    chunks: list[TranscriptChunk]
    research: ResearchPack
    insights: list[InsightEvent]
    status: Literal["ready", "partial", "error"]
    message: str = ""
    diagnostics: dict[str, Any] = Field(default_factory=dict)
