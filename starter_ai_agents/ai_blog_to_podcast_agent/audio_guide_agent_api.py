
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

explanation = """
To build an LLM-based application using an Agent API, like the one from Agno, there are four key pillars you need to master.

First, is the Instruction Layer. Unlike standard programming, you don't write logic; you write instructions. This is the System Prompt. You define the agent's role, its goal, and its constraints—for example, telling a podcast agent to be conversational or a support agent to be empathetic.

Second, is Model Configuration. The Agent API allows you to swap brains easily. You can choose GPT-4 for complex reasoning or a smaller, faster model for simple tasks, all without changing your core application code.

Third, is the Run Cycle. The 'agent dot run' method is the entry point. It manages the conversation state and handles the raw text input. It doesn't just return a string; it returns a structured response object that can include tool usage data and token counts.

Fourth, is Tool Integration. This is the most powerful part. You can give an agent tools—like a web searcher or a database connector. The Agent API handles the 'reasoning' to decide when and how to call these tools to fulfill a user's request.

By focusing on these four pillars—Instructions, Models, Runs, and Tools—you can build sophisticated agents that do more than just chat; they perform actual work.
"""

audio_path = f"/tmp/agent-api-guide-{uuid4()}.aiff"

print("Synthesizing Agent API guide...")
synthesize_aiff_with_say(explanation, audio_path)

print(f"Playing audio guide from {audio_path}...")
subprocess.run(["afplay", audio_path])
