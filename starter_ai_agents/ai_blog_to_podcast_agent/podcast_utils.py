import os
import re
import subprocess
from html import unescape


def get_openai_api_key() -> str:
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_key:
        return env_key

    user = os.environ.get("USER", "").strip()
    if not user:
        return ""

    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "OPENAI_API_KEY", "-a", user, "-w"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""

    return result.stdout.strip()


def fetch_url_with_curl(url: str) -> str:
    result = subprocess.run(
        [
            "curl",
            "-L",
            "--fail",
            "--silent",
            "--show-error",
            "--max-time",
            "30",
            url,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def extract_text_from_html(html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?is)<head.*?>.*?</head>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def synthesize_aiff_with_say(text: str, output_path: str) -> None:
    subprocess.run(
        ["say", "-o", output_path, text],
        check=True,
    )
