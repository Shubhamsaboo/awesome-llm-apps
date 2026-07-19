#!/usr/bin/env python3
"""
graveyard.py — find your dead side projects and figure out why they died.

Scans directories for git repos, separates the living from the dead, runs a
cause-of-death analysis on each corpse from its git history, detects your
personal death patterns, and ranks the dead by resurrection potential.

Everything runs locally. Nothing leaves your machine.

Usage:
    python3 graveyard.py ~/dev ~/projects            # scan these roots
    python3 graveyard.py                              # scan default roots
    python3 graveyard.py --json report.json           # full data for tooling
    python3 graveyard.py --days 90                    # custom "dead" threshold
    python3 graveyard.py --include-foreign             # include repos you didn't author

Python 3.8+, stdlib only. Read-only: never writes inside scanned repos.
"""

import argparse
import json
import os
import statistics
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_ROOTS = ["~/dev", "~/projects", "~/code", "~/src", "~/Desktop", "~/Documents/GitHub", "~/Downloads"]
SKIP_DIRS = {"node_modules", ".venv", "venv", ".tox", "vendor", ".cache", "Library",
             "__pycache__", ".npm", ".cargo", "go", ".local", ".Trash", "dist", "build"}
MAX_DEPTH = 4

CONFIG_FILES = {
    "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "tsconfig.json",
    "webpack.config.js", "vite.config.js", "vite.config.ts", "babel.config.js",
    ".eslintrc", ".eslintrc.js", ".eslintrc.json", ".prettierrc", "jest.config.js",
    "requirements.txt", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile",
    "Dockerfile", "docker-compose.yml", ".gitignore", "Makefile", ".env.example",
    "tailwind.config.js", "postcss.config.js", "next.config.js", "next.config.mjs",
}
DEPLOY_MARKERS = ["vercel.json", "netlify.toml", "fly.toml", "render.yaml", "Procfile",
                  "app.yaml", "wrangler.toml", "railway.json", ".github/workflows"]
AUTH_HINTS = ("auth", "oauth", "login", "signup", "session", "clerk", "passport",
              "jwt", "next-auth", "supabase-auth")
PAYMENT_HINTS = ("stripe", "billing", "payment", "checkout", "subscription", "paddle",
                 "lemonsqueezy", "paywall")


def sh(args, cwd=None):
    """Run a command, return stdout or '' on any failure. Never raises."""
    try:
        # Decode git output as UTF-8. With text=True and no encoding, Python uses
        # the locale default (cp1252 on Windows), which raises UnicodeDecodeError
        # on non-Latin-1 bytes in commit messages (emoji, em-dashes, …).
        out = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=30)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def find_repos(roots):
    repos = []
    for root in roots:
        root = Path(os.path.expanduser(root))
        if not root.is_dir():
            continue
        base_depth = len(root.parts)
        for dirpath, dirs, _files in os.walk(root):
            p = Path(dirpath)
            if len(p.parts) - base_depth > MAX_DEPTH:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            # .git can be a file (worktrees) — and we keep walking below a repo,
            # because real machines have accidental repos (a git-inited ~/Desktop)
            # with real projects nested inside them.
            if (p / ".git").exists():
                repos.append(p)
    # de-dup (same repo reachable from two roots) and keep paths resolved so
    # they compare equal everywhere (macOS tempdirs and symlinked dev folders
    # otherwise produce /var vs /private/var mismatches in the state file)
    seen, out = set(), []
    for r in repos:
        key = r.resolve()
        if key not in seen:
            seen.add(key)
            out.append(key)
    # Sorted so nothing downstream ever depends on filesystem walk order —
    # APFS and ext4 enumerate directories differently.
    return sorted(out)


PROJECT_MARKERS = {"package.json", "pyproject.toml", "requirements.txt", "go.mod",
                   "Cargo.toml", "Gemfile", "composer.json", "index.html"}


def find_unversioned(roots, repo_paths):
    """Project folders with no git anywhere — dead before their first commit.

    A dir counts if it has a project marker file, is not inside any git repo,
    and is not nested inside another unversioned project already found.
    """
    found = []
    repo_strs = [str(r) for r in repo_paths]
    for root in roots:
        root = Path(os.path.expanduser(root))
        if not root.is_dir():
            continue
        base_depth = len(root.parts)
        for dirpath, dirs, files in os.walk(root):
            p = Path(dirpath)
            if len(p.parts) - base_depth > MAX_DEPTH:
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            rp = str(p.resolve())
            if any(rp == r or rp.startswith(r + os.sep) for r in repo_strs):
                dirs[:] = []  # inside a git repo; its files belong to that story
                continue
            if p != root and PROJECT_MARKERS & set(files) and not (p / ".git").exists():
                found.append(p.resolve())
                dirs[:] = []  # don't count a project's subfolders as more projects
    return sorted(set(found))


