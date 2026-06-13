
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

explanation = """
You've hit on a core challenge in AI security! While it looks like one long text to us, LLMs actually see the conversation through 'Chat Templates.' 

Imagine the conversation is wrapped in special, invisible code. Most modern models use a format called ChatML. When you send a system prompt, the model sees a specific marker, like 'start-header system', followed by your instructions, and then an 'end-header' marker. User messages have their own unique markers.

These markers are 'Special Tokens' that the LLM is trained to recognize as structural boundaries. Because a user can only input plain text, they can't easily generate these underlying structural tokens.

But the real magic happens during training, specifically a process called 'Instruction Tuning.' The model is shown thousands of examples where it must follow the system instructions even if the user message contradicts them. It learns a hierarchy of roles, where the 'system' role is the master and the 'user' role is the student.

While it's not perfect—this is why 'jailbreaking' exists—this combination of structural tagging and specialized training is what keeps the model from being easily fooled by user input.
"""

audio_path = f"/tmp/llm-security-tech-{uuid4()}.aiff"

print("Synthesizing technical explanation of LLM roles...")
synthesize_aiff_with_say(explanation, audio_path)

print(f"Playing audio explanation from {audio_path}...")
subprocess.run(["afplay", audio_path])
