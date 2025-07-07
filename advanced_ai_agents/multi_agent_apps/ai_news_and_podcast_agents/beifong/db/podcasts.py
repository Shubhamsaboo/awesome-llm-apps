import json
from datetime import datetime
from typing import Dict, Any, Optional
from .connection import execute_query


def store_podcast(
    podcasts_db_path: str,
    podcast_data: Dict[str, Any],
    audio_path: Optional[str],
    banner_path: Optional[str],
    tts_engine: str = "kokoro",
    language_code: str = "en",
) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    podcast_json = json.dumps(podcast_data)
    audio_generated = 1 if audio_path else 0
    sources_json = json.dumps(podcast_data.get("sources", []))
    query = """
    INSERT INTO podcasts
    (title, date, content_json, audio_generated, audio_path, banner_img_path, 
     tts_engine, language_code, sources_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        podcast_data.get("title", f"Podcast {today}"),
        today,
        podcast_json,
        audio_generated,
        audio_path,
        banner_path,
        tts_engine,
        language_code,
        sources_json,
        datetime.now().isoformat(),
    )
    return execute_query(podcasts_db_path, query, params)


def get_podcast(podcasts_db_path: str, podcast_id: int) -> Optional[Dict[str, Any]]:
    query = """
    SELECT id, title, date, content_json, audio_generated, audio_path, banner_img_path, 
           tts_engine, language_code, sources_json, created_at
    FROM podcasts
    WHERE id = ?
    """
    podcast = execute_query(podcasts_db_path, query, (podcast_id,), fetch=True, fetch_one=True)
    if podcast:
        if podcast.get("content_json"):
            try:
                podcast["content"] = json.loads(podcast["content_json"])
            except json.JSONDecodeError:
                podcast["content"] = {}

        if podcast.get("sources_json"):
            try:
                podcast["sources"] = json.loads(podcast["sources_json"])
            except json.JSONDecodeError:
                podcast["sources"] = []
    return podcast


def get_recent_podcasts(podcasts_db_path: str, limit: int = 10) -> list:
    query = """
    SELECT id, title, date, audio_generated, audio_path, banner_img_path, 
           tts_engine, language_code, sources_json, created_at
    FROM podcasts
    ORDER BY date DESC, created_at DESC
    LIMIT ?
    """
    podcasts = execute_query(podcasts_db_path, query, (limit,), fetch=True)
    for podcast in podcasts:
        if podcast.get("sources_json"):
            try:
                podcast["sources"] = json.loads(podcast["sources_json"])
            except json.JSONDecodeError:
                podcast["sources"] = []
    return podcasts


def update_podcast_audio(podcasts_db_path: str, podcast_id: int, audio_path: str) -> bool:
    query = """
    UPDATE podcasts
    SET audio_path = ?, audio_generated = 1
    WHERE id = ?
    """
    rows_affected = execute_query(podcasts_db_path, query, (audio_path, podcast_id))
    return rows_affected > 0


def update_podcast_banner(podcasts_db_path: str, podcast_id: int, banner_path: str) -> bool:
    query = """
    UPDATE podcasts
    SET banner_img_path = ?
    WHERE id = ?
    """
    rows_affected = execute_query(podcasts_db_path, query, (banner_path, podcast_id))
    return rows_affected > 0


def update_podcast_metadata(
    podcasts_db_path: str, podcast_id: int, tts_engine: Optional[str] = None, language_code: Optional[str] = None, sources_json: Optional[str] = None
) -> bool:
    update_parts = []
    params = []
    if tts_engine is not None:
        update_parts.append("tts_engine = ?")
        params.append(tts_engine)
    if language_code is not None:
        update_parts.append("language_code = ?")
        params.append(language_code)
    if sources_json is not None:
        update_parts.append("sources_json = ?")
        params.append(sources_json)
    if not update_parts:
        return False
    query = f"""
    UPDATE podcasts
    SET {", ".join(update_parts)}
    WHERE id = ?
    """
    params.append(podcast_id)
    rows_affected = execute_query(podcasts_db_path, query, tuple(params))
    return rows_affected > 0
