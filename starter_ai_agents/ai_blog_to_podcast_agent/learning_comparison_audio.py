
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

explanation = """
To understand the difference between Unsupervised and Supervised learning in AI, think of it as the difference between 'learning to see' and 'learning to follow orders.'

Unsupervised Learning is how we build the foundation. During the pre-training phase, the model is given massive amounts of raw, unlabeled data—trillions of words from the internet. There is no teacher and no 'correct' answer. The model's only goal is to find hidden patterns and structures on its own. This is where the model learns what language is, how facts relate, and how different voices sound. It's like a child listening to millions of conversations to understand the world, without anyone ever explaining it to them.

Supervised Learning is the refinement phase, often called Fine-Tuning. Here, we provide explicit 'Input-Output' pairs. A human teacher might give the model a question and show it the exact, ideal answer. This is where we teach the model specific skills—like how to summarize a blog post, how to write code, or how to be polite. Because humans are providing the labels, the model learns the 'correct' way to behave. It's like a student in a classroom where the teacher corrects their work and gives them specific templates to follow.

In summary: Unsupervised Learning provides the 'Intelligence' and 'Breadth,' while Supervised Learning provides the 'Utility' and 'Direction.' You need the unsupervised foundation to understand the world, and the supervised training to actually be useful to humans.
"""

audio_path = f"/tmp/unsupervised-vs-supervised-{uuid4()}.aiff"

print("Synthesizing learning comparison...")
synthesize_aiff_with_say(explanation, audio_path)

print(f"Playing audio comparison from {audio_path}...")
subprocess.run(["afplay", audio_path])
