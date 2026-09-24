#!/usr/bin/env python3
"""Typed Jev routing followed by one read-only local socai search."""

# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlparse


DECISION_URL = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "~typesafe/jev-latest"
PLATFORMS = ("instagram", "tiktok", "linkedin")
ROUTES = {"%s_search" % platform: platform for platform in PLATFORMS}
PUBLIC_FIELDS = (
    "title",
    "caption",
    "description",
    "text",
    "author",
    "username",
    "nickname",
    "media_type",
    "type",
    "likes",
    "like_count",
    "comments",
    "comment_count",
    "views",
    "view_count",
)
URL_FIELDS = ("url", "web_url", "share_url", "post_url", "video_url")
PUBLIC_HOSTS = ("instagram.com", "tiktok.com", "linkedin.com")
MAX_OUTPUT_BYTES = 8 * 1024 * 1024


class JevSocialError(Exception):
    """A concise, user-actionable failure."""


def decision_request(goal, requested_platform, model):
    return {
        "model": model,
        "state": {
            "request": goal,
            "requested_platform": requested_platform,
            "supported_workflows": [
                "Read-only Instagram search via the local socai CLI",
                "Read-only TikTok search via the local socai CLI",
                "Read-only LinkedIn search via the local socai CLI",
            ],
        },
        "questions": {
            "route": {
                "type": "choice",
                "instructions": {
                    "task": "Choose the one supported workflow that should execute this request.",
                    "rules": [
                        "Honor an explicit requested_platform.",
                        "Choose unsupported unless this is a read-only social search.",
                        "Never choose a workflow for posting, engagement, or messaging.",
                    ],
                },
                "criteria": {
                    "instagram_search": "Search Instagram content, profiles, posts, or reels.",
                    "tiktok_search": "Search TikTok content, creators, or videos.",
                    "linkedin_search": "Search LinkedIn people, companies, posts, or experience.",
                    "unsupported": "Anything else, including remote account changes or an ambiguous route.",
                },
            }
        },
    }


def validate_decision(payload, requested_platform):
    if not isinstance(payload, dict):
        raise JevSocialError("Jev returned an invalid response object.")
    answers = payload.get("answers")
    if not isinstance(answers, dict):
        raise JevSocialError("Jev returned an invalid answers object.")
    answer = answers.get("route")
    if not isinstance(answer, dict):
        raise JevSocialError("Jev returned an invalid route answer.")
    route = answer.get("choice")
    confidence = answer.get("confidence")
    if answer.get("type") != "choice" or route not in {*ROUTES, "unsupported"}:
        raise JevSocialError("Jev returned an invalid route.")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise JevSocialError("Jev returned an invalid confidence value.")
    if not 0 <= confidence <= 1:
        raise JevSocialError("Jev confidence was outside the supported range.")
    platform = ROUTES.get(route)
    if platform is None:
        raise JevSocialError("Jev rejected this request as unsupported or not read-only.")
    if requested_platform != "auto" and platform != requested_platform:
        raise JevSocialError(
            "Jev selected %s, which conflicts with explicit platform %s."
            % (platform, requested_platform)
        )
    probabilities = answer.get("probabilities")
    if probabilities is not None:
        if not isinstance(probabilities, dict) or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
            for value in probabilities.values()
        ):
            raise JevSocialError("Jev returned invalid route probabilities.")
    return {
        "route": route,
        "platform": platform,
        "confidence": float(confidence),
        "model": payload.get("model") or "unknown",
    }


def call_jev(goal, requested_platform, api_key, model, timeout=20):
    if not api_key:
        raise JevSocialError("OPENROUTER_API_KEY is not set.")
    body = json.dumps(decision_request(goal, requested_platform, model)).encode("utf-8")
    request = urllib.request.Request(
        DECISION_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": "Bearer %s" % api_key,
            "Content-Type": "application/json",
            "X-Title": "awesome-llm-apps-jev-social",
        },
    )
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(MAX_OUTPUT_BYTES + 1)
            if len(raw) > MAX_OUTPUT_BYTES:
                raise JevSocialError("OpenRouter response exceeded the safe size limit.")
            payload = json.loads(raw)
    except urllib.error.HTTPError as error:
        raise JevSocialError("OpenRouter rejected the Jev decision (HTTP %s)." % error.code) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise JevSocialError("Could not reach OpenRouter for the Jev decision.") from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise JevSocialError("OpenRouter returned an invalid Jev response.") from error
    return validate_decision(payload, requested_platform), int((time.monotonic() - started) * 1000)


