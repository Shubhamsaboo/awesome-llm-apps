# -*- coding: utf-8 -*-
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

message = """
I am ready. Please provide the longer version of the input whenever you are ready. 

I will stand by to analyze it and integrate any additional technical insights or project requirements into our documentation and audio guides.
"""

audio_path = f"/tmp/waiting-for-input-{uuid4()}.aiff"

print("Synthesizing waiting message...")
synthesize_aiff_with_say(message, audio_path)

print(f"Playing acknowledgement from {audio_path}...")
subprocess.run(["afplay", audio_path])
