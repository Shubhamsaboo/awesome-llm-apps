import asyncio
import random
import curses
import time
import numpy as np
import numpy.typing as npt
import sounddevice as sd
from typing import AsyncGenerator

from agents import Agent, function_tool
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    SingleAgentWorkflowCallbacks,
    VoicePipeline,
)
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions


@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    choices = ["sunny", "cloudy", "rainy", "snowy"]
    return f"The weather in {city} is {random.choice(choices)}."


@function_tool
def get_landmark_info(landmark: str) -> str:
    """Get information about a tourist landmark."""
    landmarks = {
        "eiffel tower": "The Eiffel Tower is a 324-meter wrought-iron lattice tower in Paris, built in 1889.",
        "statue of liberty": "The Statue of Liberty is a colossal neoclassical sculpture in New York Harbor.",
        "taj mahal": "The Taj Mahal is an ivory-white marble mausoleum in Agra, India."
    }
    return landmarks.get(landmark.lower(), f"I don't have information about {landmark}.")


history_expert = Agent(
    name="History Expert",
    handoff_description="A history expert who provides detailed historical context.",
    instructions=prompt_with_handoff_instructions(
        "You are a knowledgeable historian. Provide detailed historical context about landmarks, events, and cultural significance."
    ),
    model="gpt-4o-mini",
)

agent = Agent(
    name="Tour Guide",
    instructions=prompt_with_handoff_instructions(
        """You are a friendly tour guide assistant. Help visitors explore and learn about different locations and landmarks.
        If users ask for detailed historical information, hand off to the history expert."""
    ),
    model="gpt-4o-mini",
    handoffs=[history_expert],
    tools=[get_weather, get_landmark_info],
)


class WorkflowCallbacks(SingleAgentWorkflowCallbacks):
    def on_run(self, workflow: SingleAgentVoiceWorkflow, transcription: str) -> None:
        print(f"Transcribed: {transcription}")


def _record_audio(screen: curses.window) -> npt.NDArray[np.float32]:
    """Record audio using curses interface."""
    screen.nodelay(True)
    screen.clear()
    screen.addstr("Press <spacebar> to start/stop recording\n")
    screen.refresh()

    recording = False
    audio_buffer: list[npt.NDArray[np.float32]] = []

    def _audio_callback(indata, frames, time_info, status):
        if recording:
            audio_buffer.append(indata.copy())

    with sd.InputStream(samplerate=24000, channels=1, dtype=np.float32, callback=_audio_callback):
        while True:
            key = screen.getch()
            if key == ord(" "):
                recording = not recording
                screen.addstr("Recording...\n" if recording else "Stopped.\n")
                screen.refresh()
                if not recording:
                    break
            time.sleep(0.01)

    return np.concatenate(audio_buffer, axis=0) if audio_buffer else np.empty((0,), dtype=np.float32)


def record_audio():
    """Record audio with curses interface."""
    return curses.wrapper(_record_audio)


class AudioPlayer:
    """Audio playback handler."""
    def __enter__(self):
        self.stream = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
        self.stream.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stream.close()

    def add_audio(self, audio_data: npt.NDArray[np.int16]):
        self.stream.write(audio_data)


async def main():
    """Run the tour guide voice agent."""
    pipeline = VoicePipeline(
        workflow=SingleAgentVoiceWorkflow(agent, callbacks=WorkflowCallbacks())
    )

    print("=== Tour Guide Voice Agent ===")
    print("Press Ctrl+C to exit")

    while True:
        try:
            audio_data = record_audio()
            if len(audio_data) == 0:
                continue
                
            result = await pipeline.run(AudioInput(buffer=audio_data))

            with AudioPlayer() as player:
                async for event in result.stream():
                    if event.type == "voice_stream_event_audio":
                        player.add_audio(event.data)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())