#!/usr/bin/env python3
"""
registry_lint.py — membership check for agent_skills/registry.json.

Discovers every agent_skills/<dir>/SKILL.md the same way skill-evals CI does,
projects frontmatter into a committed registry, and fails when a skill is
missing from the registry or from either README listing people copy install
URLs from.

Usage:
    python3 registry_lint.py [--check|--write] [--root .]

  --write  regenerate agent_skills/registry.json from SKILL.md frontmatter
  --check  compare the committed registry to what --write would produce, and
           require every skill to appear in both README listings (default)

Exit codes: 0 = no errors (warnings allowed), 1 = errors found, 2 = usage error.
Python 3 stdlib only. Reuses skill_lint.parse_frontmatter; no PyYAML.
"""

import argparse
import glob
import json
import os
import posixpath
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skill_lint  # noqa: E402

REGISTRY_REL = posixpath.join("agent_skills", "registry.json")
SKILLS_README_REL = posixpath.join("agent_skills", "README.md")
ROOT_README_REL = "README.md"
INSTALL_FMT = (
    "npx skills add https://github.com/Shubhamsaboo/awesome-llm-apps/"
    "tree/main/agent_skills/%s"
)
ROOT_SECTION_RE = re.compile(r"^#{1,6}\s+.*Agent Skills\b")
SKILLS_HEADING_RE = re.compile(r"^##\s+Skills\s*$")


def collapse_text(value):
    if value is None:
        return ""
    if isinstance(value, dict):
        return ""
    return " ".join(str(value).split())


def extract_section(text, heading_re):
    """Return the markdown section whose heading matches heading_re, or ''."""
    lines = text.splitlines()
    start = None
    start_level = None
    heading_line = re.compile(r"^(#{1,6})\s+")
    for i, line in enumerate(lines):
        hm = heading_line.match(line)
        if start is None:
            if heading_re.search(line):
                start = i
                start_level = len(hm.group(1)) if hm else 2
            continue
        if hm and len(hm.group(1)) <= start_level:
            return "\n".join(lines[start:i])
    if start is None:
        return ""
    return "\n".join(lines[start:])


def has_md_link(text, target):
    """True if text contains ](target) or ](target/)."""
    return re.search(r"\]\(%s/?\)" % re.escape(target.rstrip("/")), text) is not None


