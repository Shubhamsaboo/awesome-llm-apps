#!/usr/bin/env python3
"""Unit tests for registry_lint.py (stdlib unittest, temp trees only)."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry_lint  # noqa: E402


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def _skill_md(name, description=None):
    desc = description or (
        "Use when testing the registry linter against a fake skill named %s." % name
    )
    return (
        "---\n"
        "name: %s\n"
        "description: >-\n"
        "  %s\n"
        "license: Apache-2.0\n"
        "metadata:\n"
        "  author: \"Test\"\n"
        "  version: \"1.0.0\"\n"
        "---\n\n"
        "# %s\n" % (name, desc, name)
    )


def _skills_readme(names):
    rows = "\n".join("| [%s](%s/) | A fake skill |" % (n, n) for n in names)
    return (
        "# Agent Skills\n\n"
        "## Skills\n\n"
        "| Skill | What it does |\n"
        "|---|---|\n"
        "%s\n\n"
        "## Install\n\n"
        "npx skills add <url>\n" % rows
    )


def _root_readme(names):
    bullets = "\n".join(
        "*   [%s](agent_skills/%s/) - fake skill" % (n, n) for n in names
    )
    return (
        "# awesome-llm-apps\n\n"
        "### Agent Skills\n\n"
        "%s\n\n"
        "### Starter AI Agents\n\n"
        "*   [other](starter_ai_agents/other/) - not a skill\n" % bullets
    )


def build_tree(root, names=("alpha", "beta"), listed=None, evals=None, extra_dirs=()):
    listed = list(names) if listed is None else list(listed)
    evals = set(names) if evals is None else set(evals)
    for name in names:
        _write(os.path.join(root, "agent_skills", name, "SKILL.md"), _skill_md(name))
        if name in evals:
            _write(
                os.path.join(root, "agent_skills", "evals", name, "evals.json"),
                "{}\n",
            )
    for extra in extra_dirs:
        _write(
            os.path.join(root, "agent_skills", extra, "README.md"),
            "# app, not a skill\n",
        )
    _write(os.path.join(root, "agent_skills", "README.md"), _skills_readme(listed))
    _write(os.path.join(root, "README.md"), _root_readme(listed))


def run_cli(args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = registry_lint.main(args)
    return code, buf.getvalue()


class RegistryLintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_write_then_check_happy_path(self):
        build_tree(self.root, extra_dirs=("app-only",))
        code, out = run_cli(["--write", "--root", self.root])
        self.assertEqual(code, 0, out)
        registry_path = os.path.join(self.root, "agent_skills", "registry.json")
        with open(registry_path, encoding="utf-8") as fh:
            data = json.load(fh)
        names = [row["name"] for row in data["skills"]]
        self.assertEqual(names, ["alpha", "beta"])
        self.assertNotIn("app-only", names)
        self.assertNotIn("self-improving-agent-skills", names)
        alpha = data["skills"][0]
        self.assertEqual(alpha["path"], "agent_skills/alpha")
        self.assertEqual(
            alpha["install"],
            "npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/"
            "tree/main/agent_skills/alpha",
        )
        self.assertEqual(alpha["evals_dir"], "agent_skills/evals/alpha")
        self.assertEqual(alpha["license"], "Apache-2.0")
        self.assertEqual(data["version"], 1)
        code, out = run_cli(["--check", "--root", self.root])
        self.assertEqual(code, 0, out)
        self.assertIn("PASS", out)

    def test_dir_without_skill_md_is_ignored(self):
        build_tree(self.root, extra_dirs=("self-improving-agent-skills",))
        code, out = run_cli(["--write", "--root", self.root])
        self.assertEqual(code, 0, out)
        with open(
            os.path.join(self.root, "agent_skills", "registry.json"), encoding="utf-8"
        ) as fh:
            data = json.load(fh)
        self.assertEqual(
            [row["name"] for row in data["skills"]],
            ["alpha", "beta"],
        )

    def test_missing_root_bullet_fails_check(self):
        build_tree(self.root, listed=["alpha", "beta"])
        run_cli(["--write", "--root", self.root])
        _write(
            os.path.join(self.root, "README.md"),
            _root_readme(["alpha"]),
        )
        code, out = run_cli(["--check", "--root", self.root])
        self.assertEqual(code, 1, out)
        self.assertIn("ERROR:", out)
        self.assertIn("beta", out)
        self.assertIn("root README.md", out)

    def test_extra_registry_row_fails_check(self):
        build_tree(self.root)
        run_cli(["--write", "--root", self.root])
        registry_path = os.path.join(self.root, "agent_skills", "registry.json")
        with open(registry_path, encoding="utf-8") as fh:
            data = json.load(fh)
        data["skills"].append(
            {
                "name": "ghost-skill",
                "path": "agent_skills/ghost-skill",
                "description": "not real",
                "license": "Apache-2.0",
                "metadata": {},
                "install": "npx skills add https://example.test/ghost-skill",
                "evals_dir": "",
            }
        )
        with open(registry_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
            fh.write("\n")
        code, out = run_cli(["--check", "--root", self.root])
        self.assertEqual(code, 1, out)
        self.assertIn("ghost-skill", out)
        self.assertIn("SKILL.md was not found", out)

    def test_name_mismatch_fails(self):
        build_tree(self.root)
        _write(
            os.path.join(self.root, "agent_skills", "alpha", "SKILL.md"),
            _skill_md("other-name"),
        )
        code, out = run_cli(["--write", "--root", self.root])
        self.assertEqual(code, 1, out)
        self.assertIn("other-name", out)
        self.assertIn("alpha", out)

    def test_missing_skills_readme_link_fails_check(self):
        build_tree(self.root)
        run_cli(["--write", "--root", self.root])
        _write(
            os.path.join(self.root, "agent_skills", "README.md"),
            _skills_readme(["alpha"]),
        )
        code, out = run_cli(["--check", "--root", self.root])
        self.assertEqual(code, 1, out)
        self.assertIn("agent_skills/README.md", out)
        self.assertIn("beta", out)

    def test_missing_evals_dir_warns_but_passes(self):
        build_tree(self.root, evals={"alpha"})
        code, out = run_cli(["--write", "--root", self.root])
        self.assertEqual(code, 0, out)
        self.assertIn("WARN:", out)
        self.assertIn("beta", out)
        with open(
            os.path.join(self.root, "agent_skills", "registry.json"), encoding="utf-8"
        ) as fh:
            data = json.load(fh)
        by_name = {row["name"]: row for row in data["skills"]}
        self.assertEqual(by_name["beta"]["evals_dir"], "")
        self.assertEqual(by_name["alpha"]["evals_dir"], "agent_skills/evals/alpha")


if __name__ == "__main__":
    unittest.main()
