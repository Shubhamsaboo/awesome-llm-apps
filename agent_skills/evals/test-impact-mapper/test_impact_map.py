#!/usr/bin/env python3
"""
Executable eval for test-impact-mapper. Builds a temporary git repository,
edits a source file, and checks the deterministic mapper.

    python3 agent_skills/evals/test-impact-mapper/test_impact_map.py

The fixture contains a billing change with a conventional test pair, a
transitive importer, a symbol-only test, an unrelated docs file, and a JS
spec. It uses only git and the Python stdlib.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile


SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "test-impact-mapper",
    "scripts",
    "impact_map.py",
)

checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    suffix = ": %s" % detail if detail and not ok else ""
    print("  %s %s%s" % ("PASS" if ok else "FAIL", name, suffix))


def write(root, path, content):
    target = os.path.join(root, path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(content)


def git(root, *args, env=None):
    merged = dict(os.environ)
    if env:
        merged.update(env)
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, env=merged)


def run_mapper(root, extra):
    result = subprocess.run(
        [sys.executable, SCRIPT, "--repo", root, "--no-history", *extra],
        capture_output=True,
        text=True,
    )
    return result


def load_json(result):
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def recommended_paths(report):
    return [item["path"] for item in report.get("recommended", [])]


def evidence_kinds(report, path):
    for item in report.get("recommended", []):
        if item["path"] == path:
            return {ev["kind"] for ev in item.get("evidence", [])}
    return set()


def build_repo(root):
    git(root, "init", "-q")
    git(root, "config", "user.email", "impact-eval@example.com")
    git(root, "config", "user.name", "impact eval")
    git(root, "checkout", "-qb", "main")

    write(
        root,
        "billing/invoice.py",
        "def compute_total(items):\n"
        "    return sum(item[\"price\"] for item in items)\n",
    )
    write(
        root,
        "billing/tax.py",
        "from billing.invoice import compute_total\n"
        "\n"
        "def taxed_total(items, rate):\n"
        "    return compute_total(items) * (1 + rate)\n",
    )
    write(
        root,
        "auth/tokens.py",
        "def mint_token(user_id):\n"
        "    return \"tok-%s\" % user_id\n",
    )
    write(
        root,
        "web/cart.js",
        "export function cartTotal(items) {\n"
        "  return items.reduce((sum, item) => sum + item.price, 0);\n"
        "}\n",
    )
    write(
        root,
        "tests/test_invoice.py",
        "from billing.invoice import compute_total\n"
        "from billing.tax import taxed_total\n"
        "\n"
        "def test_compute_total():\n"
        "    assert compute_total([{\"price\": 10}]) == 10\n"
        "\n"
        "def test_taxed_total():\n"
        "    assert taxed_total([{\"price\": 10}], 0.1) == 11\n",
    )
    write(
        root,
        "tests/test_sessions.py",
        "from auth.tokens import mint_token\n"
        "\n"
        "def test_mint_token():\n"
        "    assert mint_token(\"ada\") == \"tok-ada\"\n",
    )
    write(
        root,
        "web/cart.test.js",
        "import { cartTotal } from './cart.js';\n"
        "\n"
        "test('cart total', () => {\n"
        "  expect(cartTotal([{price: 2}])).toBe(2);\n"
        "});\n",
    )
    write(root, "docs/guide.md", "# Billing\nHow invoices work.\n")
    write(root, ".gitattributes", "*.bin diff=impact-eval-textconv\n")
    write(root, "assets/sample.bin", "before\x00data\n")
    git(root, "add", "-A")
    git(root, "commit", "-qm", "baseline")

    write(
        root,
        "billing/invoice.py",
        "def compute_total(items):\n"
        "    if not items:\n"
        "        return 0\n"
        "    return sum(item[\"price\"] for item in items)\n",
    )
    write(root, "docs/guide.md", "# Billing\nHow invoices work, with empty carts.\n")
    write(root, "assets/sample.bin", "after\x00data\n")


def main():
    root = tempfile.mkdtemp(prefix="test-impact-eval-")
    try:
        build_repo(root)

        marker = os.path.join(root, "textconv-ran")
        helper = os.path.join(root, "textconv.py")
        write(
            root,
            "textconv.py",
            "import pathlib\n"
            "import sys\n"
            "pathlib.Path(sys.argv[1]).write_text('ran', encoding='utf-8')\n"
            "print(pathlib.Path(sys.argv[2]).read_bytes().hex())\n",
        )
        git(
            root,
            "config",
            "diff.impact-eval-textconv.textconv",
            "%s %s %s" % (sys.executable, helper, marker),
        )

        result = run_mapper(root, ["--json"])
        print("working-tree map:")
        check("script exits successfully", result.returncode == 0, result.stderr.strip())
        report = load_json(result)
        check("stdout is valid JSON", bool(report), result.stdout[:200])

        paths = recommended_paths(report)
        kinds = {item["path"]: item["kind"] for item in report.get("changed_files", [])}

        check("invoice test is recommended", "tests/test_invoice.py" in paths, paths)
        check(
            "invoice test has path evidence",
            "path" in evidence_kinds(report, "tests/test_invoice.py"),
            evidence_kinds(report, "tests/test_invoice.py"),
        )
        check(
            "invoice test has import evidence",
            "import" in evidence_kinds(report, "tests/test_invoice.py"),
            evidence_kinds(report, "tests/test_invoice.py"),
        )
        check(
            "sessions test is not recommended for an invoice change",
            "tests/test_sessions.py" not in paths,
            paths,
        )
        check("docs file is unmapped", "docs/guide.md" in report.get("unmapped", []), report.get("unmapped"))
        check("docs file is labeled other", kinds.get("docs/guide.md") == "other", kinds)
        check("invoice is labeled source", kinds.get("billing/invoice.py") == "source", kinds)
        check("git textconv command is not executed", not os.path.exists(marker), marker)
        check(
            "diff source is working",
            report.get("diff_source") == "working",
            report.get("diff_source"),
        )

        human = run_mapper(root, [])
        check("human report exits 0", human.returncode == 0, human.stderr.strip())
        check("human report names TEST IMPACT", "TEST IMPACT" in human.stdout, human.stdout[:80])
        check("human report lists the invoice test", "tests/test_invoice.py" in human.stdout, human.stdout)

        # Staged: the working tree change is unstaged, so staging invoice
        # should still map, and a later staged-only file should appear.
        git(root, "add", "billing/invoice.py")
        staged = run_mapper(root, ["--staged", "--json"])
        staged_report = load_json(staged)
        check("staged mode exits 0", staged.returncode == 0, staged.stderr.strip())
        check(
            "staged source is staged",
            staged_report.get("diff_source") == "staged",
            staged_report.get("diff_source"),
        )
        check(
            "staged invoice test is recommended",
            "tests/test_invoice.py" in recommended_paths(staged_report),
            recommended_paths(staged_report),
        )

        # Branch diff: commit the invoice change, then compare against main's parent.
        git(root, "checkout", "-qb", "feat/empty-cart")
        git(root, "add", "billing/invoice.py")
        git(root, "commit", "-qm", "handle empty invoice")
        base = run_mapper(root, ["--base", "main", "--json"])
        base_report = load_json(base)
        check("base mode exits 0", base.returncode == 0, base.stderr.strip())
        check(
            "base source names the ref",
            base_report.get("diff_source") == "base:main",
            base_report.get("diff_source"),
        )
        check(
            "base invoice test is recommended",
            "tests/test_invoice.py" in recommended_paths(base_report),
            recommended_paths(base_report),
        )

        # Plain unified diff without git headers, plus --diff.
        plain = os.path.join(root, "plain.diff")
        write(
            root,
            "plain.diff",
            "--- a/auth/tokens.py\n"
            "+++ b/auth/tokens.py\n"
            "@@ -1,2 +1,3 @@\n"
            " def mint_token(user_id):\n"
            "+    if not user_id:\n"
            "+        return \"\"\n"
            "     return \"tok-%s\" % user_id\n",
        )
        # Restore tokens.py so the import graph still sees mint_token.
        write(
            root,
            "auth/tokens.py",
            "def mint_token(user_id):\n"
            "    if not user_id:\n"
            "        return \"\"\n"
            "    return \"tok-%s\" % user_id\n",
        )
        diff_result = run_mapper(root, ["--diff", plain, "--json"])
        diff_report = load_json(diff_result)
        check("diff mode exits 0", diff_result.returncode == 0, diff_result.stderr.strip())
        check(
            "diff source is diff",
            diff_report.get("diff_source") == "diff",
            diff_report.get("diff_source"),
        )
        check(
            "symbol/import maps mint_token to sessions tests",
            "tests/test_sessions.py" in recommended_paths(diff_report),
            recommended_paths(diff_report),
        )
        check(
            "invoice test is not in the token-only diff shortlist",
            "tests/test_invoice.py" not in recommended_paths(diff_report),
            recommended_paths(diff_report),
        )
        token_kinds = evidence_kinds(diff_report, "tests/test_sessions.py")
        check(
            "sessions test cites import or symbol evidence",
            "import" in token_kinds or "symbol" in token_kinds,
            token_kinds,
        )

        # JS conventional pair.
        write(
            root,
            "js.diff",
            "--- a/web/cart.js\n"
            "+++ b/web/cart.js\n"
            "@@ -1,3 +1,4 @@\n"
            " export function cartTotal(items) {\n"
            "+  if (!items.length) return 0;\n"
            "   return items.reduce((sum, item) => sum + item.price, 0);\n"
            " }\n",
        )
        js_result = run_mapper(root, ["--diff", os.path.join(root, "js.diff"), "--json"])
        js_report = load_json(js_result)
        check(
            "JS spec is the conventional pair",
            "web/cart.test.js" in recommended_paths(js_report),
            recommended_paths(js_report),
        )
        check(
            "JS spec has path evidence",
            "path" in evidence_kinds(js_report, "web/cart.test.js"),
            evidence_kinds(js_report, "web/cart.test.js"),
        )

        # Changed test file is recommended as self.
        test_diff = os.path.join(root, "self.diff")
        write(
            root,
            "self.diff",
            "--- a/tests/test_invoice.py\n"
            "+++ b/tests/test_invoice.py\n"
            "@@ -1,3 +1,4 @@\n"
            " from billing.invoice import compute_total\n"
            "+# extra assertion later\n"
            " from billing.tax import taxed_total\n",
        )
        self_result = run_mapper(root, ["--diff", os.path.join(root, "self.diff"), "--json"])
        self_report = load_json(self_result)
        check(
            "changed test is recommended as self",
            "self" in evidence_kinds(self_report, "tests/test_invoice.py"),
            evidence_kinds(self_report, "tests/test_invoice.py"),
        )

        # Limit caps the shortlist.
        limited = run_mapper(root, ["--diff", plain, "--limit", "1", "--json"])
        limited_report = load_json(limited)
        check(
            "limit 1 returns at most one test",
            limited.returncode == 0 and limited_report.get("stats", {}).get("recommended") == 1,
            limited_report.get("stats"),
        )

        # Empty diff.
        empty = os.path.join(root, "empty.diff")
        write(root, "empty.diff", "")
        empty_result = run_mapper(root, ["--diff", empty, "--json"])
        empty_report = load_json(empty_result)
        check("empty diff exits 0", empty_result.returncode == 0, empty_result.stderr.strip())
        check(
            "empty diff recommends nothing",
            empty_report.get("recommended") == [],
            empty_report.get("recommended"),
        )

        # Read-only: HEAD still points at the feature commit; working tree files
        # we wrote for diffs must not have been committed by the script.
        head = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=root, capture_output=True, text=True, check=True,
        )
        check("script does not switch branches", head.stdout.strip() == "feat/empty-cart", head.stdout.strip())

        # --diff cannot combine with --staged.
        combo = subprocess.run(
            [sys.executable, SCRIPT, "--repo", root, "--diff", plain, "--staged"],
            capture_output=True, text=True,
        )
        check("diff plus staged is an error", combo.returncode != 0, combo.stderr.strip())

        print()
        if all(checks):
            print("PASS: %d/%d checks" % (len(checks), len(checks)))
            return 0
        print("FAIL: %d/%d checks passed" % (sum(checks), len(checks)))
        return 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
