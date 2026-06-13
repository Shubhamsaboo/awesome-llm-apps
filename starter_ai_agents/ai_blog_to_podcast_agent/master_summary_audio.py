# -*- coding: utf-8 -*-
import os
from uuid import uuid4
from podcast_utils import synthesize_aiff_with_say
import subprocess

explanation = """
Welcome to the Master Summary of our deep dive into LLM Tokenomics and Cache Architecture. We have covered the entire spectrum, from basic units of data to advanced infrastructure blueprints.

First, let's recap the three types of tokens. 
Input tokens are your raw prompts, processed in parallel. 
Output tokens are generated sequentially and are much more expensive. 
But the game-changer is Cached Tokens. These are static parts of your history that the model recalls instantly at a ninety percent discount.

On Anthropic's platform, caching is a precision sport. Because models like Claude Sonnet use strict linear prefix matching, even a single extra space at the beginning of your prompt can bust the cache, turning a thirty-cent request into a six-dollar disaster.

We also identified the Disastrous Financial Loop. This is a failure state where a small context window forces frequent micro-compactions. Every time the history is slightly trimmed, the text string changes, causing a total cache miss and forcing you to pay premium 'Cache Write' fees for every single turn.

To defeat this, we've established the Infrastructure Blueprint. 
Step one is the Static Warm-Up Turn. By sending an identical, deterministic prompt in turn one, you seed the Global Base Cache for your entire workspace.
Step two is Decoupled State Injection. You wait until turn two to introduce your dynamic task and session summary.
Step three is the Chunked Compaction Reset. Instead of trimming, you aggressively purge thirty percent of your history and restart with a clean session summary file.

By mastering these architectural patterns—Static Warm-ups, Decoupled Injections, and Chunked Resets—you move from being an AI user to an AI Infrastructure Architect. You ensure that your giant codebase configurations remain a fixed, discounted cost, while your dynamic engineering work remains fast, cheap, and hyper-focused.

This concludes our comprehensive technical session.
"""

audio_path = f"/tmp/master-summary-{uuid4()}.aiff"

print("Synthesizing Master Summary...")
synthesize_aiff_with_say(explanation, audio_path)

print(f"Playing Master Summary from {audio_path}...")
subprocess.run(["afplay", audio_path])
