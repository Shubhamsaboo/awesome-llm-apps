"""Read-only MCP retrieval over an explicitly supplied JSON activity log."""
import json
import os
from datetime import datetime
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("work-history")
DATA_PATH = Path(os.environ.get("ACTIVITY_FILE", Path(__file__).with_name("activity.json")))


def parse_time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamps must include a timezone")
    return result


def load_records() -> list[dict]:
    records = json.loads(DATA_PATH.read_text())
    seen = set()
    for record in records:
        for key in ("id", "timestamp", "app", "project", "text"):
            if not isinstance(record.get(key), str):
                raise ValueError(f"Every record needs a string {key}")
        parse_time(record["timestamp"])
        if record["id"] in seen:
            raise ValueError("Record IDs must be unique")
        seen.add(record["id"])
    return records


@mcp.tool()
def search_activity(query: str = "", project: str = "", start: str = "", end: str = "", limit: int = 10) -> dict:
    """Search activity with all query words, exact project, and [start, end) UTC/offset bounds.

    Returns source IDs and timestamps for citations. Empty query lists matching records.
    A missing result means no matching recorded evidence, not that no work occurred.
    """
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    lower, upper = parse_time(start) if start else None, parse_time(end) if end else None
    if lower and upper and lower >= upper:
        raise ValueError("start must precede end")
    words = query.casefold().split()
    matches = []
    for record in load_records():
        timestamp = parse_time(record["timestamp"])
        if lower and timestamp < lower or upper and timestamp >= upper:
            continue
        if project and record["project"].casefold() != project.casefold():
            continue
        if not all(word in record["text"].casefold() for word in words):
            continue
        matches.append(record)
    matches.sort(key=lambda record: parse_time(record["timestamp"]))
    return {"records": matches[:limit], "total_matches": len(matches), "truncated": len(matches) > limit}


if __name__ == "__main__":
    mcp.run(transport="stdio")
