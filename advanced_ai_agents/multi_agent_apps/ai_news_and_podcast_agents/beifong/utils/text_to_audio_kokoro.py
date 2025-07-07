# ruff: noqa: E402
import os
import warnings
from typing import List, Any
import numpy as np
import soundfile as sf
from .translate_podcast import translate_script

os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

from kokoro import KPipeline


class ScriptEntry:
    def __init__(self, text: str, speaker: int):
        self.text = text
        self.speaker = speaker


def create_slience_audio(silence_duration: float, sampling_rate: int) -> np.ndarray:
    return np.zeros(int(sampling_rate * silence_duration), dtype=np.float32)


def text_to_speech(pipeline: KPipeline, text: str, speaker_id: int, sampling_rate: int, lang_code: str) -> np.ndarray:
    if lang_code == "h":
        voices = {1: "hf_alpha", 2: "hm_omega"}
    else:
        voices = {1: "af_heart", 2: "bm_lewis"}
    voice = voices[speaker_id]
    audio_chunks = []
    for _, _, audio in pipeline(text, voice=voice, speed=1.0):
        if audio is not None:
            audio_chunk = np.array(audio, dtype=np.float32)
            if np.max(np.abs(audio_chunk)) > 0:
                audio_chunk = audio_chunk / np.max(np.abs(audio_chunk)) * 0.9
            audio_chunks.append(audio_chunk)
    if audio_chunks:
        return np.concatenate(audio_chunks)
    else:
        return np.zeros(0, dtype=np.float32)


def create_audio_segments(
    pipeline: KPipeline,
    script: Any,
    silence_duration: float,
    sampling_rate: int,
    lang_code: str,
) -> List[np.ndarray]:
    audio_segments = []
    silence = create_slience_audio(silence_duration, sampling_rate)
    entries = script if isinstance(script, list) else script.entries
    for entry in entries:
        text = entry["text"] if isinstance(entry, dict) else entry.text
        speaker = entry["speaker"] if isinstance(entry, dict) else entry.speaker
        segment_audio = text_to_speech(
            pipeline,
            text,
            speaker,
            sampling_rate=sampling_rate,
            lang_code=lang_code,
        )
        if len(segment_audio) > 0:
            try:
                audio_segments.append(segment_audio)
            except Exception:
                fallback_silence = create_slience_audio(len(text) * 0.1, sampling_rate)
                audio_segments.append(fallback_silence)
            audio_segments.append(silence)
    return audio_segments


def combine_full_segments(audio_segments: List[np.ndarray]) -> np.ndarray:
    full_audio = np.concatenate(audio_segments)
    max_amp = np.max(np.abs(full_audio))
    if max_amp > 0:
        full_audio = full_audio / max_amp * 0.9
    return full_audio


def write_to_disk(output_path: str, full_audio: np.ndarray, sampling_rate: int) -> None:
    return sf.write(output_path, full_audio, sampling_rate, subtype="PCM_16")


def create_podcast(
    script: Any,
    output_path: str,
    silence_duration: float = 0.7,
    sampling_rate: int = 24_000,
    lang_code: str = "b",
) -> str:
    pipeline = KPipeline(lang_code=lang_code)
    if lang_code != "b":
        if isinstance(script, list):
            script = translate_script(script, lang_code)
        else:
            script = translate_script(script.entries, lang_code)
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    audio_segments = create_audio_segments(pipeline, script, silence_duration, sampling_rate, lang_code)
    full_audio = combine_full_segments(audio_segments)
    write_to_disk(output_path, full_audio, sampling_rate)
    return output_path


if __name__ == "__main__":
    create_podcast("", "output.wav")