def resolve_socai(candidate):
    if candidate:
        path = Path(candidate).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        resolved = shutil.which(candidate)
    else:
        resolved = shutil.which("socai")
    if not resolved:
        raise JevSocialError("The local socai CLI is not installed or not executable.")
    return resolved


def build_socai_command(executable, platform, goal, limit):
    if platform not in PLATFORMS:
        raise JevSocialError("Refusing to build a command for an unsupported platform.")
    if not 1 <= limit <= 20:
        raise JevSocialError("Result limit must be between 1 and 20.")
    return [executable, platform, "search", "--num", str(limit), "--pretty", "--", goal]


def collect_bounded(command, child_env, timeout, max_output_bytes):
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=child_env,
        )
    except OSError as error:
        raise JevSocialError("Could not start the local socai CLI.") from error

    chunks = {"stdout": [], "stderr": []}
    total = [0]
    lock = threading.Lock()
    overflow = threading.Event()

    def drain(name, stream):
        while True:
            data = stream.read(64 * 1024)
            if not data:
                return
            with lock:
                remaining = max_output_bytes - total[0]
                if len(data) > remaining:
                    if remaining > 0:
                        chunks[name].append(data[:remaining])
                    total[0] += len(data)
                    overflow.set()
                    return
                chunks[name].append(data)
                total[0] += len(data)

    readers = [
        threading.Thread(target=drain, args=("stdout", process.stdout), daemon=True),
        threading.Thread(target=drain, args=("stderr", process.stderr), daemon=True),
    ]
    for reader in readers:
        reader.start()

    deadline = time.monotonic() + timeout
    timed_out = False
    while process.poll() is None:
        if overflow.is_set():
            process.kill()
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            process.kill()
            break
        try:
            process.wait(timeout=min(0.05, remaining))
        except subprocess.TimeoutExpired:
            pass

    process.wait()
    for reader in readers:
        reader.join(timeout=1)
    process.stdout.close()
    process.stderr.close()

    if timed_out:
        raise JevSocialError("socai timed out before the read-only search finished.")
    if overflow.is_set():
        raise JevSocialError("socai output exceeded the safe size limit.")
    try:
        stdout = b"".join(chunks["stdout"]).decode("utf-8")
        stderr = b"".join(chunks["stderr"]).decode("utf-8")
    except UnicodeDecodeError as error:
        raise JevSocialError("socai returned output that was not valid UTF-8 text.") from error
    return process.returncode, stdout, stderr


def run_socai(executable, platform, goal, limit, timeout=180, max_output_bytes=MAX_OUTPUT_BYTES):
    command = build_socai_command(executable, platform, goal, limit)
    child_env = os.environ.copy()  # skillscan:allow -- remove the routing credential before subprocess execution
    child_env.pop("OPENROUTER_API_KEY", None)
    started = time.monotonic()
    returncode, stdout, _stderr = collect_bounded(
        command, child_env, timeout, max_output_bytes
    )
    if returncode != 0:
        raise JevSocialError("socai could not complete the read-only search.")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise JevSocialError("socai returned invalid JSON.") from error
    return payload, int((time.monotonic() - started) * 1000)


