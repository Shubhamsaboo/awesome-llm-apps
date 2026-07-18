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
    """Return the HeyGen API key.

    A non-empty override (e.g. the sidebar field) always wins over the
    HEYGEN_API_KEY environment variable.
    """
    return (override or "").strip() or os.getenv("HEYGEN_API_KEY", "")