def read_repo(path, my_emails):
    """Pull the facts out of one repo. Fast git commands only, read-only."""
    log = sh(["git", "log", "--format=%at|%ae|%s", "--no-merges"], cwd=path)
    if not log:
        return None
    commits = []
    for line in log.splitlines():
        parts = line.split("|", 2)
        if len(parts) == 3:
            try:
                commits.append({"at": int(parts[0]), "email": parts[1], "msg": parts[2]})
            except ValueError:
                continue
    if not commits:
        return None
    commits.sort(key=lambda c: c["at"])

    mine = (sum(1 for c in commits if c["email"].lower() in my_emails)
            if my_emails else len(commits))
    remote = sh(["git", "remote", "get-url", "origin"], cwd=path)

    files = sh(["git", "ls-files"], cwd=path).splitlines()
    file_names = {Path(f).name for f in files}
    top_dirs = {f.split("/")[0] for f in files if "/" in f}

    # files touched by the last 3 commits — where it died
    last_touched = sh(["git", "log", "-3", "--name-only", "--format="], cwd=path).lower()

    has_deploy = any(
        m in files or any(f.startswith(m) for f in files) for m in DEPLOY_MARKERS
    )
    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files)
    has_tags = bool(sh(["git", "tag", "--list"], cwd=path))
    has_readme = any(n.lower().startswith("readme") for n in file_names)

    # how much of the history is config-shuffling vs actual code
    # (--format= keeps the output to file paths only, one per touch)
    touches = [l for l in
               sh(["git", "log", "--name-only", "--format=", "--no-merges"], cwd=path).splitlines()
               if l.strip()]
    config_touches = sum(1 for l in touches if Path(l).name in CONFIG_FILES)
    total_touches = len(touches)

    return {
        "path": str(path),
        "name": path.name,
        "first": commits[0]["at"],
        "last": commits[-1]["at"],
        "commits": len(commits),
        "mine": mine,
        "messages": [c["msg"] for c in commits],
        "remote": remote,
        "files": len(files),
        "top_dirs": len(top_dirs),
        "last_touched": last_touched,
        "has_deploy": has_deploy,
        "has_tags": has_tags,
        "has_tests": has_tests,
        "has_readme": has_readme,
        "config_ratio": (config_touches / total_touches) if total_touches else 0.0,
        "gaps": [b["at"] - a["at"] for a, b in zip(commits, commits[1:])],
    }


