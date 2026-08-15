#!/usr/bin/env python3
"""Deterministic offline eval for the multi-source report validator."""

# SPDX-License-Identifier: Apache-2.0

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "sandbase-multi-source-research" / "scripts" / "validate_report.py"
CHECKS = []


def check(name, condition, detail=""):
    CHECKS.append(bool(condition))
    suffix = "" if condition or not detail else ": " + detail
    print("  %s %s%s" % ("PASS" if condition else "FAIL", name, suffix))


def base_report():
    return {
        "question": "Does the measured result replicate independently?",
        "searched_at": "2026-08-15",
        "providers": ["tavily_search", "exa_search", "scholar_search_mixed"],
        "unavailable_providers": [],
        "sources": [
            {"id": "s1", "url": "https://example.org/a", "publisher": "A", "source_type": "primary"},
            {"id": "s2", "url": "https://example.net/b", "publisher": "B", "source_type": "secondary"},
            {"id": "s3", "url": "https://example.com/c", "publisher": "C", "source_type": "primary"},
        ],
        "claims": [{
            "id": "c1", "text": "Three independent sources report the result.",
            "kind": "sourced", "confidence": "high", "source_ids": ["s1", "s2", "s3"],
            "independent_source_count": 3, "conflict": False,
        }],
        "gaps": ["The raw benchmark data is not public."],
    }


def run_report(root, name, report):
    path = root / name
    path.write_text(json.dumps(report), encoding="utf-8")
    return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True, timeout=10)


def main():
    print("sandbase-multi-source-research eval:")
    with tempfile.TemporaryDirectory(prefix="sandbase-research-eval-") as temp_dir:
        root = Path(temp_dir)
        valid = run_report(root, "valid.json", base_report())
        check("valid report passes", valid.returncode == 0, valid.stderr)
        check("valid report prints bounded summary", valid.stdout.strip() == "VALID: 3 source(s), 1 claim(s), 3 provider(s)")

        weak = copy.deepcopy(base_report())
        weak["claims"][0]["independent_source_count"] = 2
        weak_result = run_report(root, "weak.json", weak)
        check("inflated high confidence fails", weak_result.returncode == 1)
        check("confidence failure is explained", "requires at least 3 independent sources" in weak_result.stderr)

        unknown = copy.deepcopy(base_report())
        unknown["claims"][0]["source_ids"][2] = "missing"
        unknown_result = run_report(root, "unknown.json", unknown)
        check("unknown source reference fails", unknown_result.returncode == 1)
        check("unknown source is named", "unknown source id: missing" in unknown_result.stderr)

        circular = copy.deepcopy(base_report())
        circular["sources"][2]["url"] = circular["sources"][0]["url"]
        circular_result = run_report(root, "circular.json", circular)
        check("duplicate source URL fails", circular_result.returncode == 1)
        check("duplicate URL is explained", "duplicate source URL" in circular_result.stderr)

        conflict = copy.deepcopy(base_report())
        conflict["claims"][0]["conflict"] = True
        conflict_result = run_report(root, "conflict.json", conflict)
        check("conflicting high-confidence claim fails", conflict_result.returncode == 1)
        check("conflict rule is explained", "cannot be high confidence" in conflict_result.stderr)

        unused = copy.deepcopy(base_report())
        unused["claims"][0]["source_ids"] = ["s1", "s2"]
        unused["claims"][0]["confidence"] = "medium"
        unused["claims"][0]["independent_source_count"] = 2
        unused_result = run_report(root, "unused.json", unused)
        check("unused ledger source fails", unused_result.returncode == 1)
        check("unused source is named", "source is not referenced by any claim: s3" in unused_result.stderr)

    passed = sum(CHECKS)
    print("\n%s: %d/%d checks" % ("PASS" if passed == len(CHECKS) else "FAIL", passed, len(CHECKS)))
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())


def test_multi_source_report_eval():
    assert main() == 0

