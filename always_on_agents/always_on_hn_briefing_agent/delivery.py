"""Optional delivery hooks for scheduled AgentScout runs."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def send_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """Send a rendered brief to a configured webhook.

    The app stays safe by default: no webhook is called unless
    AGENTSCOUT_WEBHOOK_URL is present.
    """

    webhook_url = os.environ.get("AGENTSCOUT_WEBHOOK_URL")
    if not webhook_url:
        return {
            "configured": False,
            "sent": False,
            "status": "skipped_no_webhook",
            "detail": "Set AGENTSCOUT_WEBHOOK_URL to deliver scheduled briefs.",
        }

    body = json.dumps(
        {
            "subject": payload["subject"],
            "text": payload["text"],
            "html": payload["html"],
            "stories": payload["stories"],
            "next_actions": payload["next_actions"],
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("AGENTSCOUT_WEBHOOK_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            return {
                "configured": True,
                "sent": 200 <= response.status < 300,
                "status": response.status,
                "response": response_text[:500],
            }
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "configured": True,
            "sent": False,
            "status": exc.code,
            "error": detail[:500],
        }
    except urllib.error.URLError as exc:
        return {
            "configured": True,
            "sent": False,
            "status": "connection_error",
            "error": str(exc),
        }
