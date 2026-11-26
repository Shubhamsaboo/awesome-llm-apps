import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent


class Part:
    @classmethod
    def from_bytes(cls, data, mime_type):
        return types.SimpleNamespace(data=data, mime_type=mime_type)


class Content:
    def __init__(self, parts):
        self.parts = parts


genai = types.ModuleType("google.genai")
genai.types = types.SimpleNamespace(Part=Part, Content=Content)
google = types.ModuleType("google")
google.genai = genai
with patch.dict(sys.modules, {"chromadb": types.ModuleType("chromadb"), "google": google,
                              "google.genai": genai, "google.genai.types": genai.types}):
    spec = importlib.util.spec_from_file_location("video_store_under_test", ROOT / "video_store.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


class VideoFrameCleanupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.store = module.VideoStore.__new__(module.VideoStore)
        self.store.frames_dir = Path(self.directory.name)
        self.selected = self.store.frames_dir / "a123bcde"
        self.other = self.store.frames_dir / "b123cdef"
        for path in [self.selected, self.other]:
            path.mkdir()
            (path / "frame_0001.jpg").write_bytes(b"frame")
        self.deleted = []
        self.store.collection = types.SimpleNamespace(
            get=lambda **kwargs: {"ids": ["a123bcde_f0001"]},
            delete=lambda **kwargs: self.deleted.append(kwargs["ids"]),
        )

    def test_deletion_removes_only_the_selected_video_frames(self):
        self.assertTrue(self.store.delete_video("a123bcde"))
        self.assertEqual(self.deleted, [["a123bcde_f0001"]])
        self.assertFalse(self.selected.exists())
        self.assertEqual((self.other / "frame_0001.jpg").read_bytes(), b"frame")

    def test_unknown_video_reports_not_found_without_deleting_files(self):
        self.store.collection.get = lambda **kwargs: {"ids": []}
        self.assertFalse(self.store.delete_video("a123bcde"))
        self.assertTrue(self.selected.exists())
        self.assertEqual(self.deleted, [])

    def test_failed_index_deletion_keeps_the_frames(self):
        def fail(**kwargs):
            raise RuntimeError("database unavailable")
        self.store.collection.delete = fail
        self.assertFalse(self.store.delete_video("a123bcde"))
        self.assertTrue(self.selected.exists())

    def test_already_missing_frames_do_not_prevent_index_deletion(self):
        (self.selected / "frame_0001.jpg").unlink()
        self.selected.rmdir()
        self.assertTrue(self.store.delete_video("a123bcde"))


if __name__ == "__main__":
    unittest.main()
