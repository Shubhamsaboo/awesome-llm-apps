"""Offline regressions using the real Gemini request serializer and Chroma store."""
import base64
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx
from google import genai
from PIL import Image

from video_store import VideoStore


class VideoStoreTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        previous = os.getcwd()
        os.chdir(directory.name)
        self.addCleanup(os.chdir, previous)
        self.batches = []
        self.empty_response = False
        transport = httpx.MockTransport(self.respond)
        client = genai.Client(api_key="test-key", http_options={
            "client_args": {"transport": transport, "trust_env": False},
            "async_client_args": {"transport": transport, "trust_env": False},
        })
        self.addCleanup(client.close)
        with patch("video_store.genai.Client", return_value=client):
            self.store = VideoStore(str(Path(directory.name) / "chroma"))

    def respond(self, request):
        entries = json.loads(request.content)["requests"]
        self.batches.append(len(entries))
        vectors = []
        for entry in entries:
            data = base64.urlsafe_b64decode(entry["content"]["parts"][0]["inline_data"]["data"])
            with Image.open(io.BytesIO(data)) as image:
                vectors.append({"values": [float(image.getpixel((0, 0))[0]), 1.0]})
        return httpx.Response(200, json={"embeddings": [] if self.empty_response else vectors})

    def frames(self, count=7):
        folder = self.store.frames_dir / "a123bcde"
        folder.mkdir()
        frames = []
        for index in range(count):
            path = folder / f"frame_{index + 1:04d}.jpg"
            Image.new("RGB", (1, 1), (index,) * 3).save(path)
            frames.append({"path": str(path), "frame_num": index + 1,
                           "timestamp": index, "video_id": folder.name})
        return frames, count, folder.name

    def test_ingestion_keeps_one_vector_per_frame_across_batches(self):
        progress = []
        with patch.object(self.store, "extract_frames", return_value=self.frames()):
            result = self.store.ingest_video("unused.mp4", "clip.mp4",
                                             on_progress=lambda *args: progress.append(args))
        rows = self.store.collection.get(include=["embeddings", "metadatas"])
        self.assertEqual(result["frames_extracted"], 7)
        self.assertEqual(self.batches, [6, 1])
        self.assertEqual(progress, [(6, 7), (7, 7)])
        self.assertEqual(len(rows["ids"]), 7)
        for vector, metadata in zip(rows["embeddings"], rows["metadatas"]):
            self.assertAlmostEqual(vector[0], metadata["frame_num"] - 1, places=5)
            self.assertAlmostEqual(vector[1], 1.0, places=5)

    def test_incomplete_embedding_response_does_not_write_index_rows(self):
        self.empty_response = True
        with patch.object(self.store, "extract_frames", return_value=self.frames(2)):
            with self.assertRaisesRegex(ValueError, "one vector per frame"):
                self.store.ingest_video("unused.mp4", "clip.mp4")
        self.assertEqual(self.store.collection.count(), 0)

    def test_empty_batch_makes_no_model_request(self):
        self.assertEqual(self.store._embed_images_batch([]), [])
        self.assertEqual(self.batches, [])

    def indexed_video(self):
        frames, _, video_id = self.frames(1)
        self.store.collection.add(ids=["frame"], embeddings=[[1.0, 1.0]],
                                  metadatas=[{"video_id": video_id}])
        return Path(frames[0]["path"])

    def test_deleting_video_removes_its_index_and_frames_only(self):
        selected = self.indexed_video()
        other = self.store.frames_dir / "b123cdef"
        other.mkdir()
        (other / "frame.jpg").write_bytes(b"other video")
        self.assertTrue(self.store.delete_video("a123bcde"))
        self.assertEqual(self.store.collection.count(), 0)
        self.assertFalse(selected.parent.exists())
        self.assertEqual((other / "frame.jpg").read_bytes(), b"other video")

    def test_unknown_video_does_not_delete_an_unindexed_directory(self):
        frames, _, video_id = self.frames(1)
        self.assertFalse(self.store.delete_video(video_id))
        self.assertTrue(Path(frames[0]["path"]).exists())

    def test_failed_index_deletion_preserves_frames(self):
        selected = self.indexed_video()
        with patch.object(self.store.collection, "delete", side_effect=RuntimeError("unavailable")):
            self.assertFalse(self.store.delete_video("a123bcde"))
        self.assertTrue(selected.exists())
        self.assertEqual(self.store.collection.count(), 1)

    def test_missing_frame_directory_does_not_block_index_deletion(self):
        selected = self.indexed_video()
        selected.unlink()
        selected.parent.rmdir()
        self.assertTrue(self.store.delete_video("a123bcde"))
        self.assertEqual(self.store.collection.count(), 0)


if __name__ == "__main__":
    unittest.main()
