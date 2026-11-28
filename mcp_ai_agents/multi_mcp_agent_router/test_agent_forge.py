"""MCP connection ownership and tool-result forwarding regressions."""

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from mcp.types import CallToolResult, TextContent, Tool

import agent_forge as forge


class AgentForgeTests(unittest.IsolatedAsyncioTestCase):
    async def connect(self, events, failure=None):
        @asynccontextmanager
        async def transport(params):
            events.append(f"open {params.command}")
            try:
                yield params.command, None
            finally:
                events.append(f"close {params.command}")

        @asynccontextmanager
        async def session(name, _):
            events.append(f"enter {name}")
            initialize = AsyncMock()
            list_tools = AsyncMock(return_value=SimpleNamespace(tools=[
                Tool(name=name, description="Example tool", inputSchema={"type": "object"}),
            ]))
            if name == "second":
                if failure == "initialize":
                    initialize.side_effect = RuntimeError("initialize failed")
                elif failure == "tools":
                    list_tools.side_effect = RuntimeError("list_tools failed")
                elif failure == "cancel":
                    initialize.side_effect = asyncio.CancelledError()
            try:
                yield SimpleNamespace(initialize=initialize, list_tools=list_tools)
            finally:
                events.append(f"exit {name}")

        agent = forge.Agent("Test", "Test agent", "Use the tools", mcp_servers=[
            {"command": "first"}, {"command": "second"},
        ])
        with patch.object(forge, "stdio_client", transport), patch.object(forge, "ClientSession", session):
            return await forge.connect_mcp_servers(agent)

    async def test_failed_or_cancelled_startup_closes_all_connections(self):
        for failure in ("initialize", "tools", "cancel"):
            with self.subTest(failure=failure):
                events = []
                error = asyncio.CancelledError if failure == "cancel" else RuntimeError
                with self.assertRaises(error):
                    await self.connect(events, failure)
                self.assertEqual(events[-4:], [
                    "exit second", "close second", "exit first", "close first",
                ])

    async def test_success_transfers_connection_ownership_to_caller(self):
        events = []
        stack, tools, sessions = await self.connect(events)
        try:
            self.assertEqual([tool["name"] for tool in tools], ["first", "second"])
            self.assertEqual(set(sessions), {"first", "second"})
            self.assertEqual(events, ["open first", "enter first", "open second", "enter second"])
        finally:
            await stack.aclose()
        self.assertEqual(events[-4:], ["exit second", "close second", "exit first", "close first"])

    async def test_tool_error_flag_reaches_model_with_original_content(self):
        for is_error in (True, False):
            with self.subTest(is_error=is_error):
                result = CallToolResult(
                    content=[TextContent(type="text", text="Tool response")], isError=is_error,
                )
                session = SimpleNamespace(call_tool=AsyncMock(return_value=result))
                stack = SimpleNamespace(aclose=AsyncMock())
                connect = AsyncMock(return_value=(stack, [], {"lookup": session}))
                tool_call = SimpleNamespace(type="tool_use", id="call-1", name="lookup", input={})
                client = MagicMock()
                client.messages.create.side_effect = [
                    SimpleNamespace(stop_reason="tool_use", content=[tool_call]),
                    SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(text="Done")]),
                ]
                agent = forge.Agent("Test", "Test agent", "Use the tools", mcp_servers=[{"command": "test"}])
                with patch.object(forge, "connect_mcp_servers", connect):
                    answer = await forge.run_agent_async(client, agent, "Find a document", [])

                block = client.messages.create.call_args.kwargs["messages"][-1]["content"][0]
                self.assertEqual(block.get("is_error", False), is_error)
                self.assertEqual(block["tool_use_id"], "call-1")
                self.assertEqual(block["content"], "Tool response")
                self.assertEqual(answer, "Done")
                session.call_tool.assert_awaited_once_with("lookup", {})
                stack.aclose.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
