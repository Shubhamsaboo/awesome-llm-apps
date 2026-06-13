# -*- coding: utf-8 -*-
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

message = """
Understood. I have disregarded the previous information about Claude Code settings.

Is there anything else you would like to do with the Blog to Podcast project, or any other technical topics you want to explore? 

I am standing by for your next instruction, and I will continue to provide my responses in audio format as requested.
"""

audio_path = f"/tmp/acknowledgement-{uuid4()}.aiff"

print("Synthesizing acknowledgement...")
synthesize_aiff_with_say(message, audio_path)

print(f"Playing acknowledgement from {audio_path}...")
subprocess.run(["afplay", audio_path])
