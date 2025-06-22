import json
from typing import List, Dict, Any
from openai import OpenAI
from utils.load_api_keys import load_api_key

TRANSLATION_MODEL = "gpt-4o"
LANG_CODE_TO_NAME = {
    "en": "English",
    "h": "Hindi",
    "b": None,
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "it": "Italian",
    "pt": "Portuguese",
    "ar": "Arabic",
}


def translate_script(script: List[Dict[str, Any]], lang_code: str = "b") -> List[Dict[str, Any]]:
    script = [{"text": e["text"], "speaker": e["speaker"]} for e in script]
    target_lang = LANG_CODE_TO_NAME.get(lang_code)
    if target_lang is None:
        return script
    api_key = load_api_key("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    client = OpenAI(api_key=api_key)
    prompt = f"""Translate the following podcast script from English to {target_lang} also keep the characters espeak compatible.
                Maintain the exact same structure and keep the 'speaker' values identical.
                Only translate the text in each entry's 'text' field. and return the json output with translated json format (keys also will be in english only text value will be translated).

                Input script:
                {json.dumps(script, indent=2)}
            """
    response = client.chat.completions.create(
        model=TRANSLATION_MODEL,
        messages=[
            {"role": "system", "content": "You are a professional translator specializing in podcast content."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
    )
    response_content = response.choices[0].message.content
    response_data = json.loads(response_content)
    if "script" in response_data:
        translated_script = response_data["script"]
    else:
        translated_script = response_data
    if not isinstance(translated_script, list):
        raise ValueError("Unexpected response format: not a list")
    if len(translated_script) != len(script):
        raise ValueError(f"Translation returned {len(translated_script)} entries, expected {len(script)}")
    return translated_script
