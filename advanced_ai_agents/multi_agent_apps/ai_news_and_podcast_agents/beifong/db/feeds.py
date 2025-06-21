from datetime import datetime
import sqlite3
from .connection import db_connection, execute_query


def get_active_feeds(sources_db_path, limit=None, offset=0):
    if limit:
        query = """
        SELECT sf.id, sf.source_id, sf.feed_url, sf.feed_type, sf.last_crawled, 
               s.name as source_name
        FROM source_feeds sf
        JOIN sources s ON sf.source_id = s.id
        WHERE sf.is_active = 1 AND s.is_active = 1
        LIMIT ? OFFSET ?
        """
        return execute_query(sources_db_path, query, (limit, offset), fetch=True)
    else:
        query = """
        SELECT sf.id, sf.source_id, sf.feed_url, sf.feed_type, sf.last_crawled, 
               s.name as source_name
        FROM source_feeds sf
        JOIN sources s ON sf.source_id = s.id
        WHERE sf.is_active = 1 AND s.is_active = 1
        """
        return execute_query(sources_db_path, query, fetch=True)


def count_active_feeds(sources_db_path):
    query = """
    SELECT COUNT(*) as count
    FROM source_feeds sf
    JOIN sources s ON sf.source_id = s.id
    WHERE sf.is_active = 1 AND s.is_active = 1
    """
    result = execute_query(sources_db_path, query, fetch=True, fetch_one=True)
    return result["count"] if result else 0


def get_feed_tracking_info(tracking_db_path, feed_id):
    query = "SELECT * FROM feed_tracking WHERE feed_id = ?"
    return execute_query(tracking_db_path, query, (feed_id,), fetch=True, fetch_one=True)


def update_feed_tracking(tracking_db_path, feed_id, etag, modified, entry_hash):
    query = """
    UPDATE feed_tracking 
    SET last_processed = ?, last_etag = ?, last_modified = ?, entry_hash = ?
    WHERE feed_id = ?
    """
    params = (datetime.now().isoformat(), etag, modified, entry_hash, feed_id)
    return execute_query(tracking_db_path, query, params)


def store_feed_entries(tracking_db_path, feed_id, source_id, entries):
    count = 0
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        for entry in entries:
            try:
                cursor.execute(
                    """
                INSERT INTO feed_entries 
                (feed_id, source_id, entry_id, title, link, published_date, content, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        feed_id,
                        source_id,
                        entry.get("entry_id", ""),
                        entry.get("title", ""),
                        entry.get("link", ""),
                        entry.get("published_date", datetime.now().isoformat()),
                        entry.get("content", ""),
                        entry.get("summary", ""),
                    ),
                )
                count += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
    return count


def update_tracking_info(tracking_db_path, feeds):
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        for feed in feeds:
            cursor.execute(
                """
            INSERT OR IGNORE INTO feed_tracking 
            (feed_id, source_id, feed_url, last_processed)
            VALUES (?, ?, ?, NULL)
            """,
                (feed["id"], feed["source_id"], feed["feed_url"]),
            )
        conn.commit()


def get_uncrawled_entries(tracking_db_path, limit=20, max_attempts=3):
    reset_stuck_entries(tracking_db_path)
    query = """
    SELECT e.id, e.feed_id, e.source_id, e.title, e.link, e.published_date,
           e.crawl_attempts, e.entry_id as original_entry_id
    FROM feed_entries e
    WHERE (e.crawl_status = 'pending' OR e.crawl_status = 'failed') 
          AND e.crawl_attempts < ?
          AND e.link IS NOT NULL
          AND e.link != ''
          AND NOT EXISTS (
              SELECT 1 FROM crawled_articles ca WHERE ca.url = e.link
          )
    ORDER BY e.published_date DESC
    LIMIT ?
    """
    entries = execute_query(tracking_db_path, query, (max_attempts, limit), fetch=True)
    if entries:
        entry_ids = [e["id"] for e in entries]
        mark_entries_as_processing(tracking_db_path, entry_ids)
    return entries


def reset_stuck_entries(tracking_db_path):
    query = """
    UPDATE feed_entries 
    SET crawl_status = 'pending' 
    WHERE crawl_status = 'processing'
    """
    return execute_query(tracking_db_path, query)


def mark_entries_as_processing(tracking_db_path, entry_ids):
    if not entry_ids:
        return 0
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(entry_ids))
        query = f"""
        UPDATE feed_entries 
        SET crawl_status = 'processing' 
        WHERE id IN ({placeholders})
        """
        cursor.execute(query, entry_ids)
        conn.commit()
        return cursor.rowcount


def ensure_feed_tracking_exists(tracking_db_path, feed_id, source_id, feed_url):
    query = """
    INSERT OR IGNORE INTO feed_tracking 
    (feed_id, source_id, feed_url, last_processed)
    VALUES (?, ?, ?, NULL)
    """
    return execute_query(tracking_db_path, query, (feed_id, source_id, feed_url))


def get_feed_sources_with_categories(sources_db_path):
    query = """
    SELECT sf.id, sf.source_id, sf.feed_url, sf.feed_type, sf.last_crawled, 
           s.name as source_name, c.name as category_name
    FROM source_feeds sf
    JOIN sources s ON sf.source_id = s.id
    LEFT JOIN source_categories sc ON s.id = sc.source_id
    LEFT JOIN categories c ON sc.category_id = c.id
    WHERE sf.is_active = 1 AND s.is_active = 1
    """
    return execute_query(sources_db_path, query, fetch=True)


def get_feed_stats(tracking_db_path):
    query = """
    SELECT 
        COUNT(*) as total_entries,
        SUM(CASE WHEN crawl_status = 'pending' THEN 1 ELSE 0 END) as pending_entries,
        SUM(CASE WHEN crawl_status = 'processing' THEN 1 ELSE 0 END) as processing_entries,
        SUM(CASE WHEN crawl_status = 'success' THEN 1 ELSE 0 END) as success_entries,
        SUM(CASE WHEN crawl_status = 'failed' THEN 1 ELSE 0 END) as failed_entries
    FROM feed_entries
    """
    return execute_query(tracking_db_path, query, fetch=True, fetch_one=True)
