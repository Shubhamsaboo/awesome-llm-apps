"""Exercise the preprocessing function without starting the Streamlit UI."""
import ast
import csv
import io
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock

import pandas as pd


source = Path(__file__).with_name("ai_data_analyst.py")
tree = ast.parse(source.read_text(encoding="utf-8"))
function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                and node.name == "preprocess_and_save")
namespace = {"pd": pd, "csv": csv, "re": re, "tempfile": tempfile, "st": Mock()}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(source), "exec"), namespace)
preprocess_and_save = namespace["preprocess_and_save"]


class PreprocessingTests(unittest.TestCase):
    def process(self, content):
        upload = io.BytesIO(content.encode())
        upload.name = "data.csv"
        path, columns, frame = preprocess_and_save(upload)
        self.assertIsNotNone(path)
        self.addCleanup(Path(path).unlink, missing_ok=True)
        return frame

    def test_non_date_columns_retain_their_original_values(self):
        frame = self.process("candidate,update_status\nAlice,pending\nBob,complete\n")
        self.assertEqual(frame["candidate"].tolist(), ["Alice", "Bob"])
        self.assertEqual(frame["update_status"].tolist(), ["pending", "complete"])

    def test_date_tokens_are_still_parsed(self):
        frame = self.process("Order Date,date_created,amount\n2026-01-02,2026-02-03,12.5\n")
        self.assertEqual(frame["Order Date"].iloc[0], pd.Timestamp("2026-01-02"))
        self.assertEqual(frame["date_created"].iloc[0], pd.Timestamp("2026-02-03"))
        self.assertEqual(frame["amount"].iloc[0], 12.5)


if __name__ == "__main__":
    unittest.main()
