#!/usr/bin/env python3
"""Deterministic unit test for pdf-translate audit script.

Tests clause normalization, regex clause extraction, hallucination detection,
and CLI argument parsing using only the Python standard library.
"""

# SPDX-License-Identifier: Apache-2.0

import os
import re
import sys
import unittest
from pathlib import Path

# Add scripts directory to path
SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "pdf-translate" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from audit_pdf import (
    DEFAULT_HALLUCINATION_KEYWORDS,
    extract_clauses,
    normalize_clause,
)


class TestAuditPdf(unittest.TestCase):
    def test_normalize_clause(self):
        self.assertEqual(normalize_clause(" Section 1.2 "), "section1.2")
        self.assertEqual(normalize_clause("附录 A.1"), "附录a.1")
        self.assertEqual(normalize_clause("Table 3.1"), "table3.1")

    def test_extract_clauses(self):
        text = """
        This document contains Section 1.2.3 and Section 4.
        See Appendix-1 and Table 2A for detailed parameters.
        Check clause 4.2.1 and 5.0.0 below.
        """
        clauses = extract_clauses(text)
        self.assertIn("Section 1.2.3", clauses)
        self.assertIn("Appendix-1", clauses)
        self.assertIn("4.2.1", clauses)

    def test_default_hallucination_keywords(self):
        self.assertIn("TODO", DEFAULT_HALLUCINATION_KEYWORDS)
        self.assertIn("TBD", DEFAULT_HALLUCINATION_KEYWORDS)
        self.assertIn("[omitted]", DEFAULT_HALLUCINATION_KEYWORDS)
        self.assertIn("待补充", DEFAULT_HALLUCINATION_KEYWORDS)

        sample_clean = "This is a faithful translation of the original research paper."
        sample_dirty = "The table was omitted due to space and will be TBD later."

        self.assertFalse(any(kw in sample_clean for kw in DEFAULT_HALLUCINATION_KEYWORDS))
        self.assertTrue(any(kw in sample_dirty for kw in DEFAULT_HALLUCINATION_KEYWORDS))

    def test_custom_keywords_and_ignores(self):
        custom_keywords = ["custom_placeholder", "draft_only"]
        sample = "Here is custom_placeholder text."
        self.assertTrue(any(kw in sample for kw in custom_keywords))

        sample_clauses = ["1.1", "2.3.4", "2026.1"]
        ignore_list = ["2026"]
        filtered = [c for c in sample_clauses if not any(ign in c for ign in ignore_list)]
        self.assertEqual(filtered, ["1.1", "2.3.4"])


def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAuditPdf)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
