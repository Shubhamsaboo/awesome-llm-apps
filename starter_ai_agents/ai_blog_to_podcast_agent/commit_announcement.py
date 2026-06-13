
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

message = """
Great news! I have successfully created a new branch named 'feature slash linkedin-scraping-keychain-security'.

I have committed all the key changes, including the updated Streamlit app, the new podcast utilities, the improved LinkedIn scraping logic, and the macOS Keychain security integration. I also included the unit tests and the full pipeline verification script to ensure everything stays robust.

The workspace is now organized and your changes are safely versioned. You are all set to continue building or to push these changes to your remote repository.
"""

audio_path = f"/tmp/commit-announcement-{uuid4()}.aiff"

print("Synthesizing commit announcement...")
synthesize_aiff_with_say(message, audio_path)

print(f"Playing announcement from {audio_path}...")
subprocess.run(["afplay", audio_path])
