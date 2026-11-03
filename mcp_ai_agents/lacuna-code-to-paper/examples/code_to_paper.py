# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp==2.3.0"]
# ///
"""Trace a public ML repository to recorded paper links through Lacuna MCP.

Run: uv run examples/code_to_paper.py
No model API key is needed. This is a bounded retrieval workflow, not an LLM.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from time import perf_counter
from typing import Any
from urllib.parse import urlparse

from mcp import Client

MCP_URL = "https://lacuna.tiptreesystems.com/api/mcp"


def github_key(value: str) -> str:
    """Normalize a public GitHub repository URL or owner/name, without guessing aliases."""
    value = value.strip()
    if "://" in value:
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or parsed.hostname != "github.com":
            raise ValueError("Use a public github.com repository URL or owner/name.")
        value = parsed.path.strip("/")
    key = value.rstrip("/").removesuffix(".git").lower()
    if len(key.split("/")) != 2 or not all(key.split("/")):
        raise ValueError("Use owner/name, not a file URL or a bare repository name.")
    return key


def select_resource(results: list[dict[str, Any]], repository: str) -> dict[str, Any]:
    """Require one identity match; a high search rank alone is not enough."""
    wanted = github_key(repository)
    matches = {}
    for item in results:
        if item.get("provider") != "github":
            continue
        for field in ("provider_key", "title", "canonical_url", "url"):
            try:
                matched = github_key(item.get(field) or "") == wanted
            except ValueError:
                continue
            if matched and item.get("id"):
                matches[item["id"]] = item
    if len(matches) != 1:
        candidates = [item.get("title", item.get("id")) for item in results]
        raise ValueError(
            f"Expected one exact repository match, found {len(matches)}. "
            f"Inspect these candidates or refine --query: {candidates}"
        )
    return next(iter(matches.values()))


async def call_json(client: Client, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Read structured MCP data or its JSON text fallback, surfacing tool errors."""
    result = await client.call_tool(name, arguments)
    if result.is_error:
        message = "\n".join(block.text for block in result.content if block.type == "text")
        raise RuntimeError(f"{name}: {message}")
    data = result.structured_content
    if data is None:
        text = "\n".join(block.text for block in result.content if block.type == "text")
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{name} returned a non-object payload")
    return data


async def trace_repository(
    repository: str = "Dao-AILab/flash-attention",
    query: str = "FlashAttention",
    max_papers: int = 3,
    *,
    server: Any = MCP_URL,
) -> dict[str, Any]:
    """Search, resolve a repository, and follow a bounded set of recorded paper edges."""
    github_key(repository)
    if not 1 <= max_papers <= 10:
        raise ValueError("max_papers must be between 1 and 10")
    started = perf_counter()
    calls = []
    async with Client(server, read_timeout_seconds=60) as client:

        async def read(name: str, **arguments: Any) -> dict[str, Any]:
            calls.append({"tool": name, "arguments": arguments})
            return await call_json(client, name, arguments)

        search = await read(
            "search_lacuna", query=query, search_type="resource", resource_kind="codebase", limit=5
        )
        selected = select_resource(search.get("results", []), repository)
        resource = await read("get_resource", resource_id_or_url=selected["id"])
        edges = resource.get("publications") or []
        papers = []
        seen = set()
        for edge in edges:
            paper_id = edge.get("paper_id")
            if not paper_id or paper_id in seen:
                continue
            seen.add(paper_id)
            paper = await read(
                "get_paper", artifact_id_or_url=paper_id, view="context", figure_limit=0
            )
            papers.append(
                {
                    "paper_id": paper_id,
                    "title": paper.get("title"),
                    "year": paper.get("year"),
                    "lacuna_url": paper.get("url"),
                    "relationship": edge.get("relationship"),
                    "evidence_url": edge.get("evidence_url"),
                    "identifiers": paper.get("identifiers", {}),
                }
            )
            if len(papers) == max_papers:
                break

    return {
        "retrieved_at": datetime.now(UTC).isoformat(),
        "repository": repository,
        "resource_id": selected["id"],
        "resource_url": selected.get("context_url"),
        "external_url": resource.get("url"),
        "resource_collected_at": resource.get("collected_at"),
        "papers": papers,
        "publication_edges_returned": len(edges),
        "papers_fetched": len(papers),
        "tool_calls": calls,
        "elapsed_seconds": round(perf_counter() - started, 3),
        "note": (
            "Relationships are records in Lacuna. Inspect the linked sources to verify them. "
            "An empty or bounded result does not establish that no other papers exist."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default="Dao-AILab/flash-attention")
    parser.add_argument("--query", default="FlashAttention")
    parser.add_argument("--max-papers", type=int, default=3)
    args = parser.parse_args()
    result = asyncio.run(trace_repository(args.repository, args.query, args.max_papers))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
