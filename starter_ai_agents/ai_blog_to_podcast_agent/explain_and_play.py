
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

explanation = """
Hello! Let's take a look under the hood of the Blog to Podcast Agent.

The architecture is split into three main layers. 

First is the Infrastructure layer in podcast_utils.py. It handles the heavy lifting like fetching raw HTML with curl, cleaning it with regular expressions, and securely pulling your API keys from the macOS Keychain. It also manages the audio synthesis using the system's say command.

Second is the Orchestration layer. This is where the Agno Agent lives. The Agent is more than just a wrapper for GPT-4; it's a high-level API that manages the context, instructions, and response formatting. We use the Agent constructor to define the persona—like telling it to ignore LinkedIn boilerplate—and the agent.run method to process the messy blog text into a polished podcast script.

Finally, there is the Presentation layer in blog_to_podcast_agent.py. This uses Streamlit to create the web interface you see in your browser. It connects the buttons and inputs to the underlying logic and displays the audio player.

By combining these layers, the app transforms complex web content into a conversational audio experience in just a few seconds.
"""

audio_path = f"/tmp/explanation-{uuid4()}.aiff"

print("Synthesizing explanation audio...")
synthesize_aiff_with_say(explanation, audio_path)

print(f"Playing explanation from {audio_path}...")
subprocess.run(["afplay", audio_path])
