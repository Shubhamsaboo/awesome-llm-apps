import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from google.genai.types import Content

ROOT = Path(__file__).resolve().parent

with patch.dict(sys.modules, {"chromadb": types.ModuleType("chromadb")}):
    spec = importlib.util.spec_from_file_location("video_store_under_test", ROOT / "video_store.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


class EmbeddingService:
    """Model the documented distinction between Parts and separate Content inputs."""
    def __init__(self):
        self.calls = []

    def embed_content(self, model, contents):
        self.calls.append(contents)
        if all(isinstance(value, Content) for value in contents):
            values = [[float(value.parts[0].inline_data.data[-1])] for value in contents]
        else:
            values = [[-1.0]]  # Multiple Parts form one aggregate embedding.
        return types.SimpleNamespace(embeddings=[types.SimpleNamespace(values=value) for value in values])


class Collection:
    def __init__(self):
        self.saved = None

    def add(self, **kwargs):
        if len(kwargs["ids"]) != len(kwargs["embeddings"]):
            raise ValueError("IDs and embeddings must have equal length")
        self.saved = kwargs


class FrameEmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.store = module.VideoStore.__new__(module.VideoStore)
        self.service = EmbeddingService()
        self.store.client = types.SimpleNamespace(models=self.service)
        self.store.collection = Collection()
        self.store._resize_image = lambda data: data

    def test_seven_frames_keep_one_embedding_each_across_batches(self):
        result = self.store._embed_images_batch([(bytes([index]), "image/jpeg") for index in range(7)])
        self.assertEqual(result, [[float(index)] for index in range(7)])
        self.assertEqual([len(call) for call in self.service.calls], [6, 1])

    def test_ingestion_preserves_frame_vector_alignment_and_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            frames = []
            for index in range(7):
                path = Path(directory) / f"frame_{index + 1:04d}.jpg"
                path.write_bytes(bytes([index]))
                frames.append({"path": str(path), "timestamp": index, "frame_num": index + 1, "video_id": "abcdefgh"})
            self.store.extract_frames = lambda *args: (frames, 7, "abcdefgh")
            progress = []
            result = self.store.ingest_video("unused.mp4", "clip.mp4", on_progress=lambda *args: progress.append(args))
        saved = self.store.collection.saved
        self.assertEqual(saved["embeddings"], [[float(index)] for index in range(7)])
        self.assertEqual([meta["frame_num"] for meta in saved["metadatas"]], list(range(1, 8)))
        self.assertEqual(progress, [(6, 7), (7, 7)])
        self.assertEqual(result["frames_extracted"], 7)

    def test_unexpected_embedding_count_is_rejected(self):
        with patch.object(self.service, "embed_content", return_value=types.SimpleNamespace(embeddings=[])):
            with self.assertRaisesRegex(ValueError, "one vector per frame"):
                self.store._embed_images_batch([(b"frame", "image/jpeg")])
        self.assertIsNone(self.store.collection.saved)

    def test_empty_batch_makes_no_request(self):
        self.assertEqual(self.store._embed_images_batch([]), [])
        self.assertEqual(self.service.calls, [])


if __name__ == "__main__":
    unittest.main()
