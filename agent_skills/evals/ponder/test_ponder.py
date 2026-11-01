#!/usr/bin/env python3
"""
Executable eval for ponder. Builds a temporary git repository, drives the
bundled zero-dependency CLI (agent_skills/ponder/scripts/ponder) across a
multi-pass session, and verifies:

1. Strict-scope unit enumeration catches omitted files and accepts complete inventories.
2. The coverage gate blocks `decide stop` (exit 2) while any unit is ungraded.
3. Pass 2 `add` and `delete` deltas close the coverage gap and retract a false positive.
4. Consecutive zero-delta passes converge (`advice: stop`) and allow `decide stop` (exit 0).
5. `ponder verify` reconciles the append-only ledger and rejects hand-tampered state files.
"""

import json
import os
import subprocess
import sys
import tempfile

SCRIPT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "..",
    "ponder",
    "scripts",
    "ponder",
)

checks = []


def check(name, ok, detail=""):
    checks.append(bool(ok))
    suffix = ": %s" % detail if detail and not ok else ""
    print("  %s %s%s" % ("PASS" if ok else "FAIL", name, suffix))


def write_text(root, rel_path, content):
    target = os.path.join(root, rel_path)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as handle:
        handle.write(content)


def write_json(root, rel_path, payload):
    write_text(root, rel_path, json.dumps(payload, indent=2) + "\n")


def run_ponder(root, args):
    env = os.environ.copy()
    env["PONDER_OCA"] = "off"
    return subprocess.run(
        [SCRIPT] + list(args),
        cwd=root,
        env=env,
        text=True,
        capture_output=True,
    )


