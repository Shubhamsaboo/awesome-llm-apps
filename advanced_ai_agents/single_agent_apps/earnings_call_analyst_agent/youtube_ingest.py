from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import parse_qs, urlparse

import requests

from .adk_runtime import run_adk_agent_content
from .schemas import TranscriptChunk, TranscriptSegment, VideoMetadata


VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _int_env(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)) or str(default))
    except ValueError:
        value = default
    return max(minimum, min(maximum, value))


AUDIO_CHUNK_SECONDS = _int_env("EARNINGS_AUDIO_CHUNK_SECONDS", 300, minimum=60, maximum=900)


try:
    from google.adk.agents import Agent

    transcription_agent = Agent(
        name="earnings_audio_transcription_agent",
        model=os.getenv(
            "EARNINGS_TRANSCRIPT_MODEL",
            os.getenv("EARNINGS_GEMINI_MODEL", "gemini-3-flash-preview"),
        ),
        description="Transcribes earnings-call audio into timestamped transcript segments.",
        instruction=(
            "Transcribe supplied audio into timestamped English transcript segments. "
            "Return strict JSON only with key segments. Preserve financial numbers, speaker names, "
            "tickers, and guidance language exactly."
        ),
    )
except Exception:
    transcription_agent = None


def extract_video_id(value: str) -> str:
    raw = (value or "").strip()
    if VIDEO_ID_RE.match(raw):
        return raw

    parsed = urlparse(raw)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if host.endswith("youtube.com") or host.endswith("youtube-nocookie.com"):
        query_id = parse_qs(parsed.query).get("v", [""])[0]
        if VIDEO_ID_RE.match(query_id):
            return query_id
        if path_parts and path_parts[0] in {"live", "embed", "shorts"}:
            candidate = path_parts[1] if len(path_parts) > 1 else ""
            if VIDEO_ID_RE.match(candidate):
                return candidate

    if host == "youtu.be" and path_parts and VIDEO_ID_RE.match(path_parts[0]):
        return path_parts[0]

    raise ValueError("Enter a valid YouTube URL or 11-character video id.")


def fetch_video_metadata(url: str, video_id: str) -> VideoMetadata:
    endpoint = "https://www.youtube.com/oembed"
    try:
        response = requests.get(
            endpoint,
            params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"},
            timeout=8,
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        data = {}

    return VideoMetadata(
        video_id=video_id,
        title=data.get("title") or "Untitled earnings call",
        author_name=data.get("author_name") or "",
        thumbnail_url=data.get("thumbnail_url") or "",
        source_url=url,
    )


def fetch_transcript(video_id: str) -> list[TranscriptSegment]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:
        raise RuntimeError(
            "Missing youtube-transcript-api. Install requirements.txt before running the app."
        ) from exc

    try:
        items = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
    except AttributeError:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en", "en-US"])
        items = [
            {
                "start": snippet.start,
                "duration": snippet.duration,
                "text": snippet.text,
            }
            for snippet in fetched
        ]
    except Exception as exc:
        raise RuntimeError(
            "Could not load captions for this video. Try a YouTube earnings call with English captions."
        ) from exc

    return [
        TranscriptSegment(
            start=float(item.get("start", 0)),
            duration=float(item.get("duration", 0)),
            text=" ".join(str(item.get("text", "")).replace("\n", " ").split()),
        )
        for item in items
        if str(item.get("text", "")).strip()
    ]


def load_transcript(video_id: str) -> tuple[list[TranscriptSegment], str]:
    try:
        return fetch_transcript(video_id), "youtube_captions"
    except Exception as captions_error:
        try:
            return transcribe_audio_with_adk(video_id), "adk_audio"
        except Exception as audio_error:
            raise RuntimeError(
                "Could not load captions and ADK audio transcription fallback failed. "
                f"Captions error: {captions_error}. Audio fallback error: {audio_error}"
            ) from audio_error


def transcribe_audio_with_adk(
    video_id: str, on_progress: Optional[Callable[[int, str], None]] = None
) -> list[TranscriptSegment]:
    if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY is required for audio transcription fallback.")

    try:
        from google.genai import types
        from yt_dlp import YoutubeDL
    except ImportError as exc:
        raise RuntimeError(
            "Audio fallback requires google-genai and yt-dlp. Run pip install -r requirements.txt."
        ) from exc

    with tempfile.TemporaryDirectory(prefix="earnings-audio-") as temp_dir:
        if on_progress:
            on_progress(34, "Downloading low-bitrate audio for ADK transcription")
        output_template = str(Path(temp_dir) / "audio.%(ext)s")
        ydl_opts = {
            "format": "worstaudio[ext=m4a]/worstaudio[ext=webm]/worstaudio/bestaudio",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)

        audio_files = [path for path in Path(temp_dir).iterdir() if path.is_file()]
        if not audio_files:
            raise RuntimeError("yt-dlp did not produce an audio file.")

        audio_path = max(audio_files, key=lambda path: path.stat().st_size)
        audio_chunks = _prepare_audio_chunks(audio_path, Path(temp_dir))
        if not audio_chunks:
            audio_chunks = [audio_path]

        segments: list[TranscriptSegment] = []
        for index, chunk_path in enumerate(audio_chunks):
            if on_progress:
                chunk_progress = 38 + int((index / max(1, len(audio_chunks))) * 22)
                on_progress(
                    chunk_progress,
                    f"Transcribing audio chunk {index + 1} of {len(audio_chunks)} with ADK",
                )
            chunk_offset = index * AUDIO_CHUNK_SECONDS
            mime_type = _audio_mime_type(chunk_path)
            prompt = f"""
Transcribe this earnings-call audio into timestamped English segments.
Return strict JSON only:
{{"segments":[{{"start":0,"duration":8.5,"text":"..."}}]}}

            Rules:
- Use seconds from the beginning of this audio chunk, not the full original video.
- Keep segments between 5 and 20 seconds when possible.
- Preserve financial numbers, speaker names, tickers, and guidance language exactly.
- If audio is not an earnings call, still transcribe accurately.
Chunk starts at {chunk_offset} seconds in the original video.
"""
            if transcription_agent is None:
                raise RuntimeError("ADK transcription agent is unavailable.")
            message = types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(data=chunk_path.read_bytes(), mime_type=mime_type),
                    types.Part.from_text(text=prompt),
                ],
            )
            chunk_segments = parse_transcribed_segments(
                run_adk_agent_content(transcription_agent, message)
            )
            for segment in chunk_segments:
                segments.append(
                    TranscriptSegment(
                        start=segment.start + chunk_offset,
                        duration=segment.duration,
                        text=segment.text,
                    )
                )
        if on_progress:
            on_progress(62, "Audio transcription complete; preparing transcript")
        if not segments:
            raise RuntimeError("ADK transcription returned no transcript segments from audio.")
        return sorted(segments, key=lambda segment: segment.start)

