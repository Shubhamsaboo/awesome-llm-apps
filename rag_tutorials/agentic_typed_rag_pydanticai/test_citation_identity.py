import unittest

from rag import HashingEmbeddingBackend, InMemoryVectorStore


class CitationIdentityTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_named_documents_keep_distinct_citation_targets(self):
        store = InMemoryVectorStore(HashingEmbeddingBackend())
        first = "Apples are shipped every Monday."
        second = "Bananas are shipped every Friday."
        await store.add_document("report.pdf", first, locator="p1")
        await store.add_document("report.pdf", second, locator="p1")
        self.assertNotEqual(store.chunks[0].chunk_id, store.chunks[1].chunk_id)
        for chunk in store.chunks:
            self.assertEqual(store.find_chunk(chunk.source, chunk.chunk_id).text, chunk.text)
        self.assertEqual(store.find_chunk("report.pdf", store.chunks[1].chunk_id).text, second)

    async def test_identical_document_ids_remain_deterministic(self):
        stores = [InMemoryVectorStore(HashingEmbeddingBackend()) for _ in range(2)]
        for store in stores:
            await store.add_document("policy.pdf", "Travel receipts are required.", locator="p2")
        self.assertEqual(stores[0].chunks[0].chunk_id, stores[1].chunks[0].chunk_id)
        self.assertTrue(stores[0].chunks[0].chunk_id.startswith("policy.pdf:p2:c1"))


if __name__ == "__main__":
    unittest.main()