def candidate_records(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("results", "items", "posts", "videos"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
    for key in ("result", "data"):
        nested = payload.get(key)
        found = candidate_records(nested)
        if found:
            return found
    return []


def public_url(record):
    for key in URL_FIELDS:
        value = record.get(key)
        if isinstance(value, str):
            parsed = urlparse(value)
            hostname = (parsed.hostname or "").lower().rstrip(".")
            if (
                parsed.scheme in ("http", "https")
                and any(hostname == host or hostname.endswith("." + host) for host in PUBLIC_HOSTS)
            ):
                return value
    return ""


def scalar(value):
    if isinstance(value, (str, int, float)) and not isinstance(value, bool):
        return str(value).strip()
    if isinstance(value, dict):
        for key in ("name", "username", "nickname", "title", "text"):
            nested = value.get(key)
            if isinstance(nested, (str, int, float)) and not isinstance(nested, bool):
                return str(nested).strip()
    return ""


def compact_text(value, width=120):
    cleaned = " ".join(value.split())
    shortened = cleaned if len(cleaned) <= width else cleaned[: width - 1].rstrip() + "…"
    shortened = shortened.replace("://", "&#58;//")
    for marker in ("\\", "|", "[", "]", "*", "_", "`", "<", ">", "~"):
        shortened = shortened.replace(marker, "\\" + marker)
    return shortened


def markdown_url(value):
    return quote(value, safe=":/?#@!$&'*+,;=%-._~")


def project_records(payload, limit):
    projected = []
    for record in candidate_records(payload):
        if not isinstance(record, dict):
            continue
        url = public_url(record)
        if not url:
            continue
        item = {"url": url}
        for key in PUBLIC_FIELDS:
            value = scalar(record.get(key))
            if value:
                item[key] = compact_text(value)
        projected.append(item)
        if len(projected) >= limit:
            break
    return projected


def outcome_note(payload):
    if not isinstance(payload, dict):
        return ""
    states = [payload]
    for key in ("search_state", "result", "data"):
        if isinstance(payload.get(key), dict):
            states.append(payload[key])
    labels = []
    for state in states:
        for key, label in (
            ("login_required", "login required"),
            ("challenge_required", "platform challenge"),
            ("rate_limited", "rate limited"),
        ):
            if state.get(key) is True and label not in labels:
                labels.append(label)
    if labels:
        return ", ".join(labels)
    for state in states:
        status = state.get("status")
        if isinstance(status, str):
            normalized = status.strip().lower().replace("-", "_").replace(" ", "_")
            if normalized in {
                "ok",
                "success",
                "complete",
                "completed",
                "partial",
                "empty",
                "no_results",
                "login_required",
                "challenge_required",
                "rate_limited",
                "failed",
                "error",
            }:
                return normalized.replace("_", " ")
    return ""


def first(item, keys, default="—"):
    for key in keys:
        if item.get(key):
            return item[key]
    return default


def render_markdown(decision, items, jev_ms, socai_ms, note=""):
    print(
        "Jev routed this request to **%s** at **%.0f%% confidence**."
        % (decision["platform"], decision["confidence"] * 100)
    )
    print("\n| # | Author | Evidence | Source |")
    print("|---:|---|---|---|")
    for index, item in enumerate(items, 1):
        author = first(item, ("author", "username", "nickname"))
        evidence = first(item, ("title", "caption", "description", "text"))
        print("| %d | %s | %s | [Open](%s) |" % (index, author, evidence, markdown_url(item["url"])))
    if not items:
        print("| — | — | No previewable source-linked records were returned. | — |")
    if note:
        print("\nRun status: %s" % compact_text(note, 100))
    print("\nTiming: Jev %.2fs · socai %.2fs" % (jev_ms / 1000, socai_ms / 1000))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Route one read-only social search through Jev and the local socai CLI."
    )
    parser.add_argument("goal", help="Natural-language social research goal")
    parser.add_argument("--platform", choices=("auto",) + PLATFORMS, default="auto")
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=180)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    goal = args.goal.strip()
    if not goal:
        print("error: research goal cannot be empty", file=sys.stderr)
        return 2
    try:
        if not 1 <= args.limit <= 20:
            raise JevSocialError("Result limit must be between 1 and 20.")
        if not 1 <= args.timeout <= 600:
            raise JevSocialError("Timeout must be between 1 and 600 seconds.")
        decision, jev_ms = call_jev(
            goal,
            args.platform,
            os.environ.get("OPENROUTER_API_KEY", "").strip(),
            os.environ.get("OPENROUTER_JEV_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        )
        executable = resolve_socai(os.environ.get("SOCAI_BIN", "").strip())
        payload, socai_ms = run_socai(
            executable,
            decision["platform"],
            goal,
            args.limit,
            timeout=args.timeout,
        )
        items = project_records(payload, args.limit)
        render_markdown(decision, items, jev_ms, socai_ms, outcome_note(payload))
        return 0 if items else 3
    except JevSocialError as error:
        print("error: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
