"""
Agent definitions for the OpenVoiceUI Voice Pipeline.

Two agents work in sequence after Whisper transcribes the user's voice:
  1. VoiceAssistant  — answers the question, using WebSearch for real-time info
  2. TTSDirector     — writes delivery instructions so the TTS sounds natural
"""

from pydantic import BaseModel
from agents import Agent, WebSearchTool
from agents.model_settings import ModelSettings


# ─────────────────────────────────────────────────────────────
#  Structured output schema
# ─────────────────────────────────────────────────────────────

class AssistantResponse(BaseModel):
    text: str
    """
    The response to speak aloud.
    Natural, conversational language only — no markdown, no bullet points.
    """

    used_web_search: bool
    """True if web search was needed to answer this question."""


# ─────────────────────────────────────────────────────────────
#  Agent 1 — Voice Assistant (STT output → LLM response)
# ─────────────────────────────────────────────────────────────

VOICE_ASSISTANT_INSTRUCTIONS = """
You are a helpful voice AI assistant. Your responses will be spoken aloud, so:

- Write in natural, conversational language — no markdown, lists, or headers.
- Keep responses concise: 2–4 sentences for simple questions, up to 6 for complex ones.
- For questions about current events, news, prices, weather, or real-time data, use web search.
- Be warm and direct — you are heard, not read.

When conversation history is provided, use it to give contextually relevant answers.
"""

voice_assistant_agent = Agent(
    name="VoiceAssistant",
    instructions=VOICE_ASSISTANT_INSTRUCTIONS,
    model="gpt-4o",
    tools=[WebSearchTool()],
    output_type=AssistantResponse,
)


# ─────────────────────────────────────────────────────────────
#  Agent 2 — TTS Director (LLM response → delivery instructions)
# ─────────────────────────────────────────────────────────────

TTS_DIRECTOR_INSTRUCTIONS = """
You are a text-to-speech delivery director.
Given a short text response, write 1–2 sentences of delivery instructions for a TTS model.

Describe:
- Tone (warm, informative, enthusiastic, calm, empathetic, etc.)
- Pacing (measured, brisk, gentle, etc.)
- Any key phrases or words to emphasize

Example: "Speak warmly and at a measured pace. Emphasize the phrase 'right now' in the second sentence."

Keep instructions under 40 words. Focus only on delivery — do not comment on the content.
"""

tts_director_agent = Agent(
    name="TTSDirector",
    instructions=TTS_DIRECTOR_INSTRUCTIONS,
    model="gpt-4o-mini",
)
