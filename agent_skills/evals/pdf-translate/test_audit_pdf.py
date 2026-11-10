#!/usr/bin/env python3
"""Deterministic unit test for pdf-translate audit script.

Tests clause normalization, regex clause extraction, hallucination detection,
and CLI argument parsing using only the Python standard library.
"""

# SPDX-License-Identifier: Apache-2.0

import os
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "pdf-translate" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit_pdf import (
    DEFAULT_HALLUCINATION_KEYWORDS,
    audit_document,
    clause_number,
    extract_clauses,
    normalize_clause,
    parse_csv_list,
)


class FakePage:
    def __init__(self, text):
        self._text = text
        self.rect = types.SimpleNamespace(width=595, height=842)

    def get_images(self):
        return []

    def get_text(self):
        return self._text


def run_audit(src_text, tgt_text, **kwargs):
    """Run audit_document() on single-page fake PDFs via a stub fitz module."""
    pages = {"src.pdf": [FakePage(src_text)], "tgt.pdf": [FakePage(tgt_text)]}
    fake_fitz = types.ModuleType("fitz")
    fake_fitz.open = lambda path: pages[os.path.basename(path)]

    with tempfile.TemporaryDirectory() as tmpdir:
        src_pdf = os.path.join(tmpdir, "src.pdf")
        tgt_pdf = os.path.join(tmpdir, "tgt.pdf")
        Path(src_pdf).write_text("dummy", encoding="utf-8")
        Path(tgt_pdf).write_text("dummy", encoding="utf-8")
        with patch.dict(sys.modules, {"fitz": fake_fitz}):
            return audit_document(src_pdf, tgt_pdf, **kwargs)


class TestAuditPdf(unittest.TestCase):
    def test_normalize_clause(self):
        self.assertEqual(normalize_clause(" Section 1.2 "), "section1.2")
        self.assertEqual(normalize_clause("附录 A.1"), "附录a.1")
        self.assertEqual(normalize_clause("Table 3.1"), "table3.1")

    def test_extract_clauses(self):
        text = """
        This document contains Section 1.2.3 and Section 4.
        See Appendix-1 and Table 2A for detailed parameters.
        Check clause 4.2.1 and 5.0.0 below. Refer to Table 3.1.
        """
        clauses = extract_clauses(text)
        self.assertIn("Section 1.2.3", clauses)
        self.assertIn("Appendix-1", clauses)
        self.assertIn("4.2.1", clauses)
        self.assertIn("Table 3.1", clauses)

    def test_clause_number(self):
        self.assertEqual(clause_number("Section 1.2"), "1.2")
        self.assertEqual(clause_number("第 1.2 部分"), "1.2")
        self.assertEqual(clause_number("Table 3.1"), "3.1")
        self.assertIsNone(clause_number("Appendix-1"))

    def test_parse_csv_list_drops_empty_entries(self):
        self.assertEqual(parse_csv_list("TODO,"), ["TODO"])
        self.assertEqual(parse_csv_list(" a , ,b,"), ["a", "b"])
        self.assertIsNone(parse_csv_list(","))
        self.assertIsNone(parse_csv_list(None))

    def test_default_hallucination_keywords(self):
        self.assertIn("TODO", DEFAULT_HALLUCINATION_KEYWORDS)
        self.assertIn("TBD", DEFAULT_HALLUCINATION_KEYWORDS)
        self.assertIn("[omitted]", DEFAULT_HALLUCINATION_KEYWORDS)
        self.assertIn("待补充", DEFAULT_HALLUCINATION_KEYWORDS)

        src = "Section 1.1 describes the full scope of the work in detail."
        self.assertTrue(run_audit(src, "Section 1.1 is a faithful translation of the scope."))
        self.assertFalse(run_audit(src, "Section 1.1 content is TBD and will be added later."))

    def test_custom_hallucination_keywords(self):
        src = "Section 1.1 describes the full scope of the work in detail."
        tgt = "Section 1.1 here is custom_placeholder text for the scope."
        self.assertFalse(run_audit(src, tgt, hallucination_keywords=["custom_placeholder"]))
        self.assertTrue(run_audit(src, tgt, hallucination_keywords=["draft_only"]))

        # Trailing comma must not produce an empty keyword that matches every page
        clean = "Section 1.1 is a faithful translation of the original scope."
        self.assertTrue(run_audit(src, clean, hallucination_keywords=parse_csv_list("draft_only,")))
        self.assertTrue(run_audit(src, clean, hallucination_keywords=["draft_only", ""]))

    def test_ignore_clauses(self):
        src = "Section 1.1 and clause 2026.1 are both described here in detail."
        tgt = "Section 1.1 is described here in detail, the other one is gone."
        self.assertFalse(run_audit(src, tgt, strict=True))
        self.assertTrue(run_audit(src, tgt, strict=True, ignore_clauses=["2026"]))

        # Trailing comma must not produce an empty pattern that ignores every clause
        src2 = "Section 1.1 and clause 3.4 are both described here in detail."
        tgt2 = "Section 1.1 is described here in detail, the other one is gone."
        self.assertFalse(run_audit(src2, tgt2, strict=True, ignore_clauses=parse_csv_list("2026,")))
        self.assertFalse(run_audit(src2, tgt2, strict=True, ignore_clauses=["2026", ""]))

    def test_strict_mode_missing_clauses(self):
        src = "Section 1.1 and clause 1.2 are present here in detail."
        tgt = "Section 1.1 is present here in detail without the second one."
        self.assertTrue(run_audit(src, tgt, strict=False))
        self.assertFalse(run_audit(src, tgt, strict=True))

    def test_cross_language_labels_match_by_number(self):
        src = "Section 1.2 defines the scope. See Table 3.1 for parameters."
        tgt = "第 1.2 部分 定义了工作范围。参数详见 表 3.1 中的内容。"
        self.assertTrue(run_audit(src, tgt, strict=True))

        tgt_missing_table = "第 1.2 部分 定义了工作范围。参数详见下表中的内容。"
        self.assertFalse(run_audit(src, tgt_missing_table, strict=True))


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuditPdf)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
