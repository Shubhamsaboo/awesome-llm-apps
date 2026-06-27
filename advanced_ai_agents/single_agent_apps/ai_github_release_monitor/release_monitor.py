#!/usr/bin/env python3
"""
AI GitHub Release Monitor
=========================
Monitors GitHub repositories for new releases and uses Anthropic Claude to
provide semantic analysis — categorizing changes, identifying breaking changes,
security fixes, deprecations, and assessing impact for dependency users.

Pipeline: watchlist → fetch releases → AI analysis → structured report

Usage:
    python release_monitor.py                         # Check all watched repos
    python release_monitor.py --add owner/repo        # Add repo to watchlist
    python release_monitor.py --remove owner/repo     # Remove from watchlist
    python release_monitor.py --list                  # Show watchlist
    python release_monitor.py --history               # Show past analyses
    python release_monitor.py --show <id-prefix>      # Show specific analysis

Requirements:  pip install -r requirements.txt
Environment:   ANTHROPIC_API_KEY (required), GITHUB_TOKEN (optional, raises rate limit)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from rich.console import Console
    from rich.markup import escape
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path.home() / ".release_monitor"
DB_PATH = DATA_DIR / "releases.db"
WATCHLIST_PATH = DATA_DIR / "watchlist.json"
MODEL = os.environ.get("RELEASE_MONITOR_MODEL", "claude-sonnet-4-6")
GITHUB_API = "https://api.github.com"


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------


def get_db() -> sqlite3.Connection:
    """Open (and initialize if needed) the SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            repo TEXT NOT NULL,
            tag_name TEXT NOT NULL,
            release_name TEXT,
            published_at TEXT,
            analysis_json TEXT,
            categories TEXT,
            impact_score REAL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS seen_releases (
            repo TEXT NOT NULL,
            tag_name TEXT NOT NULL,
            seen_at TEXT NOT NULL,
            PRIMARY KEY (repo, tag_name)
        );
        """
    )
    return conn


# ---------------------------------------------------------------------------
# Watchlist management
# ---------------------------------------------------------------------------


def load_watchlist() -> list[str]:
    """Load the repo watchlist from disk."""
    if not WATCHLIST_PATH.exists():
        return []
    return json.loads(WATCHLIST_PATH.read_text())


def save_watchlist(repos: list[str]) -> None:
    """Persist the watchlist to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    WATCHLIST_PATH.write_text(json.dumps(sorted(set(repos)), indent=2) + "\n")


def add_repo(repo: str) -> bool:
    """Add a repo to the watchlist after validating it exists on GitHub."""
    if "/" not in repo or len(repo.split("/")) != 2:
        _print_error(f"Invalid format: '{repo}'. Use owner/repo (e.g., anthropics/anthropic-sdk-python)")
        return False

    # Validate repo exists
    headers = _github_headers()
    try:
        r = httpx.head(f"{GITHUB_API}/repos/{repo}", headers=headers, timeout=10)
        if r.status_code == 404:
            _print_error(f"Repository not found: {repo}")
            return False
        if r.status_code == 403:
            _print_error("GitHub API rate limit exceeded. Set GITHUB_TOKEN to increase limit.")
            return False
    except httpx.RequestError as e:
        _print_error(f"Network error validating repo: {e}")
        return False

    repos = load_watchlist()
    if repo in repos:
        _print_info(f"Already watching: {repo}")
        return True

    repos.append(repo)
    save_watchlist(repos)

    # Baseline the repo's current releases as "seen" so the first check doesn't
    # fire an AI analysis for every pre-existing release (up to per_page each).
    # Best-effort: a failure here must never prevent the repo from being added.
    try:
        conn = get_db()
        try:
            now = datetime.now(timezone.utc).isoformat()
            for rel in get_releases(repo):
                tag = rel.get("tag_name")
                if tag:
                    conn.execute(
                        "INSERT OR IGNORE INTO seen_releases (repo, tag_name, seen_at) VALUES (?, ?, ?)",
                        (repo, tag, now),
                    )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:  # noqa: BLE001 — baselining is best-effort
        _print_info(f"Note: could not baseline existing releases for {repo}: {e}")

    _print_success(f"Added to watchlist: {repo}")
    return True


