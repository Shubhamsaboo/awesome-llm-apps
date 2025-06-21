from agno.agent import Agent
import os
from datetime import datetime
import tempfile
import numpy as np
import soundfile as sf
from typing import Any, Dict, List, Optional, Tuple
from utils.load_api_keys import load_api_key
from openai import OpenAI
from scipy import signal


PODCASTS_FOLDER = "podcasts"
PODCAST_AUDIO_FOLDER = os.path.join(PODCASTS_FOLDER, "audio")
PODCAST_MUSIC_FOLDER = os.path.join('static', "musics")
OPENAI_VOICES = {1: "alloy", 2: "echo", 3: "fable", 4: "onyx", 5: "nova", 6: "shimmer"}
DEFAULT_VOICE_MAP = {1: "alloy", 2: "nova"}
TTS_MODEL = "gpt-4o-mini-tts"
INTRO_MUSIC_FILE = os.path.join(PODCAST_MUSIC_FOLDER, "intro_audio.mp3")
OUTRO_MUSIC_FILE = os.path.join(PODCAST_MUSIC_FOLDER, "intro_audio.mp3")


def resample_audio_scipy(audio, original_sr, target_sr):
    if original_sr == target_sr:
        return audio
    resampling_ratio = target_sr / original_sr
    num_samples = int(len(audio) * resampling_ratio)
    resampled = signal.resample(audio, num_samples)
    return resampled


def create_silence_audio(silence_duration: float, sampling_rate: int) -> np.ndarray:
    if sampling_rate <= 0:
        print(f"Invalid sampling rate ({sampling_rate}) for silence generation")
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


def process_audio_file(temp_path: str) -> Optional[Tuple[np.ndarray, int]]:
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
        return samples, frame_rate
    except ImportError:
        print("Pydub not available, falling back to soundfile")
    except Exception as e:
        print(f"Pydub processing failed: {e}")
    try:
        audio_np, samplerate = sf.read(temp_path)
        return audio_np, samplerate
    except Exception as e:
        print(f"Failed to process audio with soundfile: {e}")
        try:
            from pydub import AudioSegment

            sound = AudioSegment.from_mp3(temp_path)
            wav_path = temp_path.replace(".mp3", ".wav")
            sound.export(wav_path, format="wav")
            audio_np, samplerate = sf.read(wav_path)
            os.unlink(wav_path)
            return audio_np, samplerate
        except Exception as e:
            print(f"All audio processing methods failed: {e}")
    return None


def resample_audio(audio, orig_sr, target_sr):
    try:
        import librosa

        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    except ImportError:
        print("Librosa not available for resampling")
        return audio
    except Exception as e:
        print(f"Resampling failed: {e}")
        return audio


def text_to_speech_openai(
    client: OpenAI,
    text: str,
    speaker_id: int,
    voice_map: Dict[int, str] = None,
    model: str = TTS_MODEL,
) -> Optional[Tuple[np.ndarray, int]]:
    if not text.strip():
        print("Empty text provided, skipping TTS generation")
        return None
    voice_map = voice_map or DEFAULT_VOICE_MAP
    voice = voice_map.get(speaker_id)
    if not voice:
        if speaker_id in OPENAI_VOICES:
            voice = OPENAI_VOICES[speaker_id]
        else:
            voice = next(iter(voice_map.values()), "alloy")
        print(f"No voice mapping for speaker {speaker_id}, using {voice}")
    try:
        print(f"Generating TTS for speaker {speaker_id} using voice '{voice}'")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3",
        )
        audio_data = response.content
        if not audio_data:
            print("OpenAI TTS returned empty response")
            return None
        print(f"Received {len(audio_data)} bytes from OpenAI TTS")
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = temp_file.name
        temp_file.close()
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        try:
            return process_audio_file(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        print(f"OpenAI TTS API error: {e}")
        import traceback

        traceback.print_exc()
        return None


def create_podcast(
    script: Any,
    output_path: str,
    tts_engine: str = "openai",
    language_code: str = "en",
    silence_duration: float = 0.7,
    voice_map: Dict[int, str] = None,
    model: str = TTS_MODEL,
) -> Optional[str]:
    if tts_engine.lower() != "openai":
        print(f"Only OpenAI TTS engine is available in this standalone version. Requested: {tts_engine}")
        return None
    try:
        api_key = load_api_key("OPENAI_API_KEY")
        if not api_key:
            print("No OpenAI API key provided")
            return None
        client = OpenAI(api_key=api_key)
        print("OpenAI client initialized")
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {e}")
        return None
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if voice_map is None:
        voice_map = DEFAULT_VOICE_MAP.copy()
    model_to_use = model
    if model == "tts-1" and language_code == "en":
        model_to_use = "tts-1-hd"
        print(f"Using high-definition TTS model for English: {model_to_use}")
    generated_segments = []
    sampling_rate_detected = None

    if hasattr(script, "entries"):
        entries = script.entries
    else:
        entries = script

    print(f"Processing {len(entries)} script entries")
    for i, entry in enumerate(entries):
        if hasattr(entry, "speaker"):
            speaker_id = entry.speaker
            entry_text = entry.text
        else:
            speaker_id = entry["speaker"]
            entry_text = entry["text"]
        print(f"Processing entry {i + 1}/{len(entries)}: Speaker {speaker_id}")
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
                print(f"Using sample rate: {sampling_rate_detected} Hz")
            elif sampling_rate_detected != segment_rate:
                print(f"Sample rate mismatch: {sampling_rate_detected} vs {segment_rate}")
                try:
                    segment_audio = resample_audio(segment_audio, segment_rate, sampling_rate_detected)
                    print(f"Resampled to {sampling_rate_detected} Hz")
                except Exception as e:
                    sampling_rate_detected = segment_rate
                    print(f"Resampling failed: {e}")
            generated_segments.append(segment_audio)
        else:
            print(f"Failed to generate audio for entry {i + 1}")
    if not generated_segments:
        print("No audio segments were generated")
        return None
    if sampling_rate_detected is None:
        print("Could not determine sample rate")
        return None
    print(f"Combining {len(generated_segments)} audio segments")
    full_audio = combine_audio_segments(generated_segments, silence_duration, sampling_rate_detected)
    if full_audio.size == 0:
        print("Combined audio is empty")
        return None

    try:
        if os.path.exists(INTRO_MUSIC_FILE):
            intro_music, intro_sr = sf.read(INTRO_MUSIC_FILE)
            print(f"Loaded intro music: {len(intro_music) / intro_sr:.1f} seconds")

            if intro_music.ndim == 2:
                intro_music = np.mean(intro_music, axis=1)

            if intro_sr != sampling_rate_detected:
                intro_music = resample_audio_scipy(intro_music, intro_sr, sampling_rate_detected)

            full_audio = np.concatenate([intro_music, full_audio])
            print("Added intro music")

        if os.path.exists(OUTRO_MUSIC_FILE):
            outro_music, outro_sr = sf.read(OUTRO_MUSIC_FILE)
            print(f"Loaded outro music: {len(outro_music) / outro_sr:.1f} seconds")

            if outro_music.ndim == 2:
                outro_music = np.mean(outro_music, axis=1)

            if outro_sr != sampling_rate_detected:
                outro_music = resample_audio_scipy(outro_music, outro_sr, sampling_rate_detected)

            full_audio = np.concatenate([full_audio, outro_music])
            print("Added outro music")

    except Exception as e:
        print(f"Could not add intro/outro music: {e}")
        print("Continuing without background music")

    print(f"Writing audio to {output_path}")
    try:
        sf.write(output_path, full_audio, sampling_rate_detected)
    except Exception as e:
        print(f"Failed to write audio file: {e}")
        return None
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"Audio file created: {output_path} ({file_size / 1024:.1f} KB)")
        return output_path
    else:
        print(f"Failed to create audio file at {output_path}")
        return None


