"""
Create a GitHub issue with the 'pilot' label.

Once the issue exists, Pilot (running via `pilot start --github`) will
automatically pick it up, plan the implementation, write code, and open a PR.

Usage:
    python demo_github_issue.py --repo owner/repo --title "Add health check endpoint"
    python demo_github_issue.py --repo owner/repo --title "Fix login bug" --body "Details..."
"""

import argparse
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()


def create_pilot_issue(repo: str, title: str, body: str, label: str, token: str) -> dict:
    """Create a GitHub issue with the pilot label."""
    owner, repo_name = repo.split("/")
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    payload = {
        "title": title,
        "body": body or f"Pilot task: {title}",
        "labels": [label],
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="Create a GitHub issue for Pilot to execute")
    parser.add_argument("--repo", required=True, help="GitHub repo (owner/repo)")
    parser.add_argument("--title", required=True, help="Issue title describing the task")
    parser.add_argument("--body", default="", help="Issue body with details (optional)")
    parser.add_argument("--label", default="pilot", help="Label for Pilot to pick up (default: pilot)")
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN"), help="GitHub token (or set GITHUB_TOKEN env var)")
    args = parser.parse_args()

    if not args.token:
        print("Error: GITHUB_TOKEN not set. Pass --token or set GITHUB_TOKEN env var.", file=sys.stderr)
        sys.exit(1)

    if "/" not in args.repo:
        print("Error: --repo must be in owner/repo format", file=sys.stderr)
        sys.exit(1)

    issue = create_pilot_issue(args.repo, args.title, args.body, args.label, args.token)

    print(f"Created issue #{issue['number']}: {issue['html_url']}")
    print(f"Label: {args.label}")
    print()
    print("Pilot will pick this up automatically if running with --github flag.")
    print("Start Pilot: pilot start --github --dashboard")


if __name__ == "__main__":
    main()
