from agno.agent import Agent
from datetime import datetime
from db.config import get_podcasts_db_path, DB_PATH
import os
import sqlite3
import json


def _save_podcast_to_database_sync(session_state: dict) -> tuple[bool, str, int]:
    try:
        if session_state.get("podcast_id"):
            return (
                True,
                f"Podcast already saved with ID: {session_state['podcast_id']}",
                session_state["podcast_id"],
            )
        tts_engine = session_state.get("tts_engine", "openai")
        podcast_info = session_state.get("podcast_info", {})
        generated_script = session_state.get("generated_script", {})
        banner_url = session_state.get("banner_url")
        banner_images = json.dumps(session_state.get("banner_images", []))
        audio_url = session_state.get("audio_url")
        selected_language = session_state.get("selected_language", {"code": "en", "name": "English"})
        language_code = selected_language.get("code", "en")
        if not generated_script or not isinstance(generated_script, dict):
            return (
                False,
                "Cannot complete podcast: Generated script is missing or invalid.",
                None,
            )
        if "title" not in generated_script:
            generated_script["title"] = podcast_info.get("topic", "Untitled Podcast")
        if "sections" not in generated_script or not isinstance(generated_script["sections"], list):
            return (
                False,
                "Cannot complete podcast: Generated script is missing required 'sections' array.",
                None,
            )
        sources = []
        if "sources" in generated_script and generated_script["sources"]:
            for source in generated_script["sources"]:
                if isinstance(source, str):
                    sources.append(source)
                elif isinstance(source, dict) and "url" in source:
                    sources.append(source["url"])
                elif isinstance(source, dict) and "link" in source:
                    sources.append(source["link"])
        generated_script["sources"] = sources
        db_path = get_podcasts_db_path()
        db_directory = DB_PATH
        os.makedirs(db_directory, exist_ok=True)

        conn = sqlite3.connect(db_path)
        content_json = json.dumps(generated_script)
        sources_json = json.dumps(sources) if sources else None
        current_time = datetime.now().isoformat()
        query = """
            INSERT INTO podcasts (
                title, 
                date, 
                content_json, 
                audio_generated, 
                audio_path,
                banner_img_path, 
                tts_engine, 
                language_code, 
                sources_json,
                created_at,
                banner_images
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        conn.execute(
            query,
            (
                generated_script.get("title", "Untitled Podcast"),
                datetime.now().strftime("%Y-%m-%d"),
                content_json,
                1 if audio_url else 0,
                audio_url,
                banner_url,
                tts_engine,
                language_code,
                sources_json,
                current_time,
                banner_images,
            ),
        )
        conn.commit()

        cursor = conn.execute("SELECT last_insert_rowid()")
        podcast_id = cursor.fetchone()
        podcast_id = podcast_id[0] if podcast_id else None
        cursor.close()
        conn.close()

        session_state["podcast_id"] = podcast_id
        return True, f"Podcast successfully saved with ID: {podcast_id}", podcast_id
    except Exception as e:
        print(f"Error saving podcast to database: {e}")
        return False, f"Error saving podcast to database: {str(e)}", None


def update_language(agent: Agent, language_code: str) -> str:
    """
    Update the podcast language with the specified language code.
    This ensures the language is properly tracked for generating content and audio.
    Args:
        agent: The agent instance
        language_code: The language code (e.g., 'en', 'es', 'fr', etc..)

    Returns:
        Confirmation message
    """
    from services.internal_session_service import SessionService

    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    session_state = session["state"]
    language_name = "English"
    for lang in session_state.get("available_languages", []):
        if lang.get("code") == language_code:
            language_name = lang.get("name")
            break
    session_state["selected_language"] = {
        "code": language_code,
        "name": language_name,
    }
    SessionService.save_session(session_id, session_state)
    return f"Podcast language set to: {language_name} ({language_code})"


def update_chat_title(agent: Agent, title: str) -> str:
    """
    Update the chat title with the specified short title.
    Args:
        agent: The agent instance
        title: The short title to set for the chat

    Returns:
        Confirmation message
    """
    from services.internal_session_service import SessionService

    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    current_state = session["state"]
    current_state["title"] = title
    current_state["created_at"] = datetime.now().isoformat()
    SessionService.save_session(session_id, current_state)
    return f"Chat title updated to: {title}"


def toggle_podcast_generated(session_state: dict, status: bool = False) -> str:
    """
    Toggle the podcast_generated flag.
    When set to true, this indicates the podcast creation process is complete and
    the UI should show the final presentation view with all components.
    If status is True, also saves the podcast to the podcasts database.
    """
    if status:
        session_state["podcast_generated"] = status
        session_state["stage"] = "complete" if status else session_state.get("stage")
        if status:
            try:
                success, message, podcast_id = _save_podcast_to_database_sync(session_state)
                if success and podcast_id:
                    session_state["podcast_id"] = podcast_id
                    return f"Podcast generated and saved to database with ID: {podcast_id}. You can now access it from the Podcasts section."
                else:
                    return f"Podcast generated, but there was an issue with saving: {message}"
            except Exception as e:
                print(f"Error saving podcast to database: {e}")
                return f"Podcast generated, but there was an error saving it to the database: {str(e)}"
    else:
        session_state["podcast_generated"] = status
        session_state["stage"] = "complete" if status else session_state.get("stage")
    return f"Podcast generated status changed to: {status}"


def mark_session_finished(agent: Agent) -> str:
    """
    Mark the session as finished.
    Args:
        agent: The agent instance

    Returns:
        Confirmation message
    """
    from services.internal_session_service import SessionService

    session_id = agent.session_id
    session = SessionService.get_session(session_id)
    session_state = session["state"]
    if not session_state.get("generated_script"):
        return "Podcast Script is not generated yet."
    if not session_state.get("banner_url"):
        return "Banner is not generated yet."
    if not session_state.get("audio_url"):
        return "Audio is not generated yet."
    session_state["finished"] = True
    session_state["stage"] = "complete"
    toggle_podcast_generated(session_state, True)
    SessionService.save_session(session_id, session_state)
    return "Session marked as finished and generated podcast stored into podcasts database and No further conversation are allowed and only new session can be started."
