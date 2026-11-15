"""HTTP and Pub/Sub scheduler hooks for Page Watch.

Run locally with:
    uvicorn scheduler_api:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import base64
import json
from json import JSONDecodeError
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool

try:
    from .delivery import send_brief
    from .watch import run_page_watch
except ImportError:
    from delivery import send_brief
    from watch import run_page_watch


app = FastAPI(
    title="Page Watch Scheduler API",
    description="HTTP and Pub/Sub hooks for scheduled page-change briefs.",
)


def _as_bool(value: Any, *, default: bool | None = None) -> bool | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in {"1", "true", "yes"}:
            return True
        if lowered in {"0", "false", "no"}:
            return False
    return default


def run_scheduled_watch(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run Page Watch from a scheduler payload with dry-run as the default."""

    payload = payload if isinstance(payload, dict) else {}
    dry_run = _as_bool(payload.get("dry_run"), default=True)
    live = _as_bool(payload.get("live"), default=None)
    live_model = _as_bool(payload.get("live_model"), default=None)
    page_name = str(payload.get("page_name") or "")

    brief = run_page_watch(
        live=live,
        live_model=live_model,
        page_name=page_name,
    )
    delivery = {
        "attempted": False,
        "sent": False,
        "status": "dry_run",
        "detail": "Set dry_run=false to use configured Gmail or webhook delivery.",
    }
    if dry_run is False:
        delivery = {"attempted": True, **send_brief(brief)}
    return {
        "dry_run": dry_run,
        "delivery": delivery,
        "brief": brief,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/page-watch/dry-run")
def dry_run_preview(
    live: Optional[bool] = None,
    page_name: str = "",
) -> dict[str, Any]:
    return run_scheduled_watch(
        {
            "dry_run": True,
            "live": live,
            "page_name": page_name,
        }
    )


@app.post("/page-watch/trigger")
async def scheduler_trigger(request: Request) -> dict[str, Any]:
    try:
        payload = await request.json() if request.headers.get("content-length") else {}
    except JSONDecodeError:
        payload = {}
    return await run_in_threadpool(run_scheduled_watch, payload)


@app.post("/page-watch/pubsub")
async def pubsub_trigger(request: Request) -> dict[str, Any]:
    """Handle a Cloud Scheduler to Pub/Sub push envelope."""

    envelope = await request.json()
    message = envelope.get("message", {}) if isinstance(envelope, dict) else {}
    payload: dict[str, Any] = {}
    encoded_data = message.get("data") if isinstance(message, dict) else None
    if encoded_data:
        try:
            payload = json.loads(base64.b64decode(encoded_data).decode("utf-8"))
        except (ValueError, JSONDecodeError, UnicodeDecodeError):
            payload = {}
    return await run_in_threadpool(run_scheduled_watch, payload)
