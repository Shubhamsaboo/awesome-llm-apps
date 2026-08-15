"""Brief rendering and opt-in delivery for Release Radar."""

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

try:
    from .ranker import RankedRelease
except ImportError:
    from ranker import RankedRelease


GMAIL_REQUIRED_ENV = [
    "RELEASE_RADAR_EMAIL_TO",
    "RELEASE_RADAR_EMAIL_FROM",
    "RELEASE_RADAR_GMAIL_CLIENT_ID",
    "RELEASE_RADAR_GMAIL_CLIENT_SECRET",
    "RELEASE_RADAR_GMAIL_REFRESH_TOKEN",
]


@dataclass(frozen=True)
class Brief:
    generated_at: str
    watch_mode: str
    manifest_path: str
    subject: str
    text: str
    html: str
    releases: list[RankedRelease]
    dependencies_checked: int
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "watch_mode": self.watch_mode,
            "manifest_path": self.manifest_path,
            "subject": self.subject,
            "text": self.text,
            "html": self.html,
            "releases": [release.to_dict() for release in self.releases],
            "dependencies_checked": self.dependencies_checked,
            "errors": self.errors,
        }


def render_brief(
    releases: list[RankedRelease],
    *,
    watch_mode: str,
    manifest_path: str,
    dependencies_checked: int,
    errors: list[str] | None = None,
    now: dt.datetime | None = None,
) -> Brief:
    """Render ranked dependency changes in plain text and HTML."""

    now = now or dt.datetime.now(dt.timezone.utc)
    generated_at = now.isoformat(timespec="seconds")
    subject = f"Release Radar dependency brief - {now:%Y-%m-%d}"
    text_lines = [
        "Release Radar Dependency Brief",
        f"Generated: {generated_at}",
        f"Manifest: {manifest_path}",
        f"Watch mode: {watch_mode}",
        f"Dependencies checked: {dependencies_checked}",
        "",
        "Changes that need attention:",
    ]
    html_lines = [
        "<h2>Release Radar Dependency Brief</h2>",
        f"<p><strong>Generated:</strong> {html.escape(generated_at)}<br>",
        f"<strong>Manifest:</strong> {html.escape(manifest_path)}<br>",
        f"<strong>Watch mode:</strong> {html.escape(watch_mode)}<br>",
        f"<strong>Dependencies checked:</strong> {dependencies_checked}</p>",
    ]

    grouped: dict[str, list[RankedRelease]] = {}
    for release in releases:
        grouped.setdefault(release.dependency, []).append(release)

    for dependency, dependency_releases in grouped.items():
        text_lines.extend(["", dependency])
        html_lines.extend([f"<h3>{html.escape(dependency)}</h3>", "<ul>"])
        for release in dependency_releases:
            current = release.current_version or "unknown"
            version_change = f"{current} -> {release.release_version}"
            reasons = ", ".join(release.reasons)
            text_lines.extend(
                [
                    f"- {version_change}: {release.title}",
                    f"  Reason: {reasons}",
                    f"  Why you care: {release.why_you_care}",
                    f"  Link: {release.release_url}",
                ]
            )
            html_lines.extend(
                [
                    "<li>",
                    f"<strong>{html.escape(version_change)}: {html.escape(release.title)}</strong>",
                    f"<p><strong>Reason:</strong> {html.escape(reasons)}<br>",
                    f"<strong>Why you care:</strong> {html.escape(release.why_you_care)}<br>",
                    f'<a href="{html.escape(release.release_url)}">release notes</a></p>',
                    "</li>",
                ]
            )
        html_lines.append("</ul>")

    if not releases:
        text_lines.append("No breaking, deprecation, security, or major-version changes found.")
        html_lines.append(
            "<p>No breaking, deprecation, security, or major-version changes found.</p>"
        )

    brief_errors = errors or []
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
        manifest_path=manifest_path,
        subject=subject,
        text="\n".join(text_lines),
        html="\n".join(html_lines),
        releases=releases,
        dependencies_checked=dependencies_checked,
        errors=brief_errors,
    )


def _gmail_configured() -> bool:
    return all(os.environ.get(name) for name in GMAIL_REQUIRED_ENV)


def _missing_gmail_config() -> list[str]:
    return [name for name in GMAIL_REQUIRED_ENV if not os.environ.get(name)]


def send_brief(payload: dict[str, Any]) -> dict[str, Any]:
    """Send a rendered brief only when a delivery target is configured."""

    delivery_mode = os.environ.get("RELEASE_RADAR_DELIVERY", "auto").lower()
    if delivery_mode == "gmail":
        return send_gmail(payload)
    if delivery_mode == "webhook":
        return send_webhook(payload)
    if _gmail_configured():
        return send_gmail(payload)
    if os.environ.get("RELEASE_RADAR_WEBHOOK_URL"):
        return send_webhook(payload)
    return {
        "configured": False,
        "sent": False,
        "status": "skipped_no_delivery",
        "detail": (
            "Set Gmail environment variables or RELEASE_RADAR_WEBHOOK_URL to "
            "deliver scheduled briefs."
        ),
    }


def _fetch_gmail_access_token() -> str:
    request = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=urllib.parse.urlencode(
            {
                "client_id": os.environ["RELEASE_RADAR_GMAIL_CLIENT_ID"],
                "client_secret": os.environ["RELEASE_RADAR_GMAIL_CLIENT_SECRET"],
                "refresh_token": os.environ["RELEASE_RADAR_GMAIL_REFRESH_TOKEN"],
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
        message["To"] = os.environ["RELEASE_RADAR_EMAIL_TO"]
        message["From"] = os.environ["RELEASE_RADAR_EMAIL_FROM"]
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

    webhook_url = os.environ.get("RELEASE_RADAR_WEBHOOK_URL")
    if not webhook_url:
        return {
            "provider": "webhook",
            "configured": False,
            "sent": False,
            "status": "skipped_no_webhook",
            "detail": "Set RELEASE_RADAR_WEBHOOK_URL to deliver scheduled briefs.",
        }

    body = json.dumps(
        {
            "subject": payload["subject"],
            "text": payload["text"],
            "html": payload["html"],
            "releases": payload["releases"],
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("RELEASE_RADAR_WEBHOOK_TOKEN")
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

