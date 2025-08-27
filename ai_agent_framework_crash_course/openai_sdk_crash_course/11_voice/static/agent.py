import asyncio
import random

import numpy as np

from agents import Agent, function_tool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.voice import (
    AudioInput,
    SingleAgentVoiceWorkflow,
    SingleAgentWorkflowCallbacks,
    VoicePipeline,
)

from .util import AudioPlayer, record_audio

"""
This is a simple example that uses a recorded audio buffer. Run it via:
`python -m ai_agent_framework_crash_course.openai_sdk_crash_course.11_voice.static.agent`

1. You can record an audio clip in the terminal.
2. The pipeline automatically transcribes the audio.
3. The agent workflow is a simple one that starts at the Assistant agent.
4. The output of the agent is streamed to the audio player.

Try examples like:
- Tell me a joke (will respond with a joke)
- What's the weather in Tokyo? (will call the `get_weather` tool and then speak)
- Hola, como estas? (will handoff to the spanish agent)
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
def calculate_tip(bill_amount: float, tip_percentage: float = 15.0) -> str:
    """Calculate tip amount for a bill."""
    tip_amount = bill_amount * (tip_percentage / 100)
    total_amount = bill_amount + tip_amount
    print(f"[debug] calculate_tip called with bill: ${bill_amount}, tip: {tip_percentage}%")
    return f"For a bill of ${bill_amount:.2f} with {tip_percentage}% tip, the tip is ${tip_amount:.2f} and total is ${total_amount:.2f}."


spanish_agent = Agent(
    name="Spanish",
    handoff_description="A spanish speaking agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. Speak in Spanish only. "
        "Help with weather, time, and calculations as needed."
    ),
    model="gpt-4o-mini",
    tools=[get_weather, get_time, calculate_tip]
)

french_agent = Agent(
    name="French",
    handoff_description="A french speaking agent.",
    instructions=prompt_with_handoff_instructions(
        "You're speaking to a human, so be polite and concise. Speak in French only. "
        "Help with weather, time, and calculations as needed."
    ),
    model="gpt-4o-mini",
    tools=[get_weather, get_time, calculate_tip]
)

agent = Agent(
    name="Assistant",
    instructions=prompt_with_handoff_instructions(
        """You're speaking to a human, so be polite and concise. 
        
        You can help with:
        - Weather information for any city
        - Current time
        - Tip calculations
        - General conversation and jokes
        
        Language handling:
        - If the user speaks in Spanish, handoff to the Spanish agent
        - If the user speaks in French, handoff to the French agent
        - Otherwise, respond in English
        
        Keep responses conversational and friendly for voice interaction."""
    ),
    model="gpt-4o-mini",
    handoffs=[spanish_agent, french_agent],
    tools=[get_weather, get_time, calculate_tip],
)


class WorkflowCallbacks(SingleAgentWorkflowCallbacks):
    """Custom callbacks to monitor the voice workflow."""
    
    def on_run(self, workflow: SingleAgentVoiceWorkflow, transcription: str) -> None:
        """Called when the workflow runs with a new transcription."""
        print(f"[debug] 🎯 Workflow running with transcription: '{transcription}'")
    
    def on_tool_call(self, tool_name: str, arguments: dict) -> None:
        """Called when a tool is about to be executed."""
        print(f"[debug] 🔧 Tool call: {tool_name} with args: {arguments}")
    
    def on_handoff(self, from_agent: str, to_agent: str) -> None:
        """Called when a handoff occurs between agents."""
        print(f"[debug] 🔄 Handoff from {from_agent} to {to_agent}")


async def main():
    """Main function to run the static voice agent example."""
    print("🎙️ Static Voice Agent Demo")
    print("=" * 50)
    print()
    
    # Create the voice pipeline with our agent and callbacks
    pipeline = VoicePipeline(
        workflow=SingleAgentVoiceWorkflow(agent, callbacks=WorkflowCallbacks())
    )
    
    print("This demo will:")
    print("1. 🎤 Record your voice for a few seconds")
    print("2. 🔄 Transcribe your speech to text")
    print("3. 🤖 Process with AI agent")
    print("4. 🔊 Convert response back to speech")
    print()
    
    # Record audio input
    try:
        audio_buffer = record_audio(duration=5.0)
        print(f"📊 Recorded {len(audio_buffer)} audio samples")
        
        # Create audio input for the pipeline
        audio_input = AudioInput(buffer=audio_buffer)
        
        # Run the voice pipeline
        print("\n🔄 Processing with voice pipeline...")
        result = await pipeline.run(audio_input)
        
        # Play the result audio
        print("🔊 Playing AI response...")
        
        with AudioPlayer() as player:
            audio_chunks_received = 0
            lifecycle_events = 0
            
            async for event in result.stream():
                if event.type == "voice_stream_event_audio":
                    player.add_audio(event.data)
                    audio_chunks_received += 1
                    if audio_chunks_received % 10 == 0:  # Progress indicator
                        print(f"🎵 Received {audio_chunks_received} audio chunks...")
                
                elif event.type == "voice_stream_event_lifecycle":
                    lifecycle_events += 1
                    print(f"📋 Lifecycle event: {event.event}")
                
                elif event.type == "voice_stream_event_error":
                    print(f"❌ Error event: {event.error}")
            
            # Add 1 second of silence to ensure the audio finishes playing
            print("🔇 Adding silence buffer...")
            player.add_audio(np.zeros(24000 * 1, dtype=np.int16))
            
            print(f"\n✅ Voice interaction complete!")
            print(f"📊 Statistics:")
            print(f"   - Audio chunks played: {audio_chunks_received}")
            print(f"   - Lifecycle events: {lifecycle_events}")
    
    except KeyboardInterrupt:
        print("\n⏹️ Demo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


def demo_with_examples():
    """Run multiple example scenarios for demonstration."""
    examples = [
        "Tell me a joke",
        "What's the weather in New York?",
        "What time is it?",
        "Calculate a 20% tip on a $50 bill",
        "Hola, como estas?",  # Spanish handoff
        "Bonjour, comment allez-vous?"  # French handoff
    ]
    
    print("🎭 Demo Examples:")
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example}")
    print()
    print("You can try saying any of these examples when recording!")


if __name__ == "__main__":
    print("🚀 OpenAI Agents SDK - Static Voice Demo")
    print("=" * 60)
    
    # Show example prompts
    demo_with_examples()
    
    # Run the main demo
    asyncio.run(main())
