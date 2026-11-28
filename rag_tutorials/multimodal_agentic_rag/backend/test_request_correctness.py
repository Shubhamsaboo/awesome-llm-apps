import asyncio
import io
import unittest
from unittest.mock import patch

from fastapi import HTTPException, UploadFile
from google.adk.events import Event
from google.adk.sessions import InMemorySessionService
from google.genai import types
from starlette.datastructures import Headers

import server
from rag_store import MultimodalRagStore, RackSource


class TextIngestionTests(unittest.TestCase):
    def setUp(self):
        self.store = MultimodalRagStore(dimensions=2)
        with patch.object(self.store, "_embed_text", return_value=[1.0, 0.0]):
            self.existing = self.store.add_text_source("Existing", "Existing evidence")
        self.text = " ".join(f"word{i}" for i in range(300))

    def test_failed_embedding_leaves_existing_state_unchanged(self):
        before = (self.store.sources[:], self.store.chunks[:], self.store.events[:])
        for vectors in ([RuntimeError("unavailable")], [[0.0, 1.0], RuntimeError("unavailable")]):
            with self.subTest(failed_chunk=len(vectors)):
                with patch.object(self.store, "_embed_text", side_effect=vectors):
                    with self.assertRaisesRegex(RuntimeError, "unavailable"):
                        self.store.add_text_source("Failed", self.text)
                self.assertEqual((self.store.sources, self.store.chunks, self.store.events), before)

    def test_success_publishes_all_chunks_and_one_event(self):
        with patch.object(self.store, "_embed_text", return_value=[0.0, 1.0]):
            source = self.store.add_text_source("Complete", self.text)
        chunks = [chunk for chunk in self.store.chunks if chunk.source_id == source.id]
        self.assertEqual(source.chunks, 3)
        self.assertEqual(len(chunks), source.chunks)
        self.assertEqual([chunk.metadata["chunk_index"] for chunk in chunks], [1, 2, 3])
        self.assertEqual(len(self.store.sources), 2)
        self.assertEqual(len(self.store.events), 2)
        self.assertEqual(self.store.events[-1]["source_id"], source.id)

    def test_seed_source_does_not_emit_an_event(self):
        before = self.store.events[:]
        with patch.object(self.store, "_embed_text", return_value=[0.0, 1.0]):
            source = self.store.add_text_source("Seed", self.text, seed=True)
        self.assertIn(source, self.store.sources)
        self.assertEqual(self.store.events, before)


class RequestSessionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.sessions = InMemorySessionService()
        self.existing = await self.sessions.create_session(
            app_name=server.APP_NAME, user_id=server.USER_ID
        )
        self.addCleanup(patch.stopall)
        patch.object(server, "ADK_AVAILABLE", True).start()
        patch.object(server, "session_service", self.sessions).start()

    async def assert_existing_session_only(self):
        remaining = await self.sessions.list_sessions(
            app_name=server.APP_NAME, user_id=server.USER_ID
        )
        self.assertEqual([session.id for session in remaining.sessions], [self.existing.id])

    async def test_success_releases_request_session_and_returns_last_text(self):
        async def events(**kwargs):
            for text in ("Working", "Grounded answer"):
                yield Event(author="agent", content=types.Content(parts=[types.Part(text=text)]))

        with patch.object(server, "Runner") as runner:
            runner.return_value.run_async.side_effect = events
            answer = await server._run_adk_agent("Question", {"matches": []})
        self.assertEqual(answer, "Grounded answer")
        await self.assert_existing_session_only()

    async def test_model_failure_releases_request_session(self):
        async def events(**kwargs):
            raise RuntimeError("model unavailable")
            yield

        with patch.object(server, "Runner") as runner:
            runner.return_value.run_async.side_effect = events
            with self.assertRaisesRegex(RuntimeError, "model unavailable"):
                await server._run_adk_agent("Question", {"matches": []})
        await self.assert_existing_session_only()

    async def test_cancellation_releases_request_session(self):
        async def events(**kwargs):
            raise asyncio.CancelledError()
            yield

        with patch.object(server, "Runner") as runner:
            runner.return_value.run_async.side_effect = events
            with self.assertRaises(asyncio.CancelledError):
                await server._run_adk_agent("Question", {"matches": []})
        await self.assert_existing_session_only()


class UploadLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_small_and_exact_limit_uploads_preserve_bytes_and_metadata(self):
        for size in (16, 32):
            with self.subTest(size=size):
                data = b"x" * size
                upload = UploadFile(
                    io.BytesIO(data), filename="sample.pdf",
                    headers=Headers({"content-type": "application/pdf"}),
                )
                source = RackSource("saved", "Sample", "pdf", "Notes", 1)
                with patch.object(server, "MAX_UPLOAD_BYTES", 32, create=True), \
                     patch.object(server.RAG_STORE, "add_file_source", return_value=source) as add, \
                     patch.object(server.RAG_STORE, "snapshot", return_value={"sources": [source.id]}):
                    response = await server.add_file_source(upload, "Sample", "Notes")
                add.assert_called_once_with(
                    title="Sample", data=data, mime_type="application/pdf", notes="Notes"
                )
                self.assertEqual(response["source"]["id"], source.id)
                self.assertEqual(response["space"], {"sources": [source.id]})

    async def test_oversize_upload_stops_reading_after_limit_plus_one(self):
        for size in (33, 4096):
            with self.subTest(size=size):
                stream = io.BytesIO(b"x" * size)
                upload = UploadFile(stream, filename="large.pdf")
                with patch.object(server, "MAX_UPLOAD_BYTES", 32, create=True), \
                     patch.object(server.RAG_STORE, "add_file_source") as add:
                    with self.assertRaises(HTTPException) as raised:
                        await server.add_file_source(upload, "Large", "")
                self.assertEqual(raised.exception.status_code, 400)
                self.assertEqual(stream.tell(), 33)
                add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
