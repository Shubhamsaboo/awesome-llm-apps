import whisper  # Whisper model for transcribing audio
from moviepy.editor import VideoFileClip  # Correct import

# Optional: Configure moviepy to use ffmpeg from a specific path
import moviepy.config as mp_config

mp_config.change_settings(
    {"FFMPEG_BINARY": "D:/ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe"}
)  # Updated path to ffmpeg.exe


def extract_audio_from_video(video_path):
    video = VideoFileClip(video_path)
    audio_path = video_path.replace(".mp4", ".wav")  # Change extension to .wav
    video.audio.write_audiofile(audio_path)
    print(f"Extracted audio saved to: {audio_path}")  # Debugging line
    return audio_path


def transcribe_audio(audio_path):
    model = whisper.load_model("base")  # You can use a different model size if desired
    result = model.transcribe(audio_path)
    return result["text"]