def remove_repo(repo: str) -> bool:
    """Remove a repo from the watchlist."""
    repos = load_watchlist()
    if repo not in repos:
        _print_error(f"Not in watchlist: {repo}")
        return False
    repos.remove(repo)
    save_watchlist(repos)
    _print_success(f"Removed from watchlist: {repo}")
    return True


# ---------------------------------------------------------------------------
# GitHub API
# ---------------------------------------------------------------------------


def _github_headers() -> dict[str, str]:
    """Build headers for GitHub API requests."""
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    # Read the token at request time, not at import — Streamlit (app.py) sets
    # os.environ["GITHUB_TOKEN"] after this module is already imported, so a
    # module-level global would never see a token pasted into the UI.
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def get_releases(repo: str, per_page: int = 5) -> list[dict]:
    """Fetch the latest releases for a repository."""
    headers = _github_headers()
    try:
        r = httpx.get(
            f"{GITHUB_API}/repos/{repo}/releases",
            params={"per_page": per_page},
            headers=headers,
            timeout=15,
        )
        if r.status_code == 404:
            _print_error(f"Repository not found: {repo}")
            return []
        if r.status_code == 403:
            _print_error(f"Rate limited fetching {repo}. Set GITHUB_TOKEN for higher limits.")
            return []
        r.raise_for_status()
        return r.json()
    except httpx.RequestError as e:
        _print_error(f"Network error fetching releases for {repo}: {e}")
        return []


