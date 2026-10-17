"""GitHub Copilot as a model provider — sign-in state and the models your plan allows.

Reuses LiteLLM's own authenticator, so tokens live where `github_copilot/` model
calls already look for them (~/.config/litellm/github_copilot). Sign in once with
scripts/copilot_login.py; nothing here starts the blocking device flow.
"""

import os

import httpx

PREFIX = "github_copilot/"


def _authenticator():
    # Imported lazily: this module loads during Streamlit's script run, and the
    # first `import litellm` there can race with the event-loop thread's logging
    # (LiteLLM's log filter imports its own modules mid-initialisation). Keeping
    # litellm's first import in triage_optimizer preserves the original order.
    from litellm.llms.github_copilot.authenticator import Authenticator

    return Authenticator()


def is_signed_in() -> bool:
    """True once the device flow has cached a GitHub access token."""
    path = _authenticator().access_token_file
    try:
        return os.path.getsize(path) > 0
    except OSError:
        return False


def list_models() -> list:
    """Chat models enabled for this Copilot account, as LiteLLM model strings.

    Returns [] when not signed in or the endpoint is unreachable, so callers can
    fall back to a free-text model ID.
    """
    if not is_signed_in():
        return []
    try:
        from litellm.llms.github_copilot.common_utils import (
            DEFAULT_GITHUB_COPILOT_API_BASE,
            get_copilot_default_headers,
        )

        auth = _authenticator()
        key = auth.get_api_key()  # refreshes the short-lived key; never prompts once signed in
        base = auth.get_api_base() or DEFAULT_GITHUB_COPILOT_API_BASE
        resp = httpx.get(f"{base}/models", headers=get_copilot_default_headers(key), timeout=15)
        resp.raise_for_status()
        rows = resp.json().get("data", [])
    except Exception:  # noqa: BLE001 — any failure degrades to free text
        return []
    ids = []
    for m in rows:
        if (m.get("capabilities") or {}).get("type") != "chat":
            continue
        if (m.get("policy") or {}).get("state") == "disabled":
            continue  # turned off by your plan or org policy
        if m.get("id") and m["id"] not in ids:
            ids.append(m["id"])
    return [PREFIX + i for i in ids]
