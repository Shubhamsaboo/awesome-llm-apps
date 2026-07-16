#!/usr/bin/env python3
"""Diagnose dependency manifest footguns with an offline-first core.

Supported inputs are requirements.txt, pyproject.toml, and package.json.
The default run reads only the selected file. Passing --online explicitly adds
PyPI lookups for exact Python pins so fully yanked releases can be reported.
"""

# SPDX-License-Identifier: Apache-2.0

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys


PYTHON_NAME_RE = re.compile(
    r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]+\])?\s*(.*)$"
)
EXACT_PIN_RE = re.compile(r"(?:^|,)\s*==\s*([^,;\s]+)")
NPM_UNPINNED_RE = re.compile(r"^(?:|\*|latest|[xX](?:\.[xX*]){0,2})$")
PYTHON_MARKER_RE = re.compile(
    r"^python_(full_)?version\s*(==|!=|<=|>=|<|>)\s*['\"](\d+(?:\.\d+){1,2})['\"]$",
    re.IGNORECASE,
)

BACKPORTS = {
    "asyncio": "Python 3.4 and newer include asyncio in the standard library.",
    "configparser": "Python 3 includes configparser in the standard library.",
    "dataclasses": "Python 3.7 and newer include dataclasses in the standard library.",
    "enum34": "Python 3.4 and newer include enum in the standard library.",
    "functools32": "Modern Python includes the relevant functools features.",
    "futures": "Python 3.2 and newer include concurrent.futures.",
    "ipaddress": "Python 3.3 and newer include ipaddress in the standard library.",
    "pathlib": "Python 3.4 and newer include pathlib in the standard library.",
    "singledispatch": "Python 3.4 and newer include functools.singledispatch.",
    "subprocess32": "Modern Python includes the maintained subprocess implementation.",
    "typing": "Python 3.5 and newer include typing in the standard library.",
}


def normalize_name(name):
    """Return the normalized package name used for grouping."""
    return re.sub(r"[-_.]+", "-", name).lower()


def new_entry(name, spec, line, ecosystem, marker=""):
    """Build the internal representation shared by all manifest parsers."""
    return {
        "package": normalize_name(name),
        "spec": spec.strip(),
        "line": line,
        "ecosystem": ecosystem,
        "marker": marker.strip(),
    }


def parse_python_requirement(value, line, ecosystem="python"):
    """Parse the useful subset of a PEP 508 requirement without packaging."""
    value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
    if not value or value.startswith(("#", "-")):
        return None
    parts = value.split(";", 1)
    requirement = parts[0].strip()
    marker = parts[1].strip() if len(parts) == 2 else ""
    match = PYTHON_NAME_RE.match(requirement)
    if not match:
        return None
    name, spec = match.groups()
    spec = spec.strip()
    if spec.startswith("(") and spec.endswith(")"):
        spec = spec[1:-1].strip()
    return new_entry(name, spec, line, ecosystem, marker)


def line_locator(text):
    """Return a function that locates repeated package names in source order."""
    lines = text.splitlines()
    cursors = defaultdict(int)
    match_cache = {}

    def locate(name):
        key = name.lower()
        if key not in match_cache:
            package_pattern = re.compile(
                r"(?<![A-Za-z0-9_.@/-])%s(?![A-Za-z0-9_.@/-])" % re.escape(name),
                re.IGNORECASE,
            )
            match_cache[key] = [
                number
                for number, source_line in enumerate(lines, 1)
                if package_pattern.search(source_line)
            ]
        matches = match_cache[key]
        index = cursors[key]
        cursors[key] += 1
        if index < len(matches):
            return matches[index]
        return matches[-1] if matches else 1

    return locate


def load_requirements(text):
    """Read one requirement per physical line."""
    entries = []
    for line_number, line in enumerate(text.splitlines(), 1):
        entry = parse_python_requirement(line, line_number)
        if entry:
            entries.append(entry)
    return entries


def load_pyproject(text):
    """Read PEP 621 and common Poetry dependency tables with tomllib."""
    try:
        import tomllib

        data = tomllib.loads(text)
    except (ImportError, ValueError) as error:
        raise ValueError("could not parse pyproject.toml: %s" % error) from error

    locate = line_locator(text)
    values = []
    project = data.get("project", {})
    values.extend(project.get("dependencies", []) or [])
    for group in (project.get("optional-dependencies", {}) or {}).values():
        values.extend(group or [])

    entries = []
    for value in values:
        if isinstance(value, str):
            entry = parse_python_requirement(value, locate(value.split("[", 1)[0]))
            if entry:
                entries.append(entry)

    poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {}) or {}
    for name, value in poetry.items():
        if normalize_name(name) == "python":
            continue
        if isinstance(value, str):
            spec = value
        elif isinstance(value, dict):
            spec = str(value.get("version", ""))
        else:
            spec = ""
        if re.match(r"^[0-9]+(?:\.[0-9A-Za-z-]+){0,3}$", spec):
            spec = "==" + spec
        entries.append(new_entry(name, spec, locate(name), "python"))
    return entries


