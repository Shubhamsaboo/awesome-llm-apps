from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import HTTPException
from services.db_service import tasks_db


class PodcastConfigService:
    """Service for managing podcast configurations."""

    async def get_all_configs(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """Get all podcast configurations with optional filtering."""
        try:
            if active_only:
                query = """
                SELECT id, name, description, prompt, time_range_hours, limit_articles, 
                       is_active, tts_engine, language_code, podcast_script_prompt, 
                       image_prompt, created_at, updated_at
                FROM podcast_configs
                WHERE is_active = 1
                ORDER BY name
                """
                params = ()
            else:
                query = """
                SELECT id, name, description, prompt, time_range_hours, limit_articles, 
                       is_active, tts_engine, language_code, podcast_script_prompt, 
                       image_prompt, created_at, updated_at
                FROM podcast_configs
                ORDER BY name
                """
                params = ()
            configs = await tasks_db.execute_query(query, params, fetch=True)
            for config in configs:
                config["is_active"] = bool(config.get("is_active", 0))
            return configs
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching podcast configurations: {str(e)}")

    async def get_config(self, config_id: int) -> Dict[str, Any]:
        """Get a specific podcast configuration by ID."""
        try:
            query = """
            SELECT id, name, description, prompt, time_range_hours, limit_articles, 
                   is_active, tts_engine, language_code, podcast_script_prompt, 
                   image_prompt, created_at, updated_at
            FROM podcast_configs
            WHERE id = ?
            """
            config = await tasks_db.execute_query(query, (config_id,), fetch=True, fetch_one=True)
            if not config:
                raise HTTPException(status_code=404, detail="Podcast configuration not found")
            config["is_active"] = bool(config.get("is_active", 0))
            return config
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching podcast configuration: {str(e)}")

    async def create_config(
        self,
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
    ) -> Dict[str, Any]:
        """Create a new podcast configuration."""
        try:
            current_time = datetime.now().isoformat()
            query = """
            INSERT INTO podcast_configs 
            (name, description, prompt, time_range_hours, limit_articles, 
             is_active, tts_engine, language_code, podcast_script_prompt, 
             image_prompt, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
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
                current_time,
                current_time,
            )
            config_id = await tasks_db.execute_query(query, params)
            return await self.get_config(config_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error creating podcast configuration: {str(e)}")

    async def update_config(self, config_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing podcast configuration."""
        try:
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
            set_clauses = []
            params = []
            set_clauses.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            for field, value in updates.items():
                if field in allowed_fields:
                    if field == "is_active":
                        value = 1 if value else 0
                    set_clauses.append(f"{field} = ?")
                    params.append(value)
            if not set_clauses:
                return await self.get_config(config_id)
            params.append(config_id)
            update_query = f"""
            UPDATE podcast_configs
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """
            await tasks_db.execute_query(update_query, tuple(params))
            return await self.get_config(config_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error updating podcast configuration: {str(e)}")

    async def delete_config(self, config_id: int) -> Dict[str, str]:
        """Delete a podcast configuration."""
        try:
            config = await self.get_config(config_id)
            query = """
            DELETE FROM podcast_configs
            WHERE id = ?
            """
            await tasks_db.execute_query(query, (config_id,))
            return {"message": f"Podcast configuration '{config['name']}' has been deleted"}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error deleting podcast configuration: {str(e)}")

    async def toggle_config(self, config_id: int, enable: bool) -> Dict[str, Any]:
        """Enable or disable a podcast configuration."""
        try:
            query = """
            UPDATE podcast_configs
            SET is_active = ?, updated_at = ?
            WHERE id = ?
            """
            current_time = datetime.now().isoformat()
            await tasks_db.execute_query(query, (1 if enable else 0, current_time, config_id))
            return await self.get_config(config_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error updating podcast configuration: {str(e)}")


podcast_config_service = PodcastConfigService()
