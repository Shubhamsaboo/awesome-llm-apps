"""Cynative Security Research Agent — runnable example.

Cynative is a single Go binary that researches your code, cloud and runtime
read-only. This script is a thin driver: it checks the CLI and your LLM
credentials are in place, then hands off to the agent.

Usage:
    python cynative_agent.py
        Opens an interactive session — ask whatever you want.

    python cynative_agent.py "audit my S3 buckets for public access"
        Runs that one task non-interactively and exits.
"""

import os
import shutil
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()  # loads CYNATIVE_* and provider keys from a .env file if present

INSTALL_HINT = """Cynative CLI not found on PATH.

Install it with Homebrew:
    brew install cynative/tap/cynative

Or with the install script:
    curl -fsSL https://raw.githubusercontent.com/cynative/cynative/main/install.sh | sh
"""

CREDS_HINT = """Missing LLM configuration.

Set a provider, a model and its API key, for example:
    export CYNATIVE_LLM_PROVIDER=anthropic
    export CYNATIVE_LLM_MODEL=claude-fable-5
    export ANTHROPIC_API_KEY=<your-anthropic-api-key>

Cynative supports 23+ providers (OpenAI, Bedrock, Vertex, Azure, Ollama, ...).
See https://github.com/cynative/cynative/blob/main/docs/providers
"""


def preflight() -> None:
    """Fail fast with an actionable message instead of a cryptic traceback."""
    if shutil.which("cynative") is None:
        sys.exit(INSTALL_HINT)

    if not os.getenv("CYNATIVE_LLM_PROVIDER") or not os.getenv("CYNATIVE_LLM_MODEL"):
        sys.exit(CREDS_HINT)


def run(task: str | None) -> int:
    """Hand off to the agent.

    With no task, opens an interactive session so you can ask anything about
    your code, cloud or runtime. With a task, -p runs it once and exits —
    useful for scripts and pipes.

    Either way, every underlying call is resolved to its required IAM actions
    and authorized against a read-only policy before any credential is
    attached, so this is safe to point at real infrastructure.
    """
    cmd = ["cynative"] if task is None else ["cynative", "-p", task]
    return subprocess.run(cmd, check=False).returncode


def main() -> None:
    preflight()
    task = " ".join(sys.argv[1:]) or None
    sys.exit(run(task))


if __name__ == "__main__":
    main()
