import os
from typing import Any, Callable, Optional
from utils.load_api_keys import load_api_key

_TTS_ENGINES = {}
TTS_OPENAI_MODEL = "gpt-4o-mini-tts"
TTS_ELEVENLABS_MODEL = "eleven_multilingual_v2"


def register_tts_engine(name: str, generator_func: Callable):
    _TTS_ENGINES[name.lower()] = generator_func


def generate_podcast_audio(
    script: Any, output_path: str, tts_engine: str = "kokoro", language_code: str = "en", silence_duration: float = 0.7, voice_map=None
) -> Optional[str]:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    engine_name = tts_engine.lower()
    if engine_name not in _TTS_ENGINES:
        print(f"Unsupported TTS engine: {tts_engine}")
        return None
    try:
        return _TTS_ENGINES[engine_name](
            script=script, output_path=output_path, language_code=language_code, silence_duration=silence_duration, voice_map=voice_map
        )
    except Exception as e:
        import traceback

        print(f"Error generating audio with {tts_engine}: {e}")
        traceback.print_exc()
        return None


def register_default_engines():
    def elevenlabs_generator(script, output_path, language_code, silence_duration, voice_map):
        from utils.text_to_audio_elevenslab import create_podcast as elevenlabs_create_podcast

        if voice_map is None:
            voice_map = {1: "Rachel", 2: "Adam"}
            if language_code == "hi":
                voice_map = {1: "Rachel", 2: "Adam"}
        return elevenlabs_create_podcast(
            script=script,
            output_path=output_path,
            silence_duration=silence_duration,
            voice_map=voice_map,
            elevenlabs_model=TTS_ELEVENLABS_MODEL,
            api_key=load_api_key("ELEVENSLAB_API_KEY"),
        )

    def kokoro_generator(script, output_path, language_code, silence_duration, voice_map):
        from utils.text_to_audio_kokoro import create_podcast as kokoro_create_podcast

        kokoro_lang_code = "b"
        if language_code == "hi":
            kokoro_lang_code = "h"
        return kokoro_create_podcast(
            script=script, output_path=output_path, silence_duration=silence_duration, sampling_rate=24_000, lang_code=kokoro_lang_code
        )

    def openai_generator(script, output_path, language_code, silence_duration, voice_map):
        from utils.text_to_audio_openai import create_podcast as openai_create_podcast

        if voice_map is None:
            voice_map = {1: "alloy", 2: "nova"}
            if language_code == "hi":
                voice_map = {1: "alloy", 2: "nova"}
        model = TTS_OPENAI_MODEL
        return openai_create_podcast(
            script=script,
            output_path=output_path,
            silence_duration=silence_duration,
            lang_code=language_code,
            model=model,
            voice_map=voice_map,
            api_key=load_api_key("OPENAI_API_KEY"),
        )

    register_tts_engine("elevenlabs", elevenlabs_generator)
    register_tts_engine("kokoro", kokoro_generator)
    register_tts_engine("openai", openai_generator)


register_default_engines()
