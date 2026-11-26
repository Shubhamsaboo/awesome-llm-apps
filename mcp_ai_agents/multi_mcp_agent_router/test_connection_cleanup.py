"""Partially connected MCP servers must close when startup fails."""

import ast
import asyncio
from contextlib import AsyncExitStack, asynccontextmanager
import os
from pathlib import Path
from types import SimpleNamespace
import unittest


class ConnectionCleanupTests(unittest.IsolatedAsyncioTestCase):
    async def connect(self, failure=None):
        source = Path(__file__).with_name("agent_forge.py")
        node = next(n for n in ast.parse(source.read_text()).body
                    if isinstance(n, ast.AsyncFunctionDef) and n.name == "connect_mcp_servers")
        events = []

        @asynccontextmanager
        async def transport(params):
            events.append(f"open {params.command}")
            try:
                yield params.command, None
            finally:
                events.append(f"close {params.command}")

        class Session:
            def __init__(self, name, _):
                self.name = name

            async def __aenter__(self):
                events.append(f"enter {self.name}")
                return self

            async def __aexit__(self, *args):
                events.append(f"exit {self.name}")

            async def initialize(self):
                if self.name == "second" and failure == "initialize":
                    raise RuntimeError("failed initialize")
                if self.name == "second" and failure == "cancel":
                    raise asyncio.CancelledError()

            async def list_tools(self):
                if self.name == "second" and failure == "tools":
                    raise RuntimeError("failed list_tools")
                return SimpleNamespace(tools=[])

        namespace = {"AsyncExitStack": AsyncExitStack, "ClientSession": Session, "os": os,
                     "StdioServerParameters": SimpleNamespace, "stdio_client": transport,
                     "Agent": SimpleNamespace}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
        agent = SimpleNamespace(mcp_servers=[{"command": "first"}, {"command": "second"}])
        return namespace["connect_mcp_servers"](agent), events

    async def test_failure_and_cancellation_close_all_entered_resources(self):
        for failure in ("initialize", "tools", "cancel"):
            with self.subTest(failure=failure):
                call, events = await self.connect(failure)
                expected_error = asyncio.CancelledError if failure == "cancel" else RuntimeError
                with self.assertRaises(expected_error):
                    await call
                self.assertEqual(events[-4:], ["exit second", "close second", "exit first", "close first"])

    async def test_success_leaves_connections_available_until_caller_closes(self):
        call, events = await self.connect()
        stack, _, _ = await call
        self.assertFalse(any(event.startswith("close") for event in events))
        await stack.aclose()
        self.assertEqual(events[-4:], ["exit second", "close second", "exit first", "close first"])


if __name__ == "__main__":
    unittest.main()