def lifespan_days(r):
    return max(1, (r["last"] - r["first"]) // 86400)


def autopsy(repo, all_repos):
    """Cause of death, with evidence. Returns (cause, evidence) — best guess first.

    These are forensic reads of the git history, not certainties. The evidence
    string is the part that matters: it has to be true even if the verdict is
    debatable.
    """
    findings = []

    # killed by a newer project: another repo you own was born right after this
    # one died. Several can qualify; the nearest in time is the likeliest
    # killer — and picking it keeps the verdict deterministic regardless of
    # filesystem discovery order (name breaks exact-timestamp ties).
    killer, kgap = None, None
    for other in all_repos:
        if other is repo:
            continue
        gap = other["first"] - repo["last"]
        if 0 <= gap <= 14 * 86400:
            if kgap is None or (gap, other["name"]) < (kgap, killer["name"]):
                killer, kgap = other, gap
    if killer:
        findings.append((
            "shiny_object",
            "killed by `%s`, whose first commit came %d day(s) after this repo's last"
            % (killer["name"], max(1, kgap // 86400)),
        ))

    last = repo["last_touched"]
    if any(h in last for h in PAYMENT_HINTS):
        findings.append(("payments_wall", "the final commits touch payment code — died at the checkout"))
    elif any(h in last for h in AUTH_HINTS):
        findings.append(("auth_wall", "the final commits touch auth code — died at the login screen"))

    if repo["config_ratio"] >= 0.6 and repo["commits"] >= 5:
        findings.append((
            "boilerplate_wall",
            "%d%% of all file touches were config files — more time configuring than building"
            % round(repo["config_ratio"] * 100),
        ))

    if (repo["has_readme"] and repo["commits"] >= 20 and not repo["has_deploy"]
            and not repo["has_tags"]):  # tagged releases = it shipped, just not as a deployment
        findings.append((
            "deploy_fear",
            "README written, %d commits in, tests %s, and no deploy config anywhere. "
            "It worked. It just never shipped." % (repo["commits"], "present" if repo["has_tests"] else "absent"),
        ))

    rewrite_msgs = [m for m in repo["messages"]
                    if any(w in m.lower() for w in ("rewrite", "migrate to", "port to", "switch to"))]
    if len(rewrite_msgs) >= 2:
        findings.append((
            "rewrite_spiral",
            "history contains %d rewrite/migration commits — it kept being rebuilt instead of finished"
            % len(rewrite_msgs),
        ))

    if repo["files"] > 100 and not repo["has_deploy"] and lifespan_days(repo) > 30:
        findings.append((
            "scope_explosion",
            "%d files across %d top-level directories, zero deploy config — it grew instead of shipping"
            % (repo["files"], repo["top_dirs"]),
        ))

    if not findings and len(repo["gaps"]) >= 3:
        med = statistics.median(repo["gaps"])
        if med and repo["gaps"][-1] > 3 * med:
            findings.append((
                "slow_fade",
                "the last gap between commits was %dx the median — it didn't die, it drifted"
                % (repo["gaps"][-1] // max(1, int(med))),
            ))

    if not findings:
        findings.append(("unknown", "no clear wound. Sometimes a project just stops."))
    return findings


def pulse(repo):
    """0-100: how resurrectable is this corpse. Higher = closer to shipping."""
    score = 0
    why = []
    if repo["has_readme"]:
        score += 15; why.append("has a README")
    if repo["has_tests"]:
        score += 20; why.append("has tests")
    if repo["config_ratio"] < 0.5:
        score += 20; why.append("real code outweighs config")
    score += min(15, repo["commits"] // 4)
    if repo["commits"] >= 20:
        why.append("%d commits of momentum" % repo["commits"])
    if repo["remote"]:
        score += 10; why.append("already on a remote")
    age_days = (datetime.now().timestamp() - repo["last"]) / 86400
    if age_days < 180:
        score += 10; why.append("corpse is still warm (<6 months)")
    if repo["has_deploy"]:
        score += 10; why.append("deploy config already exists")
    missing = []
    if not repo["has_deploy"]:
        missing.append("deploy config")
    if not repo["has_tests"]:
        missing.append("tests")
    if not repo["has_readme"]:
        missing.append("README")
    return min(100, score), why, missing


def fmt_date(ts):
    return datetime.fromtimestamp(ts).strftime("%b %Y")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find your dead side projects and why they died.")
    ap.add_argument("roots", nargs="*", default=None, help="directories to scan (default: common dev dirs)")
    ap.add_argument("--days", type=int, default=45, help="no commits in N days = dead (default 45)")
    ap.add_argument("--json", metavar="PATH", help="write full machine-readable report")
    ap.add_argument("--include-foreign", action="store_true",
                    help="include repos where you authored <20%% of commits (clones, forks, work checkouts)")
    ap.add_argument("--max", type=int, default=60, dest="max_repos", help="stop after N repos (default 60)")
    ap.add_argument("--redact", action="store_true",
                    help="replace project names with project-1..n (for sharing the report)")
    ap.add_argument("--me", action="append", default=[], metavar="EMAIL",
                    help="extra email(s) you commit under (work address, web edits, "
                         "builder tools). Repeatable. Repos authored by these count as yours.")
    ap.add_argument("--no-art", action="store_true",
                    help="skip the headstone (for piping, or for people who hate fun)")
    ap.add_argument("--state", metavar="FILE",
                    help="remember scans and resurrections in FILE. Enables relapse "
                         "detection (a resurrected project going silent again) and "
                         "gives necromancer mode something to grep.")
    ap.add_argument("--mark-resurrected", metavar="PATH",
                    help="record that PATH was resurrected today (requires --state); "
                         "future scans call it out if it starts dying again.")
    args = ap.parse_args(argv)

    state = {"resurrections": [], "last_scan": None}
    if args.state and os.path.exists(args.state):
        try:
            state.update(json.load(open(args.state)))
        except (OSError, ValueError):
            print("warning: could not read state file %s; starting fresh" % args.state,
                  file=sys.stderr)

    if args.mark_resurrected:
        if not args.state:
            print("error: --mark-resurrected needs --state FILE to write into", file=sys.stderr)
            return 2
        target = str(Path(os.path.expanduser(args.mark_resurrected)).resolve())
        state["resurrections"] = [r for r in state["resurrections"] if r["path"] != target]
        state["resurrections"].append({"path": target, "name": Path(target).name,
                                       "date": datetime.now().strftime("%Y-%m-%d")})
        with open(args.state, "w") as f:
            json.dump(state, f, indent=1)
        print("recorded: %s resurrected %s. The next scan holds it to that."
              % (Path(target).name, state["resurrections"][-1]["date"]))
        return 0

    roots = args.roots or DEFAULT_ROOTS
    my_emails = {e.lower() for e in filter(None, [
        sh(["git", "config", "--global", "user.email"]),
        sh(["git", "config", "user.email"]),
    ])} | {e.strip().lower() for e in args.me if e.strip()}

    paths = find_repos(roots)
    unversioned = find_unversioned(roots, paths)
    if not paths:
        print("No git repos found under: %s" % ", ".join(roots))
        if unversioned:
            print("But %d project folder(s) with no git at all: %s"
                  % (len(unversioned), ", ".join(p.name for p in unversioned[:8])))
            print("No history means no autopsy — get them under git before they rot further.")
        print("Pass the directories where your projects actually live.")
        return 1
    if len(paths) > args.max_repos:
        print("(found %d repos; reading the first %d — raise --max to widen)"
              % (len(paths), args.max_repos), file=sys.stderr)
        paths = paths[: args.max_repos]

    if len(paths) > 15:
        print("reading %d repos (a few seconds each on big histories)..." % len(paths),
              file=sys.stderr)
    repos, skipped = [], []
    for p in paths:
        r = read_repo(p, my_emails)
        if r is None:
            continue
        if not args.include_foreign and my_emails and r["mine"] / r["commits"] < 0.2:
            skipped.append("%s (%d/%d commits yours)" % (r["name"], r["mine"], r["commits"]))
            continue  # someone else's repo you cloned; not your corpse to bury
        repos.append(r)
    foreign = len(skipped)

    if args.redact:
        for i, r in enumerate(sorted(repos, key=lambda r: r["first"]), 1):
            r["name"] = "project-%d" % i
            r["path"] = "(redacted)"

    cutoff = datetime.now().timestamp() - args.days * 86400
    silent = [r for r in repos if r["last"] < cutoff]
    alive = [r for r in repos if r["last"] >= cutoff]
    # A silent repo that shipped (deploy config + pushed + README) isn't dead —
    # it's a finished tool that reached stability. Don't eulogize it.
    # Shipped means deployed (deploy config) OR released (tags) — an
    # open-sourced library with releases is finished, not deploy-fearful.
    finished = [r for r in silent
                if r["remote"] and r["has_readme"] and (r["has_deploy"] or r["has_tags"])]
    dead = [r for r in silent if r not in finished]
    dead.sort(key=lambda r: r["last"], reverse=True)

    for r in dead:
        r["causes"] = autopsy(r, repos)
        s, w, m = pulse(r)
        r["pulse"], r["pulse_why"], r["missing"] = s, w, m
        r["lifespan_days"] = lifespan_days(r)

    # ---- census ----
    total_days = sum(r["lifespan_days"] for r in dead)
    print()
    if not args.no_art:
        print("          .--------.")
        print("         /          \\")
        print("        |   R.I.P.   |")
        print("        |    your    |")
        print("        |    side    |")
        print("        |  projects  |")
        print("     ___|____________|___")
        print("    ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~")
        print()
    print("GRAVEYARD REPORT · %s" % datetime.now().strftime("%Y-%m-%d"))
    print("=" * 60)
    print("repos scanned: %d   alive: %d   finished: %d   dead: %d   not yours (skipped): %d"
          % (len(repos) + foreign, len(alive), len(finished), len(dead), foreign))
    if finished:
        print("finished (shipped, just stable — not corpses): %s"
              % ", ".join(r["name"] for r in finished[:8]))
    if skipped:
        print("skipped as not-yours (by commit email): %s" % ", ".join(s.split(" (")[0] for s in skipped[:10])
              + (" …" if len(skipped) > 10 else ""))
        print("  (yours under another email? rerun with --me that@email.com, or --include-foreign)")
    if unversioned:
        if args.redact:
            print("unversioned (no git — died before their first commit): %d project folder(s)"
                  % len(unversioned))
        else:
            print("unversioned (no git — died before their first commit): %s"
                  % ", ".join(p.name for p in unversioned[:8])
                  + (" …" if len(unversioned) > 8 else ""))
        print("  no history means no autopsy; `git init` is the only medicine here")
    if not dead:
        print("\nNo corpses. Either you finish everything or you delete the evidence.")
        return 0
    print("combined lifespan of the dead: ~%d days of your life" % total_days)
    oldest = min(dead, key=lambda r: r["last"])
    print("oldest corpse: %s (silent since %s)" % (oldest["name"], fmt_date(oldest["last"])))

    # ---- the dead ----
    print("\nTHE DEAD" + " " * 24 + "lived      commits  cause of death")
    print("-" * 60)
    for r in dead:
        cause = r["causes"][0][0].replace("_", " ")
        print("%-30s %4dd %9d   %s" % (r["name"][:30], r["lifespan_days"], r["commits"], cause))

    # ---- patterns ----
    print("\nPATTERNS")
    print("-" * 60)
    spans = [r["lifespan_days"] for r in dead]
    med_span = statistics.median(spans)
    print("- median lifespan of a dead project: %d day%s" % (med_span, "" if med_span == 1 else "s"))
    burst = [r for r in dead if r["lifespan_days"] <= 1 and r["commits"] >= 5]
    if len(burst) >= 2:
        print("- %d projects lived exactly one day: built in a single burst, never reopened." % len(burst))
    shiny = [r for r in dead if r["causes"][0][0] == "shiny_object"]
    if shiny:
        print("- %d of %d were killed by a newer project. You don't abandon projects;"
              % (len(shiny), len(dead)))
        print("  you leave them for younger ones.")
    walls = [r for r in dead if r["causes"][0][0] in ("auth_wall", "payments_wall")]
    if len(walls) >= 2:
        print("- %d projects died at the same wall (auth/payments). That wall isn't moving;" % len(walls))
        print("  your approach to it has to.")
    fear = [r for r in dead if any(c[0] == "deploy_fear" for c in r["causes"])]
    if fear:
        print("- %d finished project(s) never shipped. Building was never the problem." % len(fear))

    # ---- relapse watch: hold past resurrections to their promise ----
    if state["resurrections"]:
        by_path = {r["path"]: r for r in repos}
        lines = []
        for res in state["resurrections"]:
            r = by_path.get(res["path"])
            if r is None:
                lines.append("- %s: resurrected %s, no longer found on disk. Buried for good, or moved."
                             % (res["name"], res["date"]))
                continue
            silent_days = int((datetime.now().timestamp() - r["last"]) / 86400)
            if silent_days > 14:
                lines.append("- %s: resurrected %s, silent for %d days since. It's dying again — "
                             "decide: recommit or bury it honestly." % (res["name"], res["date"], silent_days))
            else:
                lines.append("- %s: resurrected %s, last commit %dd ago. Holding."
                             % (res["name"], res["date"], silent_days))
        print("\nRELAPSE WATCH")
        print("-" * 60)
        for l in lines:
            print(l)

    # ---- pulse ----
    print("\nSTRONGEST PULSE --------/\\_/\\-------- (most resurrectable)")
    print("-" * 60)
    for r in sorted(dead, key=lambda r: r["pulse"], reverse=True)[:3]:
        print("%-30s pulse %d/100" % (r["name"][:30], r["pulse"]))
        print("   evidence: %s" % ("; ".join(r["pulse_why"]) or "not much"))
        print("   cause:    %s" % r["causes"][0][1])
        if r["missing"]:
            print("   to ship:  needs %s" % ", ".join(r["missing"]))
    print()

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"generated": datetime.now().isoformat(timespec="seconds"),
                       "days_threshold": args.days,
                       "alive": [{k: r[k] for k in ("name", "path", "last", "commits")} for r in alive],
                       "finished": [{k: r[k] for k in ("name", "path", "last", "commits")} for r in finished],
                       "unversioned": [{"name": u.name, "path": str(u)} for u in unversioned],
                       "dead": [{k: r[k] for k in r if k not in ("messages", "gaps", "last_touched")}
                                for r in dead]}, f, indent=1)
        print("full report: %s" % args.json)

    if args.state:
        state["last_scan"] = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "roots": [str(r) for r in roots],
            "dead": [{"name": r["name"], "path": r["path"], "cause": r["causes"][0][0],
                      "pulse": r["pulse"]} for r in dead],
            "alive": [{"name": r["name"], "path": r["path"]} for r in alive],
            "finished": [{"name": r["name"], "path": r["path"]} for r in finished],
            "unversioned": [{"name": u.name, "path": str(u)} for u in unversioned],
        }
        with open(args.state, "w") as f:
            json.dump(state, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
