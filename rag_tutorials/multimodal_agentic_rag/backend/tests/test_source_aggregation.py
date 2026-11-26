"""Source centroids preserve their values without quadratic chunk scans."""

import os
import unittest
from unittest.mock import patch

from rag_store import MultimodalRagStore, RackChunk, RackSource


class CountedChunks(list):
    visits = 0

    def __iter__(self):
        for chunk in super().__iter__():
            self.visits += 1
            yield chunk


class SourceAggregationTests(unittest.TestCase):
    def setUp(self):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": ""}):
            self.store = MultimodalRagStore(dimensions=3)

    def test_centroids_match_individual_sources(self):
        self.store.sources = [RackSource(s, s, "text", "", 0) for s in ["a", "b", "empty"]]
        values = [("a", [1, 0, 1]), ("b", [0, 2]), ("a", [0, 1, 0, 99]),
                  ("orphan", [1, 1, 1])]
        self.store.chunks = [RackChunk(str(i), s, s, "text", "", v)
                             for i, (s, v) in enumerate(values)]
        expected = {source.id: self.store._source_vector(source.id)
                    for source in self.store.sources}
        self.assertEqual(self.store._source_vectors(), expected)

    def test_chunk_visits_scale_with_corpus_size(self):
        size = 250
        self.store.sources = [RackSource(str(i), "doc", "text", "", 1) for i in range(size)]
        self.store.chunks = CountedChunks(
            RackChunk(str(i), str(i), "doc", "text", "", [1, 2, 3]) for i in range(size)
        )
        result = self.store._source_vectors()
        self.assertEqual(len(result), size)
        self.assertLessEqual(self.store.chunks.visits, 2 * size)


if __name__ == "__main__":
    unittest.main()
