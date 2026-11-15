"""Brief rendering and opt-in delivery for Page Watch."""

from __future__ import annotations

import base64
import datetime as dt
import html
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any


GMAIL_REQUIRED_ENV = [
    "PAGE_WATCH_EMAIL_TO",
    "PAGE_WATCH_EMAIL_FROM",
    "PAGE_WATCH_GMAIL_CLIENT_ID",
    "PAGE_WATCH_GMAIL_CLIENT_SECRET",
    "PAGE_WATCH_GMAIL_REFRESH_TOKEN",
]


@dataclass(frozen=True)
class Brief:
    generated_at: str
    watch_mode: str
    watchlist_path: str
    subject: str
    text: str
    html: str
    pages: list[dict[str, Any]]
    pages_checked: int
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "watch_mode": self.watch_mode,
            "watchlist_path": self.watchlist_path,
            "subject": self.subject,
            "text": self.text,
            "html": self.html,
            "pages": self.pages,
            "pages_checked": self.pages_checked,
            "errors": self.errors,
        }


def _material_judgments(page: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in page.get("judgments") or []
        if item.get("classification") == "material"
    ]


def _source_note(source: str) -> str:
    if source == "prefilter_fallback":
        return "prefilter_fallback (Gemini did not judge this hunk)"
    if source == "sample_fallback":
        return "sample_fallback (no recorded fixture; used the pre-filter)"
    return source or "unknown"


def render_brief(
    pages: list[dict[str, Any]],
    *,
    watch_mode: str,
    watchlist_path: str,
    pages_checked: int,
    errors: list[str] | None = None,
    now: dt.datetime | None = None,
    judge_mode: str = "sample",
) -> Brief:
    """Render page changes grouped by page in plain text and HTML."""

    now = now or dt.datetime.now(dt.timezone.utc)
    generated_at = now.isoformat(timespec="seconds")
    subject = f"Page Watch brief - {now:%Y-%m-%d}"
    text_lines = [
        "Page Watch Brief",
        f"Generated: {generated_at}",
        f"Watch list: {watchlist_path}",
        f"Watch mode: {watch_mode}",
        f"Judge mode: {judge_mode}",
        f"Pages checked: {pages_checked}",
        "",
        "Changes that need attention:",
    ]
    html_lines = [
        "<h2>Page Watch Brief</h2>",
        f"<p><strong>Generated:</strong> {html.escape(generated_at)}<br>",
        f"<strong>Watch list:</strong> {html.escape(watchlist_path)}<br>",
        f"<strong>Watch mode:</strong> {html.escape(watch_mode)}<br>",
        f"<strong>Judge mode:</strong> {html.escape(judge_mode)}<br>",
        f"<strong>Pages checked:</strong> {pages_checked}</p>",
    ]

    any_material = False
    for page in pages:
        name = str(page.get("name") or "Untitled page")
        url = str(page.get("url") or "")
        status = str(page.get("status") or "")
        material = _material_judgments(page)
        text_lines.extend(["", name, f"URL: {url}"])
        html_lines.extend(
            [
                f"<h3>{html.escape(name)}</h3>",
                f"<p><a href=\"{html.escape(url)}\">{html.escape(url)}</a></p>",
            ]
        )
        if status == "baseline":
            note = str(page.get("note") or "Baseline captured.")
            text_lines.append(f"- {note}")
            html_lines.append(f"<p>{html.escape(note)}</p>")
            continue
        if status == "error":
            note = str(page.get("note") or "Could not fetch this page.")
            text_lines.append(f"- Error: {note}")
            html_lines.append(f"<p><strong>Error:</strong> {html.escape(note)}</p>")
            continue
        if not material:
            text_lines.append("- No material change.")
            html_lines.append("<p>No material change.</p>")
            continue
        any_material = True
        html_lines.append("<ul>")
        for item in material:
            reasons = ", ".join(item.get("prefilter_reasons") or []) or "none"
            before = item.get("before") or "(none)"
            after = item.get("after") or "(none)"
            source_note = _source_note(str(item.get("source") or ""))
            text_lines.extend(
                [
                    f"- {item.get('classification')}: {item.get('summary')}",
                    f"  Impact: {item.get('impact')}",
                    f"  Pre-filter: {item.get('prefilter_verdict')} ({reasons})",
                    f"  Source: {source_note}",
                    f"  Before: {before}",
                    f"  After: {after}",
                ]
            )
            html_lines.extend(
                [
                    "<li>",
                    f"<strong>{html.escape(str(item.get('classification')))}: "
                    f"{html.escape(str(item.get('summary')))}</strong>",
                    f"<p><strong>Impact:</strong> {html.escape(str(item.get('impact')))}<br>",
                    f"<strong>Pre-filter:</strong> {html.escape(str(item.get('prefilter_verdict')))} "
                    f"({html.escape(reasons)})<br>",
                    f"<strong>Source:</strong> {html.escape(source_note)}</p>",
                    f"<p><strong>Before:</strong> {html.escape(str(before))}<br>",
                    f"<strong>After:</strong> {html.escape(str(after))}</p>",
                    "</li>",
                ]
            )
        html_lines.append("</ul>")

    if not any_material and not any(page.get("status") == "baseline" for page in pages):
        if not pages:
            text_lines.append("No watched pages produced a brief.")
            html_lines.append("<p>No watched pages produced a brief.</p>")

    fallback_count = sum(
        1
        for page in pages
        for item in page.get("judgments") or []
        if item.get("source") == "prefilter_fallback"
    )
    brief_errors = list(errors or [])
    if fallback_count:
        brief_errors.append(
            f"{fallback_count} hunk(s) marked source=prefilter_fallback; "
            "Gemini did not judge them and the deterministic pre-filter was used."
        )
    if brief_errors:
        text_lines.extend(["", "Scan notes:", *[f"- {error}" for error in brief_errors]])
        html_lines.extend(
            [
                "<h3>Scan notes</h3>",
                "<ul>",
                *[f"<li>{html.escape(error)}</li>" for error in brief_errors],
                "</ul>",
            ]
        )

    return Brief(
        generated_at=generated_at,
        watch_mode=watch_mode,
        watchlist_path=watchlist_path,
        subject=subject,
        text="\n".join(text_lines),
        html="\n".join(html_lines),
        pages=pages,
        pages_checked=pages_checked,
        errors=brief_errors,
    )


