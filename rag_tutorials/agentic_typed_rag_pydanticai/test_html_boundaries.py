"""HTML source text must preserve words before chunking and retrieval."""

import unittest

from rag import HashingEmbeddingBackend, InMemoryVectorStore, html_to_text


class HTMLBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def test_table_cells_remain_searchable_words(self):
        text = html_to_text(
            "<table><tr><th>Plan</th><th>Monthly price</th></tr>"
            "<tr><td>Starter</td><td>10</td></tr>"
            "<tr><td>Pro</td><td>25</td></tr></table>"
        )
        self.assertEqual(text.split(), ["Plan", "Monthly", "price", "Starter", "10", "Pro", "25"])
        store = InMemoryVectorStore(HashingEmbeddingBackend())
        await store.add_document("prices", text)
        results = await store.search("Starter")
        self.assertGreater(results[0].score, 0)

    async def test_block_boundaries_preserve_inline_word_fragments(self):
        text = html_to_text(
            "<h4>Features</h4><dl><dt>Protocol</dt>"
            "<dd><strong>inter</strong>operability</dd></dl>"
            "<script>ignored()</script><pre>Example</pre><footer>Contact</footer>"
        )
        self.assertEqual(text.split(), ["Features", "Protocol", "interoperability", "Example", "Contact"])


if __name__ == "__main__":
    unittest.main()
