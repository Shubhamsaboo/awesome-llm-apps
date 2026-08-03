import unittest
from unittest.mock import AsyncMock, patch

from app.models import ChatRequest
from app.routers import chat


class ChatProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_direct_chat_does_not_initialize_dashscope_embeddings(self):
        request = ChatRequest(question="hello")

        with patch.object(chat, "get_rag_service") as get_rag_service:
            messages, sources, question = await chat._prepare_messages(
                request,
                AsyncMock(),
            )

        get_rag_service.assert_not_called()
        self.assertEqual(question, "hello")
        self.assertEqual(sources, [])
        self.assertEqual(messages[-1], {"role": "user", "content": "hello"})


if __name__ == "__main__":
    unittest.main()
