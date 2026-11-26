"""Preserve MCP tool failure semantics across the Anthropic tool bridge."""

import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, MagicMock

from mcp.types import CallToolResult, TextContent


class ToolErrorTests(unittest.IsolatedAsyncioTestCase):
    async def test_protocol_errors_reach_model_as_error_results(self):
        for is_error in (True, False):
            with self.subTest(is_error=is_error):
                source = Path(__file__).with_name("agent_forge.py")
                node = next(n for n in ast.parse(source.read_text()).body
                            if isinstance(n, ast.AsyncFunctionDef) and n.name == "run_agent_async")
                tool_result = CallToolResult(
                    content=[TextContent(type="text", text="Document is unavailable")],
                    isError=is_error,
                )
                session = SimpleNamespace(call_tool=AsyncMock(return_value=tool_result))
                stack = SimpleNamespace(aclose=AsyncMock())
                connect = AsyncMock(return_value=(stack, [], {"lookup": session}))
                tool_call = SimpleNamespace(type="tool_use", id="call1", name="lookup", input={})
                client = MagicMock()
                client.messages.create.side_effect = [
                    SimpleNamespace(stop_reason="tool_use", content=[tool_call]),
                    SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(text="Done")]),
                ]
                namespace = {"Anthropic": object, "Agent": object, "connect_mcp_servers": connect}
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"), namespace)
                response = await namespace["run_agent_async"](
                    client, SimpleNamespace(mcp_servers=[{}], system_prompt="Research"), "Find a doc", []
                )
                result_block = client.messages.create.call_args.kwargs["messages"][-1]["content"][0]
                self.assertEqual(result_block.get("is_error", False), is_error)
                self.assertEqual(result_block["tool_use_id"], "call1")
                self.assertEqual(result_block["content"], "Document is unavailable")
                self.assertEqual(response, "Done")
                stack.aclose.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
