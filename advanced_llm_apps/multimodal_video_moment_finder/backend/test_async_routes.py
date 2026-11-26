import asyncio
import importlib.util
import io
import os
from pathlib import Path
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

from fastapi import FastAPI, HTTPException, UploadFile

ROOT = Path(__file__).resolve().parent
video_store = types.ModuleType("video_store")
video_store.VideoStore = object
with tempfile.TemporaryDirectory() as import_directory:
    previous = os.getcwd()
    os.chdir(import_directory)
    try:
        with patch.dict(sys.modules, {"video_store": video_store}):
            spec = importlib.util.spec_from_file_location("video_server_under_test", ROOT / "server.py")
            server = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(server)
    finally:
        os.chdir(previous)


class AsyncRouteTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        server.uploads_dir = Path(self.directory.name)
        server.ingestion_lock = asyncio.Lock()
        self.calls = []

    def blocking_call(self, name, result):
        loop = asyncio.get_running_loop()
        loop_thread = threading.get_ident()
        def operation(*args, **kwargs):
            self.assertNotEqual(threading.get_ident(), loop_thread, name + " blocks the event loop")
            progressed = threading.Event()
            loop.call_soon_threadsafe(progressed.set)
            self.assertTrue(progressed.wait(2), "the event loop cannot progress during store work")
            self.calls.append(name)
            return result
        return operation

    def moment(self):
        return {"frame_path": "frames/abc/frame_0001.jpg", "timestamp": 0, "video_id": "abc"}

    async def test_upload_ingestion_runs_in_a_worker(self):
        server.store = types.SimpleNamespace(ingest_video=self.blocking_call("ingest", {"video_id": "abc"}))
        upload = UploadFile(file=io.BytesIO(b"video"), filename="clip.mp4")
        result = await server.upload_video(upload, 1.0)
        self.assertEqual(result, {"video_id": "abc"})
        self.assertEqual((server.uploads_dir / "clip.mp4").read_bytes(), b"video")

    async def test_image_search_and_description_leave_the_loop_available(self):
        server.store = types.SimpleNamespace(
            find_moment=self.blocking_call("find", [self.moment()]),
            describe_moment=self.blocking_call("describe", "A frame"),
        )
        result = await server.find_moment(UploadFile(file=io.BytesIO(b"image"), filename="query.jpg"), None, 5)
        self.assertEqual(result["moments"][0]["description"], "A frame")
        self.assertEqual(self.calls, ["find", "describe"])

    async def test_text_search_and_description_leave_the_loop_available(self):
        server.store = types.SimpleNamespace(
            find_moment_by_text=self.blocking_call("text", [self.moment()]),
            describe_moment=self.blocking_call("describe", "A frame"),
        )
        result = await server.find_moment_text(server.TextSearchRequest(query="A frame"))
        self.assertEqual(result["moments"][0]["description"], "A frame")
        self.assertEqual(self.calls, ["text", "describe"])

    async def test_list_videos_runs_in_a_worker(self):
        server.store = types.SimpleNamespace(list_videos=self.blocking_call("list", [{"filename": "clip.mp4"}]))
        result = await server.list_videos()
        self.assertEqual(result["videos"][0]["video_url"], "/uploads/clip.mp4")

    async def test_delete_runs_in_a_worker_and_preserves_not_found(self):
        server.store = types.SimpleNamespace(delete_video=self.blocking_call("delete", False))
        with self.assertRaises(HTTPException) as error:
            await server.delete_video("missing")
        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(self.calls, ["delete"])

    async def test_health_keeps_its_response_shape(self):
        server.store = types.SimpleNamespace(list_videos=self.blocking_call("health", [{"total_frames": 8}]))
        self.assertEqual(await server.health(), {"status": "ok", "videos": 1, "total_frames": 8})

    async def test_uploads_with_the_same_filename_do_not_overlap_ingestion(self):
        loop = asyncio.get_running_loop()
        loop_thread = threading.get_ident()
        entered = asyncio.Event()
        release = threading.Event()
        observed = []
        def ingest(path, filename, fps):
            self.assertNotEqual(threading.get_ident(), loop_thread)
            content = Path(path).read_bytes()
            observed.append(content)
            if content == b"first":
                loop.call_soon_threadsafe(entered.set)
                self.assertTrue(release.wait(2))
                self.assertEqual(Path(path).read_bytes(), b"first")
            return {"video_id": content.decode()}
        def upload(content):
            file = tempfile.SpooledTemporaryFile()
            self.addCleanup(file.close)
            file.write(content)
            file.seek(0)
            return UploadFile(file=file, filename="same.mp4")
        server.store = types.SimpleNamespace(ingest_video=ingest)
        first = asyncio.create_task(server.upload_video(upload(b"first"), 1.0))
        try:
            await asyncio.wait_for(entered.wait(), 1)
            second = asyncio.create_task(server.upload_video(upload(b"second"), 1.0))
            await asyncio.sleep(0)
            self.assertEqual((server.uploads_dir / "same.mp4").read_bytes(), b"first")
        finally:
            release.set()
        self.assertEqual(await first, {"video_id": "first"})
        self.assertEqual(await second, {"video_id": "second"})
        self.assertEqual(observed, [b"first", b"second"])

    async def test_cancelled_upload_keeps_its_file_until_worker_finishes(self):
        loop = asyncio.get_running_loop()
        entered = asyncio.Event()
        release = threading.Event()
        observed = []

        def ingest(path, filename, fps):
            content = Path(path).read_bytes()
            if content == b"first":
                loop.call_soon_threadsafe(entered.set)
                release.wait(2)
                observed.append(Path(path).read_bytes())
            return {"video_id": content.decode()}

        server.store = types.SimpleNamespace(ingest_video=ingest)
        def upload(content):
            file = tempfile.SpooledTemporaryFile()
            self.addCleanup(file.close)
            file.write(content)
            file.seek(0)
            return UploadFile(file=file, filename="same.mp4")
        first = asyncio.create_task(server.upload_video(
            upload(b"first"), 1.0
        ))
        second = None
        try:
            await asyncio.wait_for(entered.wait(), 1)
            first.cancel()
            await asyncio.sleep(0)
            second = asyncio.create_task(server.upload_video(
                upload(b"second"), 1.0
            ))
            await asyncio.sleep(0)
            self.assertEqual((server.uploads_dir / "same.mp4").read_bytes(), b"first")
        finally:
            release.set()
            tasks = [first] + ([second] if second else [])
            await asyncio.gather(*tasks, return_exceptions=True)
        self.assertTrue(first.cancelled())
        self.assertEqual(observed, [b"first"])
        self.assertEqual(second.result(), {"video_id": "second"})


if __name__ == "__main__":
    unittest.main()
