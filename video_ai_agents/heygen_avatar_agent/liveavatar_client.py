"""Client for the HeyGen LiveAvatar REST API.

This layer owns every HTTP detail (base URL, auth header, error handling) and
stays completely UI-agnostic: on failure it raises `LiveAvatarError` instead of
calling Streamlit. That separation keeps the client reusable from any frontend,
script, or test (Single Responsibility + Dependency Inversion).
"""

import requests

from config import BASE_URL


class LiveAvatarError(Exception):
    """Raised when a LiveAvatar API call fails."""


class LiveAvatarClient:
    """Thin wrapper around the LiveAvatar endpoints this agent needs."""

    def __init__(self, api_key, base_url=BASE_URL, timeout=30):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    @property
    def _headers(self):
        return {"X-API-KEY": self._api_key, "Content-Type": "application/json"}

    def _request(self, method, path, body=None):
        """Send a request and return the `data` object, or raise LiveAvatarError."""
        try:
            response = requests.request(
                method,
                f"{self._base_url}{path}",
                json=body,
                headers=self._headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            detail = getattr(exc.response, "text", None) or str(exc)
            raise LiveAvatarError(detail) from exc
        payload = response.json()
        return payload.get("data")

    def list_contexts(self, page=1, page_size=100):
        """Return the list of contexts owned by this API key."""
        data = self._request(
            "GET", f"/v1/contexts?page={page}&page_size={page_size}"
        )
        return (data or {}).get("results", [])

    def create_context(self, name, prompt, opening_text):
        """Create an avatar persona (context) and return its id."""
        body = {"name": name, "prompt": prompt, "opening_text": opening_text}
        return self._request("POST", "/v1/contexts", body)["id"]

    def update_context(self, context_id, name, prompt, opening_text):
        """Update an existing context and return its id."""
        body = {"name": name, "prompt": prompt, "opening_text": opening_text}
        return self._request("PATCH", f"/v1/contexts/{context_id}", body)["id"]

    def ensure_context(self, name, prompt, opening_text):
        """Create or update a context by name so relaunches never collide.

        LiveAvatar requires unique context names. Reusing the same role template
        would fail on the second Launch; this upserts instead.
        """
        for context in self.list_contexts():
            if context.get("name") == name:
                return self.update_context(
                    context["id"], name, prompt, opening_text
                )
        return self.create_context(name, prompt, opening_text)

    def list_public_avatars(self, page=1, page_size=50):
        """Return public avatars as [{id, name, preview_url}, ...]."""
        data = self._request(
            "GET", f"/v1/avatars/public?page={page}&page_size={page_size}"
        )
        results = (data or {}).get("results", [])
        return [
            {
                "id": item["id"],
                "name": item.get("name") or item["id"],
                "preview_url": item.get("preview_url") or "",
            }
            for item in results
            if item.get("status", "ACTIVE") == "ACTIVE" or "status" not in item
        ]

    def get_avatar(self, avatar_id):
        """Fetch a single avatar by id (name + preview_url)."""
        data = self._request("GET", f"/v1/avatars/{avatar_id}") or {}
        return {
            "id": data.get("id") or avatar_id,
            "name": data.get("name") or "Wayne",
            "preview_url": data.get("preview_url") or "",
        }

    def create_embed(self, avatar_id, context_id, is_sandbox):
        """Provision a managed session and return the embed URL."""
        body = {
            "avatar_id": avatar_id,
            "context_id": context_id,
            "is_sandbox": is_sandbox,
        }
        return self._request("POST", "/v2/embeddings", body)["url"]
