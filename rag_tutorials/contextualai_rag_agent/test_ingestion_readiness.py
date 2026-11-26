import ast
from pathlib import Path
from typing import List, Optional
import unittest
from unittest.mock import Mock

import requests


source = Path(__file__).with_name("contextualai_rag_agent.py")
tree = ast.parse(source.read_text(encoding="utf-8"))
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "wait_until_documents_ready")


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.http = Mock(RequestException=requests.RequestException)
        self.namespace = {"requests": self.http, "time": Mock(), "st": Mock(),
                          "Optional": Optional, "List": List}
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), self.namespace)
        self.wait = self.namespace["wait_until_documents_ready"]

    def response(self, payload, code=200):
        return Mock(status_code=code, json=Mock(return_value=payload))

    def test_completed_documents_are_ready(self):
        self.http.get.return_value = self.response({"documents": [{"status": "completed"}]})
        self.assertIs(self.wait("key", "store", "https://api.example/v1", max_checks=1), True)

    def test_nonterminal_empty_and_failed_results_are_not_ready(self):
        for status in ("retrying", "pending", "processing", "failed", "cancelled", "unknown", None):
            with self.subTest(status=status):
                docs = [{"status": status}] if status is not None else []
                self.http.get.return_value = self.response({"documents": docs})
                self.assertIs(self.wait("key", "store", "https://api.example/v1", max_checks=1), False)

    def test_http_failure_does_not_report_success_after_timeout(self):
        self.http.get.return_value = self.response({}, code=503)
        self.assertIs(self.wait("key", "store", "https://api.example/v1", max_checks=2), False)
        self.assertEqual(self.http.get.call_count, 2)

    def test_only_uploaded_document_ids_are_polled(self):
        self.http.get.side_effect = [self.response({"status": "completed"}), self.response({"status": "retrying"})]
        self.assertIs(self.wait("key", "store", "https://api.example/v1", max_checks=1,
                                document_ids=["first", "second"]), False)
        self.assertEqual([call.args[0] for call in self.http.get.call_args_list], [
            "https://api.example/v1/datastores/store/documents/first/metadata",
            "https://api.example/v1/datastores/store/documents/second/metadata",
        ])


if __name__ == "__main__":
    unittest.main()
