"""stipple.py — thin typed client for the Stipple REST API (stdlib only).

Verified against the live API (2026-08). The contract: https://www.stipple.sh/openapi.json

API surface reality:
  - document tools take a multipart 'file' upload (or 'bytes_b64' form field), not JSON
  - options (scheme, deep, fresh, stream) are query parameters
  - company resolve / tender match / key creation take JSON
Copy this single file into any project.
"""
from __future__ import annotations

import base64
import json
import os
import tempfile
import urllib.error
import urllib.request
import uuid

DEFAULT_BASE = "https://www.stipple.sh"


class StippleError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.message = message


class Stipple:
    """Stipple REST client. Anonymous (free tier) unless api_key given."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None,
                 user_agent: str = "stipple-sdk/1.0", timeout: int = 300):
        self.api_key = (api_key or os.environ.get("STIPPLE_API_KEY", "")).strip() or None
        self.base_url = (base_url or os.environ.get("STIPPLE_BASE_URL", DEFAULT_BASE)).rstrip("/")
        self.user_agent = user_agent
        self.timeout = timeout

    # -- transport -----------------------------------------------------------
    def _headers(self, extra: dict | None = None) -> dict:
        h = {"User-Agent": self.user_agent, **(extra or {})}
        if self.api_key:
            h["Authorization"] = "Bearer " + self.api_key
        return h

    def _json(self, method: str, path: str, body: dict | None = None) -> dict:
        req = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers=self._headers({"Content-Type": "application/json",
                                   "Accept": "application/json"}),
        )
        return self._do(req)

    def _multipart(self, path: str, file_path: str | None = None,
                   b64: str | None = None, files_field: str = "file",
                   params: dict | None = None, extra_fields: dict | None = None) -> dict:
        """Multipart upload. One file, optional query params + extra form fields."""
        qs = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in (params or {}).items())
        url = self.base_url + path + (("?" + qs) if qs else "")
        boundary = "----stipple" + uuid.uuid4().hex
        parts = []
        if extra_fields:
            for k, v in extra_fields.items():
                if v is None:
                    continue
                parts.append(
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
        if file_path:
            with open(file_path, "rb") as f:
                content = f.read()
            fname = os.path.basename(file_path)
            ctype = "application/octet-stream"
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{files_field}\"; "
                f"filename=\"{fname}\"\r\nContent-Type: {ctype}\r\n\r\n".encode()
                + content + b"\r\n")
        elif b64:
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"bytes_b64\"\r\n\r\n{b64}\r\n".encode())
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        req = urllib.request.Request(url, data=body, method="POST", headers=self._headers({
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        }))
        return self._do(req)

    def _do(self, req) -> dict:
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                raw = r.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            raise StippleError(e.code, e.read().decode()[:500]) from None

    @staticmethod
    def _fetch_url(url: str) -> str:
        """Download a remote document to a temp file (intake is upload-based)."""
        req = urllib.request.Request(url, headers={"User-Agent": "stipple-sdk/1.0"})
        fd, path = tempfile.mkstemp(suffix=os.path.splitext(url.split("?")[0])[1] or ".bin")
        with urllib.request.urlopen(req, timeout=120) as r, os.fdopen(fd, "wb") as f:
            f.write(r.read())
        return path

    # -- free tools ------------------------------------------------------------
    def tenders(self, q: str | None = None, jurisdiction: str | None = None,
                limit: int = 10, offset: int = 0) -> dict:
        params = [f"limit={limit}", f"offset={offset}"]
        if q:
            params.append(f"q={q}")
        if jurisdiction:
            params.append(f"jurisdiction={jurisdiction}")
        return self._json("GET", "/v1/tenders?" + "&".join(params))

    def tender_sources(self) -> dict:
        return self._json("GET", "/v1/tenders/sources")

    def check_document(self, sha256: str) -> dict:
        """Has this exact file been inspected before? Free cache check."""
        return self._json("GET", f"/v1/warrants/check?sha256={sha256}")

    def get_warrant(self, warrant_id: str) -> dict:
        return self._json("GET", f"/v1/warrants/{warrant_id}")

    def pricing(self) -> dict:
        return self._json("GET", "/v1/pricing")

    def usage(self) -> dict:
        """Requires an API key."""
        return self._json("GET", "/v1/usage")

    def create_key(self, email: str, name: str | None = None,
                   label: str | None = None) -> dict:
        return self._json("POST", "/v1/keys",
                          {"email": email, "name": name, "label": label})

    # -- document tools (multipart) ---------------------------------------------
    def verify_document(self, file_path: str | None = None, url: str | None = None,
                        b64: str | None = None, fresh: bool = False,
                        **opts) -> dict:
        if url and not file_path:
            file_path = self._fetch_url(url)
        return self._multipart("/v1/warrants", file_path, b64,
                               params={"fresh": fresh} if fresh else None)

    def extract_fields(self, file_path: str | None = None, url: str | None = None,
                       b64: str | None = None, fields: list | None = None,
                       template: str | None = None, **opts) -> dict:
        if url and not file_path:
            file_path = self._fetch_url(url)
        extra = {}
        if fields:
            extra["fields"] = json.dumps([{"name": f} for f in fields] if
                                         all(isinstance(f, str) for f in fields) else fields)
        if template:
            extra["template"] = template
        return self._multipart("/v1/extract", file_path, b64, extra_fields=extra)

    def detect_ai_text(self, file_path: str | None = None, url: str | None = None,
                       b64: str | None = None, text: str | None = None) -> dict:
        if text is not None:
            fd, path = tempfile.mkstemp(suffix=".txt")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            file_path = path
        elif url and not file_path:
            file_path = self._fetch_url(url)
        return self._multipart("/v1/detect-ai-text", file_path, b64)

    def verify_identity(self, files: list[str] | None = None,
                        scheme: str | None = None, **opts) -> dict:
        """Multiple file uploads (paths or URLs). scheme as query param."""
        uploaded = [f if not f.startswith(("http://", "https://")) else self._fetch_url(f)
                    for f in (files or [])]
        # multipart with several 'files' parts
        boundary = "----stipple" + uuid.uuid4().hex
        parts = []
        for path in uploaded:
            with open(path, "rb") as f:
                parts.append(
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; "
                    f"filename=\"{os.path.basename(path)}\"\r\n"
                    f"Content-Type: application/octet-stream\r\n\r\n".encode() + f.read() + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        qs = f"scheme={scheme}" if scheme else ""
        req = urllib.request.Request(
            self.base_url + "/v1/identity-check" + (("?" + qs) if qs else ""),
            data=b"".join(parts), method="POST",
            headers=self._headers({"Content-Type": f"multipart/form-data; boundary={boundary}",
                                   "Accept": "application/json"}))
        return self._do(req)

    def check_pack(self, files: list[str] | None = None,
                   scheme: str | None = None, **opts) -> dict:
        return self.verify_identity(files=files, scheme=scheme, _endpoint="/v1/check-pack")

    def screen_adverse_media(self, file_path: str | None = None, url: str | None = None,
                             b64: str | None = None, **opts) -> dict:
        """Screens the person/organisation named in the uploaded document."""
        if url and not file_path:
            file_path = self._fetch_url(url)
        return self._multipart("/v1/adverse-media", file_path, b64)

    def verify_references(self, file_path: str | None = None, url: str | None = None,
                          b64: str | None = None, deep: bool = False, **opts) -> dict:
        if url and not file_path:
            file_path = self._fetch_url(url)
        return self._multipart("/v1/verify-references", file_path, b64,
                               params={"deep": deep} if deep else None)

    # -- tender matching -------------------------------------------------------
    def resolve_company(self, query: str, jurisdiction: str | None = None) -> dict:
        """query = company name or website."""
        body = {"query": query}
        if jurisdiction:
            body["jurisdiction"] = jurisdiction
        return self._json("POST", "/v1/companies/resolve", body)

    def match_tenders(self, url: str, jurisdiction: str | None = None,
                      tier: str | None = None, closing_before: str | None = None) -> dict:
        body = {"url": url}
        if jurisdiction:
            body["jurisdiction"] = jurisdiction
        if tier:
            body["tier"] = tier
        if closing_before:
            body["closing_before"] = closing_before
        return self._json("POST", "/v1/tenders/match", body)
