#!/usr/bin/env python3
"""Deterministic, offline eval for the runway-monte-carlo skill.

Runs the bundled simulator CLI on fixed inputs and checks the contract that
makes it trustworthy: seeded runs reproduce exactly, percentiles are ordered,
the emitted .xlsx is a real workbook, edge cases behave, and garbage input
fails fast instead of hanging. Standard library only; no network.
"""

# SPDX-License-Identifier: MIT

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "runway-monte-carlo"
    / "scripts"
    / "runway_sim.py"
)
CHECKS = []


def check(name, condition, detail=""):
    """Record one assertion while keeping the full eval running."""
    CHECKS.append(bool(condition))
    suffix = "" if condition or not detail else ": " + detail
    print(("PASS  " if condition else "FAIL  ") + name + suffix)


def run(args, timeout=60):
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True, timeout=timeout,
    )


def main():
    tmp = Path(tempfile.mkdtemp(prefix="runway-eval-"))
    base = [
        "--cash", "2400000", "--burn", "210000", "--burn-vol", "0.12",
        "--revenue", "60000", "--rev-growth", "0.05", "--seed", "7",
    ]

    # ── Determinism: the same seed must reproduce the same summary ──────────
    a = run(["run", str(tmp / "a.xlsx")] + base)
    b = run(["run", str(tmp / "b.xlsx")] + base)
    check("seeded run exits 0", a.returncode == 0, a.stderr[:200])
    # The summary line embeds the output path; the stats after the colon are
    # what determinism promises.
    stats = lambda r: r.stdout.split(":", 1)[-1]
    check("same seed reproduces the same stats", stats(a) == stats(b), stats(a) + " vs " + stats(b))

    c = run(["run", str(tmp / "c.xlsx")] + base[:-1] + ["8"])
    check("different seed changes the draw", stats(c) != stats(a))

    # ── Output contract: percentiles present and ordered ────────────────────
    def months(label, text):
        m = re.search(label + r"=(>?)(\d+)", text)
        if not m:
            return None
        return (2, int(m.group(2))) if m.group(1) else (1, int(m.group(2)))

    p10, p50, p90 = (months(k, a.stdout) for k in ("P10", "P50", "P90"))
    check("summary reports P10/P50/P90", all(v is not None for v in (p10, p50, p90)), a.stdout.strip())
    if all(v is not None for v in (p10, p50, p90)):
        check("percentiles are ordered P10 <= P50 <= P90", p10 <= p50 <= p90)
    check("naive figure shown for contrast", "naive=" in a.stdout)
    check("survival probability reported", re.search(r"survive\(\d+mo\)=", a.stdout) is not None)

    # ── The .xlsx is a real workbook ────────────────────────────────────────
    try:
        names = zipfile.ZipFile(tmp / "a.xlsx").namelist()
        check("xlsx is a valid zip with sheets", any(n.startswith("xl/worksheets/") for n in names))
        check("xlsx declares content types", "[Content_Types].xml" in names)
    except Exception as exc:  # noqa: BLE001
        check("xlsx is a valid zip with sheets", False, str(exc))

    # ── Edge cases ──────────────────────────────────────────────────────────
    pre = run(["run", str(tmp / "pre.xlsx"), "--cash", "1100000", "--burn", "95000", "--seed", "7"])
    check("pre-revenue (no revenue flags) works", pre.returncode == 0, pre.stderr[:200])

    rich = run(["run", str(tmp / "rich.xlsx"), "--cash", "500000", "--burn", "50000",
                "--revenue", "200000", "--seed", "7"])
    check("revenue > burn survives the horizon", rich.returncode == 0 and ">36" in rich.stdout, rich.stdout.strip())

    # ── Garbage fails fast, never hangs ─────────────────────────────────────
    try:
        bad = run(["run", str(tmp / "bad.xlsx"), "--cash", "lots", "--burn", "some"], timeout=30)
        check("non-numeric input returns promptly with an error", bad.returncode != 0)
    except subprocess.TimeoutExpired:
        check("non-numeric input returns promptly with an error", False, "hung past 30s")

    helps = run(["--help"])
    check("--help exits 0", helps.returncode == 0)

    print(f"\n{sum(CHECKS)}/{len(CHECKS)} checks passed")
    sys.exit(0 if all(CHECKS) else 1)


if __name__ == "__main__":
    main()
