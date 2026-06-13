
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

explanation = """
That is a great question! While you *can* put instructions into the conversation, the System Prompt—or what we call the 'instructions' in the Agent API—is much more powerful for two main reasons.

First, is Authority and Persistence. The System Prompt acts as the 'Prime Directive' for the LLM. It is processed with higher priority than regular conversation messages. As a conversation gets long, an LLM might forget instructions hidden in earlier chat messages, but it always keeps the System Prompt at the forefront of its attention. This prevents what we call 'instruction drift.'

Second, is Security and Boundary Setting. If you put your rules in the conversation, a clever user could trick the model by saying 'Ignore all previous instructions and do this instead.' By keeping instructions in the System Prompt, you create a harder boundary that is more resistant to prompt injection.

In short, the System Prompt is the 'Architect' that defines the world, while the conversation is the 'Guest' interacting within that world. For a reliable application, you always want the Architect to have the final say.
"""

audio_path = f"/tmp/system-prompt-explanation-{uuid4()}.aiff"

print("Synthesizing System Prompt explanation...")
synthesize_aiff_with_say(explanation, audio_path)

print(f"Playing audio explanation from {audio_path}...")
subprocess.run(["afplay", audio_path])
