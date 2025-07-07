import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime


def get_podcast_config(db_path: str, config_id: int) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, description, prompt, time_range_hours, limit_articles, 
                   is_active, tts_engine, language_code, podcast_script_prompt, 
                   image_prompt, created_at, updated_at
            FROM podcast_configs
            WHERE id = ?
            """,
            (config_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        config = dict(row)
        config["is_active"] = bool(config.get("is_active", 0))
        return config
    except Exception as e:
        print(f"Error fetching podcast config: {e}")
        return None
    finally:
        conn.close()


def get_all_podcast_configs(db_path: str, active_only: bool = False) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        if active_only:
            query = """
            SELECT id, name, description, prompt, time_range_hours, limit_articles, 
                   is_active, tts_engine, language_code, podcast_script_prompt, 
                   image_prompt, created_at, updated_at
            FROM podcast_configs
            WHERE is_active = 1
            ORDER BY name
            """
            cursor.execute(query)
        else:
            query = """
            SELECT id, name, description, prompt, time_range_hours, limit_articles, 
                   is_active, tts_engine, language_code, podcast_script_prompt, 
                   image_prompt, created_at, updated_at
            FROM podcast_configs
            ORDER BY name
            """
            cursor.execute(query)
        configs = []
        for row in cursor.fetchall():
            config = dict(row)
            config["is_active"] = bool(config.get("is_active", 0))
            configs.append(config)
        return configs
    except Exception as e:
        print(f"Error fetching podcast configs: {e}")
        return []
    finally:
        conn.close()


def create_podcast_config(
    db_path: str,
    name: str,
    prompt: str,
    description: Optional[str] = None,
    time_range_hours: int = 24,
    limit_articles: int = 20,
    is_active: bool = True,
    tts_engine: str = "kokoro",
    language_code: str = "en",
    podcast_script_prompt: Optional[str] = None,
    image_prompt: Optional[str] = None,
) -> Optional[int]:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            """
            INSERT INTO podcast_configs
            (name, description, prompt, time_range_hours, limit_articles, 
             is_active, tts_engine, language_code, podcast_script_prompt, 
             image_prompt, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                description,
                prompt,
                time_range_hours,
                limit_articles,
                1 if is_active else 0,
                tts_engine,
                language_code,
                podcast_script_prompt,
                image_prompt,
                now,
                now,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        print(f"Error creating podcast config: {e}")
        return None
    finally:
        conn.close()


def update_podcast_config(db_path: str, config_id: int, updates: Dict[str, Any]) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM podcast_configs WHERE id = ?", (config_id,))
        if not cursor.fetchone():
            return False
        if not updates:
            return True
        set_clauses = []
        params = []
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        allowed_fields = [
            "name",
            "description",
            "prompt",
            "time_range_hours",
            "limit_articles",
            "is_active",
            "tts_engine",
            "language_code",
            "podcast_script_prompt",
            "image_prompt",
        ]
        for field, value in updates.items():
            if field in allowed_fields:
                if field == "is_active":
                    value = 1 if value else 0
                set_clauses.append(f"{field} = ?")
                params.append(value)
        params.append(config_id)
        query = f"""
        UPDATE podcast_configs
        SET {", ".join(set_clauses)}
        WHERE id = ?
        """
        cursor.execute(query, tuple(params))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating podcast config: {e}")
        return False
    finally:
        conn.close()


def delete_podcast_config(db_path: str, config_id: int) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM podcast_configs WHERE id = ?", (config_id,))
        conn.commit()

        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error deleting podcast config: {e}")
        return False
    finally:
        conn.close()


def toggle_podcast_config(db_path: str, config_id: int, is_active: bool) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            """
            UPDATE podcast_configs
            SET is_active = ?, updated_at = ?
            WHERE id = ?
            """,
            (1 if is_active else 0, now, config_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error toggling podcast config: {e}")
        return False
    finally:
        conn.close()
