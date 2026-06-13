
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

explanation = """
Let's zoom out and look at the entire system from three perspectives: the protocol, the training, and the psychology of role-playing.

First, the Protocol. When an Agent interacts with an LLM, it follows a 'Stateless Protocol' called Chat Completion. Because the LLM has no memory of its own, the Agent must act as the 'Memory Keeper.' Every time you send a new message, the Agent bundles the entire history—the System Prompt, previous turns, and the new query—into a single structured payload. This is then wrapped in a template like ChatML, using those special tokens we discussed, and sent to the LLM as a giant text block to 'complete.'

Second, the Training. How does an LLM become a conversational expert? It's a three-step journey. 
Stage one is 'Pre-training,' where the model reads the entire internet to learn the 'probability' of the next word. 
Stage two is 'Supervised Fine-Tuning,' or SFT. Here, humans write 'perfect' dialogues to teach the model how a helpful assistant should sound. 
Stage three is 'RLHF'—Reinforcement Learning from Human Feedback. This is like a beauty pageant where humans rank different model responses, teaching it to be safe, honest, and engaging.

Finally, why does the 'Role-Playing' trick work? It’s because the LLM is essentially a 'Chameleon.' During pre-training, it has seen millions of personas—from senior engineers to pirate captains. When you give it a role in the System Prompt, you are performing 'Latent Space Activation.' You are essentially telling the model to narrow its focus to a specific subset of its knowledge and speaking style. By setting the role, you are significantly increasing the probability that the model will choose words and behaviors consistent with that persona, while suppressing irrelevant patterns.

This combination—the Agent managing the state, the LLM using its specialized training, and the System Prompt activating a specific persona—is what makes the 'Agent' feel like a distinct, intelligent entity.
"""

audio_path = f"/tmp/agent-llm-deep-dive-{uuid4()}.aiff"

print("Synthesizing Agent-LLM Deep Dive...")
synthesize_aiff_with_say(explanation, audio_path)

print(f"Playing audio deep dive from {audio_path}...")
subprocess.run(["afplay", audio_path])