def _gmail_configured() -> bool:
    return all(os.environ.get(name) for name in GMAIL_REQUIRED_ENV)


def _missing_gmail_config() -> list[str]:
    return [name for name in GMAIL_REQUIRED_ENV if not os.environ.get(name)]


def send_brief(payload: dict[str, Any]) -> dict[str, Any]:
    """Send a rendered brief only when a delivery target is configured."""

    delivery_mode = os.environ.get("PAGE_WATCH_DELIVERY", "auto").lower()
    if delivery_mode == "gmail":
        return send_gmail(payload)
    if delivery_mode == "webhook":
        return send_webhook(payload)
    if _gmail_configured():
        return send_gmail(payload)
    if os.environ.get("PAGE_WATCH_WEBHOOK_URL"):
        return send_webhook(payload)
    return {
        "configured": False,
        "sent": False,
        "status": "skipped_no_delivery",
        "detail": (
            "Set Gmail environment variables or PAGE_WATCH_WEBHOOK_URL to "
            "deliver scheduled briefs."
        ),
    }


def _fetch_gmail_access_token() -> str:
    request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode(
            {
                "client_id": os.environ["PAGE_WATCH_GMAIL_CLIENT_ID"],
                "client_secret": os.environ["PAGE_WATCH_GMAIL_CLIENT_SECRET"],
                "refresh_token": os.environ["PAGE_WATCH_GMAIL_REFRESH_TOKEN"],
                "grant_type": "refresh_token",
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        token_payload = json.loads(response.read().decode("utf-8"))
    return str(token_payload["access_token"])


def send_gmail(payload: dict[str, Any]) -> dict[str, Any]:
    """Send the brief through Gmail when all OAuth settings are present."""

    missing = _missing_gmail_config()
    if missing:
        return {
            "provider": "gmail",
            "configured": False,
            "sent": False,
            "status": "skipped_missing_gmail_config",
            "missing": missing,
        }

    try:
        message = EmailMessage()
        message["To"] = os.environ["PAGE_WATCH_EMAIL_TO"]
        message["From"] = os.environ["PAGE_WATCH_EMAIL_FROM"]
        message["Subject"] = payload["subject"]
        message.set_content(payload["text"])
        message.add_alternative(payload["html"], subtype="html")
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        request = urllib.request.Request(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            data=json.dumps({"raw": encoded_message}).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {_fetch_gmail_access_token()}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
        return {
            "provider": "gmail",
            "configured": True,
            "sent": True,
            "status": "sent",
            "message_id": response_payload.get("id"),
        }
    except urllib.error.HTTPError as exc:
        return {
            "provider": "gmail",
            "configured": True,
            "sent": False,
            "status": exc.code,
            "error": exc.read().decode("utf-8", errors="replace")[:500],
        }
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "provider": "gmail",
            "configured": True,
            "sent": False,
            "status": "connection_error",
            "error": str(exc),
        }


def send_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """Post the brief to a configured webhook."""

    webhook_url = os.environ.get("PAGE_WATCH_WEBHOOK_URL")
    if not webhook_url:
        return {
            "provider": "webhook",
            "configured": False,
            "sent": False,
            "status": "skipped_no_webhook",
            "detail": "Set PAGE_WATCH_WEBHOOK_URL to deliver scheduled briefs.",
        }

    body = json.dumps(
        {
            "subject": payload["subject"],
            "text": payload["text"],
            "html": payload["html"],
            "pages": payload.get("pages") or [],
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("PAGE_WATCH_WEBHOOK_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(webhook_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            return {
                "provider": "webhook",
                "configured": True,
                "sent": 200 <= response.status < 300,
                "status": response.status,
                "response": response_text[:500],
            }
    except urllib.error.HTTPError as exc:
        return {
            "provider": "webhook",
            "configured": True,
            "sent": False,
            "status": exc.code,
            "error": exc.read().decode("utf-8", errors="replace")[:500],
        }
    except (urllib.error.URLError, TimeoutError) as exc:
        return {
            "provider": "webhook",
            "configured": True,
            "sent": False,
            "status": "connection_error",
            "error": str(exc),
        }