def load_package_json(text):
    """Read dependency sections from package.json."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError("could not parse package.json: %s" % error) from error

    locate = line_locator(text)
    entries = []
    sections = (
        "dependencies",
        "devDependencies",
        "optionalDependencies",
        "peerDependencies",
    )
    for section in sections:
        dependencies = data.get(section, {}) or {}
        if not isinstance(dependencies, dict):
            continue
        for name, value in dependencies.items():
            spec = value if isinstance(value, str) else ""
            entries.append(new_entry(name, spec, locate(name), "npm"))
    return entries


def load_manifest(path):
    """Select a parser from the manifest name."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError("could not read %s: %s" % (path, error)) from error

    if path.name == "package.json":
        return load_package_json(text)
    if path.name == "pyproject.toml":
        return load_pyproject(text)
    if path.name == "requirements.txt" or path.suffix == ".txt":
        return load_requirements(text)
    raise ValueError("unsupported manifest; use requirements.txt, pyproject.toml, or package.json")


def has_version_spec(entry):
    """Return whether an entry constrains or directly identifies a version."""
    spec = entry["spec"].strip()
    if entry["ecosystem"] == "npm":
        return not NPM_UNPINNED_RE.match(spec)
    return bool(spec and spec != "*")


def marker_applies(entry):
    """Evaluate simple Python-version markers, conservatively keeping others."""
    marker = entry["marker"]
    if not marker or entry["ecosystem"] != "python" or re.search(r"\s+or\s+", marker, re.I):
        return True

    for clause in re.split(r"\s+and\s+", marker, flags=re.IGNORECASE):
        match = PYTHON_MARKER_RE.match(clause.strip())
        if not match:
            continue
        full_version, comparison, requested = match.groups()
        width = 3 if full_version else 2
        current = tuple(sys.version_info[:width])
        requested_parts = tuple(int(part) for part in requested.split("."))
        target = (requested_parts + (0,) * width)[:width]
        comparisons = {
            "==": current == target,
            "!=": current != target,
            "<=": current <= target,
            ">=": current >= target,
            "<": current < target,
            ">": current > target,
        }
        if not comparisons[comparison]:
            return False
    return True


def exact_pin(entry):
    """Return an exact version, or None for ranges and direct references."""
    spec = entry["spec"].strip()
    if entry["ecosystem"] == "npm":
        if re.match(r"^[0-9]+(?:\.[0-9A-Za-z-]+){0,3}$", spec):
            return spec
        return None
    match = EXACT_PIN_RE.search(spec)
    if match and "*" not in match.group(1):
        return match.group(1)
    return None


def make_finding(severity, kind, entry, why, fix):
    """Create one finding in the public JSON shape."""
    return {
        "severity": severity,
        "kind": kind,
        "package": entry["package"],
        "line": entry["line"],
        "why": why,
        "fix": fix,
    }


def offline_findings(entries):
    """Run checks that read no state beyond the selected manifest."""
    findings = []
    stdlib_names = set(getattr(sys, "stdlib_module_names", ()))

    for entry in entries:
        package = entry["package"]
        remove_instead_of_pin = False
        if entry["ecosystem"] == "python":
            module_name = package.replace("-", "_")
            if module_name in stdlib_names:
                remove_instead_of_pin = True
                findings.append(make_finding(
                    "high",
                    "stdlib-shadowing",
                    entry,
                    "%s is provided by this Python runtime. Installing a package with the same name can shadow the maintained standard-library module."
                    % package,
                    "Remove %s from the manifest and import the standard-library module directly."
                    % package,
                ))
            if package in BACKPORTS:
                remove_instead_of_pin = True
                findings.append(make_finding(
                    "high",
                    "abandoned-backport",
                    entry,
                    BACKPORTS[package] + " The old backport can conflict with supported runtimes.",
                    "Remove %s on supported Python versions. If an older runtime is required, guard the backport with a Python-version marker."
                    % package,
                ))

        if not has_version_spec(entry):
            if remove_instead_of_pin:
                fix = (
                    "Do not add a pin for %s. Remove it on supported Python versions, "
                    "or guard a required backport with a Python-version marker." % package
                )
            else:
                fix = (
                    "Pin %s to a reviewed version after checking the version installed "
                    "in the working environment." % package
                )
            findings.append(make_finding(
                "medium",
                "unpinned",
                entry,
                "%s has no usable version constraint, so a future install can resolve to different code."
                % package,
                fix,
            ))

    grouped = defaultdict(list)
    for entry in entries:
        grouped[(entry["ecosystem"], entry["package"])].append(entry)

    for (_ecosystem, package), package_entries in sorted(grouped.items()):
        if len(package_entries) < 2:
            continue
        pins = {pin for pin in (exact_pin(item) for item in package_entries) if pin}
        lines = ", ".join(str(item["line"]) for item in package_entries)
        representative = package_entries[1]
        if len(pins) > 1:
            findings.append(make_finding(
                "high",
                "conflicting-constraints",
                representative,
                "%s is pinned to incompatible exact versions on lines %s."
                % (package, lines),
                "Choose one compatible version for %s and keep a single constraint."
                % package,
            ))
        else:
            specs = {item["spec"] for item in package_entries}
            detail = "the same constraint" if len(specs) == 1 else "separate constraints"
            findings.append(make_finding(
                "medium",
                "duplicate-constraint",
                representative,
                "%s appears on lines %s with %s. Multiple entries are easy to update inconsistently."
                % (package, lines, detail),
                "Keep one %s entry and combine any compatible constraints on that line."
                % package,
            ))

    return findings


