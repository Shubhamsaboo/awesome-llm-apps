"""
Trigger a Pilot task via its webhook API.

This sends a simulated GitHub webhook event to Pilot's gateway server,
causing it to execute the task and create a PR.

Requires Pilot running with gateway enabled:
    pilot start --github

Usage:
    python demo_webhook_trigger.py --url http://localhost:9090 --repo owner/repo --title "Add rate limiting"
"""

import argparse
import hashlib
import hmac
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()


def build_github_webhook_payload(repo: str, title: str, body: str) -> dict:
    """Build a minimal GitHub issues webhook payload."""
    owner, repo_name = repo.split("/")
    issue_id = int(time.time()) % 100000  # pseudo-unique ID

    return {
        "action": "labeled",
        "issue": {
            "number": issue_id,
            "title": title,
            "body": body or f"Pilot task: {title}",
            "html_url": f"https://github.com/{repo}/issues/{issue_id}",
            "labels": [{"name": "pilot"}],
            "state": "open",
            "user": {"login": owner},
        },
        "label": {"name": "pilot"},
        "repository": {
            "full_name": repo,
            "name": repo_name,
            "owner": {"login": owner},
            "clone_url": f"https://github.com/{repo}.git",
        },
    }


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for webhook validation."""
    mac = hmac.new(secret.encode(), payload_bytes, hashlib.sha256)
    return f"sha256={mac.hexdigest()}"


def send_webhook(url: str, payload: dict, secret: str | None = None) -> requests.Response:
    """Send webhook to Pilot's gateway."""
    endpoint = f"{url.rstrip('/')}/webhooks/github"
    payload_bytes = json.dumps(payload).encode()

    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issues",
    }

    if secret:
        headers["X-Hub-Signature-256"] = sign_payload(payload_bytes, secret)

    return requests.post(endpoint, data=payload_bytes, headers=headers, timeout=30)


def main():
    parser = argparse.ArgumentParser(description="Trigger a Pilot task via webhook")
    parser.add_argument("--url", default="http://localhost:9090", help="Pilot gateway URL (default: http://localhost:9090)")
    parser.add_argument("--repo", required=True, help="GitHub repo (owner/repo)")
    parser.add_argument("--title", required=True, help="Task title")
    parser.add_argument("--body", default="", help="Task description (optional)")
    parser.add_argument("--secret", default=os.getenv("GITHUB_WEBHOOK_SECRET"), help="Webhook secret for HMAC signing (optional)")
    args = parser.parse_args()

    if "/" not in args.repo:
        print("Error: --repo must be in owner/repo format", file=sys.stderr)
        sys.exit(1)

    payload = build_github_webhook_payload(args.repo, args.title, args.body)

    print(f"Sending webhook to {args.url}/webhooks/github")
    print(f"Task: {args.title}")
    print(f"Repo: {args.repo}")
    print()

    try:
        resp = send_webhook(args.url, payload, args.secret)
        print(f"Response: {resp.status_code}")
        if resp.status_code == 200:
            print("Pilot accepted the task. Check the dashboard or GitHub for PR.")
        else:
            print(f"Unexpected response: {resp.text}")
    except requests.ConnectionError:
        print(f"Error: Cannot connect to {args.url}", file=sys.stderr)
        print("Make sure Pilot is running: pilot start --github", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
