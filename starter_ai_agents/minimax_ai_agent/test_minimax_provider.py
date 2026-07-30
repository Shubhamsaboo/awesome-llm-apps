"""Offline tests for the MiniMax provider client.

These stub the HTTP layer so they run without network access or an API key.
Run with: python -m unittest test_minimax_provider
"""

import unittest
from unittest.mock import MagicMock

from minimax_provider import (
    DEFAULT_MODEL,
    MODELS,
    REGIONS,
    MiniMaxClient,
)


def _fake_session(payload):
    """A session whose .post returns a response yielding ``payload``."""
    session = MagicMock()
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    session.post.return_value = response
    return session


class ModelCatalogTests(unittest.TestCase):
    def test_default_model_is_m3(self):
        self.assertEqual(DEFAULT_MODEL, "MiniMax-M3")

    def test_both_models_present(self):
        self.assertEqual(set(MODELS), {"MiniMax-M3", "MiniMax-M2.7"})

    def test_m3_capabilities(self):
        m3 = MODELS["MiniMax-M3"]
        self.assertEqual(m3.context_window, 1_000_000)
        self.assertEqual(m3.input_modalities, ["text", "image", "video"])
        self.assertEqual(m3.thinking, ["adaptive", "disabled"])

    def test_m27_capabilities(self):
        m27 = MODELS["MiniMax-M2.7"]
        self.assertEqual(m27.context_window, 204_800)
        self.assertEqual(m27.input_modalities, ["text"])
        self.assertEqual(m27.thinking, ["always_on"])


class EndpointTests(unittest.TestCase):
    def test_regions_cover_global_and_china(self):
        self.assertEqual(set(REGIONS), {"global", "china"})

    def test_chat_completions_urls(self):
        self.assertEqual(
            MiniMaxClient("k", region="global", protocol="chat_completions")._endpoint(),
            "https://api.minimax.io/v1/chat/completions",
        )
        self.assertEqual(
            MiniMaxClient("k", region="china", protocol="chat_completions")._endpoint(),
            "https://api.minimaxi.com/v1/chat/completions",
        )

    def test_messages_urls(self):
        self.assertEqual(
            MiniMaxClient("k", region="global", protocol="messages")._endpoint(),
            "https://api.minimax.io/anthropic/v1/messages",
        )
        self.assertEqual(
            MiniMaxClient("k", region="china", protocol="messages")._endpoint(),
            "https://api.minimaxi.com/anthropic/v1/messages",
        )

    def test_invalid_region_and_protocol(self):
        with self.assertRaises(ValueError):
            MiniMaxClient("k", region="mars")
        with self.assertRaises(ValueError):
            MiniMaxClient("k", protocol="carrier-pigeon")


class RequestTests(unittest.TestCase):
    def test_chat_completions_request_and_parse(self):
        session = _fake_session(
            {"choices": [{"message": {"content": "hello from M3"}}]}
        )
        client = MiniMaxClient("secret", protocol="chat_completions", session=session)
        reply = client.complete("hi", model="MiniMax-M3")

        self.assertEqual(reply, "hello from M3")
        url = session.post.call_args.args[0]
        kwargs = session.post.call_args.kwargs
        self.assertEqual(url, "https://api.minimax.io/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")
        self.assertNotIn("anthropic-version", kwargs["headers"])
        self.assertEqual(kwargs["json"]["model"], "MiniMax-M3")
        self.assertEqual(kwargs["json"]["messages"][-1]["content"], "hi")

    def test_messages_request_and_parse(self):
        session = _fake_session({"content": [{"text": "hello from "}, {"text": "M2.7"}]})
        client = MiniMaxClient(
            "secret", region="china", protocol="messages", session=session
        )
        reply = client.complete("hi", model="MiniMax-M2.7", system="be brief")

        self.assertEqual(reply, "hello from M2.7")
        kwargs = session.post.call_args.kwargs
        self.assertEqual(
            session.post.call_args.args[0],
            "https://api.minimaxi.com/anthropic/v1/messages",
        )
        self.assertEqual(kwargs["headers"]["anthropic-version"], "2023-06-01")
        self.assertEqual(kwargs["json"]["system"], "be brief")
        self.assertEqual(kwargs["json"]["model"], "MiniMax-M2.7")

    def test_image_input_builds_multimodal_content(self):
        session = _fake_session({"choices": [{"message": {"content": "ok"}}]})
        client = MiniMaxClient("secret", session=session)
        client.complete("describe", image_url="https://example.com/a.png")

        content = session.post.call_args.kwargs["json"]["messages"][-1]["content"]
        self.assertEqual(content[0], {"type": "text", "text": "describe"})
        self.assertEqual(
            content[1],
            {"type": "image_url", "image_url": {"url": "https://example.com/a.png"}},
        )

    def test_unknown_model_rejected(self):
        client = MiniMaxClient("secret", session=_fake_session({}))
        with self.assertRaises(ValueError):
            client.complete("hi", model="MiniMax-M99")


if __name__ == "__main__":
    unittest.main()