def main():
    print("Running ponder deterministic eval...")
    with tempfile.TemporaryDirectory(prefix="ponder-eval-") as root:
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "eval@example.com"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "ponder eval"], cwd=root, check=True)

        write_text(root, "src/auth.js", "exports.verifyToken = (t) => Boolean(t);\n")
        write_text(root, "src/session.js", "exports.openSession = (u) => ({ user: u });\n")

        # 1. Start session
        r_start = run_ponder(
            root,
            ["start", "auth boundary review", "--lens", "architecture", "--min-passes", "2", "--max-passes", "5", "--json"],
        )
        check("start creates session", r_start.returncode == 0, r_start.stderr)
        start_data = json.loads(r_start.stdout) if r_start.returncode == 0 else {}
        session_id = start_data.get("session", "")
        check("start returns session slug", bool(session_id), r_start.stdout)

        # 2. Predict pass 1
        r_pred1 = run_ponder(
            root,
            ["predict", "--session", session_id, "--churn", "0.8", "--claim", "Pass 1 seeds auth and session units."],
        )
        check("pass 1 predict succeeds", r_pred1.returncode == 0, r_pred1.stderr)

        # 3. Strict-scope scan rejects incomplete unit inventory (missing src/session.js)
        write_json(
            root,
            "tmp/units-incomplete.json",
            [{"id": "u-auth", "label": "Auth verifier", "path": "src/auth.js", "kind": "module"}],
        )
        r_units_bad = run_ponder(
            root,
            ["units", "--session", session_id, "--file", "tmp/units-incomplete.json", "--scan", "src", "--strict-scope"],
        )
        check("strict-scope rejects omitted file", r_units_bad.returncode != 0, r_units_bad.stdout)

        # 4. Complete inventory passes strict-scope
        write_json(
            root,
            "tmp/units.json",
            [
                {"id": "u-auth", "label": "Auth verifier", "path": "src/auth.js", "kind": "module"},
                {"id": "u-session", "label": "Session store", "path": "src/session.js", "kind": "module"},
            ],
        )
        r_units_ok = run_ponder(
            root,
            ["units", "--session", session_id, "--file", "tmp/units.json", "--scan", "src", "--strict-scope"],
        )
        check("complete unit inventory passes strict-scope", r_units_ok.returncode == 0, r_units_ok.stderr)

        # 5. Grade only u-auth on pass 1 (leaving u-session ungraded so coverage is 0.50)
        write_json(
            root,
            "tmp/findings-1.json",
            {
                "version": 1,
                "findings": [
                    {
                        "unit": "u-auth",
                        "title": "verifyToken accepts any truthy string without signature verification",
                        "detail": "Tokens are checked only with Boolean(t), allowing forged strings.",
                        "dimension": "boundary-integrity",
                        "score": 2,
                        "severity": "must",
                        "confidence": 0.9,
                        "effort": "s",
                        "evidence": ["src/auth.js:1"],
                        "recommendation": "Verify token signature before returning true.",
                    },
                    {
                        "unit": "u-auth",
                        "title": "Speculative note on export style",
                        "detail": "CommonJS export style was flagged without defect evidence.",
                        "dimension": "cohesion",
                        "score": 4,
                        "severity": "note",
                        "confidence": 0.4,
                        "effort": "xs",
                        "evidence": ["src/auth.js:1"],
                        "recommendation": "Keep CommonJS exports consistent across modules.",
                    },
                ],
            },
        )
        r_grade = run_ponder(root, ["grade", "--session", session_id, "--file", "tmp/findings-1.json"])
        check("pass 1 grade records initial findings", r_grade.returncode == 0, r_grade.stderr)

        delib_payload = {
            "question": "Do the pass 1 findings hold against the source?",
            "skeptic": {"confidence": 0.85, "argument": "f-0002 is speculative and lacks defect evidence; f-0001 is real."},
            "builder": {"confidence": 0.90, "argument": "Verify HMAC signature in src/auth.js before returning true."},
            "dreamer": {"confidence": 0.80, "argument": "u-session still needs grading on token expiry propagation."},
            "empath": {"confidence": 0.85, "argument": "Forged tokens impact every authenticated route."},
        }
        write_json(root, "tmp/delib.json", delib_payload)
        write_text(root, "tmp/empty.jsonl", "")

        run_ponder(root, ["deliberate", "--session", session_id, "--file", "tmp/delib.json"])
        run_ponder(root, ["delta", "--session", session_id, "--file", "tmp/empty.jsonl"])

        r_judge1 = run_ponder(root, ["judge", "--session", session_id, "--json"])
        check("pass 1 judge succeeds", r_judge1.returncode == 0, r_judge1.stderr)
        j1 = json.loads(r_judge1.stdout)
        check("pass 1 coverage is 0.50", abs(j1.get("metrics", {}).get("coverage", 0) - 0.5) < 1e-6, r_judge1.stdout)
        check("pass 1 verdict is blocked", j1.get("verdict") == "blocked", r_judge1.stdout)

        # 6. Coverage gate must block decide stop with exit code 2
        r_stop_blocked = run_ponder(
            root,
            ["decide", "stop", "--session", session_id, "--why", "Attempt premature stop with ungraded unit"],
        )
        check("coverage gate blocks premature stop (exit 2)", r_stop_blocked.returncode == 2, r_stop_blocked.stderr)

        r_cont1 = run_ponder(
            root,
            ["decide", "continue", "--session", session_id, "--why", "Grade u-session and retract speculative note on pass 2."],
        )
        check("pass 1 decide continue advances to pass 2", r_cont1.returncode == 0, r_cont1.stderr)

        # 7. Pass 2: add finding for u-session (closing coverage to 1.00) and delete speculative f-0002
        run_ponder(root, ["predict", "--session", session_id, "--churn", "0.5", "--claim", "Grade u-session and retract f-0002."])
        run_ponder(root, ["deliberate", "--session", session_id, "--file", "tmp/delib.json"])
        deltas_p2 = [
            {
                "op": "add",
                "perspective": "dreamer",
                "why": "Grade u-session after inspecting src/session.js.",
                "finding": {
                    "unit": "u-session",
                    "title": "openSession does not attach an expiration timestamp",
                    "detail": "Sessions remain valid indefinitely without expiresAt.",
                    "dimension": "failure-modes",
                    "score": 2,
                    "severity": "should",
                    "confidence": 0.85,
                    "effort": "s",
                    "evidence": ["src/session.js:1"],
                    "recommendation": "Include an expiresAt timestamp when creating a session.",
                },
            },
            {
                "op": "delete",
                "target": "f-0002",
                "perspective": "skeptic",
                "why": "Skeptic verified exports style conforms to repo conventions; retracting note.",
            },
        ]
        write_text(root, "tmp/deltas-2.jsonl", "\n".join(json.dumps(d) for d in deltas_p2) + "\n")
        r_delta2 = run_ponder(root, ["delta", "--session", session_id, "--file", "tmp/deltas-2.jsonl"])
        check("pass 2 delta applies add and delete", r_delta2.returncode == 0, r_delta2.stderr)

        r_judge2 = run_ponder(root, ["judge", "--session", session_id, "--json"])
        j2 = json.loads(r_judge2.stdout)
        check("pass 2 coverage reaches 1.00", abs(j2.get("metrics", {}).get("coverage", 0) - 1.0) < 1e-6, r_judge2.stdout)
        run_ponder(root, ["decide", "continue", "--session", session_id, "--why", "Verify stability on pass 3."])

        # 8. Pass 3 & Pass 4: zero deltas -> epistemic silence -> verdict: stop
        for p in (3, 4):
            run_ponder(root, ["predict", "--session", session_id, "--churn", "0.0", "--claim", "Findings hold with zero churn."])
            run_ponder(root, ["deliberate", "--session", session_id, "--file", "tmp/delib.json"])
            run_ponder(root, ["delta", "--session", session_id, "--file", "tmp/empty.jsonl"])
            r_j = run_ponder(root, ["judge", "--session", session_id, "--json"])
            j_data = json.loads(r_j.stdout)
            if p == 3:
                run_ponder(root, ["decide", "continue", "--session", session_id, "--why", "Confirm two consecutive quiet passes."])
            else:
                check("pass 4 judge advises stop after two zero-churn passes", j_data.get("verdict") == "stop", r_j.stdout)

        r_stop_ok = run_ponder(
            root,
            ["decide", "stop", "--session", session_id, "--why", "1.00 coverage and two consecutive zero-churn passes."],
        )
        check("decide stop succeeds once converged", r_stop_ok.returncode == 0, r_stop_ok.stderr)

        # 9. Verify ledger reconciliation and report generation
        r_verify = run_ponder(root, ["verify", "--session", session_id])
        check("verify reconciles append-only ledger", r_verify.returncode == 0, r_verify.stderr)

        r_report = run_ponder(root, ["report", "--session", session_id, "--out", "report.md"])
        check("report generates markdown output", r_report.returncode == 0 and os.path.isfile(os.path.join(root, "report.md")), r_report.stderr)

        # 10. Tampering with findings.json is caught by ponder verify
        findings_path = os.path.join(root, ".ponder", session_id, "findings.json")
        with open(findings_path, "r", encoding="utf-8") as fh:
            tampered = json.load(fh)
        if isinstance(tampered, dict) and "findings" in tampered:
            tampered["findings"][0]["severity"] = "note"
        else:
            tampered[0]["severity"] = "note"
        with open(findings_path, "w", encoding="utf-8") as fh:
            json.dump(tampered, fh)
        r_verify_tampered = run_ponder(root, ["verify", "--session", session_id])
        check("verify rejects hand-tampered findings.json", r_verify_tampered.returncode != 0, r_verify_tampered.stdout)

    passed = sum(1 for c in checks if c)
    total = len(checks)
    print("\n%d/%d checks passed" % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