def get_compare(repo: str, base: str, head: str) -> str | None:
    """Fetch the comparison between two tags (for additional context)."""
    headers = _github_headers()
    try:
        r = httpx.get(
            f"{GITHUB_API}/repos/{repo}/compare/{base}...{head}",
            headers=headers,
            timeout=15,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        commits = data.get("commits", [])
        if not commits:
            return None
        lines = [f"- {c['commit']['message'].splitlines()[0]}" for c in commits[:30]]
        return f"{len(commits)} commits between {base} and {head}:\n" + "\n".join(lines)
    except (httpx.RequestError, KeyError):
        return None


def get_rate_limit() -> dict | None:
    """Check current GitHub API rate limit status."""
    headers = _github_headers()
    try:
        r = httpx.get(f"{GITHUB_API}/rate_limit", headers=headers, timeout=10)
        if r.status_code == 200:
            core = r.json()["resources"]["core"]
            return {"remaining": core["remaining"], "limit": core["limit"], "reset": core["reset"]}
    except (httpx.RequestError, KeyError):
        pass
    return None


# ---------------------------------------------------------------------------
# Claude analysis
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM = """You are a senior software engineer analyzing a GitHub release.
Given the release notes (and optionally a commit comparison), produce a structured
analysis that helps developers understand the impact of this release on their projects.

Return ONLY valid JSON matching this schema:
{
  "summary": "<2-3 sentence plain-english summary of what shipped>",
  "categories": ["<applicable items from: breaking_change, security_fix, deprecation, new_feature, bug_fix, performance, documentation, dependency_update>"],
  "breaking_changes": [{"description": "...", "migration": "..."}],
  "security_fixes": [{"description": "...", "severity": "critical|high|medium|low", "cve": null}],
  "deprecations": [{"what": "...", "replacement": "...", "removal_version": "..."}],
  "highlights": ["<top 3-5 most notable changes>"],
  "impact_score": 0.0,
  "impact_reasoning": "<who is affected and how urgently>",
  "upgrade_urgency": "immediate|soon|routine|skip",
  "upgrade_notes": "<practical advice for users upgrading>"
}

Rules:
- impact_score: 0.9+ for security/breaking, 0.5-0.8 for features, 0.1-0.4 for minor fixes
- upgrade_urgency: "immediate" only for critical security; "skip" only for pure docs/CI
- Be specific about migration paths for breaking changes
- If release notes are sparse, say so honestly — don't fabricate details
- categories should only include items that actually apply
- Empty arrays for sections with no applicable items"""


def analyze_release(
    client: "anthropic.Anthropic",
    repo: str,
    release: dict,
    diff_context: str | None = None,
    model: str | None = None,
) -> dict:
    """Use Claude to semantically analyze a release."""
    tag = release.get("tag_name", "unknown")
    name = release.get("name", tag)
    body = release.get("body", "") or ""
    published = release.get("published_at", "")

    user_content = f"## Release: {repo} @ {tag}\n"
    user_content += f"**Name:** {name}\n"
    user_content += f"**Published:** {published}\n\n"
    user_content += f"### Release Notes\n\n{body if body.strip() else '(No release notes provided)'}\n"

    if diff_context:
        user_content += f"\n### Commit History\n\n{diff_context}\n"

    try:
        response = client.messages.create(
            model=model or MODEL,
            max_tokens=2048,
            system=ANALYSIS_SYSTEM,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = response.content[0].text
        return _parse_json_response(raw)
    except Exception as e:
        return {"error": str(e), "summary": f"Analysis failed: {e}", "categories": [], "impact_score": 0.0}


def _parse_json_response(text: str) -> dict:
    """Parse JSON from Claude's response, stripping code fences if present."""
    # Strip markdown code fences
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw_response": text, "categories": [], "impact_score": 0.0}


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def check_releases(
    client: "anthropic.Anthropic",
    conn: sqlite3.Connection,
    repos: list[str] | None = None,
    model: str | None = None,
    callback=None,
) -> list[dict]:
    """Main pipeline: check watchlist for new releases, analyze each one."""
    repos = repos or load_watchlist()
    if not repos:
        _print_error("No repos in watchlist. Add some with: --add owner/repo")
        return []

    results = []
    for repo in repos:
        if callback:
            callback("checking", repo)

        releases = get_releases(repo)
        if not releases:
            continue

        # Filter to unseen releases
        new_releases = []
        for rel in releases:
            tag = rel.get("tag_name")
            if not tag:
                continue
            row = conn.execute(
                "SELECT 1 FROM seen_releases WHERE repo = ? AND tag_name = ?", (repo, tag)
            ).fetchone()
            if not row:
                new_releases.append(rel)

        if not new_releases:
            if callback:
                callback("up_to_date", repo)
            continue

        # Get previous release tag for diff context
        all_tags = [r.get("tag_name") for r in releases if r.get("tag_name")]

        for rel in new_releases:
            tag = rel["tag_name"]
            if callback:
                callback("analyzing", f"{repo}@{tag}")

            # Try to get diff from previous release
            diff_context = None
            tag_idx = all_tags.index(tag) if tag in all_tags else -1
            if tag_idx >= 0 and tag_idx + 1 < len(all_tags):
                prev_tag = all_tags[tag_idx + 1]
                diff_context = get_compare(repo, prev_tag, tag)

            analysis = analyze_release(client, repo, rel, diff_context, model)

            # Generate stable ID
            analysis_id = hashlib.sha256(f"{repo}:{tag}".encode()).hexdigest()[:12]

            # Store
            conn.execute(
                """INSERT OR REPLACE INTO analyses
                   (id, repo, tag_name, release_name, published_at, analysis_json, categories, impact_score, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    analysis_id,
                    repo,
                    tag,
                    rel.get("name", tag),
                    rel.get("published_at", ""),
                    json.dumps(analysis),
                    ",".join(analysis.get("categories", [])),
                    analysis.get("impact_score", 0.0),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO seen_releases (repo, tag_name, seen_at) VALUES (?, ?, ?)",
                (repo, tag, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()

            results.append({"id": analysis_id, "repo": repo, "tag": tag, "analysis": analysis})

            if callback:
                callback("done", f"{repo}@{tag}")

    return results


# ---------------------------------------------------------------------------
# CLI display
# ---------------------------------------------------------------------------

# Impact score → color/label mapping
URGENCY_COLORS = {
    "immediate": ("red", "IMMEDIATE"),
    "soon": ("yellow", "SOON"),
    "routine": ("green", "ROUTINE"),
    "skip": ("dim", "SKIP"),
}

CATEGORY_COLORS = {
    "breaking_change": "red",
    "security_fix": "red",
    "deprecation": "yellow",
    "new_feature": "cyan",
    "bug_fix": "green",
    "performance": "blue",
    "documentation": "dim",
    "dependency_update": "magenta",
}


def display_results(results: list[dict]) -> None:
    """Display analysis results in the terminal."""
    if not results:
        _print_info("No new releases found across watched repositories.")
        return

    if RICH_AVAILABLE:
        _display_results_rich(results)
    else:
        _display_results_plain(results)


def _display_results_rich(results: list[dict]) -> None:
    """Rich-formatted output."""
    console.print(f"\n[bold]Found {len(results)} new release(s)[/bold]\n")

    for item in results:
        analysis = item["analysis"]
        urgency = analysis.get("upgrade_urgency", "routine")
        color, label = URGENCY_COLORS.get(urgency, ("white", urgency.upper()))
        score = analysis.get("impact_score", 0.0)

        # Header
        header = f"[bold]{item['repo']}[/bold] @ [cyan]{item['tag']}[/cyan]"
        header += f"  [{color}]{label}[/{color}] (impact: {score:.1f})"

        # Categories
        cats = analysis.get("categories", [])
        cat_str = " ".join(f"[{CATEGORY_COLORS.get(c, 'white')}]{c}[/{CATEGORY_COLORS.get(c, 'white')}]" for c in cats)

        # Body
        body = f"{analysis.get('summary', 'No summary available')}\n\n"
        body += f"Categories: {cat_str}\n"

        # Breaking changes
        breaking = analysis.get("breaking_changes", [])
        if breaking:
            body += f"\n[red]Breaking Changes ({len(breaking)}):[/red]\n"
            for bc in breaking:
                body += f"  - {escape(bc.get('description', ''))}\n"
                if bc.get("migration"):
                    body += f"    Migration: {escape(bc['migration'])}\n"

        # Security fixes
        security = analysis.get("security_fixes", [])
        if security:
            body += f"\n[red]Security Fixes ({len(security)}):[/red]\n"
            for sf in security:
                sev = sf.get("severity", "unknown")
                body += f"  - [{sev}] {escape(sf.get('description', ''))}\n"

        # Highlights
        highlights = analysis.get("highlights", [])
        if highlights:
            body += "\nHighlights:\n"
            for h in highlights:
                body += f"  - {escape(h)}\n"

        # Upgrade notes
        notes = analysis.get("upgrade_notes")
        if notes:
            body += f"\nUpgrade: {escape(notes)}\n"

        body += f"\n[dim]ID: {item['id']}[/dim]"

        console.print(Panel(body, title=header, border_style=color))
        console.print()


def _display_results_plain(results: list[dict]) -> None:
    """Fallback plain-text output when Rich is not installed."""
    print(f"\nFound {len(results)} new release(s)\n")
    print("=" * 70)

    for item in results:
        analysis = item["analysis"]
        urgency = analysis.get("upgrade_urgency", "routine")
        score = analysis.get("impact_score", 0.0)

        print(f"\n{item['repo']} @ {item['tag']}")
        print(f"  Urgency: {urgency.upper()}  |  Impact: {score:.1f}")
        print(f"  Categories: {', '.join(analysis.get('categories', []))}")
        print(f"  Summary: {analysis.get('summary', 'N/A')}")

        breaking = analysis.get("breaking_changes", [])
        if breaking:
            print(f"  Breaking Changes ({len(breaking)}):")
            for bc in breaking:
                print(f"    - {bc.get('description', '')}")

        highlights = analysis.get("highlights", [])
        if highlights:
            print("  Highlights:")
            for h in highlights:
                print(f"    - {h}")

        notes = analysis.get("upgrade_notes")
        if notes:
            print(f"  Upgrade: {notes}")

        print(f"  ID: {item['id']}")
        print("-" * 70)


def display_history(conn: sqlite3.Connection, limit: int = 20) -> None:
    """Show past analyses."""
    rows = conn.execute(
        "SELECT id, repo, tag_name, impact_score, categories, created_at FROM analyses ORDER BY created_at DESC LIMIT ?",
        (limit,),
    ).fetchall()

    if not rows:
        _print_info("No analyses in history yet. Run --check to analyze releases.")
        return

    if RICH_AVAILABLE:
        table = Table(title="Release Analysis History")
        table.add_column("ID", style="dim", width=12)
        table.add_column("Repository", style="bold")
        table.add_column("Tag", style="cyan")
        table.add_column("Impact", justify="right")
        table.add_column("Categories")
        table.add_column("Analyzed", style="dim")

        for row in rows:
            score = row["impact_score"] or 0.0
            color = "red" if score >= 0.8 else "yellow" if score >= 0.5 else "green"
            table.add_row(
                row["id"],
                row["repo"],
                row["tag_name"],
                f"[{color}]{score:.1f}[/{color}]",
                row["categories"] or "",
                row["created_at"][:16],
            )
        console.print(table)
    else:
        print(f"{'ID':<12} {'Repository':<35} {'Tag':<15} {'Impact':<7} {'Date':<17}")
        print("-" * 90)
        for row in rows:
            print(
                f"{row['id']:<12} {row['repo']:<35} {row['tag_name']:<15} "
                f"{(row['impact_score'] or 0.0):<7.1f} {row['created_at'][:16]}"
            )


def display_single(conn: sqlite3.Connection, id_prefix: str) -> None:
    """Show a single analysis by ID prefix."""
    row = conn.execute("SELECT * FROM analyses WHERE id LIKE ?", (f"{id_prefix}%",)).fetchone()
    if not row:
        _print_error(f"No analysis found matching ID: {id_prefix}")
        return

    analysis = json.loads(row["analysis_json"])
    results = [{"id": row["id"], "repo": row["repo"], "tag": row["tag_name"], "analysis": analysis}]
    display_results(results)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _print_error(msg: str) -> None:
    if RICH_AVAILABLE:
        console.print(f"[red]Error:[/red] {msg}")
    else:
        print(f"Error: {msg}", file=sys.stderr)


def _print_success(msg: str) -> None:
    if RICH_AVAILABLE:
        console.print(f"[green]{msg}[/green]")
    else:
        print(msg)


def _print_info(msg: str) -> None:
    if RICH_AVAILABLE:
        console.print(f"[dim]{msg}[/dim]")
    else:
        print(msg)


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="AI GitHub Release Monitor — semantic analysis of repository releases using Claude"
    )
    parser.add_argument("--add", metavar="OWNER/REPO", help="Add a repository to the watchlist")
    parser.add_argument("--remove", metavar="OWNER/REPO", help="Remove a repository from the watchlist")
    parser.add_argument("--list", action="store_true", help="Show the current watchlist")
    parser.add_argument("--check", action="store_true", help="Check for new releases (default action)")
    parser.add_argument("--history", action="store_true", help="Show past release analyses")
    parser.add_argument("--show", metavar="ID", help="Show a specific analysis by ID prefix")
    parser.add_argument("--repo", metavar="OWNER/REPO", help="Check a specific repo (doesn't need to be in watchlist)")
    parser.add_argument("--model", default=MODEL, help=f"Claude model to use (default: {MODEL})")
    args = parser.parse_args()

    # Watchlist management (no API key needed)
    if args.add:
        add_repo(args.add)
        return

    if args.remove:
        remove_repo(args.remove)
        return

    if args.list:
        repos = load_watchlist()
        if not repos:
            _print_info("Watchlist is empty. Add repos with: --add owner/repo")
        else:
            _print_info(f"Watching {len(repos)} repositories:")
            for r in repos:
                print(f"  - {r}")
        return

    # History (no API key needed)
    conn = get_db()

    if args.history:
        display_history(conn)
        return

    if args.show:
        display_single(conn, args.show)
        return

    # Check releases (needs Anthropic key)
    if anthropic is None:
        _print_error("anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        _print_error("ANTHROPIC_API_KEY not set. Export it or pass via environment.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    repos = [args.repo] if args.repo else None

    # Show rate limit info
    rate = get_rate_limit()
    if rate:
        _print_info(f"GitHub API: {rate['remaining']}/{rate['limit']} requests remaining")
        if rate["remaining"] < 10 and not os.environ.get("GITHUB_TOKEN"):
            _print_info("Tip: Set GITHUB_TOKEN to increase rate limit from 60 to 5000/hour")

    # Run the pipeline
    def cli_callback(status: str, detail: str) -> None:
        if status == "checking":
            _print_info(f"Checking {detail}...")
        elif status == "analyzing":
            _print_info(f"  Analyzing {detail}...")
        elif status == "up_to_date":
            _print_info(f"  {detail}: up to date")

    results = check_releases(client, conn, repos=repos, model=args.model, callback=cli_callback)
    display_results(results)

    conn.close()


if __name__ == "__main__":
    main()
