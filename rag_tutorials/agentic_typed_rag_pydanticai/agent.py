"""Pydantic AI agent, typed retrieval tool, and grounding guardrails."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_ai import Agent, RunContext

from rag import InMemoryVectorStore


DEFAULT_MIN_RELEVANCE = 0.2
REFUSAL_TEXT = (
    "I do not have enough evidence in the indexed sources to answer that question."
)
DEFAULT_MODELS = {
    "openai": "openai:gpt-5.2",
    "anthropic": "anthropic:claude-sonnet-4-6",
}


class Citation(BaseModel):
    """An exact quote that connects an answer to one stored chunk."""

    source: str = Field(description="Source document name or URL")
    chunk_id: str = Field(description="Stable identifier returned by retrieve")
    quoted_span: str = Field(description="Short verbatim quote from the chunk")

    @field_validator("source", "chunk_id", "quoted_span")
    @classmethod
    def values_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("citation values must not be blank")
        return value


class Answer(BaseModel):
    """Validated output rendered by the Streamlit app."""

    text: str
    citations: list[Citation]
    confidence: float = Field(ge=0.0, le=1.0)
    answered: bool

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must not be blank")
        return value

    @model_validator(mode="after")
    def answer_and_citations_must_agree(self) -> "Answer":
        if self.answered and not self.citations:
            raise ValueError("answered responses require at least one citation")
        if not self.answered and self.citations:
            raise ValueError("refused responses must not contain citations")
        return self

    @classmethod
    def insufficient_evidence(cls, top_score: float = 0.0) -> "Answer":
        return cls(
            text=REFUSAL_TEXT,
            citations=[],
            confidence=round(min(max(top_score, 0.0), 1.0), 3),
            answered=False,
        )


class RetrievedChunk(BaseModel):
    """A serializable chunk returned by the retrieve tool."""

    source: str
    chunk_id: str
    text: str
    score: float = Field(ge=0.0, le=1.0)


class RetrievalEvidence(BaseModel):
    """The typed result of one vector search."""

    query: str
    enough_evidence: bool
    top_score: float = Field(ge=0.0, le=1.0)
    chunks: list[RetrievedChunk]


@dataclass
class RagDependencies:
    """Per-run resources injected into tools through RunContext."""

    store: InMemoryVectorStore
    min_relevance: float = DEFAULT_MIN_RELEVANCE
    top_k: int = 4


AGENT_INSTRUCTIONS = """
You answer questions only from evidence returned by the retrieve tool.

Rules:
1. Always call retrieve before producing the final output.
2. If retrieve returns enough_evidence=false, set answered=false, use no citations,
   and say that the indexed sources do not contain enough evidence.
3. If enough evidence exists, answer only claims supported by returned chunks.
4. Every citation must copy source and chunk_id exactly from retrieve.
5. quoted_span must be a short verbatim substring of that chunk's text.
6. confidence is a number from 0 to 1. Lower it when evidence is partial.
7. Never use background knowledge to fill a gap in the sources.
""".strip()


rag_agent: Agent[RagDependencies, Answer] = Agent(
    deps_type=RagDependencies,
    output_type=Answer,
    instructions=AGENT_INSTRUCTIONS,
    retries=2,
)


async def retrieve_evidence(deps: RagDependencies, query: str) -> RetrievalEvidence:
    """Search dependencies and expose the relevance decision as typed data."""
    results = await deps.store.search(query, limit=deps.top_k)
    top_score = results[0].score if results else 0.0
    return RetrievalEvidence(
        query=query,
        enough_evidence=bool(results and top_score >= deps.min_relevance),
        top_score=top_score,
        chunks=[
            RetrievedChunk(
                source=result.chunk.source,
                chunk_id=result.chunk.chunk_id,
                text=result.chunk.text,
                score=result.score,
            )
            for result in results
        ],
    )


@rag_agent.tool
async def retrieve(ctx: RunContext[RagDependencies], query: str) -> RetrievalEvidence:
    """Retrieve source chunks relevant to the user's question."""
    return await retrieve_evidence(ctx.deps, query)


def resolve_model_name() -> str:
    """Resolve a configured Pydantic AI model from environment variables."""
    if configured := os.getenv("RAG_MODEL", "").strip():
        return configured
    if os.getenv("OPENAI_API_KEY"):
        return DEFAULT_MODELS["openai"]
    if os.getenv("ANTHROPIC_API_KEY"):
        return DEFAULT_MODELS["anthropic"]
    raise RuntimeError(
        "Set OPENAI_API_KEY or ANTHROPIC_API_KEY before asking a question"
    )


def model_for_provider(provider: str) -> str:
    """Return a default model name for a UI provider selection."""
    normalized = provider.strip().casefold()
    try:
        return DEFAULT_MODELS[normalized]
    except KeyError as exc:
        raise ValueError(f"Unsupported provider: {provider}") from exc


def _normalize_quote(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _valid_citations(answer: Answer, deps: RagDependencies) -> list[Citation]:
    valid = []
    for citation in answer.citations:
        chunk = deps.store.find_chunk(citation.source, citation.chunk_id)
        quoted_span = _normalize_quote(citation.quoted_span)
        if (
            chunk
            and len(quoted_span) >= 8
            and quoted_span in _normalize_quote(chunk.text)
        ):
            valid.append(citation)
    return valid


def _used_retrieve(messages: list[Any]) -> bool:
    return any(
        getattr(part, "tool_name", None) == "retrieve"
        and getattr(part, "part_kind", None) in {"tool-call", "tool-return"}
        for message in messages
        for part in message.parts
    )


def validate_grounded_answer(
    answer: Answer,
    deps: RagDependencies,
    preflight: RetrievalEvidence,
    *,
    used_retrieve: bool,
) -> Answer:
    """Refuse outputs that skipped retrieval or cite text outside the store."""
    if not answer.answered:
        return Answer.insufficient_evidence(preflight.top_score)
    if not used_retrieve:
        return Answer.insufficient_evidence(preflight.top_score)

    citations = _valid_citations(answer, deps)
    if not citations:
        return Answer.insufficient_evidence(preflight.top_score)
    return answer.model_copy(update={"citations": citations})


async def answer_question(
    question: str,
    deps: RagDependencies,
    model: str | None = None,
) -> Answer:
    """Run the typed agent only after a deterministic retrieval gate."""
    question = question.strip()
    if not question:
        raise ValueError("question must not be empty")

    preflight = await retrieve_evidence(deps, question)
    if not preflight.enough_evidence:
        return Answer.insufficient_evidence(preflight.top_score)

    run_options: dict[str, Any] = {"deps": deps}
    if model is not None:
        run_options["model"] = model
    result = await rag_agent.run(question, **run_options)
    return validate_grounded_answer(
        result.output,
        deps,
        preflight,
        used_retrieve=_used_retrieve(result.all_messages()),
    )
