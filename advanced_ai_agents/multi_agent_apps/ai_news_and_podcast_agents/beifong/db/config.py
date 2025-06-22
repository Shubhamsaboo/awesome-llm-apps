import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)
DEFAULT_DB_PATHS = {
    "sources_db": "databases/sources.db",
    "tracking_db": "databases/feed_tracking.db",
    "podcasts_db": "databases/podcasts.db",
    "tasks_db": "databases/tasks.db",
    "agent_session_db": "databases/agent_sessions.db",
    "faiss_index_db": "databases/faiss/article_index.faiss",
    "faiss_mapping_file": "databases/faiss/article_id_map.npy",
    "internal_sessions_db": "databases/internal_sessions.db",
    "social_media_db": "databases/social_media.db",
    "slack_sessions_db": "databases/slack_sessions.db",
}


def get_db_path(db_name):
    env_var = f"{db_name.upper()}_PATH"
    path = os.environ.get(env_var, DEFAULT_DB_PATHS.get(db_name))
    db_dir = os.path.dirname(path)
    os.makedirs(db_dir, exist_ok=True)
    return path


def get_sources_db_path():
    return get_db_path("sources_db")


def get_tracking_db_path():
    return get_db_path("tracking_db")


def get_podcasts_db_path():
    return get_db_path("podcasts_db")


def get_tasks_db_path():
    return get_db_path("tasks_db")


def get_agent_session_db_path():
    return get_db_path("agent_session_db")


def get_faiss_db_path():
    return get_db_path("faiss_index_db"), get_db_path("faiss_mapping_file")


def get_internal_sessions_db_path():
    return get_db_path("internal_sessions_db")


def get_social_media_db_path():
    return get_db_path("social_media_db")


def get_browser_session_path():
    return "browsers/playwright_persistent_profile"

def get_slack_sessions_db_path():
    return get_db_path("slack_sessions_db")

DB_PATH = "databases"
PODCAST_DIR = "podcasts"
PODCAST_IMG_DIR = PODCAST_DIR + "/images"
PODCAST_AUIDO_DIR = PODCAST_DIR + "/audio"
PODCAST_RECORDINGS_DIR = PODCAST_DIR + "/recordings"
