"""Central configuration for the HeyGen Avatar Agent.

Keeping settings in one place means the UI and API layers never hardcode
endpoints or IDs, which makes the agent easy to point at a different
environment or reuse in tests.
"""

import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.liveavatar.com"

# Free sandbox test avatar: no credits consumed, sessions last ~1 minute.
SANDBOX_AVATAR_ID = "dd73ea75-1218-4ef3-92ce-606d5f7fbc0a"

# Height (px) of the embedded avatar iframe — tall enough to show the Chat button.
EMBED_HEIGHT = 720


def resolve_api_key(override=None):
    """Return the LiveAvatar (HeyGen) API key.

    A non-empty override (e.g. the sidebar field) always wins. Otherwise
    HEYGEN_API_KEY is used (LIVEAVATAR_API_KEY is accepted as a fallback).
    Get a key at https://app.liveavatar.com/developers
    """
    return (
        (override or "").strip()
        or os.getenv("HEYGEN_API_KEY", "")
        or os.getenv("LIVEAVATAR_API_KEY", "")
    )
