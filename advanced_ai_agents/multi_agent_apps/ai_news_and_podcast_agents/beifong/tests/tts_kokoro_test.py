import os
import soundfile as sf
import platform
import time
import warnings


os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

from kokoro import KPipeline


def play_audio(file_path):
    system = platform.system()
    try:
        if system == "Darwin":
            os.system(f"afplay {file_path}")
        elif system == "Linux":
            os.system(f"aplay {file_path}")
        elif system == "Windows":
            os.system(f'start "" "{file_path}"')
        else:
            print(f"Audio saved to {file_path} (auto-play not supported on this system)")
    except Exception as e:
        print(f"Failed to auto-play audio: {e}")
        print(f"Audio saved to {file_path}")


print("Testing Kokoro TTS in English and Hindi...")

print("\n=== Testing English ===")
pipeline_en = KPipeline(lang_code="a")
english_text = "This is a test of the Kokoro text-to-speech system in English."
generator_en = pipeline_en(english_text, voice="af_heart")

for i, (gs, ps, audio) in enumerate(generator_en):
    output_file = f"english_sample_{i}.wav"
    sf.write(output_file, audio, 24000)
    print(f"Generated English audio: {output_file}")
    print(f"Text: {gs}")
    play_audio(output_file)
    time.sleep(2)

print("\n=== Testing Hindi ===")
pipeline_hi = KPipeline(lang_code="h")
hindi_text = "यह हिंदी में कोकोरो टेक्स्ट-टू-स्पीच सिस्टम का एक परीक्षण है।"
generator_hi = pipeline_hi(hindi_text, voice="af_heart")

for i, (gs, ps, audio) in enumerate(generator_hi):
    output_file = f"hindi_sample_{i}.wav"
    sf.write(output_file, audio, 24000)
    print(f"Generated Hindi audio: {output_file}")
    print(f"Text: {gs}")
    play_audio(output_file)
    time.sleep(2)

print("\nTest completed. Audio files have been generated and should have auto-played.")
