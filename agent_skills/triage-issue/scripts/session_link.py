#!/usr/bin/env python3
"""Print the AgentsView replay link for the session writing this RCA.

    python scripts/session_link.py                 # newest active session in this cwd
    python scripts/session_link.py --id <uuid>     # a specific session
    python scripts/session_link.py --json          # link plus health signals

Requires a running local server: `agentsview daemon start`. Exits 1 with a
message on stderr (and prints nothing on stdout) when no link can be resolved,
so the RCA's Session line is omitted rather than filled with a dead link.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

FIELDS = ("id", "web_url", "health_grade", "outcome", "tool_failure_signal_count",
          "message_count", "started_at")


def _cli(*args):
    out = subprocess.run(["agentsview", *args, "--json"], capture_output=True,
                         text=True, timeout=30)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"agentsview {' '.join(args)} failed")
    return json.loads(out.stdout)


def resolve(session_id=None, cwd=None):
    if session_id:
        return _cli("session", "get", session_id)
    # Pick up the current transcript before the daemon's file watcher does.
    subprocess.run(["agentsview", "sync"], capture_output=True, timeout=120)
    data = _cli("session", "list", "--active", "--agent", "claude", "--limit", "20")
    sessions = data if isinstance(data, list) else data.get("sessions", [])
    cwd = os.path.realpath(cwd or os.getcwd())
    # A session started in a parent directory still owns this work.
    for s in sessions:
        root = os.path.realpath(s.get("cwd") or "")
        if root and (cwd == root or cwd.startswith(root + os.sep)):
            return s
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--id", help="Session UUID; skips cwd matching.")
    p.add_argument("--cwd", help="Directory to match against (default: current).")
    p.add_argument("--json", action="store_true", help="Emit link plus health signals.")
    args = p.parse_args()

    if not shutil.which("agentsview"):
        print("agentsview not installed; omit the Session line.", file=sys.stderr)
        return 1
    try:
        s = resolve(args.id, args.cwd)
    except (RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"could not resolve session: {e}", file=sys.stderr)
        return 1
    if not s or not s.get("web_url"):
        print("no active session matches this directory; pass --id.", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({k: s.get(k) for k in FIELDS}, indent=2))
    else:
        print(s["web_url"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
