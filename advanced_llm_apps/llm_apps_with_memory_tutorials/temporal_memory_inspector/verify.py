"""Executable verification for current and point-in-time recall."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from temporal_memory import contents, run_scenario


def verify_receipt(result: dict[str, Any], label: str) -> None:
    receipt = result.get("receipt")
    expected = result.get("receipt_sha256")
    if not isinstance(receipt, dict) or not isinstance(expected, str):
        raise RuntimeError(f"{label} recall did not return a complete receipt")

    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), default=str)
    actual = hashlib.sha256(encoded.encode()).hexdigest()
    if actual != expected:
        raise RuntimeError(f"{label} receipt hash does not match its payload")


def main() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        results = run_scenario(Path(temp_dir) / "memory.db")

    current = contents(results["current"])
    historical = contents(results["historical"])

    if not any("Monday" in item for item in current):
        raise RuntimeError("current recall did not return the Monday estimate")
    if any("Friday" in item for item in current):
        raise RuntimeError("current recall leaked the superseded Friday estimate")
    if not any("Friday" in item for item in historical):
        raise RuntimeError("historical recall did not return the Friday estimate")
    if any("Monday" in item for item in historical):
        raise RuntimeError("historical recall leaked the later Monday estimate")

    verify_receipt(results["current"], "current")
    verify_receipt(results["historical"], "historical")
    print("PASS: current and point-in-time memory stayed separated")


if __name__ == "__main__":
    main()
