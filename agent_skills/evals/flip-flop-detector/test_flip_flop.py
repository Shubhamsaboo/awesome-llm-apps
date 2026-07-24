#!/usr/bin/env python3
"""
Executable eval for flip-flop-detector. Builds a temporary git repository
with a file whose return value oscillates across commits, and a second file
that only ever changes monotonically (never reverts), then checks that the
deterministic detector flags the first and not the second.

    python3 agent_skills/evals/flip-flop-detector/test_flip_flop.py

Uses only git and the Python stdlib.
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "flip-flop-detector", "scripts", "flip_flop.py",
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


def commit(root, message):
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=root, check=True)


def build_repo(root):
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "flipflop-eval@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "flipflop eval"], cwd=root, check=True)

    # src/config.py: the retry count oscillates 3 -> 5 -> 3 -> 5 across commits.
    write(root, "src/config.py", "def get_retry_count():\n    return 3\n")
    commit(root, "add retry config")

    write(root, "src/config.py", "def get_retry_count():\n    return 5\n")
    commit(root, "bump retries to 5")

    write(root, "src/config.py", "def get_retry_count():\n    return 3\n")
    commit(root, "revert retries to 3")

    write(root, "src/config.py", "def get_retry_count():\n    return 5\n")
    commit(root, "bump retries to 5 again")

    # src/monotonic.py: grows steadily, never returns to a prior state.
    write(root, "src/monotonic.py", "def steps():\n    return [1]\n")
    commit(root, "add steps")

    write(root, "src/monotonic.py", "def steps():\n    return [1, 2]\n")
    commit(root, "add step 2")

    write(root, "src/monotonic.py", "def steps():\n    return [1, 2, 3]\n")
    commit(root, "add step 3")


def run_script(root, extra_args):
    result = subprocess.run(
        [sys.executable, SCRIPT, "--repo", root, "--json"] + extra_args,
        capture_output=True, text=True, check=False,
    )
    return result


def main():
    with tempfile.TemporaryDirectory() as root:
        build_repo(root)

        result = run_script(root, ["--paths", "src/config.py", "src/monotonic.py"])
        check("script exits 0", result.returncode == 0, result.stderr[:200])
        data = json.loads(result.stdout) if result.returncode == 0 else {"hotspots": []}
        hotspots = {h["file"]: h for h in data.get("hotspots", [])}

        check("flags src/config.py as a hotspot", "src/config.py" in hotspots)
        if "src/config.py" in hotspots:
            hotspot = hotspots["src/config.py"]
            check("flip_count is exactly 1", hotspot["flip_count"] == 1, str(hotspot["flip_count"]))
            check("change_count is exactly 3", hotspot["change_count"] == 3, str(hotspot["change_count"]))
            check("two distinct sample states", len(hotspot["sample_states"]) == 2, str(hotspot["sample_states"]))

        check("does not flag src/monotonic.py", "src/monotonic.py" not in hotspots)

        strict_result = run_script(root, ["--paths", "src/config.py", "src/monotonic.py", "--min-flips", "2"])
        strict_data = json.loads(strict_result.stdout) if strict_result.returncode == 0 else {"hotspots": []}
        check("min-flips 2 filters out the single-flip hotspot", len(strict_data.get("hotspots", [])) == 0)

    total = len(checks)
    passed = sum(1 for c in checks if c)
    print("\n%d/%d checks passed" % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
