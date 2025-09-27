import json
from datetime import datetime
from .connection import db_connection, execute_query


def store_crawled_article(tracking_db_path, entry, raw_content, metadata):
    metadata_json = json.dumps(metadata)
    query = """
    INSERT INTO crawled_articles 
    (entry_id, source_id, feed_id, title, url, published_date, raw_content, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        params = (
            entry["id"],
            entry.get("source_id"),
            entry.get("feed_id"),
            entry.get("title", ""),
            entry.get("link", ""),
            entry.get("published_date", datetime.now().isoformat()),
            raw_content,
            metadata_json,
        )
        execute_query(tracking_db_path, query, params)
        return True
    except Exception:
        return False


def update_entry_status(tracking_db_path, entry_id, status):
    query = """
    UPDATE feed_entries
    SET crawl_attempts = crawl_attempts + 1, crawl_status = ?
    WHERE id = ?
    """
    return execute_query(tracking_db_path, query, (status, entry_id))


def get_unprocessed_articles(tracking_db_path, limit=5, max_attempts=1):
    reset_stuck_articles(tracking_db_path)
    query = """
    SELECT id, entry_id, source_id, feed_id, title, url, published_date, raw_content, metadata, ai_attempts
    FROM crawled_articles
    WHERE (ai_status = 'pending' OR ai_status = 'error')
          AND ai_attempts < ?
          AND processed = 0
    ORDER BY published_date DESC
    LIMIT ?
    """
    articles = execute_query(tracking_db_path, query, (max_attempts, limit), fetch=True)
    for article in articles:
        if article.get("metadata"):
            try:
                article["metadata"] = json.loads(article["metadata"])
            except json.JSONDecodeError:
                article["metadata"] = {}
    if articles:
        article_ids = [a["id"] for a in articles]
        mark_articles_as_processing(tracking_db_path, article_ids)
    return articles


def reset_stuck_articles(tracking_db_path):
    query = """
    UPDATE crawled_articles 
    SET ai_status = 'pending' 
    WHERE ai_status = 'processing'
    """
    return execute_query(tracking_db_path, query)


def mark_articles_as_processing(tracking_db_path, article_ids):
    if not article_ids:
        return 0
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(article_ids))
        query = f"""
        UPDATE crawled_articles 
        SET ai_status = 'processing' 
        WHERE id IN ({placeholders})
        """
        cursor.execute(query, article_ids)
        conn.commit()
        return cursor.rowcount


def save_article_categories(tracking_db_path, article_id, categories):
    if not categories:
        return 0
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
        DELETE FROM article_categories
        WHERE article_id = ?
        """,
            (article_id,),
        )
        count = 0
        for category in categories:
            try:
                cursor.execute(
                    """
                INSERT INTO article_categories (article_id, category_name)
                VALUES (?, ?)
                """,
                    (article_id, category.lower().strip()),
                )
                count += 1
            except Exception as _:
                pass
        conn.commit()
        return count


def get_article_categories(tracking_db_path, article_id):
    query = """
    SELECT category_name
    FROM article_categories
    WHERE article_id = ?
    """
    results = execute_query(tracking_db_path, query, (article_id,), fetch=True)
    return [row["category_name"] for row in results]


