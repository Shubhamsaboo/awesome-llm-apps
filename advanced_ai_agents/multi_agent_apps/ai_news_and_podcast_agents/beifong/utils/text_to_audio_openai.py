import os
from typing import List, Optional, Tuple, Dict, Any
import tempfile
import numpy as np
import soundfile as sf
from openai import OpenAI
from utils.load_api_keys import load_api_key

OPENAI_VOICES = {1: "alloy", 2: "echo", 3: "fable", 4: "onyx", 5: "nova", 6: "shimmer"}
DEFAULT_VOICE_MAP = {1: "alloy", 2: "nova"}
TEXT_TO_SPEECH_MODEL = "gpt-4o-mini-tts"


def create_silence_audio(silence_duration: float, sampling_rate: int) -> np.ndarray:
    if sampling_rate <= 0:
        print(f"WARNING: Invalid sampling rate ({sampling_rate}) for silence generation")
        return np.zeros(0, dtype=np.float32)
    return np.zeros(int(sampling_rate * silence_duration), dtype=np.float32)


def combine_audio_segments(audio_segments: List[np.ndarray], silence_duration: float, sampling_rate: int) -> np.ndarray:
    if not audio_segments:
        return np.zeros(0, dtype=np.float32)
    silence = create_silence_audio(silence_duration, sampling_rate)
    combined_segments = []
    for i, segment in enumerate(audio_segments):
        combined_segments.append(segment)
        if i < len(audio_segments) - 1:
            combined_segments.append(silence)
    combined = np.concatenate(combined_segments)
    max_amp = np.max(np.abs(combined))
    if max_amp > 0:
        combined = combined / max_amp * 0.95
    return combined


def text_to_speech_openai(
    client: OpenAI,
    text: str,
    speaker_id: int,
    voice_map: Dict[int, str] = None,
    model: str = TEXT_TO_SPEECH_MODEL,
) -> Optional[Tuple[np.ndarray, int]]:
    if not text.strip():
        print("WARNING: Empty text provided, skipping TTS generation")
        return None
    voice_map = voice_map or DEFAULT_VOICE_MAP
    voice = voice_map.get(speaker_id)
    if not voice:
        if speaker_id in OPENAI_VOICES:
            voice = OPENAI_VOICES[speaker_id]
        else:
            voice = next(iter(voice_map.values()), "alloy")
        print(f"WARNING: No voice mapping for speaker {speaker_id}, using {voice}")
    try:
        print(f"INFO: Generating TTS for speaker {speaker_id} using voice '{voice}'")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3",
        )
        audio_data = response.content
        if not audio_data:
            print("ERROR: OpenAI TTS returned empty response")
            return None
        print(f"INFO: Received {len(audio_data)} bytes from OpenAI TTS")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_data)
        try:
            from pydub import AudioSegment

            audio_segment = AudioSegment.from_mp3(temp_path)
            channels = audio_segment.channels
            sample_width = audio_segment.sample_width
            frame_rate = audio_segment.frame_rate
            samples = np.array(audio_segment.get_array_of_samples())
            if channels == 2:
                samples = samples.reshape(-1, 2).mean(axis=1)
            max_possible_value = float(2 ** (8 * sample_width - 1))
            samples = samples.astype(np.float32) / max_possible_value
            os.unlink(temp_path)
            return samples, frame_rate
        except ImportError:
            print("WARNING: Pydub not available, falling back to soundfile")
        except Exception as e:
            print(f"ERROR: Pydub processing failed: {e}")
        try:
            audio_np, samplerate = sf.read(temp_path)
            os.unlink(temp_path)
            return audio_np, samplerate
        except Exception as e:
            print(f"ERROR: Failed to process audio with soundfile: {e}")
            try:
                from pydub import AudioSegment

                sound = AudioSegment.from_mp3(temp_path)
                wav_path = temp_path.replace(".mp3", ".wav")
                sound.export(wav_path, format="wav")
                audio_np, samplerate = sf.read(wav_path)
                os.unlink(temp_path)
                os.unlink(wav_path)
                return audio_np, samplerate
            except Exception as e:
                print(f"ERROR: All audio processing methods failed: {e}")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return None

    except Exception as e:
        print(f"ERROR: OpenAI TTS API error: {e}")
        import traceback

        traceback.print_exc()
        return None


def create_podcast(
    script: Any,
    output_path: str,
    silence_duration: float = 0.7,
    sampling_rate: int = 24000,
    lang_code: str = "en",
    model: str = TEXT_TO_SPEECH_MODEL,
    voice_map: Dict[int, str] = None,
    api_key: str = None,
) -> Optional[str]:
    try:
        if not api_key:
            api_key = load_api_key()
            if not api_key:
                print("ERROR: No OpenAI API key provided")
                return None
        client = OpenAI(api_key=api_key)
        print("INFO: OpenAI client initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize OpenAI client: {e}")
        return None
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if voice_map is None:
        voice_map = DEFAULT_VOICE_MAP.copy()
    model_to_use = model
    if model == "tts-1" and lang_code == "en":
        model_to_use = "tts-1-hd"
        print(f"INFO: Using high-definition TTS model for English: {model_to_use}")
    generated_segments = []
    sampling_rate_detected = None
    entries = script.entries if hasattr(script, "entries") else script
    print(f"INFO: Processing {len(entries)} script entries")
    for i, entry in enumerate(entries):
        if hasattr(entry, "speaker"):
            speaker_id = entry.speaker
            entry_text = entry.text
        else:
            speaker_id = entry["speaker"]
            entry_text = entry["text"]
        print(f"INFO: Processing entry {i + 1}/{len(entries)}: Speaker {speaker_id}")
        result = text_to_speech_openai(
            client=client,
            text=entry_text,
            speaker_id=speaker_id,
            voice_map=voice_map,
            model=model_to_use,
        )
        if result:
            segment_audio, segment_rate = result
            if sampling_rate_detected is None:
                sampling_rate_detected = segment_rate
                print(f"INFO: Using sample rate: {sampling_rate_detected} Hz")
            elif sampling_rate_detected != segment_rate:
                print(f"WARNING: Sample rate mismatch: {sampling_rate_detected} vs {segment_rate}")
                try:
                    import librosa

                    segment_audio = librosa.resample(segment_audio, orig_sr=segment_rate, target_sr=sampling_rate_detected)
                    print(f"INFO: Resampled to {sampling_rate_detected} Hz")
                except ImportError:
                    sampling_rate_detected = segment_rate
                    print(f"WARNING: Librosa not available for resampling, using {segment_rate} Hz")
                except Exception as e:
                    print(f"ERROR: Resampling failed: {e}")
            generated_segments.append(segment_audio)
        else:
            print(f"WARNING: Failed to generate audio for entry {i + 1}")
    if not generated_segments:
        print("ERROR: No audio segments were generated")
        return None
    if sampling_rate_detected is None:
        print("ERROR: Could not determine sample rate")
        return None
    print(f"INFO: Combining {len(generated_segments)} audio segments")
    full_audio = combine_audio_segments(generated_segments, silence_duration, sampling_rate_detected)
    if full_audio.size == 0:
        print("ERROR: Combined audio is empty")
        return None
    print(f"INFO: Writing audio to {output_path}")
    try:
        sf.write(output_path, full_audio, sampling_rate_detected)
    except Exception as e:
        print(f"ERROR: Failed to write audio file: {e}")
        return None
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"INFO: Audio file created: {output_path} ({file_size / 1024:.1f} KB)")
        return output_path
    else:
        print(f"ERROR: Failed to create audio file at {output_path}")
        return None
