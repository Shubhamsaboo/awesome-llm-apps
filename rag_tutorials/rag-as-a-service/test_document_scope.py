import ast
from pathlib import Path
from typing import Dict, List, Optional
import unittest
from unittest.mock import Mock
from urllib.parse import urlparse


source = Path(__file__).with_name("rag_app.py")
tree = ast.parse(source.read_text(encoding="utf-8"))
pipeline = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                and node.name == "RAGPipeline")


class DocumentScopeTests(unittest.TestCase):
    def setUp(self):
        self.documents = [{"metadata": {"scope": "unrelated"}, "text": "Other corpus"}]
        self.http = Mock(post=self.post)
        namespace = {"requests": self.http, "Anthropic": Mock(), "urlparse": urlparse,
                     "Dict": Dict, "List": List, "Optional": Optional}
        exec(compile(ast.Module(body=[pipeline], type_ignores=[]), str(source), "exec"), namespace)
        self.pipeline = namespace["RAGPipeline"]("ragie-key", "model-key")

    def post(self, url, *, json, headers):
        if url.endswith("/documents/url"):
            self.documents.append({"metadata": json.get("metadata", {}), "text": json["url"]})
            result = {"id": "uploaded"}
        else:
            scope_filter = json.get("filter", {})
            result = {"scored_chunks": [
                {"text": document["text"]} for document in self.documents
                if all(document["metadata"].get(key) == value for key, value in scope_filter.items())
            ]}
        return Mock(ok=True, json=Mock(return_value=result))

    def test_default_upload_is_retrievable_without_other_corpora(self):
        self.pipeline.upload_document("https://example.com/tutorial.pdf")
        self.assertEqual(self.pipeline.retrieve_chunks("question"), ["https://example.com/tutorial.pdf"])

    def test_explicit_scope_uses_the_same_upload_and_retrieval_metadata(self):
        self.pipeline.upload_document("https://example.com/one.pdf", scope="one")
        self.pipeline.upload_document("https://example.com/two.pdf", scope="two")
        self.assertEqual(self.pipeline.retrieve_chunks("question", scope="two"), ["https://example.com/two.pdf"])


if __name__ == "__main__":
    unittest.main()
