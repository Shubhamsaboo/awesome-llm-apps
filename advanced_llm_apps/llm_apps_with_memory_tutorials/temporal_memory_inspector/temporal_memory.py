"""Shared temporal-memory scenario for the Streamlit app and verifier."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lians import LocalLiansClient

AGENT_ID = "shipping-support-agent"
FACT_FILTER = {"entity": "order-1842", "field": "shipping_estimate"}
QUERY = "When will order 1842 ship?"
HISTORICAL_CUTOFF = datetime(2026, 8, 2, 12, tzinfo=UTC)


def seed_timeline(memory: LocalLiansClient) -> None:
    """Store a correction newest-first to avoid relying on insertion order."""
    memory.add(
        agent_id=AGENT_ID,
        content="Order 1842 shipping estimate changed to Monday",
        event_time=datetime(2026, 8, 2, 15, tzinfo=UTC),
        metadata=FACT_FILTER,
        source="synthetic-order-event",
    )
    memory.add(
        agent_id=AGENT_ID,
        content="Order 1842 shipping estimate is Friday",
        event_time=datetime(2026, 8, 1, 9, tzinfo=UTC),
        metadata=FACT_FILTER,
        source="synthetic-order-event",
    )


def recall(memory: LocalLiansClient, as_of: datetime | None = None) -> dict[str, Any]:
    """Recall the fact at the requested temporal boundary."""
    return memory.recall(
        agent_id=AGENT_ID,
        query=QUERY,
        filters=FACT_FILTER,
        as_of=as_of,
        k=3,
    )


def run_scenario(db_path: str | Path) -> dict[str, dict[str, Any]]:
    """Seed an isolated database and return current and historical recall."""
    with LocalLiansClient(
        db_path=db_path,
        embedding_provider="sentence-transformers",
    ) as memory:
        seed_timeline(memory)
        return {
            "current": recall(memory),
            "historical": recall(memory, as_of=HISTORICAL_CUTOFF),
        }


def contents(result: dict[str, Any]) -> list[str]:
    """Extract human-readable memory contents from a recall result."""
    return [item["content"] for item in result["memories"]]
