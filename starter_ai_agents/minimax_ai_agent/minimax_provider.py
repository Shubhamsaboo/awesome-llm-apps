"""MiniMax provider client.

A small, dependency-light client for the MiniMax models. It talks to MiniMax
through either of the two API compatibility surfaces that MiniMax exposes:

* the Chat Completions API (``/v1/chat/completions``), and
* the Messages API (``/anthropic/v1/messages``).

Both surfaces are available on the global host (``api.minimax.io``) and on the
mainland-China host (``api.minimaxi.com``). The client keeps the region and the
protocol as explicit, swappable settings so a caller can reach every endpoint
combination that MiniMax offers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

# --- Regional endpoints -----------------------------------------------------
# Each region publishes both compatibility surfaces on its own host.
REGIONS: Dict[str, Dict[str, str]] = {
    "global": {
        "label": "Global",
        "chat_completions_base_url": "https://api.minimax.io/v1",
        "messages_base_url": "https://api.minimax.io/anthropic",
        "docs_root": "https://platform.minimax.io/docs",
    },
    "china": {
        "label": "Mainland China",
        "chat_completions_base_url": "https://api.minimaxi.com/v1",
        "messages_base_url": "https://api.minimaxi.com/anthropic",
        "docs_root": "https://platform.minimaxi.com/docs",
    },
}


# --- Models -----------------------------------------------------------------
# ``context_window`` is the maximum number of tokens the model can attend to,
# ``input_modalities`` is what the model accepts as input, and ``thinking`` is
# the set of reasoning modes the model supports.
@dataclass(frozen=True)
class Model:
    model_id: str
    context_window: int
    input_modalities: List[str]
    thinking: List[str]


MODELS: Dict[str, Model] = {
    "MiniMax-M3": Model(
        model_id="MiniMax-M3",
        context_window=1_000_000,
        input_modalities=["text", "image", "video"],
        thinking=["adaptive", "disabled"],
    ),
    "MiniMax-M2.7": Model(
        model_id="MiniMax-M2.7",
        context_window=204_800,
        input_modalities=["text"],
        thinking=["always_on"],
    ),
}

DEFAULT_MODEL = "MiniMax-M3"
DEFAULT_REGION = "global"
DEFAULT_PROTOCOL = "chat_completions"

# Version header required by the Messages API compatibility surface.
MESSAGES_API_VERSION = "2023-06-01"


@dataclass
class MiniMaxClient:
    """Minimal client for MiniMax models.

    Parameters
    ----------
    api_key:
        MiniMax API key (sent as a Bearer token).
    region:
        ``"global"`` or ``"china"`` -- selects the host, see :data:`REGIONS`.
    protocol:
        ``"chat_completions"`` or ``"messages"`` -- selects the API surface.
    timeout:
        Per-request timeout in seconds.
    """

    api_key: str
    region: str = DEFAULT_REGION
    protocol: str = DEFAULT_PROTOCOL
    timeout: int = 60
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        if self.region not in REGIONS:
            raise ValueError(
                f"Unknown region {self.region!r}; expected one of {sorted(REGIONS)}"
            )
        if self.protocol not in ("chat_completions", "messages"):
            raise ValueError(
                f"Unknown protocol {self.protocol!r}; "
                "expected 'chat_completions' or 'messages'"
            )

    # -- URL / header helpers ------------------------------------------------
    def _endpoint(self) -> str:
        region = REGIONS[self.region]
        if self.protocol == "chat_completions":
            return f"{region['chat_completions_base_url']}/chat/completions"
        return f"{region['messages_base_url']}/v1/messages"

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.protocol == "messages":
            headers["anthropic-version"] = MESSAGES_API_VERSION
        return headers

    # -- Content helpers -----------------------------------------------------
    @staticmethod
    def build_user_content(text: str, image_url: Optional[str] = None) -> Any:
        """Build a user-message payload.

        With an ``image_url`` this returns the multimodal content-part list that
        MiniMax-M3 accepts on the Chat Completions API; otherwise a plain string.
        """
        if not image_url:
            return text
        return [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": image_url}},
        ]

    # -- Request -------------------------------------------------------------
    def complete(
        self,
        prompt: str,
        *,
        model: str = DEFAULT_MODEL,
        system: Optional[str] = None,
        image_url: Optional[str] = None,
        max_tokens: int = 1024,
    ) -> str:
        """Send a single-turn prompt and return the model's text reply.

        ``image_url`` demonstrates MiniMax-M3's image input and is only sent on
        the Chat Completions surface, which uses inline content parts.
        """
        if model not in MODELS:
            raise ValueError(
                f"Unknown model {model!r}; expected one of {sorted(MODELS)}"
            )

        if self.protocol == "chat_completions":
            payload = self._chat_completions_payload(
                prompt, model, system, image_url, max_tokens
            )
        else:
            payload = self._messages_payload(prompt, model, system, max_tokens)

        response = self.session.post(
            self._endpoint(),
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return self._parse_reply(response.json())

    def _chat_completions_payload(
        self,
        prompt: str,
        model: str,
        system: Optional[str],
        image_url: Optional[str],
        max_tokens: int,
    ) -> Dict[str, Any]:
        messages: List[Dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append(
            {"role": "user", "content": self.build_user_content(prompt, image_url)}
        )
        return {"model": model, "messages": messages, "max_tokens": max_tokens}

    def _messages_payload(
        self,
        prompt: str,
        model: str,
        system: Optional[str],
        max_tokens: int,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        return payload

    def _parse_reply(self, data: Dict[str, Any]) -> str:
        if self.protocol == "chat_completions":
            return data["choices"][0]["message"]["content"]
        # Messages API returns a list of content blocks.
        blocks = data.get("content", [])
        return "".join(block.get("text", "") for block in blocks)