def update_article_status(tracking_db_path, article_id, results=None, success=False, error_message=None):
    with db_connection(tracking_db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
        UPDATE crawled_articles
        SET ai_attempts = ai_attempts + 1
        WHERE id = ?
        """,
            (article_id,),
        )
        if success and results:
            categories = []
            if "categories" in results:
                if isinstance(results["categories"], str):
                    try:
                        categories = json.loads(results["categories"])
                    except json.JSONDecodeError:
                        categories = [c.strip() for c in results["categories"].split(",") if c.strip()]
                elif isinstance(results["categories"], list):
                    categories = results["categories"]
            cursor.execute(
                """
            UPDATE crawled_articles
            SET summary = ?, content = ?, processed = 1, ai_status = 'success'
            WHERE id = ?
            """,
                (results.get("summary", ""), results.get("content", ""), article_id),
            )
            conn.commit()
            if categories:
                save_article_categories(tracking_db_path, article_id, categories)
        else:
            cursor.execute(
                """
            UPDATE crawled_articles
            SET ai_status = 'error', ai_error = ?
            WHERE id = ?
            """,
                (error_message, article_id),
            )
            cursor.execute(
                """
            UPDATE crawled_articles
            SET ai_status = 'failed'
            WHERE id = ? AND ai_attempts >= 3
            """,
                (article_id,),
            )
            conn.commit()
        return cursor.rowcount


def get_articles_by_date_range(tracking_db_path, start_date=None, end_date=None, limit=None, offset=0):
    query_parts = [
        "SELECT ca.id, ca.feed_id, ca.source_id, ca.title, ca.url, ca.published_date,",
        "ca.summary, ca.content",
        "FROM crawled_articles ca",
        "WHERE ca.processed = 1",
        "AND ca.ai_status = 'success'",
    ]
    query_params = []
    if start_date:
        query_parts.append("AND ca.published_date >= ?")
        query_params.append(start_date)
    if end_date:
        query_parts.append("AND ca.published_date <= ?")
        query_params.append(end_date)
    query_parts.append("ORDER BY ca.published_date DESC")
    if limit is not None:
        query_parts.append("LIMIT ? OFFSET ?")
        query_params.append(limit)
        query_params.append(offset)
    query = " ".join(query_parts)
    return execute_query(tracking_db_path, query, tuple(query_params), fetch=True)


def get_article_by_id(tracking_db_path, article_id):
    query = """
    SELECT id, entry_id, source_id, feed_id, title, url, published_date, 
           raw_content, content, summary, metadata, ai_status, ai_error, 
           ai_attempts, crawled_date, processed
    FROM crawled_articles
    WHERE id = ?
    """
    article = execute_query(tracking_db_path, query, (article_id,), fetch=True, fetch_one=True)
    if article:
        if article.get("metadata"):
            try:
                article["metadata"] = json.loads(article["metadata"])
            except json.JSONDecodeError:
                article["metadata"] = {}
        article["categories"] = get_article_categories(tracking_db_path, article_id)
    return article


def get_articles_by_category(tracking_db_path, category, limit=20, offset=0):
    query = """
    SELECT ca.id, ca.title, ca.url, ca.published_date, ca.summary
    FROM crawled_articles ca
    JOIN article_categories ac ON ca.id = ac.article_id
    WHERE ac.category_name = ?
    AND ca.processed = 1
    AND ca.ai_status = 'success'
    ORDER BY ca.published_date DESC
    LIMIT ? OFFSET ?
    """
    return execute_query(tracking_db_path, query, (category, limit, offset), fetch=True)


def get_article_stats(tracking_db_path):
    query = """
    SELECT 
        COUNT(*) as total_articles,
        SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed_articles,
        SUM(CASE WHEN ai_status = 'pending' THEN 1 ELSE 0 END) as pending_articles,
        SUM(CASE WHEN ai_status = 'processing' THEN 1 ELSE 0 END) as processing_articles,
        SUM(CASE WHEN ai_status = 'success' THEN 1 ELSE 0 END) as success_articles,
        SUM(CASE WHEN ai_status = 'error' THEN 1 ELSE 0 END) as error_articles,
        SUM(CASE WHEN ai_status = 'failed' THEN 1 ELSE 0 END) as failed_articles
    FROM crawled_articles
    """
    return execute_query(tracking_db_path, query, fetch=True, fetch_one=True)


def get_categories_with_counts(tracking_db_path, limit=20):
    query = """
    SELECT category_name, COUNT(*) as article_count
    FROM article_categories
    GROUP BY category_name
    ORDER BY article_count DESC
    LIMIT ?
    """
    return execute_query(tracking_db_path, query, (limit,), fetch=True)


def get_articles_with_source_info(tracking_db_path, limit=20, offset=0):
    query = """
    SELECT ca.id, ca.title, ca.url, ca.published_date, ca.summary, 
           ft.feed_url, s.name as source_name
    FROM crawled_articles ca
    LEFT JOIN feed_tracking ft ON ca.feed_id = ft.feed_id
    LEFT JOIN source_feeds sf ON ca.feed_id = sf.id
    LEFT JOIN sources s ON sf.source_id = s.id
    WHERE ca.processed = 1 
    AND ca.ai_status = 'success'
    ORDER BY ca.published_date DESC
    LIMIT ? OFFSET ?
    """
    return execute_query(tracking_db_path, query, (limit, offset), fetch=True)