def audio_generate_agent_run(agent: Agent) -> str:
    """
    Generate an audio file for the podcast using the selected TTS engine.

    Args:
        agent: The agent instance

    Returns:
        A message with the result of audio generation
    """
    from services.internal_session_service import SessionService

    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    session_state = session["state"]
    script_data = session_state.get("generated_script", {})
    if not script_data or (isinstance(script_data, dict) and not script_data.get("sections")):
        error_msg = "Cannot generate audio: No podcast script data found. Please generate a script first."
        print(error_msg)
        return error_msg
    if isinstance(script_data, dict):
        podcast_title = script_data.get("title", "Your Podcast")
    else:
        podcast_title = "Your Podcast"
    session_state["stage"] = "audio"
    audio_dir = PODCAST_AUDIO_FOLDER
    audio_filename = f"podcast_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    audio_path = os.path.join(audio_dir, audio_filename)
    try:
        if isinstance(script_data, dict) and "sections" in script_data:
            speaker_map = {"ALEX": 1, "MORGAN": 2}
            script_entries = []
            for section in script_data.get("sections", []):
                for dialog in section.get("dialog", []):
                    speaker = dialog.get("speaker", "ALEX")
                    text = dialog.get("text", "")

                    if text and speaker in speaker_map:
                        script_entries.append({"text": text, "speaker": speaker_map[speaker]})
            if not script_entries:
                error_msg = "Cannot generate audio: No dialog found in the script."
                print(error_msg)
                return error_msg

            selected_language = session_state.get("selected_language", {"code": "en", "name": "English"})
            language_code = selected_language.get("code", "en")
            language_name = selected_language.get("name", "English")
            tts_engine = "openai"
            if tts_engine == "openai" and not load_api_key("OPENAI_API_KEY"):
                error_msg = "Cannot generate audio: OpenAI API key not found."
                print(error_msg)
                return error_msg
            print(f"Generating podcast audio using {tts_engine} TTS engine in {language_name} language")
            full_audio_path = create_podcast(
                script=script_entries,
                output_path=audio_path,
                tts_engine=tts_engine,
                language_code=language_code,
            )
            if not full_audio_path:
                error_msg = f"Failed to generate podcast audio with {tts_engine} TTS engine."
                print(error_msg)
                return error_msg

            audio_url = f"{os.path.basename(full_audio_path)}"
            session_state["audio_url"] = audio_url
            session_state["show_audio_for_confirmation"] = True
            SessionService.save_session(session_id, session_state)
            print(f"Successfully generated podcast audio: {full_audio_path}")
            return f"I've generated the audio for your '{podcast_title}' podcast using {tts_engine.capitalize()} voices in {language_name}. You can listen to it in the player below. What do you think? If it sounds good, click 'Sounds Great!' to complete your podcast."
        else:
            error_msg = "Cannot generate audio: Script is not in the expected format."
            print(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"Error generating podcast audio: {str(e)}"
        print(error_msg)
        return f"I encountered an error while generating the podcast audio: {str(e)}. Please try again or let me know if you'd like to proceed without audio."