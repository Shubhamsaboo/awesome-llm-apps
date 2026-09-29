#!/usr/bin/env python3
"""Unit tests for catalog/lint.py. Stdlib unittest only.

    python3 catalog/test_lint.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
LINT = os.path.join(HERE, "lint.py")

sys.path.insert(0, HERE)
import lint  # noqa: E402


MINI_README = """# Fixture

## 📂 Browse all templates

### 🌱 Starter AI Agents

*   [Listed App](starter_ai_agents/listed_app/) - A Streamlit demo that runs locally
*   [Missing App](starter_ai_agents/missing_app/) - Listed but not on disk
*   [External Demo](https://github.com/example/demo) <sub>↗ external</sub> - skipped

### 🧑‍🏫 AI Agent Framework Crash Courses

*   [Demo Course](ai_agent_framework_crash_course/demo_course/) - Nested lessons stay off the catalog
"""


def _write(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


def _run(root, *args):
    return subprocess.run(
        [sys.executable, LINT, "--root", root, *args],
        capture_output=True,
        text=True,
        check=False,
    )


class CatalogLintTests(unittest.TestCase):
    def _tree(self, with_missing_bullet=True, extra_readme=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = tmp.name
        readme = MINI_README
        if not with_missing_bullet:
            readme = readme.replace(
                "*   [Missing App](starter_ai_agents/missing_app/) - Listed but not on disk\n",
                "",
            )
        _write(os.path.join(root, "README.md"), readme)
        _write(
            os.path.join(root, "starter_ai_agents", "listed_app", extra_readme or "README.md"),
            "# listed\n",
        )
        _write(
            os.path.join(root, "starter_ai_agents", "unlisted_app", "README.md"),
            "# unlisted first-class\n",
        )
        _write(
            os.path.join(root, "ai_agent_framework_crash_course", "demo_course", "README.md"),
            "# course\n",
        )
        _write(
            os.path.join(
                root,
                "ai_agent_framework_crash_course",
                "demo_course",
                "1_starter",
                "README.md",
            ),
            "# nested lesson\n",
        )
        _write(
            os.path.join(root, "catalog", "unlisted-allowlist.txt"),
            "# nested crash-course lesson\n"
            "ai_agent_framework_crash_course/demo_course/1_starter\n",
        )
        return root

    def test_parse_skips_https_and_normalizes_paths(self):
        items = lint.parse_readme(MINI_README)
        paths = [row["path"] for row in items]
        self.assertEqual(
            paths,
            [
                "starter_ai_agents/listed_app",
                "starter_ai_agents/missing_app",
                "ai_agent_framework_crash_course/demo_course",
            ],
        )
        self.assertEqual(items[0]["category"], "starter-ai-agents")
        self.assertEqual(items[2]["category"], "ai-agent-framework-crash-courses")

    def test_listed_missing_exits_1(self):
        root = self._tree(with_missing_bullet=True)
        proc = _run(root)
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertIn("listed path missing on disk: starter_ai_agents/missing_app", proc.stderr)

    def test_unlisted_warns_without_strict_and_fails_with_strict(self):
        root = self._tree(with_missing_bullet=False)
        proc = _run(root, "--write")
        self.assertIn("unlisted first-class template: starter_ai_agents/unlisted_app", proc.stderr)
        self.assertEqual(proc.returncode, 0, proc.stderr)

        proc_strict = _run(root, "--strict")
        self.assertEqual(proc_strict.returncode, 1, proc_strict.stderr)
        self.assertIn(
            "unlisted first-class template: starter_ai_agents/unlisted_app",
            proc_strict.stderr,
        )

        _write(
            os.path.join(root, "catalog", "unlisted-allowlist.txt"),
            "starter_ai_agents/unlisted_app\n"
            "ai_agent_framework_crash_course/demo_course/1_starter\n",
        )
        proc_ok = _run(root, "--check", "--strict")
        self.assertEqual(proc_ok.returncode, 0, proc_ok.stderr)

    def test_write_then_check_is_clean(self):
        root = self._tree(with_missing_bullet=False)
        _write(
            os.path.join(root, "catalog", "unlisted-allowlist.txt"),
            "starter_ai_agents/unlisted_app\n"
            "ai_agent_framework_crash_course/demo_course/1_starter\n",
        )
        proc_write = _run(root, "--write")
        self.assertEqual(proc_write.returncode, 0, proc_write.stderr)
        path = os.path.join(root, "catalog", "templates.json")
        self.assertTrue(os.path.isfile(path))
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["version"], 1)
        self.assertEqual(
            [row["path"] for row in data["templates"]],
            [
                "ai_agent_framework_crash_course/demo_course",
                "starter_ai_agents/listed_app",
            ],
        )
        kinds = {row["path"]: row["kind"] for row in data["templates"]}
        self.assertEqual(kinds["ai_agent_framework_crash_course/demo_course"], "crash_course")
        self.assertEqual(kinds["starter_ai_agents/listed_app"], "app")

        proc_check = _run(root, "--check", "--strict")
        self.assertEqual(proc_check.returncode, 0, proc_check.stderr)

        with open(path, encoding="utf-8") as fh:
            stale = json.load(fh)
        stale["templates"][0]["description"] = "mutated"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(stale, fh)
        proc_stale = _run(root, "--check")
        self.assertEqual(proc_stale.returncode, 1, proc_stale.stderr)
        self.assertIn("stale", proc_stale.stderr)

    def test_readme_md_casing_is_accepted_with_warning(self):
        root = self._tree(with_missing_bullet=False, extra_readme="README.MD")
        _write(
            os.path.join(root, "catalog", "unlisted-allowlist.txt"),
            "starter_ai_agents/unlisted_app\n",
        )
        proc = _run(root, "--write")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("non-canonical README filename README.MD", proc.stderr)
        with open(os.path.join(root, "catalog", "templates.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        row = next(r for r in data["templates"] if r["path"] == "starter_ai_agents/listed_app")
        self.assertEqual(row["readme"], "README.MD")

    def test_nested_crash_course_lesson_is_not_first_class(self):
        root = self._tree(with_missing_bullet=False)
        discovered = lint.discover_first_class(root)
        self.assertIn("starter_ai_agents/listed_app", discovered)
        self.assertIn("starter_ai_agents/unlisted_app", discovered)
        self.assertIn("ai_agent_framework_crash_course/demo_course", discovered)
        self.assertNotIn(
            "ai_agent_framework_crash_course/demo_course/1_starter",
            discovered,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
