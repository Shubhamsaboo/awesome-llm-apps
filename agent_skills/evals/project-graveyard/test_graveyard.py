#!/usr/bin/env python3
"""
Executable eval for project-graveyard. Builds a synthetic graveyard with known
causes of death, runs the scanner against it, and asserts every classifier.

    python3 agent_skills/evals/project-graveyard/test_graveyard.py

Lives in the repo, not in the installable skill: users install only what
runs at runtime; this is what you run BEFORE installing, from the clone.

No dependencies beyond git and the Python stdlib. Creates everything in a
temp directory; touches nothing else. Commit dates are relative to today so
the fixtures never age out.

What it proves (each caught a real bug during development, or guards one):
  - alive / finished / dead separation (incl. "shipped but stable" != dead)
  - deploy_fear, payments_wall, boilerplate_wall, shiny_object classification
  - the shiny_object kill-chain names the right killer
  - config-touch ratio stays sane (once reported 111%)
  - --redact renames projects but keeps the kill-chain intact
  - --state + --mark-resurrected + relapse detection
  - --json report structure
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "..", "project-graveyard", "scripts", "graveyard.py")
EMAIL = "graveyard-eval@example.com"

checks = []


def check(name, ok, detail=""):
    checks.append(ok)
    print("  %s %s%s" % ("PASS" if ok else "FAIL", name, (" — " + detail) if detail and not ok else ""))


def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%dT10:00:00")


def repo(root, name):
    d = os.path.join(root, name)
    os.makedirs(d)
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    subprocess.run(["git", "config", "user.email", EMAIL], cwd=d, check=True)
    subprocess.run(["git", "config", "user.name", "eval"], cwd=d, check=True)
    return d


def commit(d, date, msg, files):
    for f in files:
        p = os.path.join(d, f)
        os.makedirs(os.path.dirname(p), exist_ok=True) if "/" in f else None
        with open(p, "a") as fh:
            fh.write("line\n")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    env = dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    subprocess.run(["git", "commit", "-qm", msg], cwd=d, env=env, check=True)


def run(*args):
    out = subprocess.run([sys.executable, SCRIPT, *args, "--me", EMAIL],
                         capture_output=True, text=True)
    return out.stdout + out.stderr


def build_graveyard(root):
    # boilerplate wall, then murdered: config-only commits, dies 120d ago;
    # killer-app is born 3 days later (shiny_object should win precedence)
    d = repo(root, "boiler-death")
    commit(d, days_ago(132), "init", ["package.json", ".gitignore"])
    commit(d, days_ago(130), "eslint", [".eslintrc.json", ".prettierrc"])
    commit(d, days_ago(126), "webpack hell", ["webpack.config.js", "tsconfig.json"])
    commit(d, days_ago(123), "more config", ["jest.config.js", "Dockerfile"])
    commit(d, days_ago(120), "tailwind", ["tailwind.config.js", "postcss.config.js"])

    d = repo(root, "killer-app")
    commit(d, days_ago(117), "init", ["README.md", "src/index.js"])
    commit(d, days_ago(2), "still going", ["src/more.js"])  # alive

    # deploy fear: real code, README, 22 commits, no deploy config, dies 70d ago
    d = repo(root, "almost-shipped")
    commit(d, days_ago(126), "init", ["package.json", "README.md"])
    for i in range(1, 21):
        commit(d, days_ago(125 - i), "feat: core %d" % i, ["src/core%d.js" % i])
    commit(d, days_ago(70), "polish readme", ["README.md", "tests/core.test.js"])

    # payments wall: last commits touch stripe/billing, dies 90d ago
    d = repo(root, "pay-wall")
    commit(d, days_ago(116), "init", ["main.py", "README.md"])
    commit(d, days_ago(110), "core logic", ["app/logic.py"])
    commit(d, days_ago(105), "users", ["app/users.py"])
    commit(d, days_ago(91), "start stripe integration", ["app/stripe_checkout.py"])
    commit(d, days_ago(90), "fight stripe webhooks", ["app/billing.py"])

    # finished, not dead: silent 150d but deployed + pushed + documented
    # unversioned: a project folder that never got a git init
    nb = os.path.join(root, "never-born")
    os.makedirs(nb)
    open(os.path.join(nb, "package.json"), "w").write("{}\n")
    open(os.path.join(nb, "app.js"), "w").write("// big plans\n")

    d = repo(root, "shipped-tool")
    commit(d, days_ago(150), "ship it", ["README.md", "vercel.json", "src.js"])
    subprocess.run(["git", "remote", "add", "origin",
                    "https://example.com/x/shipped-tool.git"], cwd=d, check=True)


def main():
    root = tempfile.mkdtemp(prefix="graveyard-eval-")
    try:
        build_graveyard(root)

        print("classification:")
        out = run(root, "--days", "45")
        check("census separates alive/finished/dead",
              "alive: 1   finished: 1   dead: 3" in out, out.splitlines()[2] if out else "no output")
        check("shipped-tool is finished, not eulogized",
              "shipped-tool" in out and "shipped-tool" not in out.split("THE DEAD")[-1])
        check("almost-shipped died of deploy fear",
              "almost-shipped" in out and "deploy fear" in out)
        check("pay-wall died at the payments wall", "payments wall" in out)
        check("boiler-death: shiny object takes precedence", "shiny object" in out)
        check("kill-chain names the killer", "killed by `killer-app`" in out)
        check("config ratio is sane (<=100%)", "111%" not in out and "1.0%%" not in out)
        check("unversioned folder counted, not autopsied",
              "never-born" in out and "no git" in out)

        print("redaction:")
        out = run(root, "--days", "45", "--redact")
        check("names are redacted", "project-1" in out and "almost-shipped" not in out)
        check("kill-chain survives redaction", "killed by `project-" in out)

        print("state and relapse:")
        state = os.path.join(root, "state.json")
        run(root, "--days", "45", "--state", state)
        with open(state) as f:
            s = json.load(f)
        check("state records the scan", len(s["last_scan"]["dead"]) == 3)
        check("state includes finished (necromancer needs it)",
              any(r["name"] == "shipped-tool" for r in s["last_scan"].get("finished", [])))
        out = run("--state", state, "--mark-resurrected", os.path.join(root, "almost-shipped"))
        check("resurrection is recorded", "recorded: almost-shipped" in out)
        with open(state) as f:
            s = json.load(f)
        s["resurrections"][0]["date"] = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        with open(state, "w") as f:
            json.dump(s, f)
        out = run(root, "--days", "45", "--state", state)
        check("relapse is detected and named",
              "RELAPSE WATCH" in out and "almost-shipped" in out and "dying again" in out)

        print("json report:")
        rpt = os.path.join(root, "report.json")
        run(root, "--days", "45", "--json", rpt)
        with open(rpt) as f:
            r = json.load(f)
        check("report has alive/finished/dead keys",
              all(k in r for k in ("alive", "finished", "dead")))
        check("dead entries carry causes and pulse",
              all("causes" in d and "pulse" in d for d in r["dead"]))

        print()
        if all(checks):
            print("PASS — %d/%d checks" % (len(checks), len(checks)))
            return 0
        print("FAIL — %d/%d checks passed" % (sum(checks), len(checks)))
        return 1
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
