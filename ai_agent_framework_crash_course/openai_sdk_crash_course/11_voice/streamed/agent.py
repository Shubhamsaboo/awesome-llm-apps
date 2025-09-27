import asyncio
import random
import threading
import time

import numpy as np

from agents import Agent, function_tool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.voice import (
    StreamedAudioInput,
    SingleAgentVoiceWorkflow,
    SingleAgentWorkflowCallbacks,
    VoicePipeline,
)

from .util import AudioPlayer, StreamedAudioRecorder, create_silence

"""
This is a streaming voice example that processes audio in real-time. Run it via:
`python -m ai_agent_framework_crash_course.openai_sdk_crash_course.11_voice.streamed.agent`

1. The pipeline continuously listens for audio input.
2. It automatically detects when you start and stop speaking.
3. The agent workflow processes speech in real-time.
4. The output is streamed back to you as audio.

This example demonstrates:
- Real-time speech detection and processing
- Streaming audio input and output
- Activity detection for turn-based conversation
- Interruption handling and turn management

Try examples like:
- Start speaking and the agent will respond when you finish
- Try multiple turns of conversation
- Test language handoffs with Spanish or French
"""


@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a given city."""
    print(f"[debug] get_weather called with city: {city}")
    choices = ["sunny", "cloudy", "rainy", "snowy"]
    return f"The weather in {city} is {random.choice(choices)}."


@function_tool
def get_time() -> str:
    """Get the current time."""
    import datetime
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    print(f"[debug] get_time called, current time: {current_time}")
    return f"The current time is {current_time}."


@function_tool
def set_reminder(message: str, minutes: int = 5) -> str:
    """Set a simple reminder (demo function)."""
    print(f"[debug] set_reminder called: '{message}' in {minutes} minutes")
    return f"Reminder set: '{message}' in {minutes} minutes. (This is a demo - no actual reminder will be triggered)"


@function_tool
def get_news_summary() -> str:
    """Get a brief news summary (demo function)."""
    print("[debug] get_news_summary called")
    # Mock news items
    news_items = [
        "Technology stocks continue to rise amid AI developments",
        "Climate change summit reaches new international agreements",
        "Space exploration mission launches successfully",
        "New renewable energy projects announced globally"
    ]
    selected_news = random.choice(news_items)
    return f"Here's a news update: {selected_news}. This is a demo news summary."


spanish_agent = Agent(
    name="Spanish",
    handoff_description="A spanish speaking agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human in real-time, so be polite and concise. Speak in Spanish only. "
        "Help with weather, time, reminders, and news as needed. Keep responses brief for voice interaction."
    ),
    model="gpt-4o-mini",
    tools=[get_weather, get_time, set_reminder, get_news_summary]
)

french_agent = Agent(
    name="French", 
    handoff_description="A french speaking agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human in real-time, so be polite and concise. Speak in French only. "
        "Help with weather, time, reminders, and news as needed. Keep responses brief for voice interaction."
    ),
    model="gpt-4o-mini",
    tools=[get_weather, get_time, set_reminder, get_news_summary]
)

agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions(
        """You're speaking to a human in real-time voice conversation, so be polite and concise.
        
        You can help with:
        - Weather information for any city
        - Current time
        - Setting reminders (demo)
        - News summaries (demo)
        - General conversation
        
        Language handling:
        - If the user speaks in Spanish, handoff to the Spanish agent
        - If the user speaks in French, handoff to the French agent
        - Otherwise, respond in English
        
        Keep responses brief and conversational since this is a voice interface.
        Acknowledge when users switch topics or ask follow-up questions."""
    ),
    model="gpt-4o-mini",
    handoffs=[spanish_agent, french_agent],
    tools=[get_weather, get_time, set_reminder, get_news_summary],
)


class StreamingWorkflowCallbacks(SingleAgentWorkflowCallbacks):
    """Custom callbacks to monitor the streaming voice workflow."""
    
    def __init__(self):
        self.turn_count = 0
        self.start_time = time.time()
    
    def on_run(self, workflow: SingleAgentVoiceWorkflow, transcription: str) -> None:
        """Called when the workflow runs with a new transcription."""
        self.turn_count += 1
        print(f"\n[debug] 🎯 Turn {self.turn_count} - Transcription: '{transcription}'")
    
    def on_tool_call(self, tool_name: str, arguments: dict) -> None:
        """Called when a tool is about to be executed."""
        print(f"[debug] 🔧 Tool call: {tool_name} with args: {arguments}")
    
    def on_handoff(self, from_agent: str, to_agent: str) -> None:
        """Called when a handoff occurs between agents."""
        print(f"[debug] 🔄 Handoff from {from_agent} to {to_agent}")
    
    def on_turn_start(self) -> None:
        """Called when a new turn starts."""
        elapsed = time.time() - self.start_time
        print(f"[debug] ▶️ Turn started (session time: {elapsed:.1f}s)")
    
    def on_turn_end(self) -> None:
        """Called when a turn ends."""
        print(f"[debug] ⏹️ Turn ended")


class VoiceSessionManager:
    """Manages the voice session state and audio streams."""
    
    def __init__(self):
        self.is_running = False
        self.audio_player = None
        self.pipeline = None
        self.callbacks = StreamingWorkflowCallbacks()
        self._stop_event = threading.Event()
    
    async def start_session(self):
        """Start the voice session."""
        self.is_running = True
        self._stop_event.clear()
        
        # Create the voice pipeline
        self.pipeline = VoicePipeline(
            workflow=SingleAgentVoiceWorkflow(agent, callbacks=self.callbacks)
        )
        
        print("🎙️ Voice session started. Start speaking...")
        print("💡 Tips:")
        print("   - Speak clearly and pause between sentences")
        print("   - Try asking about weather, time, or setting reminders")
        print("   - Say something in Spanish or French to test language handoffs")
        print("   - Press Ctrl+C to end the session")
        print()
        
        # Start audio recording and processing
        await self._run_streaming_session()
    
    async def _run_streaming_session(self):
        """Run the main streaming session loop."""
        with StreamedAudioRecorder() as recorder:
            with AudioPlayer() as player:
                self.audio_player = player
                
                # Create streamed audio input
                streamed_input = StreamedAudioInput()
                
                # Start the pipeline processing
                result = await self.pipeline.run(streamed_input)
                
                # Create tasks for audio input and output processing
                input_task = asyncio.create_task(self._process_audio_input(recorder, streamed_input))
                output_task = asyncio.create_task(self._process_audio_output(result))
                
                try:
                    # Run both tasks concurrently
                    await asyncio.gather(input_task, output_task)
                except asyncio.CancelledError:
                    print("\n🛑 Session cancelled")
                finally:
                    # Cleanup
                    streamed_input.finish()
                    self.is_running = False
    
    async def _process_audio_input(self, recorder: StreamedAudioRecorder, streamed_input: StreamedAudioInput):
        """Process incoming audio from the microphone."""
        print("🎤 Listening for audio input...")
        
        while self.is_running and not self._stop_event.is_set():
            if recorder.has_audio():
                audio_chunk = recorder.get_audio_chunk()
                if audio_chunk is not None:
                    # Push audio to the pipeline
                    streamed_input.push_audio(audio_chunk)
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.01)
        
        print("⏹️ Audio input processing stopped")
    
    async def _process_audio_output(self, result):
        """Process outgoing audio to the speakers."""
        print("🔊 Ready to play audio responses...")
        
        audio_chunks_count = 0
        
        async for event in result.stream():
            if self._stop_event.is_set():
                break
                
            if event.type == "voice_stream_event_audio":
                if self.audio_player:
                    self.audio_player.add_audio(event.data)
                    audio_chunks_count += 1
                    
                    # Progress indicator for long responses
                    if audio_chunks_count % 20 == 0:
                        print(f"🎵 Playing response... ({audio_chunks_count} chunks)")
            
            elif event.type == "voice_stream_event_lifecycle":
                if event.event == "turn_started":
                    print("🔄 AI is processing your speech...")
                elif event.event == "turn_ended":
                    print("✅ AI response complete. You can speak again.")
                    # Add a small silence buffer between turns
                    if self.audio_player:
                        self.audio_player.add_audio(create_silence(0.5))
            
            elif event.type == "voice_stream_event_error":
                print(f"❌ Voice error: {event.error}")
        
        print("⏹️ Audio output processing stopped")
    
    def stop_session(self):
        """Stop the voice session."""
        self.is_running = False
        self._stop_event.set()
        print("\n🛑 Stopping voice session...")


async def main():
    """Main function to run the streamed voice agent example."""
    print("🎙️ Streaming Voice Agent Demo")
    print("=" * 50)
    print()
    
    session_manager = VoiceSessionManager()
    
    try:
        await session_manager.start_session()
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user.")
        session_manager.stop_session()
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Voice session ended. Thanks for trying the demo!")


def show_streaming_features():
    """Display information about streaming voice features."""
    print("🌊 Streaming Voice Features:")
    print("=" * 40)
    print()
    print("✨ Real-time Features:")
    print("  • Continuous audio input processing")
    print("  • Automatic speech activity detection")
    print("  • Real-time agent response streaming")
    print("  • Turn-based conversation management")
    print()
    print("🔧 Advanced Capabilities:")
    print("  • Multi-language support with agent handoffs")
    print("  • Tool calling during voice conversation")
    print("  • Streaming callbacks for monitoring")
    print("  • Interruption handling (via lifecycle events)")
    print()
    print("🎯 Try These Commands:")
    print("  • 'What's the weather in Paris?'")
    print("  • 'What time is it?'")
    print("  • 'Set a reminder to call mom in 10 minutes'")
    print("  • 'Give me a news summary'")
    print("  • 'Hola, ¿cómo estás?' (Spanish)")
    print("  • 'Bonjour, comment ça va?' (French)")
    print()


if __name__ == "__main__":
    print("🚀 OpenAI Agents SDK - Streaming Voice Demo")
    print("=" * 60)
    
    # Show streaming features
    show_streaming_features()
    
    # Run the main demo
    asyncio.run(main())