def online_findings(entries):
    """Query PyPI only for exact pins after the user passes --online."""
    import urllib.parse
    import urllib.request

    findings = []
    checked = set()
    for entry in entries:
        version = exact_pin(entry)
        key = (entry["package"], version)
        if entry["ecosystem"] != "python" or not version or key in checked:
            continue
        checked.add(key)
        url = "https://pypi.org/pypi/%s/json" % urllib.parse.quote(entry["package"], safe="")
        request = urllib.request.Request(url, headers={"User-Agent": "dependency-doctor/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.load(response)
        except (OSError, ValueError) as error:
            findings.append(make_finding(
                "low",
                "online-check-failed",
                entry,
                "PyPI could not be checked for %s==%s: %s" % (entry["package"], version, error),
                "Retry with --online when PyPI is reachable, or inspect the release on PyPI manually.",
            ))
            continue

        files = payload.get("releases", {}).get(version, [])
        if files and all(file_info.get("yanked", False) for file_info in files):
            reasons = sorted({
                file_info.get("yanked_reason", "").strip()
                for file_info in files
                if file_info.get("yanked_reason", "").strip()
            })
            reason = (" PyPI reason: " + "; ".join(reasons)) if reasons else ""
            findings.append(make_finding(
                "high",
                "yanked-release",
                entry,
                "%s==%s is fully yanked on PyPI.%s" % (entry["package"], version, reason),
                "Choose a non-yanked release of %s, test it, and update the exact pin."
                % entry["package"],
            ))
    return findings


def build_report(path, entries, use_online=False):
    """Run the checks and assemble the deterministic report."""
    active_entries = [entry for entry in entries if marker_applies(entry)]
    findings = offline_findings(active_entries)
    if use_online:
        findings.extend(online_findings(active_entries))
    findings.sort(key=lambda item: (item["line"], item["kind"], item["package"]))
    severity_counts = Counter(item["severity"] for item in findings)
    kind_counts = Counter(item["kind"] for item in findings)
    return {
        "file": str(path),
        "findings": findings,
        "summary": {
            "total": len(findings),
            "by_severity": dict(sorted(severity_counts.items())),
            "by_kind": dict(sorted(kind_counts.items())),
            "online": bool(use_online),
        },
    }


def print_human(report):
    """Render a compact report for direct terminal use."""
    print("Dependency Doctor: %s" % report["file"])
    if not report["findings"]:
        print("No findings.")
    for item in report["findings"]:
        print("\n%s [%s] %s (line %d)" % (
            item["severity"].upper(), item["kind"], item["package"], item["line"]
        ))
        print("  Why: %s" % item["why"])
        print("  Fix: %s" % item["fix"])
    print("\nSummary: %d finding(s)" % report["summary"]["total"])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Diagnose dependency manifests locally; PyPI checks are opt-in."
    )
    parser.add_argument("manifest", help="requirements.txt, pyproject.toml, or package.json")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit JSON")
    parser.add_argument(
        "--online",
        action="store_true",
        help="query PyPI for fully yanked exact Python releases",
    )
    args = parser.parse_args(argv)
    path = Path(args.manifest)
    try:
        entries = load_manifest(path)
        report = build_report(path, entries, use_online=args.online)
    except ValueError as error:
        parser.error(str(error))

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=False))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
