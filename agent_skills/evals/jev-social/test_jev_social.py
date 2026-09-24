#!/usr/bin/env python3
"""Deterministic, offline eval for the jev-social skill."""

# SPDX-License-Identifier: Apache-2.0

import importlib.util
import io
import json
import stat
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[2] / "jev-social" / "scripts" / "jev_social.py"
SPEC = importlib.util.spec_from_file_location("jev_social", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CHECKS = []


def check(name, condition, detail=""):
    CHECKS.append(bool(condition))
    suffix = "" if condition or not detail else ": " + detail
    print("  %s %s%s" % ("PASS" if condition else "FAIL", name, suffix))


def decision(route="tiktok_search", confidence=0.87):
    return {
        "model": "~typesafe/jev-latest",
        "answers": {
            "route": {
                "type": "choice",
                "choice": route,
                "confidence": confidence,
                "probabilities": {route: confidence},
            }
        },
    }


def check_decisions():
    chosen = MODULE.validate_decision(decision(), "auto")
    check("typed route selects TikTok", chosen["platform"] == "tiktok")
    check("confidence is preserved", chosen["confidence"] == 0.87)

    try:
        MODULE.validate_decision([], "auto")
        malformed_rejected = False
    except MODULE.JevSocialError:
        malformed_rejected = True
    check("non-object decision is rejected", malformed_rejected)

    for malformed in ({"answers": []}, {"answers": {"route": []}}):
        try:
            MODULE.validate_decision(malformed, "auto")
            nested_rejected = False
        except MODULE.JevSocialError:
            nested_rejected = True
        check("malformed nested decision is rejected", nested_rejected)

    for name, payload, requested in (
        ("unsupported route", decision("unsupported", 0.9), "auto"),
        ("explicit route mismatch", decision("instagram_search", 0.9), "tiktok"),
        ("out-of-range confidence", decision("tiktok_search", 1.2), "auto"),
    ):
        try:
            MODULE.validate_decision(payload, requested)
            raised = False
        except MODULE.JevSocialError:
            raised = True
        check(name + " is rejected", raised)


def fake_socai(root):
    script = root / "socai"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "assert 'OPENROUTER_API_KEY' not in os.environ\n"
        "assert sys.argv[1:3] == ['tiktok', 'search']\n"
        "assert sys.argv[3:7] == ['--num', '4', '--pretty', '--']\n"
        "assert sys.argv[7] == 'AI creators'\n"
        "print(json.dumps({'results': [\n"
        " {'username': 'maker', 'caption': 'A useful demo', "
        "'url': 'https://www.tiktok.com/@maker/video/1', 'local_path': '/private/run'},\n"
        " {'title': 'missing source', 'token': 'secret'},\n"
        " {'author': {'name': 'builder'}, 'description': 'Second result', "
        "'share_url': 'https://www.tiktok.com/@builder/video/2'}\n"
        "]}))\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def fake_flood(root):
    script = root / "socai-flood"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "sys.stdout.write('x' * 512)\n"
        "sys.stderr.write('y' * 512)\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def check_execution():
    with tempfile.TemporaryDirectory(prefix="jev-social-eval-") as temp_dir:
        executable = fake_socai(Path(temp_dir))
        command = MODULE.build_socai_command(str(executable), "tiktok", "AI creators", 4)
        check("command operation is fixed to search", command[1:3] == ["tiktok", "search"])
        check("option parsing ends before the goal", command[-2] == "--")
        check("goal remains one argument", command[-1] == "AI creators")
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "must-not-reach-socai"}):
            payload, _elapsed = MODULE.run_socai(str(executable), "tiktok", "AI creators", 4)
        records = MODULE.project_records(payload, 4)
        check("only source-linked records survive", len(records) == 2)
        check("public author data is preserved", records[1]["author"] == "builder")
        serialized = json.dumps(records)
        check("local paths are not projected", "local_path" not in serialized and "/private/run" not in serialized)
        check("unknown token fields are not projected", "secret" not in serialized and "token" not in serialized)
        check(
            "login state is preserved without raw data",
            MODULE.outcome_note({"search_state": {"login_required": True}}) == "login required",
        )
        check(
            "arbitrary status text is not projected",
            MODULE.outcome_note({"status": "token=secret /private/run"}) == "",
        )

        hostile = {
            "results": [
                {
                    "author": "[fake](https://attacker.invalid)",
                    "caption": "*untrusted* | text",
                    "url": "https://www.tiktok.com/@maker/video/1) [Injected](https://attacker.invalid/)",
                },
                {"url": "https://127.0.0.1/private"},
            ]
        }
        safe_records = MODULE.project_records(hostile, 4)
        rendered = io.StringIO()
        with redirect_stdout(rendered):
            MODULE.render_markdown(
                {"platform": "tiktok", "confidence": 1.0}, safe_records, 1, 1
            )
        output = rendered.getvalue()
        check("non-platform URLs are removed", len(safe_records) == 1)
        check("record text cannot inject Markdown", "[fake](" not in output and "*untrusted*" not in output)
        check("source URL cannot close its Markdown link", ") [Injected](" not in output)
        check("strikethrough markers are escaped", MODULE.compact_text("~~untrusted~~") != "~~untrusted~~")
        check("bare text URLs are not auto-linkable", "https://" not in MODULE.compact_text("https://attacker.invalid"))

        try:
            MODULE.run_socai(
                str(fake_flood(Path(temp_dir))),
                "tiktok",
                "AI creators",
                4,
                max_output_bytes=128,
            )
            overflow_rejected = False
        except MODULE.JevSocialError as error:
            overflow_rejected = "size limit" in str(error)
        check("combined stdout and stderr are bounded while running", overflow_rejected)

    try:
        MODULE.build_socai_command("socai", "x", "topic", 4)
        rejected = False
    except MODULE.JevSocialError:
        rejected = True
    check("unsupported platforms never become commands", rejected)


def main():
    print("jev-social eval:")
    check_decisions()
    check_execution()
    print()
    passed = sum(CHECKS)
    if passed == len(CHECKS):
        print("PASS: %d/%d checks" % (passed, len(CHECKS)))
        return 0
    print("FAIL: %d/%d checks passed" % (passed, len(CHECKS)))
    return 1


if __name__ == "__main__":
    sys.exit(main())


def test_jev_social_eval():
    """Expose the standalone eval harness to pytest."""
    assert main() == 0
