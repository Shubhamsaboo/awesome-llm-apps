import ast
from datetime import datetime
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from typing import List
import unittest
from unittest.mock import Mock

from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
APPS = ["deepseek_local_rag_agent/deepseek_rag_agent.py",
        "qwen_local_rag/qwen_local_rag_agent.py",
        "gemini_agentic_rag/agentic_rag_gemini.py"]


class PdfStagingTests(unittest.TestCase):
    def setUp(self):
        self.paths = []
        self.upload = io.BytesIO()
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        writer.write(self.upload)
        self.upload.name = "small.pdf"

    def loader(self, path):
        self.paths.append(Path(path))
        def load():
            reader = PdfReader(path)
            return [SimpleNamespace(metadata={}, page_content=page.extract_text()) for page in reader.pages]
        return SimpleNamespace(load=load)

    def namespace(self):
        return {"os": os, "tempfile": tempfile, "datetime": datetime, "List": List,
                "PyPDFLoader": self.loader, "st": Mock(),
                "RecursiveCharacterTextSplitter": Mock(return_value=SimpleNamespace(split_documents=lambda docs: docs))}

    def process(self, filename, upload):
        source = ROOT / filename
        tree = ast.parse(source.read_text(encoding="utf-8"))
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == "process_pdf")
        namespace = self.namespace()
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
        return namespace["process_pdf"](upload)

    def tearDown(self):
        for path in self.paths:
            path.unlink(missing_ok=True)

    def test_small_pdfs_are_readable_and_staging_files_are_removed(self):
        for filename in APPS:
            with self.subTest(app=filename):
                self.assertEqual(len(self.process(filename, self.upload)), 1)
                self.assertFalse(self.paths[-1].exists())

    def test_loader_failure_also_removes_staged_upload(self):
        invalid = io.BytesIO(b"not a PDF")
        invalid.name = "broken.pdf"
        for filename in APPS:
            with self.subTest(app=filename):
                self.assertEqual(self.process(filename, invalid), [])
                self.assertFalse(self.paths[-1].exists())

    def test_corrective_rag_closes_writer_before_loading(self):
        source = ROOT / "corrective_rag/corrective_rag.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        block = next(node for node in tree.body if isinstance(node, ast.If)
                     and ast.unparse(node.test) == "input_option == 'URL'")
        namespace = self.namespace()
        namespace.update(input_option="File Upload", docs=None,
                         load_documents=lambda path, is_url: self.loader(path).load())
        namespace["st"].file_uploader.return_value = self.upload
        exec(compile(ast.Module(body=[block], type_ignores=[]), str(source), "exec"), namespace)
        self.assertEqual(len(namespace["docs"]), 1)
        self.assertFalse(self.paths[-1].exists())


if __name__ == "__main__":
    unittest.main()
