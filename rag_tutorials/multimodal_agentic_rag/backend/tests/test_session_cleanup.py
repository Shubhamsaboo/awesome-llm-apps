import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


class SessionCleanupTests(unittest.IsolatedAsyncioTestCase):
    async def exercise(self, error=None):
        service = SimpleNamespace(
            create_session=AsyncMock(return_value=SimpleNamespace(id="request-session")),
            delete_session=AsyncMock(),
        )

        async def events(**kwargs):
            if error:
                raise error
            yield SimpleNamespace(content=SimpleNamespace(parts=[SimpleNamespace(text="answer")]))

        with patch.multiple(server, ADK_AVAILABLE=True, session_service=service,
                            build_agent=Mock(), Runner=Mock(return_value=SimpleNamespace(run_async=events))):
            if error:
                with self.assertRaises(type(error)):
                    await server._run_adk_agent("question", {})
            else:
                self.assertEqual(await server._run_adk_agent("question", {}), "answer")
        service.delete_session.assert_awaited_once_with(
            app_name=server.APP_NAME, user_id=server.USER_ID, session_id="request-session"
        )

    async def test_success_releases_session(self):
        await self.exercise()

    async def test_runner_failure_releases_session(self):
        await self.exercise(RuntimeError("provider failed"))

    async def test_cancelled_request_releases_session(self):
        await self.exercise(asyncio.CancelledError())


if __name__ == "__main__":
    unittest.main()