def dumps(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def discover_skill_paths(root):
    pattern = os.path.join(root, "agent_skills", "*", "SKILL.md")
    return sorted(p for p in glob.glob(pattern) if os.path.isfile(p))


def load_skill(skill_md, errors):
    skill_dir = os.path.dirname(skill_md)
    dirname = os.path.basename(skill_dir)
    with open(skill_md, encoding="utf-8") as fh:
        text = fh.read()
    fm, _body, perr = skill_lint.parse_frontmatter(text)
    if perr:
        errors.append("frontmatter parse error in %s: %s" % (skill_md, perr))
        return None
    name = fm.get("name") or ""
    if name != dirname:
        errors.append(
            "name %r must equal the skill directory name %r: rename the directory "
            "or set 'name: %s'" % (name, dirname, dirname)
        )
    metadata = fm.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    evals_rel = posixpath.join("agent_skills", "evals", dirname)
    evals_abs = os.path.join(os.path.dirname(skill_dir), "evals", dirname)
    evals_dir = evals_rel if os.path.isdir(evals_abs) else ""
    row = {
        "name": name,
        "path": posixpath.join("agent_skills", dirname),
        "description": collapse_text(fm.get("description")),
        "license": collapse_text(fm.get("license")),
        "metadata": metadata,
        "install": INSTALL_FMT % dirname,
        "evals_dir": evals_dir,
    }
    return {
        "dirname": dirname,
        "row": row,
        "evals_missing": not evals_dir,
    }


def build_registry(loaded):
    rows = [item["row"] for item in loaded]
    rows.sort(key=lambda r: r["name"] or r.get("path", ""))
    return {"version": 1, "skills": rows}


def check_listings(root, loaded, errors):
    skills_path = os.path.join(root, "agent_skills", "README.md")
    root_path = os.path.join(root, "README.md")
    skills_text = ""
    root_text = ""
    if os.path.isfile(skills_path):
        with open(skills_path, encoding="utf-8") as fh:
            skills_text = fh.read()
    else:
        errors.append("%s not found" % SKILLS_README_REL)
    if os.path.isfile(root_path):
        with open(root_path, encoding="utf-8") as fh:
            root_text = fh.read()
    else:
        errors.append("%s not found" % ROOT_README_REL)

    skills_section = extract_section(skills_text, SKILLS_HEADING_RE) or skills_text
    root_section = extract_section(root_text, ROOT_SECTION_RE) or ""
    if root_text and not root_section:
        errors.append(
            "root README.md has no Agent Skills section (expected a heading matching "
            "'Agent Skills')"
        )

    for item in loaded:
        dirname = item["dirname"]
        if skills_text and not has_md_link(skills_section, dirname):
            errors.append(
                "skill %r is missing from agent_skills/README.md (add a table link "
                "to %s/)" % (dirname, dirname)
            )
        if root_section and not has_md_link(root_section, "agent_skills/%s" % dirname):
            errors.append(
                "skill %r is missing from the root README.md Agent Skills list "
                "(add a link to agent_skills/%s/)" % (dirname, dirname)
            )


def compare_registry(committed, generated, errors):
    if not isinstance(committed, dict):
        errors.append("%s must be a JSON object" % REGISTRY_REL)
        return
    committed_skills = committed.get("skills")
    if not isinstance(committed_skills, list):
        errors.append("%s is missing a 'skills' array" % REGISTRY_REL)
        committed_names = []
    else:
        committed_names = [
            row.get("name") for row in committed_skills if isinstance(row, dict)
        ]
    generated_names = [row["name"] for row in generated["skills"]]
    committed_set = set(n for n in committed_names if n)
    generated_set = set(n for n in generated_names if n)
    for name in sorted(generated_set - committed_set):
        errors.append("skill %r is missing from %s" % (name, REGISTRY_REL))
    for name in sorted(committed_set - generated_set):
        errors.append(
            "%s lists %r but agent_skills/%s/SKILL.md was not found"
            % (REGISTRY_REL, name, name)
        )
    if dumps(committed) != dumps(generated) and committed_set == generated_set:
        errors.append(
            "%s does not match SKILL.md frontmatter: run "
            "python3 agent_skills/evals/tools/registry_lint.py --write" % REGISTRY_REL
        )


def load_committed(path, errors):
    if not os.path.isfile(path):
        errors.append(
            "%s not found: run python3 agent_skills/evals/tools/registry_lint.py --write"
            % REGISTRY_REL
        )
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        errors.append("%s is not valid JSON: %s" % (REGISTRY_REL, exc))
        return None


def report(errors, warnings, mode, root):
    print("Checking registry at %s (mode=%s)" % (os.path.abspath(root), mode))
    for msg in errors:
        print("  ERROR: %s" % msg)
    for msg in warnings:
        print("  WARN:  %s" % msg)
    verdict = "PASS" if not errors else "FAIL"
    print("  %s — %d error(s), %d warning(s)" % (verdict, len(errors), len(warnings)))
    return 1 if errors else 0


def run(root, write=False, check=True):
    errors, warnings = [], []
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        errors.append("%s is not a directory" % root)
        return errors, warnings

    paths = discover_skill_paths(root)
    if not paths:
        errors.append("no SKILL.md files found under agent_skills/*/SKILL.md")

    loaded = []
    for path in paths:
        item = load_skill(path, errors)
        if item is not None:
            loaded.append(item)
            if item["evals_missing"]:
                warnings.append(
                    "skill %r has no evals directory at %s"
                    % (item["dirname"], posixpath.join("agent_skills", "evals", item["dirname"]))
                )

    generated = build_registry(loaded)
    registry_path = os.path.join(root, "agent_skills", "registry.json")

    if write:
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w", encoding="utf-8") as fh:
            fh.write(dumps(generated))
        print("Wrote %s (%d skill(s))" % (REGISTRY_REL, len(generated["skills"])))

    check_listings(root, loaded, errors)

    if check:
        committed = load_committed(registry_path, errors)
        if committed is not None:
            compare_registry(committed, generated, errors)

    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Check or regenerate agent_skills/registry.json and README listings."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="compare committed registry.json to SKILL.md frontmatter (default)",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help="regenerate agent_skills/registry.json from SKILL.md frontmatter",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="repository root (default: current directory)",
    )
    args = parser.parse_args(argv)
    write = args.write
    check = not write
    errors, warnings = run(args.root, write=write, check=check)
    return report(errors, warnings, "write" if write else "check", args.root)


if __name__ == "__main__":
    sys.exit(main())
