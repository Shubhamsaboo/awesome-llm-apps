import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag_store import MultimodalRagStore


class SourceAtomicityTests(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}):
            self.store = MultimodalRagStore(dimensions=3)

    def test_failed_embedding_preserves_only_existing_evidence(self):
        with patch.object(self.store, "_embed_text", return_value=[1.0, 0.0, 0.0]):
            self.store.add_text_source("Existing", "This source was ingested successfully.")
        sources, chunks, events = (list(self.store.sources), list(self.store.chunks), list(self.store.events))
        with patch.object(self.store, "_embed_text", side_effect=[[1.0, 0.0, 0.0], RuntimeError("quota")]):
            with self.assertRaisesRegex(RuntimeError, "quota"):
                self.store.add_text_source("Incomplete", "word " * 400)
        self.assertEqual(self.store.sources, sources)
        self.assertEqual(self.store.chunks, chunks)
        self.assertEqual(self.store.events, events)

    def test_success_publishes_all_chunks_and_one_event(self):
        with patch.object(self.store, "_embed_text", return_value=[1.0, 0.0, 0.0]):
            source = self.store.add_text_source("Complete", "word " * 400)
        self.assertEqual(source.chunks, len(self.store.chunks))
        self.assertEqual(len(self.store.sources), 1)
        self.assertEqual(len(self.store.events), 1)
        self.assertTrue(all(chunk.source_id == source.id for chunk in self.store.chunks))


if __name__ == "__main__":
    unittest.main()
