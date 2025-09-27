import os
import json
import uuid
from fastapi import status
from fastapi.responses import JSONResponse
import aiosqlite
import glob
from redis.asyncio import ConnectionPool, Redis
from db.config import get_agent_session_db_path
from db.agent_config_v2 import PODCAST_DIR, PODCAST_AUIDO_DIR, PODCAST_IMG_DIR, PODCAST_RECORDINGS_DIR, AVAILABLE_LANGS
from services.celery_tasks import agent_chat
from dotenv import load_dotenv
from services.internal_session_service import SessionService

load_dotenv()


class PodcastAgentService:
    def __init__(self):
        os.makedirs(PODCAST_DIR, exist_ok=True)
        os.makedirs(PODCAST_AUIDO_DIR, exist_ok=True)
        os.makedirs(PODCAST_IMG_DIR, exist_ok=True)
        os.makedirs(PODCAST_RECORDINGS_DIR, exist_ok=True)

        self.redis_host = os.environ.get("REDIS_HOST", "localhost")
        self.redis_port = int(os.environ.get("REDIS_PORT", 6379))
        self.redis_db = int(os.environ.get("REDIS_DB", 0))
        self.redis_pool = ConnectionPool.from_url(f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db + 1}", max_connections=10)
        self.redis = Redis(connection_pool=self.redis_pool)

    async def get_active_task(self, session_id):
        try:
            lock_info = await self.redis.get(f"lock_info:{session_id}")
            if lock_info:
                try:
                    lock_data = json.loads(lock_info.decode("utf-8"))
                    task_id = lock_data.get("task_id")
                    if task_id:
                        return task_id
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"Error parsing lock info: {e}")
            return None
        except Exception as e:
            print(f"Error checking active task: {e}")
            return None

    async def create_session(self, request=None):
        if request and request.session_id:
            session_id = request.session_id
            try:
                db_path = get_agent_session_db_path()
                async with aiosqlite.connect(db_path) as conn:
                    async with conn.execute("SELECT 1 FROM podcast_sessions WHERE session_id = ?", (session_id,)) as cursor:
                        row = await cursor.fetchone()
                        exists = row is not None
                if exists:
                    return {"session_id": session_id}
            except Exception as e:
                print(f"Error checking session existence: {e}")
        new_session_id = str(uuid.uuid4())
        return {"session_id": new_session_id}

    async def chat(self, request):
        try:
            session_id = request.session_id
            task_id = await self.get_active_task(session_id)
            if task_id:
                return {
                    "session_id": session_id,
                    "response": "Your request is already being processed.",
                    "stage": "processing",
                    "session_state": "{}",
                    "is_processing": True,
                    "process_type": "chat",
                    "task_id": task_id,
                }
            task = agent_chat.delay(request.session_id, request.message)
            return {
                "session_id": request.session_id,
                "response": "Your request is being processed.",
                "stage": "processing",
                "session_state": "{}",
                "is_processing": True,
                "process_type": "chat",
                "task_id": task.id,
            }
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "session_id": request.session_id,
                    "response": f"I encountered an error while processing your request: {str(e)}. Please try again.",
                    "stage": "error",
                    "session_state": "{}",
                    "error": str(e),
                    "is_processing": False,
                },
            )

    def _browser_recording(self, session_id):
        try:
            recordings_dir = os.path.join("podcasts/recordings", session_id)
            webm_files = glob.glob(os.path.join(recordings_dir, "*.webm"))
            if webm_files:
                browser_recording_path = webm_files[0]
                if (os.path.exists(browser_recording_path) and 
                    os.path.getsize(browser_recording_path) > 8192 and 
                    os.access(browser_recording_path, os.R_OK)):
                    return browser_recording_path
            return None
        except Exception as _:
            return None

    async def check_result_status(self, request):
        try:
            if not request.session_id:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Session ID is required"},
                )

            browser_recording_path = self._browser_recording(request.session_id)

            task_id = getattr(request, "task_id", None)
            if task_id:
                task = agent_chat.AsyncResult(task_id)
                if task.state == "PENDING" or task.state == "STARTED":
                    return {
                        "session_id": request.session_id,
                        "response": "Your request is still being processed.",
                        "stage": "processing",
                        "session_state": "{}",
                        "is_processing": True,
                        "process_type": "chat",
                        "task_id": task_id,
                        "browser_recording_path": browser_recording_path,
                    }
                elif task.state == "SUCCESS":
                    result = task.result
                    if result and isinstance(result, dict):
                        if result.get("session_id") != request.session_id:
                            return {
                                "session_id": request.session_id,
                                "response": "Error: Received result for wrong session.",
                                "stage": "error",
                                "session_state": "{}",
                                "is_processing": False,
                                "browser_recording_path": browser_recording_path,
                            }
                        return result
                else:
                    error_info = str(task.result) if task.result else f"Task failed with state: {task.state}"
                    return {
                        "session_id": request.session_id,
                        "response": f"Error processing request: {error_info}",
                        "stage": "error",
                        "session_state": "{}",
                        "is_processing": False,
                        "browser_recording_path": browser_recording_path,
                    }
            return await self.get_session_state(request.session_id)
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": f"Error checking result status: {str(e)}",
                    "session_id": request.session_id,
                    "response": f"Error checking result status: {str(e)}",
                    "stage": "error",
                    "session_state": "{}",
                    "is_processing": False,
                    "browser_recording_path": browser_recording_path,
                },
            )

    async def get_session_state(self, session_id):
        try:
            db_path = get_agent_session_db_path()
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
                async with conn.execute("SELECT session_data FROM podcast_sessions WHERE session_id = ?", (session_id,)) as cursor:
                    row = await cursor.fetchone()
            if not row:
                return {
                    "session_id": session_id,
                    "response": "No session data found.",
                    "stage": "idle",
                    "session_state": "{}",
                    "is_processing": False,
                }

            session = SessionService.get_session(session_id)
            session_state = session.get("state", {})
            return {
                "session_id": session_id,
                "response": "",
                "stage": session_state.get("stage", "idle"),
                "session_state": json.dumps(session_state),
                "is_processing": False,
            }
        except Exception as e:
            return {
                "session_id": session_id,
                "response": f"Error retrieving session state: {str(e)}",
                "stage": "error",
                "session_state": "{}",
                "is_processing": False,
            }

    async def list_sessions(self, page=1, per_page=10):
        try:
            db_path = get_agent_session_db_path()
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
                async with conn.execute(
                    """
                    select name from sqlite_master
                    where type='table' and name='podcast_sessions'
                    """
                ) as cursor:
                    table = await cursor.fetchone()
                if not table:
                    return {
                        "sessions": [],
                        "pagination": {
                            "total": 0,
                            "page": page,
                            "per_page": per_page,
                            "total_pages": 0,
                        },
                    }
                async with conn.execute("SELECT COUNT(*) as count FROM podcast_sessions") as cursor:
                    row = await cursor.fetchone()
                    total_sessions = row["count"] if row else 0
                offset = (page - 1) * per_page
                async with conn.execute(
                    "SELECT session_id, session_data, updated_at FROM podcast_sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?", (per_page, offset)
                ) as cursor:
                    rows = await cursor.fetchall()
                    sessions = []
                    for row in rows:
                        try:
                            session = SessionService.get_session(row["session_id"])
                            session_state = session.get("state", {})
                            title = session_state.get("title", "Untitled Podcast")
                            stage = session_state.get("stage", "welcome")
                            updated_at = row["updated_at"]
                            sessions.append({"session_id": row["session_id"], "topic": title, "stage": stage, "updated_at": updated_at})
                        except Exception as e:
                            print(f"Error parsing session data: {e}")
            return {
                "sessions": sessions,
                "pagination": {
                    "total": total_sessions,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total_sessions + per_page - 1) // per_page,
                },
            }
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": f"Failed to list sessions: {str(e)}"})

    async def delete_session(self, session_id: str):
        try:
            db_path = get_agent_session_db_path()
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
                async with conn.execute("SELECT session_data FROM podcast_sessions WHERE session_id = ?", (session_id,)) as cursor:
                    row = await cursor.fetchone()
                if not row:
                    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"error": f"Session with ID {session_id} not found"})
                try:
                    session = SessionService.get_session(session_id)
                    session_state = session.get("state", {})
                    stage = session_state.get("stage")
                    is_completed = stage == "complete" or session_state.get("podcast_generated", False)
                    banner_url = session_state.get("banner_url")
                    audio_url = session_state.get("audio_url")
                    web_search_recording = session_state.get("web_search_recording")
                    await conn.execute("DELETE FROM podcast_sessions WHERE session_id = ?", (session_id,))
                    await conn.commit()
                    if is_completed:
                        print(f"Session {session_id} is in 'complete' stage, keeping assets but removing session record")
                    else:
                        if banner_url:
                            banner_path = os.path.join(PODCAST_IMG_DIR, banner_url)
                            if os.path.exists(banner_path):
                                try:
                                    os.remove(banner_path)
                                    print(f"Deleted banner image: {banner_path}")
                                except Exception as e:
                                    print(f"Error deleting banner image: {e}")
                        if audio_url:
                            audio_path = os.path.join(PODCAST_AUIDO_DIR, audio_url)
                            if os.path.exists(audio_path):
                                try:
                                    os.remove(audio_path)
                                    print(f"Deleted audio file: {audio_path}")
                                except Exception as e:
                                    print(f"Error deleting audio file: {e}")
                        if web_search_recording:
                            recording_dir = os.path.join(PODCAST_RECORDINGS_DIR, session_id)
                            if os.path.exists(recording_dir):
                                try:
                                    import shutil

                                    shutil.rmtree(recording_dir)
                                    print(f"Deleted recordings directory: {recording_dir}")
                                except Exception as e:
                                    print(f"Error deleting recordings directory: {e}")
                    if is_completed:
                        return {"success": True, "message": f"Session {session_id} deleted, but assets preserved"}
                    else:
                        return {"success": True, "message": f"Session {session_id} and its associated data deleted successfully"}
                except Exception as e:
                    print(f"Error parsing session data for deletion: {e}")
                    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": f"Error deleting session: {str(e)}"})
        except Exception as e:
            print(f"Error deleting session: {e}")
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": f"Failed to delete session: {str(e)}"})

    async def _get_chat_messages(self, row, session_id):
        formatted_messages = []
        session_state = {}
        if row["session_data"]:
            try:
                session = SessionService.get_session(session_id)
                session_state = session.get("state", {})
            except Exception as e:
                print(f"Error parsing session_data: {e}")

        if row["memory"]:
            try:
                memory_data = json.loads(row["memory"]) if isinstance(row["memory"], str) else row["memory"]
                if "runs" in memory_data and isinstance(memory_data["runs"], list):
                    for run in memory_data["runs"]:
                        if "messages" in run and isinstance(run["messages"], list):
                            for msg in run["messages"]:
                                if msg.get("role") in ["user", "assistant"] and "content" in msg:
                                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                                        if not msg.get("content"):
                                            continue
                                    if msg.get("content"):
                                        formatted_messages.append({"role": msg["role"], "content": msg["content"]})
            except json.JSONDecodeError as e:
                print(f"Error parsing memory data: {e}")

        return formatted_messages, session_state

    async def get_session_history(self, session_id: str):
        try:
            db_path = get_agent_session_db_path()
            async with aiosqlite.connect(db_path) as conn:
                conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
                async with conn.execute(
                    """
                    select name from sqlite_master
                    where type='table' and name='podcast_sessions'
                    """
                ) as cursor:
                    table = await cursor.fetchone()
                    if not table:
                        return {"session_id": session_id, "messages": [], "state": "{}", "is_processing": False, "process_type": None}
                async with conn.execute("SELECT memory, session_data FROM podcast_sessions WHERE session_id = ?", (session_id,)) as cursor:
                    row = await cursor.fetchone()
                if not row:
                    return {"session_id": session_id, "messages": [], "state": "{}", "is_processing": False, "process_type": None}
                formatted_messages, session_state = await self._get_chat_messages(row, session_id)

            task_id = await self.get_active_task(session_id)
            is_processing = bool(task_id)
            process_type = "chat" if is_processing else None
            browser_recording_path = self._browser_recording(session_id)

            return {
                "session_id": session_id,
                "messages": formatted_messages,
                "state": json.dumps(session_state),
                "is_processing": is_processing,
                "process_type": process_type,
                "task_id": task_id if task_id and is_processing else None,
                "browser_recording_path": browser_recording_path,
            }
        except Exception as e:
            return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": f"Error retrieving session history: {str(e)}"})

    async def get_supported_languages(self):
        return {"languages": AVAILABLE_LANGS}


podcast_agent_service = PodcastAgentService()