import os
import sqlite3
import asyncio
import time
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from services.db_service import get_db_path


@contextmanager
def db_connection(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=10000")
    conn.execute("PRAGMA temp_store=MEMORY")
    try:
        yield conn
    finally:
        conn.close()


def init_sources_db():
    start_time = time.time()
    db_path = get_db_path("sources_db")
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            url TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_categories (
            source_id INTEGER,
            category_id INTEGER,
            PRIMARY KEY (source_id, category_id),
            FOREIGN KEY (source_id) REFERENCES sources(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_feeds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            feed_url TEXT UNIQUE,
            feed_type TEXT,
            is_active BOOLEAN DEFAULT 1,
            last_crawled TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (source_id) REFERENCES sources(id)
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_feeds_source_id ON source_feeds(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_is_active ON sources(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_feeds_is_active ON source_feeds(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_categories_source_id ON source_categories(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_categories_category_id ON source_categories(category_id)")
        conn.commit()

    elapsed = time.time() - start_time
    print(f"Sources database initialized in {elapsed:.3f}s")


def init_tracking_db():
    start_time = time.time()
    db_path = get_db_path("tracking_db")
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feed_tracking (
            feed_id INTEGER PRIMARY KEY,
            source_id INTEGER,
            feed_url TEXT,
            last_processed TIMESTAMP,
            last_etag TEXT,
            last_modified TEXT,
            entry_hash TEXT
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feed_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feed_id INTEGER,
            source_id INTEGER,
            entry_id TEXT,
            title TEXT,
            link TEXT UNIQUE,
            published_date TIMESTAMP,
            content TEXT,
            summary TEXT,
            crawl_status TEXT DEFAULT 'pending',
            crawl_attempts INTEGER DEFAULT 0,
            processed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(feed_id, entry_id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawled_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER,
            source_id INTEGER,
            feed_id INTEGER,
            title TEXT,
            url TEXT UNIQUE,
            published_date TIMESTAMP,
            raw_content TEXT,
            content TEXT,
            summary TEXT,
            metadata TEXT,
            ai_status TEXT DEFAULT 'pending',
            ai_error TEXT DEFAULT NULL,
            ai_attempts INTEGER DEFAULT 0,
            crawled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT 0,
            embedding_status TEXT DEFAULT NULL,
            FOREIGN KEY (entry_id) REFERENCES feed_entries(id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_categories (
            article_id INTEGER,
            category_name TEXT NOT NULL,
            PRIMARY KEY (article_id, category_name),
            FOREIGN KEY (article_id) REFERENCES crawled_articles(id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS article_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            embedding BLOB NOT NULL,
            embedding_model TEXT NOT NULL,
            created_at TEXT NOT NULL,
            in_faiss_index INTEGER DEFAULT 0,
            FOREIGN KEY (article_id) REFERENCES crawled_articles(id)
        )
        """)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_feed_entries_feed_id ON feed_entries(feed_id)",
            "CREATE INDEX IF NOT EXISTS idx_feed_entries_link ON feed_entries(link)",
            "CREATE INDEX IF NOT EXISTS idx_crawled_articles_url ON crawled_articles(url)",
            "CREATE INDEX IF NOT EXISTS idx_crawled_articles_entry_id ON crawled_articles(entry_id)",
            "CREATE INDEX IF NOT EXISTS idx_feed_entries_crawl_status ON feed_entries(crawl_status)",
            "CREATE INDEX IF NOT EXISTS idx_crawled_articles_processed ON crawled_articles(processed)",
            "CREATE INDEX IF NOT EXISTS idx_crawled_articles_ai_status ON crawled_articles(ai_status)",
            "CREATE INDEX IF NOT EXISTS idx_article_categories_article_id ON article_categories(article_id)",
            "CREATE INDEX IF NOT EXISTS idx_article_categories_category_name ON article_categories(category_name)",
            "CREATE INDEX IF NOT EXISTS idx_article_embeddings_article_id ON article_embeddings(article_id)",
            "CREATE INDEX IF NOT EXISTS idx_article_embeddings_in_faiss ON article_embeddings(in_faiss_index)",
            "CREATE INDEX IF NOT EXISTS idx_crawled_articles_embedding_status ON crawled_articles(embedding_status)",
        ]
        for index_sql in indexes:
            cursor.execute(index_sql)
        conn.commit()
    elapsed = time.time() - start_time
    print(f"Tracking database initialized in {elapsed:.3f}s")


def init_podcasts_db():
    start_time = time.time()
    db_path = get_db_path("podcasts_db")
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS podcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            date TEXT,
            content_json TEXT,
            audio_generated BOOLEAN DEFAULT 0,
            audio_path TEXT,
            banner_img_path TEXT,
            tts_engine TEXT DEFAULT 'elevenlabs',
            language_code TEXT DEFAULT 'en',
            sources_json TEXT,
            banner_images TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_podcasts_date ON podcasts(date)",
            "CREATE INDEX IF NOT EXISTS idx_podcasts_audio_generated ON podcasts(audio_generated)",
            "CREATE INDEX IF NOT EXISTS idx_podcasts_tts_engine ON podcasts(tts_engine)",
            "CREATE INDEX IF NOT EXISTS idx_podcasts_language_code ON podcasts(language_code)",
        ]
        for index_sql in indexes:
            cursor.execute(index_sql)
        conn.commit()
    elapsed = time.time() - start_time
    print(f"Podcasts database initialized in {elapsed:.3f}s")


def init_tasks_db():
    start_time = time.time()
    db_path = get_db_path("tasks_db")
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            task_type TEXT,
            description TEXT,
            command TEXT NOT NULL,
            frequency INTEGER NOT NULL,
            frequency_unit TEXT NOT NULL,
            enabled BOOLEAN DEFAULT 1,
            last_run TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            status TEXT NOT NULL,
            error_message TEXT,
            output TEXT,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS podcast_configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            prompt TEXT NOT NULL,
            time_range_hours INTEGER DEFAULT 24,
            limit_articles INTEGER DEFAULT 20,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tts_engine TEXT DEFAULT 'elevenlabs',
            language_code TEXT DEFAULT 'en',
            podcast_script_prompt TEXT,
            image_prompt TEXT
        )
        """)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_tasks_enabled ON tasks(enabled)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_frequency ON tasks(frequency, frequency_unit)",
            "CREATE INDEX IF NOT EXISTS idx_tasks_last_run ON tasks(last_run)",
            "CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id)",
            "CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status)",
            "CREATE INDEX IF NOT EXISTS idx_task_executions_start_time ON task_executions(start_time)",
            "CREATE INDEX IF NOT EXISTS idx_podcast_configs_is_active ON podcast_configs(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_podcast_configs_name ON podcast_configs(name)",
        ]
        for index_sql in indexes:
            cursor.execute(index_sql)
        conn.commit()
    elapsed = time.time() - start_time
    print(f"Tasks database initialized in {elapsed:.3f}s")


async def init_agent_session_db():
    """Initialize the agent session database. auto generated"""
    pass


def init_internal_sessions_db():
    start_time = time.time()
    db_path = get_db_path("internal_sessions_db")
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_state (
            session_id TEXT PRIMARY KEY,
            state JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_state_session_id ON session_state(session_id)")
        conn.commit()
    elapsed = time.time() - start_time
    print(f"Internal sessions database initialized in {elapsed:.3f}s")


def init_social_media_db():
    start_time = time.time()
    db_path = get_db_path("social_media_db")
    with db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            post_id TEXT PRIMARY KEY,
            platform TEXT,
            user_display_name TEXT,
            user_handle TEXT,
            user_profile_pic_url TEXT,
            post_timestamp TEXT,
            post_display_time TEXT,
            post_url TEXT,
            post_text TEXT,
            post_mentions TEXT,
            engagement_reply_count INTEGER,
            engagement_retweet_count INTEGER,
            engagement_like_count INTEGER,
            engagement_bookmark_count INTEGER,
            engagement_view_count INTEGER,
            media TEXT,
            media_count INTEGER,
            is_ad BOOLEAN,
            sentiment TEXT,
            categories TEXT,
            tags TEXT,
            analysis_reasoning TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform)",
            "CREATE INDEX IF NOT EXISTS idx_posts_user_handle ON posts(user_handle)",
            "CREATE INDEX IF NOT EXISTS idx_posts_post_timestamp ON posts(post_timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_posts_sentiment ON posts(sentiment)",
        ]
        for index_sql in indexes:
            cursor.execute(index_sql)
        conn.commit()
    elapsed = time.time() - start_time
    print(f"Social media database initialized in {elapsed:.3f}s")


async def init_databases():
    total_start = time.time()
    print("Initializing all databases...")
    for db_name in ["sources_db", "tracking_db", "podcasts_db", "tasks_db"]:
        db_path = get_db_path(db_name)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [
            loop.run_in_executor(executor, init_sources_db),
            loop.run_in_executor(executor, init_tracking_db),
            loop.run_in_executor(executor, init_podcasts_db),
            loop.run_in_executor(executor, init_tasks_db),
            loop.run_in_executor(executor, init_internal_sessions_db),
            loop.run_in_executor(executor, init_social_media_db),
        ]
        await asyncio.gather(*tasks)
    total_elapsed = time.time() - total_start
    print(f"All databases initialized in {total_elapsed:.3f}s")


def init_all_databases():
    asyncio.run(init_databases())