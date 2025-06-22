import os
import json
import tempfile
import numpy as np
import librosa
from moviepy import VideoFileClip
from faster_whisper import WhisperModel
from agno.tools import tool
from dotenv import load_dotenv

load_dotenv()

def extract_audio_from_video(video_path: str, output_audio_path: str) -> str:
    """
    Extracts audio from a video file and saves it as an audio file.

    Args:
        video_path: Path to the input video file.
        output_audio_path: Path to save the extracted audio file.

    Returns:
        Path to the extracted audio file.
    """
    video_clip = VideoFileClip(video_path)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_audio_path)
    audio_clip.close()
    video_clip.close()
    return output_audio_path

def load_whisper_model():
    try:
        model = WhisperModel("small", device="cpu", compute_type="int8")
        return model
    except Exception as e:
        print(f"Error loading Whisper model: {e}")
        return None
    
def transcribe_audio(audio_file):
    """
    Transcribe the audio file using faster-whisper.
    
    Returns:
        str: Transcribed text or error/fallback message.
    """
    if not audio_file or not os.path.exists(audio_file):
        return "No audio file exists at the specified path."

    model = load_whisper_model()
    if not model:
        return "Model failed to load. Please check system resources or model path."

    try:
        print("Model loaded successfully. Transcribing audio...")
        segments, _ = model.transcribe(audio_file)
        full_text = " ".join(segment.text for segment in segments)
        return full_text.strip() if full_text else "I couldn't understand the audio. Please try again."

    except Exception as e:
        print(f"Error transcribing audio with faster-whisper: {e}")
        return "I'm having trouble transcribing your audio. Please try again or speak more clearly."

def log_before_call(fc):
    """Pre-hook function that runs before the tool execution"""
    print(f"About to call function with arguments: {fc.arguments}")

def log_after_call(fc):
    """Post-hook function that runs after the tool execution"""
    print(f"Function call completed with result: {fc.result}")

@tool(
    name="analyze_voice_attributes",            # Custom name for the tool (otherwise the function name is used)
    description="Analyzes vocal attributes like clarity, intonation, and pace.",    # Custom description (otherwise the function docstring is used)
    show_result=True,                           # Show result after function call
    stop_after_tool_call=True,                  # Return the result immediately after the tool call and stop the agent
    pre_hook=log_before_call,                   # Hook to run before execution
    post_hook=log_after_call,                   # Hook to run after execution
    cache_results=False,                        # Enable caching of results
    cache_dir="/tmp/agno_cache",                # Custom cache directory
    cache_ttl=3600                              # Cache TTL in seconds (1 hour)
)
def analyze_voice_attributes(file_path: str) -> dict:
    """
    Analyzes vocal attributes in an audio file.

    Args:
        audio_path: The path to the audio file.

    Returns:
        A dictionary containing the transcribed text, speech rate, pitch variation, and volume consistency.
    """

    # Determine file extension
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # If the file is a video, extract audio
    if ext in ['.mp4']:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_audio_file:
            audio_path = extract_audio_from_video(file_path, temp_audio_file.name)
    else:
        audio_path = file_path

    # Transcribe audio
    transcription = transcribe_audio(audio_path)

    # Proceed with analysis using the audio_path
    # Load audio
    y, sr = librosa.load(audio_path, sr=16000)

    words = transcription.split()

    # Calculate speech rate
    duration = librosa.get_duration(y=y, sr=sr)
    speech_rate = len(words) / (duration / 60.0)  # words per minute

    # Pitch variation
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    pitch_values = pitches[magnitudes > np.median(magnitudes)]
    pitch_variation = np.std(pitch_values) if pitch_values.size > 0 else 0

    # Volume consistency
    rms = librosa.feature.rms(y=y)[0]
    volume_consistency = np.std(rms)

    # Clean up temporary audio file if created
    if ext in ['.mp4']:
        os.remove(audio_path)

    return json.dumps({
        "transcription": transcription,
        "speech_rate_wpm": str(round(speech_rate, 2)),
        "pitch_variation": str(round(pitch_variation, 2)),
        "volume_consistency": str(round(volume_consistency, 4))
    })