
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

explanation = """
That is a common misconception, but the truth is actually more fascinating. During pre-training, there is no manual labeling of roles. Humans don't go through the internet saying 'this is a doctor' or 'this is a coder.'

Instead, the model performs 'Unsupervised Learning.' It reads billions of pages and simply tries to predict the next word. Because the internet already contains millions of different contexts—like medical journals, software documentation, and movie scripts—the model naturally learns the statistical patterns of how a doctor, a coder, or a storyteller speaks.

The 'labeling' actually happens implicitly through the structure of the data. For example, if a text starts with 'Dear Patient,' the model learns that the following words will follow the pattern of a clinical role. 

The explicit steering—where we tell the model 'you are a helpful assistant'—happens later during the Supervised Fine-Tuning stage. That is where humans provide high-quality examples to link those internal patterns to a specific conversational role.

So, pre-training gives the model the 'potential' to be any role, and Fine-Tuning gives us the 'steering wheel' to pick one.
"""

audio_path = f"/tmp/pretraining-myth-buster-{uuid4()}.aiff"

print("Synthesizing pre-training clarification...")
synthesize_aiff_with_say(explanation, audio_path)

print(f"Playing audio clarification from {audio_path}...")
subprocess.run(["afplay", audio_path])
