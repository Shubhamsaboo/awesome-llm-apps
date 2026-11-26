import ast
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import fitz
import numpy as np
from PIL import Image


source = Path(__file__).with_name("vision_rag.py")
tree = ast.parse(source.read_text(encoding="utf-8"))
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "process_pdf_file")
namespace = {"os": os, "tempfile": tempfile, "fitz": fitz, "Image": Image, "np": np,
             "st": Mock(), "pil_to_base64": Mock(return_value="image"),
             "compute_image_embedding": Mock(return_value=np.array([1.0, 0.0]))}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)


class PdfOutputIsolationTests(unittest.TestCase):
    def pdf(self, color):
        with fitz.open() as document:
            page = document.new_page(width=72, height=72)
            page.draw_rect(page.rect, color=color, fill=color)
            upload = io.BytesIO(document.tobytes())
        upload.name = "report.pdf"
        return upload

    def test_same_named_upload_does_not_replace_previously_indexed_pages(self):
        process = namespace["process_pdf_file"]
        with tempfile.TemporaryDirectory() as folder:
            first_paths, _ = process(self.pdf((1, 0, 0)), Mock(), folder)
            first_image = Path(first_paths[0]).read_bytes()
            second_paths, _ = process(self.pdf((0, 0, 1)), Mock(), folder)
            self.assertEqual(Path(first_paths[0]).read_bytes(), first_image)
            self.assertNotEqual(first_paths, second_paths)
            self.assertNotEqual(Path(second_paths[0]).read_bytes(), first_image)


if __name__ == "__main__":
    unittest.main()
