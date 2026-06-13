# -*- coding: utf-8 -*-
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

message = """
All set! I have created a comprehensive session summary in a file named SESSION_SUMMARY.md.

This document captures everything we have built and discussed, including the architectural improvements, the macOS Keychain security integration, and our deep dives into LLM theory - from pre-training to the power of System Prompts.

I have committed this summary to your current branch. The repository now serves as both a functional application and a technical knowledge base for your work.

It was a pleasure assisting you. Goodbye!
"""

audio_path = f"/tmp/final-summary-announcement-{uuid4()}.aiff"

print("Synthesizing final announcement...")
synthesize_aiff_with_say(message, audio_path)

print(f"Playing final announcement from {audio_path}...")
subprocess.run(["afplay", audio_path])
