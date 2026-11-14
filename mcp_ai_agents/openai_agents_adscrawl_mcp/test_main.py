"""Offline checks only: no OpenAI requests and no AdsCrawl sessions are created."""

import os
import unittest
from unittest.mock import AsyncMock, patch

from agents.mcp import MCPServerStreamableHttp

from main import (
    ALLOWED_TOOLS,
    DemoError,
    ShutdownCheckedServer,
    contains_confirmation,
    required_secret,
    tool_failed,
    validate_url,
    verify_tool_names,
)


class FakeResult:
    def __init__(self, payload):
        self.payload = payload

    def model_dump(self, **kwargs):
        return self.payload


class ConfigurationTests(unittest.TestCase):
    def test_missing_key_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(DemoError):
                required_secret("ADSCRAWL_API_KEY")

    def test_placeholder_key_is_rejected(self):
        with patch.dict(os.environ, {"ADSCRAWL_API_KEY": "your-adscrawl-api-key"}, clear=True):
            with self.assertRaises(DemoError):
                required_secret("ADSCRAWL_API_KEY")

    def test_non_placeholder_environment_value_is_read(self):
        with patch.dict(os.environ, {"ADSCRAWL_API_KEY": "unit-test-not-a-real-key"}, clear=True):
            self.assertEqual(required_secret("ADSCRAWL_API_KEY"), "unit-test-not-a-real-key")

    def test_public_url(self):
        self.assertEqual(validate_url(" https://example.com "), "https://example.com")

    def test_non_http_url_is_rejected(self):
        with self.assertRaises(DemoError):
            validate_url("file:///etc/passwd")

    def test_url_credentials_are_rejected(self):
        with self.assertRaises(DemoError):
            validate_url("https://user:password@example.com")

    def test_private_literal_address_is_rejected(self):
        with self.assertRaises(DemoError):
            validate_url("http://127.0.0.1")

    def test_missing_tool_is_reported(self):
        with self.assertRaises(DemoError):
            verify_tool_names({"browser_open", "browser_read"})

    def test_screenshot_is_not_allowed(self):
        self.assertNotIn("browser_screenshot", ALLOWED_TOOLS)


class ConfirmationTests(unittest.TestCase):
    def test_structured_confirmation(self):
        self.assertTrue(contains_confirmation({"structured_content": {"confirmed": True}}))

    def test_json_text_confirmation(self):
        self.assertTrue(contains_confirmation({"content": [{"text": '{"confirmed":true}'}]}))

    def test_prose_or_string_true_is_not_confirmation(self):
        self.assertFalse(contains_confirmation("confirmed: true"))
        self.assertFalse(contains_confirmation({"confirmed": "true"}))
        self.assertFalse(contains_confirmation({"confirmed": False}))

    def test_mcp_error_spellings(self):
        self.assertTrue(tool_failed({"is_error": True}))
        self.assertTrue(tool_failed({"isError": True}))
        self.assertFalse(tool_failed({"is_error": False}))


class ToolLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def make_server(self):
        return ShutdownCheckedServer(name="offline-test", params={"url": "https://example.com/mcp"})

    async def test_second_open_is_blocked(self):
        server = self.make_server()
        result = FakeResult({"content": [], "is_error": False})
        with patch.object(MCPServerStreamableHttp, "call_tool", AsyncMock(return_value=result)) as call:
            await server.call_tool("browser_open", {})
            with self.assertRaises(DemoError):
                await server.call_tool("browser_open", {})
            self.assertEqual(call.await_count, 1)

    async def test_read_and_confirmed_close_are_recorded(self):
        server = self.make_server()
        results = [
            FakeResult({"content": [{"text": "Example Domain"}], "is_error": False}),
            FakeResult({"structured_content": {"confirmed": True}, "is_error": False}),
        ]
        with patch.object(MCPServerStreamableHttp, "call_tool", AsyncMock(side_effect=results)):
            await server.call_tool("browser_read", {})
            await server.call_tool("browser_close", {})
        self.assertTrue(server.read_succeeded)
        self.assertTrue(server.close_confirmed)

    async def test_error_close_is_not_confirmation(self):
        server = self.make_server()
        result = FakeResult({"structured_content": {"confirmed": True}, "is_error": True})
        with patch.object(MCPServerStreamableHttp, "call_tool", AsyncMock(return_value=result)):
            await server.call_tool("browser_close", {})
        self.assertFalse(server.close_confirmed)

    async def test_non_read_only_tool_never_reaches_transport(self):
        server = self.make_server()
        with patch.object(MCPServerStreamableHttp, "call_tool", AsyncMock()) as call:
            with self.assertRaises(DemoError):
                await server.call_tool("browser_screenshot", {})
            call.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
