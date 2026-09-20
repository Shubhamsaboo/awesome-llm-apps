#!/usr/bin/env python3
"""catalog/lint.py: keep README catalog bullets, on-disk templates, and
catalog/templates.json in lockstep.

Usage:
    python3 catalog/lint.py --write
    python3 catalog/lint.py --check
    python3 catalog/lint.py --check --strict

Python 3 stdlib only. Same portability rule as agent_skills/evals/tools/skill_lint.py.

Exit codes: 0 = no errors (warnings allowed unless --strict), 1 = errors, 2 = usage.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ROOT = os.path.dirname(HERE)

CATEGORY_ROOTS = (
    "starter_ai_agents",
    "advanced_ai_agents",
    "agent_skills",
    "rag_tutorials",
    "mcp_ai_agents",
    "voice_ai_agents",
    "generative_ui_agents",
    "always_on_agents",
    "advanced_llm_apps",
    "ai_agent_framework_crash_course",
)

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".agent",
    "frontend",
    "backend",
    "client",
    "web",
    "evals",
    "dist",
    "build",
}

BROWSE_HEADING = "## 📂 Browse all templates"
CANONICAL_README = "README.md"
KINDS = {"app", "skill", "crash_course"}

BULLET_RE = re.compile(r"^\* +\[([^\]]+)\]\(([^)]+)\)(.*)$")
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+"
)
SUB_TAG_RE = re.compile(r"<sub>.*?</sub>", re.I)

FRAMEWORK_PATTERNS = (
    ("streamlit", re.compile(r"\bstreamlit\b", re.I)),
    ("crewai", re.compile(r"\bcrewai\b", re.I)),
    ("langgraph", re.compile(r"\blanggraph\b", re.I)),
    ("langchain", re.compile(r"\blangchain\b", re.I)),
    ("llamaindex", re.compile(r"\bllama[- ]?index\b", re.I)),
    ("agno", re.compile(r"\bagno\b", re.I)),
    ("autogen", re.compile(r"\bautogen\b", re.I)),
    ("ag2", re.compile(r"\bag2\b", re.I)),
    ("pydantic-ai", re.compile(r"\bpydantic ai\b", re.I)),
    ("openai-agents-sdk", re.compile(r"\bopenai agents sdk\b", re.I)),
    ("google-adk", re.compile(r"\b(google )?adk\b", re.I)),
    ("mcp", re.compile(r"\bmcp\b", re.I)),
    ("evoagentx", re.compile(r"\bevoagentx\b", re.I)),
)

MODEL_PATTERNS = (
    ("gpt", re.compile(r"\bgpt(?:-?\d[\w.]*)?\b", re.I)),
    ("claude", re.compile(r"\bclaude\b", re.I)),
    ("gemini", re.compile(r"\bgemini\b", re.I)),
    ("llama", re.compile(r"\bllama\b", re.I)),
    ("deepseek", re.compile(r"\bdeepseek\b", re.I)),
    ("qwen", re.compile(r"\bqwen\b", re.I)),
    ("grok", re.compile(r"\bgrok\b", re.I)),
    ("gemma", re.compile(r"\bgemma\b", re.I)),
    ("command-r", re.compile(r"\bcommand r", re.I)),
)


def rel_from(root, abs_path):
    return os.path.relpath(abs_path, root).replace(os.sep, "/")


def abs_from(root, rel):
    return os.path.join(root, *rel.split("/"))


def heading_slug(heading):
    text = EMOJI_RE.sub(" ", heading)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def catalog_dir(root):
    return os.path.join(root, "catalog")


def templates_path(root):
    return os.path.join(catalog_dir(root), "templates.json")


def allowlist_path(root):
    return os.path.join(catalog_dir(root), "unlisted-allowlist.txt")


def load_allowlist(root):
    path = allowlist_path(root)
    entries = set()
    if not os.path.isfile(path):
        return entries
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            entries.add(line.rstrip("/"))
    return entries


def marker_name(abs_path):
    try:
        names = os.listdir(abs_path)
    except OSError:
        return None
    preferred = (
        "README.md",
        "README.MD",
        "readme.md",
        "SKILL.md",
        "skill.md",
    )
    for name in preferred:
        if name in names:
            return name
    for name in names:
        lower = name.lower()
        if lower == "readme.md" or lower == "skill.md":
            return name
    return None


def has_skill_md(abs_path):
    try:
        names = os.listdir(abs_path)
    except OSError:
        return False
    return "SKILL.md" in names or "skill.md" in names


def extract_browse_section(readme_text):
    lines = readme_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == BROWSE_HEADING:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## ") and lines[i].strip() != BROWSE_HEADING:
            end = i
            break
        if i > start and lines[i].strip() == "---":
            end = i
            break
    return "\n".join(lines[start:end]) + "\n"


def normalize_href(href):
    href = href.strip()
    href = href.split("#", 1)[0]
    if href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:"):
        return None, "external"
    href = href.lstrip("/")
    if href.startswith("./"):
        href = href[2:]
    href = href.rstrip("/")
    return href, "relative"


def parse_readme(readme_text):
    section = extract_browse_section(readme_text)
    if section is None:
        raise ValueError("README.md has no '%s' heading" % BROWSE_HEADING)
    category = None
    items = []
    for line in section.splitlines():
        if line.startswith("### "):
            category = heading_slug(line[4:].strip())
            continue
        match = BULLET_RE.match(line)
        if not match:
            continue
        title, href, rest = match.group(1), match.group(2), match.group(3)
        path, kind = normalize_href(href)
        if kind != "relative" or not path:
            continue
        desc = SUB_TAG_RE.sub("", rest).strip()
        if desc.startswith("-"):
            desc = desc[1:].strip()
        items.append(
            {
                "path": path,
                "title": title,
                "description": desc,
                "category": category or "uncategorized",
            }
        )
    return items


def is_grouping_dir(abs_path):
    try:
        names = os.listdir(abs_path)
    except OSError:
        return False
    for name in names:
        if name in SKIP_DIR_NAMES or name.startswith("."):
            continue
        child = os.path.join(abs_path, name)
        if os.path.isdir(child) and marker_name(child):
            return True
    return False


def is_first_class(rel, root):
    parts = [p for p in rel.split("/") if p]
    if len(parts) < 2:
        return False
    if parts[-1] in SKIP_DIR_NAMES or parts[-1].startswith("."):
        return False
    cat = parts[0]
    if cat not in CATEGORY_ROOTS:
        return False
    abs_path = abs_from(root, rel)
    if not marker_name(abs_path):
        return False
    shallow = {
        "starter_ai_agents",
        "agent_skills",
        "rag_tutorials",
        "mcp_ai_agents",
        "voice_ai_agents",
        "generative_ui_agents",
        "always_on_agents",
    }
    if cat in shallow:
        return len(parts) == 2
    if cat == "advanced_ai_agents":
        if len(parts) == 3 and parts[1] in {
            "single_agent_apps",
            "multi_agent_apps",
            "autonomous_game_playing_agent_apps",
        }:
            return parts[2] != "agent_teams"
        if (
            len(parts) == 4
            and parts[1] == "multi_agent_apps"
            and parts[2] == "agent_teams"
        ):
            return True
        return False
    if cat == "advanced_llm_apps":
        if len(parts) == 2:
            return not is_grouping_dir(abs_path)
        return len(parts) == 3
    if cat == "ai_agent_framework_crash_course":
        return len(parts) == 2
    return False


def discover_first_class(root):
    found = []
    for cat in CATEGORY_ROOTS:
        cat_abs = os.path.join(root, cat)
        if not os.path.isdir(cat_abs):
            continue
        for dirpath, dirnames, _filenames in os.walk(cat_abs):
            dirnames[:] = sorted(
                d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")
            )
            rel = rel_from(root, dirpath)
            if is_first_class(rel, root):
                found.append(rel)
    return found


def probe_entrypoint(abs_path):
    try:
        names = os.listdir(abs_path)
    except OSError:
        return None
    if "SKILL.md" in names:
        return "SKILL.md"
    ranked = []
    for name in names:
        lower = name.lower()
        if not lower.endswith(".py"):
            continue
        if "streamlit" in lower:
            ranked.append((0, name))
        elif name in ("app.py", "main.py"):
            ranked.append((1, name))
    if not ranked:
        return None
    ranked.sort()
    return ranked[0][1]


def extract_tags(title, description, abs_path):
    blob = "%s %s" % (title, description)
    frameworks = []
    for name, pattern in FRAMEWORK_PATTERNS:
        if pattern.search(blob) and name not in frameworks:
            frameworks.append(name)
    try:
        names = os.listdir(abs_path) if abs_path and os.path.isdir(abs_path) else []
    except OSError:
        names = []
    if any("streamlit" in n.lower() for n in names) and "streamlit" not in frameworks:
        frameworks.append("streamlit")
    models = []
    for name, pattern in MODEL_PATTERNS:
        if pattern.search(blob) and name not in models:
            models.append(name)
    local = bool(re.search(r"\blocal\b|\bollama\b|\boffline\b", blob, re.I))
    entrypoint = probe_entrypoint(abs_path) if abs_path else None
    tags = {}
    if frameworks:
        tags["frameworks"] = frameworks
    if models:
        tags["models"] = models
    if local:
        tags["local"] = True
    if entrypoint:
        tags["entrypoint"] = entrypoint
    return tags


def item_kind(rel, abs_path):
    if abs_path and has_skill_md(abs_path):
        return "skill"
    if rel.startswith("ai_agent_framework_crash_course/"):
        return "crash_course"
    return "app"


def build_template(item, root):
    rel = item["path"]
    abs_path = abs_from(root, rel)
    exists = os.path.isdir(abs_path)
    marker = marker_name(abs_path) if exists else None
    kind = item_kind(rel, abs_path if exists else None)
    row = {
        "path": rel,
        "title": item["title"],
        "description": item["description"],
        "category": item["category"],
        "kind": kind,
    }
    if marker:
        row["readme"] = marker
    if exists:
        tags = extract_tags(item["title"], item["description"], abs_path)
        if tags:
            row["tags"] = tags
    return row, exists, marker


def catalog_document(templates):
    ordered = sorted(templates, key=lambda row: row["path"])
    return {
        "version": 1,
        "source_readme": "README.md",
        "templates": ordered,
    }


def dump_json(document):
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def validate_document(document):
    errors = []
    if not isinstance(document, dict):
        return ["templates.json is not a JSON object"]
    if document.get("version") != 1:
        errors.append("templates.json version must be 1")
    if document.get("source_readme") != "README.md":
        errors.append("templates.json source_readme must be README.md")
    templates = document.get("templates")
    if not isinstance(templates, list):
        errors.append("templates.json templates must be an array")
        return errors
    seen = set()
    for i, row in enumerate(templates):
        prefix = "templates[%d]" % i
        if not isinstance(row, dict):
            errors.append("%s is not an object" % prefix)
            continue
        for key in ("path", "title", "description", "category", "kind"):
            if key not in row:
                errors.append("%s missing %s" % (prefix, key))
        path = row.get("path")
        if isinstance(path, str):
            if path.startswith("./") or path.startswith("/"):
                errors.append("%s path must be posix without a leading ./" % prefix)
            if path in seen:
                errors.append("duplicate path %s" % path)
            seen.add(path)
        kind = row.get("kind")
        if kind is not None and kind not in KINDS:
            errors.append("%s kind must be app, skill, or crash_course" % prefix)
    return errors


def lint(root, strict=False):
    errors = []
    warnings = []
    readme_file = os.path.join(root, "README.md")
    if not os.path.isfile(readme_file):
        return ["README.md is missing"], warnings, None

    with open(readme_file, encoding="utf-8") as fh:
        readme_text = fh.read()
    try:
        listed = parse_readme(readme_text)
    except ValueError as exc:
        return [str(exc)], warnings, None

    allow = load_allowlist(root)
    templates = []
    listed_paths = []
    for item in listed:
        rel = item["path"]
        listed_paths.append(rel)
        row, exists, marker = build_template(item, root)
        templates.append(row)
        if not exists:
            errors.append("listed path missing on disk: %s" % rel)
            continue
        if marker is None:
            msg = "listed path has no README.md or SKILL.md: %s" % rel
            if strict and rel not in allow:
                errors.append(msg)
            else:
                warnings.append(msg)
            continue
        if marker.lower() == "readme.md" and marker != CANONICAL_README:
            warnings.append("non-canonical README filename %s at %s" % (marker, rel))
        if item["category"] == "agent-skills" and row["kind"] != "skill":
            msg = "listed skill path has no SKILL.md: %s" % rel
            if strict and rel not in allow:
                errors.append(msg)
            else:
                warnings.append(msg)

    first_class = discover_first_class(root)
    listed_set = set(listed_paths)
    for rel in first_class:
        if rel in listed_set or rel in allow:
            continue
        msg = "unlisted first-class template: %s" % rel
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)

    document = catalog_document(templates)
    errors.extend(validate_document(document))
    return errors, warnings, document


def write_templates(root, document):
    os.makedirs(catalog_dir(root), exist_ok=True)
    path = templates_path(root)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(dump_json(document))
    return path


def check_templates(root, document):
    """Parse committed JSON and compare objects. Trailing newline is ignored."""
    path = templates_path(root)
    if not os.path.isfile(path):
        return [
            "committed catalog/templates.json is missing; run: python3 catalog/lint.py --write"
        ]
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    try:
        committed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return ["catalog/templates.json is not valid JSON: %s" % exc]
    if committed != document:
        return [
            "catalog/templates.json is stale vs README/disk; run: python3 catalog/lint.py --write"
        ]
    return []


def report(stream, label, messages):
    for msg in messages:
        stream.write("%s: %s\n" % (label, msg))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Lint the README template catalog")
    parser.add_argument("--root", default=DEFAULT_ROOT, help="repository root")
    parser.add_argument(
        "--write",
        action="store_true",
        help="regenerate catalog/templates.json (sorted by path)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if committed templates.json differs from regeneration",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat unlisted first-class dirs (and known kind mismatches) as errors",
    )
    args = parser.parse_args(argv)

    root = os.path.abspath(args.root)
    errors, warnings, document = lint(root, strict=args.strict)

    if document is not None and args.write:
        path = write_templates(root, document)
        sys.stdout.write("wrote %s (%d templates)\n" % (path, len(document["templates"])))

    if document is not None and args.check:
        tmp_path = None
        try:
            handle, tmp_path = tempfile.mkstemp(suffix=".json")
            with os.fdopen(handle, "w", encoding="utf-8") as tmp:
                tmp.write(dump_json(document))
            errors.extend(check_templates(root, document))
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    report(sys.stderr, "warning", warnings)
    report(sys.stderr, "error", errors)

    if errors:
        sys.stderr.write("hint: python3 catalog/lint.py --write\n")
        return 1
    sys.stdout.write(
        "catalog ok: %d templates, %d warning(s)\n"
        % (len(document["templates"]) if document else 0, len(warnings))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
