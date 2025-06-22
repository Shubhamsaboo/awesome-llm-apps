from agno.agent import Agent, RunResponse
from agno.agent import Agent
from agno.models.together import Together
from agents.tools.voice_analysis_tool import analyze_voice_attributes as voice_analysis_tool
from agno.utils.pprint import pprint_run_response
from dotenv import load_dotenv
import os

load_dotenv()

# Define the voice analysis agent
voice_analysis_agent = Agent(
    name="voice-analysis-agent",
    model=Together(id="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", api_key=os.getenv("TOGETHER_API_KEY")),
    tools=[voice_analysis_tool],
    description="""
        You are a voice analysis agent that evaluates vocal attributes like clarity, intonation, and pace.
        You will return the transcribed text, speech rate, pitch variation, and volume consistency.
    """,
    instructions=[
        "You will be provided with an audio file of a person speaking.",
        "Your task is to analyze the vocal attributes in the audio to detect speech rate, pitch variation, and volume consistency.",
        "The response MUST be in the following JSON format:",
        "{",
            '"transcription": [transcription]',
            '"speech_rate_wpm": [speech_rate_wpm],',
            '"pitch_variation": [pitch_variation],',
            '"volume_consistency": [volume_consistency]',
        "}",
        "The response MUST be in proper JSON format with keys and values in double quotes.",
        "The final response MUST not include any other text or anything else other than the JSON response."
    ],
    markdown=True,
    show_tool_calls=True,
    debug_mode=True
)

# audio = "../../videos/my_video.mp4"
# prompt = f"Analyze vocal attributes in the audio file to detect speech rate, pitch variation, and volume consistency in the following audio: {audio}"
# voice_analysis_agent.print_response(prompt, stream=True)

# # Run agent and return the response as a variable
# response: RunResponse = voice_analysis_agent.run(prompt)
# # Print the response in markdown format
# pprint_run_response(response, markdown=True)