def parse_transcribed_segments(text: str) -> list[TranscriptSegment]:
    data = _parse_json_object(text)
    raw_segments = data.get("segments", [])
    if not isinstance(raw_segments, list):
        return []

    segments: list[TranscriptSegment] = []
    for raw in raw_segments:
        if not isinstance(raw, dict):
            continue
        clean_text = " ".join(str(raw.get("text", "")).replace("\n", " ").split())
        if not clean_text:
            continue
        try:
            start = float(raw.get("start", 0))
            if "duration" in raw:
                duration = float(raw.get("duration", 0))
            else:
                duration = max(0, float(raw.get("end", start)) - start)
        except (TypeError, ValueError):
            continue
        segments.append(TranscriptSegment(start=start, duration=duration, text=clean_text))
    return sorted(segments, key=lambda segment: segment.start)


def chunk_transcript(
    segments: list[TranscriptSegment], window_seconds: int = 45
) -> list[TranscriptChunk]:
    chunks: list[TranscriptChunk] = []
    current: list[TranscriptSegment] = []
    window_start: Optional[float] = None

    for segment in segments:
        if window_start is None:
            window_start = segment.start
        if current and segment.end - window_start > window_seconds:
            chunks.append(_build_chunk(current))
            current = []
            window_start = segment.start
        current.append(segment)

    if current:
        chunks.append(_build_chunk(current))

    return chunks


def _build_chunk(segments: list[TranscriptSegment]) -> TranscriptChunk:
    return TranscriptChunk(
        start=segments[0].start,
        end=max(segment.end for segment in segments),
        text=" ".join(segment.text for segment in segments),
        segments=segments,
    )


def _audio_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".m4a", ".mp4"}:
        return "audio/mp4"
    if suffix == ".mp3":
        return "audio/mpeg"
    if suffix == ".wav":
        return "audio/wav"
    if suffix == ".ogg":
        return "audio/ogg"
    if suffix == ".webm":
        return "audio/webm"
    return "application/octet-stream"


def _prepare_audio_chunks(audio_path: Path, temp_dir: Path) -> list[Path]:
    if not shutil.which("ffmpeg"):
        return [audio_path]

    output_pattern = temp_dir / "chunk_%03d.mp3"
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "32k",
        "-f",
        "segment",
        "-segment_time",
        str(AUDIO_CHUNK_SECONDS),
        "-reset_timestamps",
        "1",
        str(output_pattern),
    ]
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        return [audio_path]

    chunks = sorted(temp_dir.glob("chunk_*.mp3"))
    return [chunk for chunk in chunks if chunk.stat().st_size > 0]


def _parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I | re.S)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        data = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
