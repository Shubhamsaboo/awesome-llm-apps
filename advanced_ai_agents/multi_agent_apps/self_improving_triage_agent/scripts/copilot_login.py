#!/usr/bin/env python3
"""Sign in to GitHub Copilot once, then list the models you can pass to --model.

    python scripts/copilot_login.py

Prints a github.com/login/device URL and a code; approve it in the browser. The
token is cached in ~/.config/litellm/github_copilot, so later runs — the CLIs and
the Streamlit app — use it silently.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "optimizer"))
from copilot import is_signed_in, list_models  # noqa: E402
from litellm.llms.github_copilot.authenticator import Authenticator  # noqa: E402


def main() -> int:
    if is_signed_in():
        print("  already signed in to GitHub Copilot")
    else:
        Authenticator().get_api_key()  # runs the device flow and blocks until approved
        print("  signed in")

    models = list_models()
    if not models:
        print("  could not list models — check your Copilot plan, or pass a model ID by hand",
              file=sys.stderr)
        return 1
    print("\n  available models (use with --model or TRIAGE_MODEL):")
    for m in models:
        print(f"    {m}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
