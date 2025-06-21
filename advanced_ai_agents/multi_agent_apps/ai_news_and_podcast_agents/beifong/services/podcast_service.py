import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from fastapi import HTTPException, UploadFile
from services.db_service import podcasts_db
import math

AUDIO_DIR = "podcasts/audio"
IMAGE_DIR = "podcasts/images"


class PodcastService:
    """Service for managing podcast operations with the new database structure."""

    def __init__(self):
        """Initialize the podcast service with directories."""
        os.makedirs(AUDIO_DIR, exist_ok=True)
        os.makedirs(IMAGE_DIR, exist_ok=True)

    async def get_podcasts(
        self,
        page: int = 1,
        per_page: int = 10,
        search: str = None,
        date_from: str = None,
        date_to: str = None,
        language_code: str = None,
        tts_engine: str = None,
        has_audio: bool = None,
    ) -> Dict[str, Any]:
        """
        Get a paginated list of podcasts with optional filtering.
        """
        try:
            offset = (page - 1) * per_page
            count_query = "SELECT COUNT(*) as count FROM podcasts"
            query = """
            SELECT id, title, date, audio_generated, audio_path, banner_img_path,
                   language_code, tts_engine, created_at
            FROM podcasts
            """
            where_conditions = []
            params = []
            if search:
                where_conditions.append("(title LIKE ?)")
                search_param = f"%{search}%"
                params.append(search_param)
            if date_from:
                where_conditions.append("date >= ?")
                params.append(date_from)
            if date_to:
                where_conditions.append("date <= ?")
                params.append(date_to)
            if language_code:
                where_conditions.append("language_code = ?")
                params.append(language_code)
            if tts_engine:
                where_conditions.append("tts_engine = ?")
                params.append(tts_engine)
            if has_audio is not None:
                where_conditions.append("audio_generated = ?")
                params.append(1 if has_audio else 0)
            if where_conditions:
                where_clause = " WHERE " + " AND ".join(where_conditions)
                query += where_clause
                count_query += where_clause
            query += " ORDER BY date DESC, created_at DESC"
            query += " LIMIT ? OFFSET ?"
            params.extend([per_page, offset])
            total_result = await podcasts_db.execute_query(count_query, tuple(params[:-2] if params else ()), fetch=True, fetch_one=True)
            total_items = total_result.get("count", 0) if total_result else 0
            total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
            podcasts = await podcasts_db.execute_query(query, tuple(params), fetch=True)
            for podcast in podcasts:
                podcast["audio_generated"] = bool(podcast.get("audio_generated", 0))
                if podcast.get("banner_img_path"):
                    podcast["banner_img"] = podcast.get("banner_img_path")
                else:
                    podcast["banner_img"] = None
                podcast.pop("banner_img_path", None)
                podcast["identifier"] = str(podcast.get("id", ""))
            has_next = page < total_pages
            has_prev = page > 1
            return {
                "items": podcasts,
                "total": total_items,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading podcasts: {str(e)}")

    async def get_podcast(self, podcast_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific podcast by ID without content."""
        try:
            query = """
            SELECT id, title, date, audio_generated, audio_path, banner_img_path,
                language_code, tts_engine, created_at, banner_images
            FROM podcasts
            WHERE id = ?
            """
            podcast = await podcasts_db.execute_query(query, (podcast_id,), fetch=True, fetch_one=True)
            if not podcast:
                raise HTTPException(status_code=404, detail="Podcast not found")
            podcast["audio_generated"] = bool(podcast.get("audio_generated", 0))
            if podcast.get("banner_img_path"):
                podcast["banner_img"] = podcast.get("banner_img_path")
            else:
                podcast["banner_img"] = None
            podcast.pop("banner_img_path", None)
            podcast["identifier"] = str(podcast.get("id", ""))
            sources_query = "SELECT sources_json FROM podcasts WHERE id = ?"
            sources_result = await podcasts_db.execute_query(sources_query, (podcast_id,), fetch=True, fetch_one=True)
            sources = []
            if sources_result and sources_result.get("sources_json"):
                try:
                    parsed_sources = json.loads(sources_result["sources_json"])
                    if isinstance(parsed_sources, list):
                        sources = parsed_sources
                    else:
                        sources = [parsed_sources]
                except json.JSONDecodeError:
                    sources = []
            podcast["sources"] = sources
            
            try:
                banner_images = json.loads(podcast.get("banner_images", "[]"))
            except json.JSONDecodeError:
                banner_images = []
            podcast["banner_images"] = banner_images
            
            return podcast
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error loading podcast: {str(e)}")

    async def get_podcast_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get a specific podcast by string identifier (which is actually the ID)."""
        try:
            try:
                podcast_id = int(identifier)
            except ValueError:
                raise HTTPException(status_code=404, detail="Invalid podcast identifier")
            return await self.get_podcast(podcast_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error loading podcast: {str(e)}")

    async def get_podcast_content(self, podcast_id: int) -> Dict[str, Any]:
        """Get the content of a specific podcast."""
        try:
            query = """
            SELECT content_json FROM podcasts WHERE id = ?
            """
            result = await podcasts_db.execute_query(query, (podcast_id,), fetch=True, fetch_one=True)
            if not result or not result.get("content_json"):
                raise HTTPException(status_code=404, detail="Podcast content not found")
            try:
                content = json.loads(result["content_json"])
                return content
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Invalid podcast content format")

        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error loading podcast content: {str(e)}")

    async def get_podcast_audio_url(self, podcast: Dict[str, Any]) -> Optional[str]:
        """Get the URL for the podcast audio file if available."""
        if podcast.get("audio_generated") and podcast.get("audio_path"):
            return f"/audio/{podcast.get('audio_path')}"
        return None

    async def get_podcast_formats(self) -> List[str]:
        """Get list of available podcast formats for filtering."""
        # Note: This may need to be adapted if format field is added
        return ["daily", "weekly", "tech", "news"]

    async def get_language_codes(self) -> List[str]:
        try:
            query = """
            SELECT DISTINCT language_code FROM podcasts WHERE language_code IS NOT NULL
            """
            results = await podcasts_db.execute_query(query, (), fetch=True)
            language_codes = [result["language_code"] for result in results if result["language_code"]]
            if "en" not in language_codes:
                language_codes.append("en")
            return sorted(language_codes)
        except Exception as _:
            return ["en"]

    async def get_tts_engines(self) -> List[str]:
        """Get list of available TTS engines for filtering."""
        try:
            query = """
            SELECT DISTINCT tts_engine FROM podcasts WHERE tts_engine IS NOT NULL
            """
            results = await podcasts_db.execute_query(query, (), fetch=True)
            tts_engines = [result["tts_engine"] for result in results if result["tts_engine"]]
            default_engines = ["elevenlabs", "openai", "kokoro"]
            for engine in default_engines:
                if engine not in tts_engines:
                    tts_engines.append(engine)
            return sorted(tts_engines)
        except Exception as e:
            return ["elevenlabs", "openai", "kokoro"]

    async def create_podcast(
        self, title: str, date: str, content: Dict[str, Any], sources: List[str] = None, language_code: str = "en", tts_engine: str = "kokoro"
    ) -> Dict[str, Any]:
        """Create a new podcast in the database."""
        try:
            content_json = json.dumps(content)
            sources_json = json.dumps(sources) if sources else None
            current_time = datetime.now().isoformat()
            query = """
            INSERT INTO podcasts 
            (title, date, content_json, audio_generated, sources_json, language_code, tts_engine, created_at)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?)
            """
            params = (title, date, content_json, sources_json, language_code, tts_engine, current_time)
            podcast_id = await podcasts_db.execute_query(query, params)
            return await self.get_podcast(podcast_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating podcast: {str(e)}")

    async def update_podcast(self, podcast_id: int, podcast_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update podcast metadata and content."""
        try:
            existing = await self.get_podcast(podcast_id)
            if not existing:
                raise HTTPException(status_code=404, detail="Podcast not found")
            fields = []
            params = []
            if "title" in podcast_data:
                fields.append("title = ?")
                params.append(podcast_data["title"])
            if "date" in podcast_data:
                fields.append("date = ?")
                params.append(podcast_data["date"])
            if "content" in podcast_data and isinstance(podcast_data["content"], dict):
                fields.append("content_json = ?")
                params.append(json.dumps(podcast_data["content"]))
            if "audio_generated" in podcast_data:
                fields.append("audio_generated = ?")
                params.append(1 if podcast_data["audio_generated"] else 0)
            if "audio_path" in podcast_data:
                fields.append("audio_path = ?")
                params.append(podcast_data["audio_path"])
            if "banner_img_path" in podcast_data:
                fields.append("banner_img_path = ?")
                params.append(podcast_data["banner_img_path"])
            if "sources" in podcast_data:
                fields.append("sources_json = ?")
                params.append(json.dumps(podcast_data["sources"]))
            if "language_code" in podcast_data:
                fields.append("language_code = ?")
                params.append(podcast_data["language_code"])
            if "tts_engine" in podcast_data:
                fields.append("tts_engine = ?")
                params.append(podcast_data["tts_engine"])
            if not fields:
                return existing
            params.append(podcast_id)
            query = f"""
            UPDATE podcasts SET {", ".join(fields)}
            WHERE id = ?
            """
            await podcasts_db.execute_query(query, tuple(params))
            return await self.get_podcast(podcast_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error updating podcast: {str(e)}")

    async def delete_podcast(self, podcast_id: int, delete_assets: bool = False) -> bool:
        """Delete a podcast from the database."""
        try:
            existing = await self.get_podcast(podcast_id)
            if not existing:
                raise HTTPException(status_code=404, detail="Podcast not found")
            query = "DELETE FROM podcasts WHERE id = ?"
            result = await podcasts_db.execute_query(query, (podcast_id,))
            if delete_assets:
                if existing.get("audio_path"):
                    audio_path = os.path.join(AUDIO_DIR, existing["audio_path"])
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                if existing.get("banner_img_path"):
                    img_path = os.path.join(IMAGE_DIR, existing["banner_img_path"])
                    if os.path.exists(img_path):
                        os.remove(img_path)
            return result > 0
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error deleting podcast: {str(e)}")

    async def upload_podcast_audio(self, podcast_id: int, file: UploadFile) -> Dict[str, Any]:
        """Upload an audio file for a podcast."""
        try:
            await self.get_podcast(podcast_id)
            filename = f"podcast_{podcast_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{filename}{ext}"
            else:
                filename = f"{filename}.mp3"
            file_path = os.path.join(AUDIO_DIR, filename)
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            update_data = {"audio_generated": True, "audio_path": filename}
            return await self.update_podcast(podcast_id, update_data)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error uploading audio: {str(e)}")

    async def upload_podcast_banner(self, podcast_id: int, file: UploadFile) -> Dict[str, Any]:
        """Upload a banner image for a podcast."""
        try:
            await self.get_podcast(podcast_id)
            filename = f"banner_{podcast_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if file.filename:
                ext = os.path.splitext(file.filename)[1]
                filename = f"{filename}{ext}"
            else:
                filename = f"{filename}.jpg"
            file_path = os.path.join(IMAGE_DIR, filename)
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            update_data = {"banner_img_path": filename}
            return await self.update_podcast(podcast_id, update_data)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error uploading banner: {str(e)}")


podcast_service = PodcastService()
