import sqlite3
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from agno.agent import Agent
from db.config import get_db_path


@contextmanager
def get_social_media_db():
    db_path = get_db_path("social_media_db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def social_media_search(agent: Agent, topic: str, limit: int = 10) -> str:
    """
    Search social media database for the given topic on social media post texts, so topic needs to be extact keyword or phrase.
    Returns minimal fields required for source selection.

    Args:
        agent: The agent instance
        topic: The search topic
        limit: Maximum number of results to return (default: 10)

    Returns:
        Search results matching agent's expected format
    """
    print(f"Social Media News Search: {topic}")
    try:
        days_back: int = 7
        date_from = (datetime.now() - timedelta(days=days_back)).isoformat()
        with get_social_media_db() as conn:
            cursor = conn.cursor()
            sql_query = """
            SELECT 
                post_id,
                user_display_name,
                post_timestamp,
                post_url,
                post_text,
                platform
            FROM posts 
            WHERE 
                categories LIKE '%"news"%' 
                AND sentiment = 'positive'
                AND datetime(post_timestamp) >= datetime(?)
                AND (post_text LIKE ? OR user_display_name LIKE ?)
            ORDER BY datetime(post_timestamp) DESC
            LIMIT ?
            """
            search_term = f"%{topic}%"
            cursor.execute(sql_query, (date_from, search_term, search_term, limit))
            rows = cursor.fetchall()
            if not rows:
                return f"No positive news posts found for '{topic}' in the last {days_back} days."
            results = []
            for row in rows:
                result = {
                    "id": f"social_{row['post_id']}",
                    "url": row["post_url"] or f"https://{row['platform']}/post/{row['post_id']}",
                    "published_date": row["post_timestamp"],
                    "description": row["post_text"][:200] + "..." if len(row["post_text"]) > 200 else row["post_text"],
                    "source_id": "social_media_db",
                    "source_name": f"{row['platform'].title()}",
                    "categories": ["news"],
                    "is_scrapping_required": False,
                }
                results.append(result)
            return f"Found {len(results)} positive news posts. {json.dumps({'results': results}, indent=2)}"
    except Exception as e:
        return f"Error searching social media database: {str(e)}"


def social_media_trending_search(agent: Agent, limit: int = 10) -> str:
    """
    Get trending positive news posts from social media.
    Returns trending news posts in standard results format.


    Args:
        agent: The agent instance
        limit: Maximum number of trending results (default: 10)

    Returns:
        Trending positive news posts
    """
    print(f"Social Media Trending Search: {limit}")
    days_back = 3
    try:
        date_from = (datetime.now() - timedelta(days=days_back)).isoformat()
        with get_social_media_db() as conn:
            cursor = conn.cursor()
            trending_sql = """
            SELECT 
                post_id,
                user_display_name,
                post_timestamp,
                post_url,
                post_text,
                platform
            FROM posts
            WHERE 
                categories LIKE '%"news"%'
                AND sentiment = 'positive'
                AND datetime(post_timestamp) >= datetime(?)
            ORDER BY 
                (COALESCE(engagement_like_count, 0) + 
                 COALESCE(engagement_retweet_count, 0) + 
                 COALESCE(engagement_reply_count, 0)) DESC,
                datetime(post_timestamp) DESC
            LIMIT ?
            """
            cursor.execute(trending_sql, (date_from, limit))
            rows = cursor.fetchall()
            if not rows:
                return f"No trending positive news found in the last {days_back} days."
            results = []
            for row in rows:
                result = {
                    "id": f"social_{row['post_id']}",
                    "url": row["post_url"] or f"https://{row['platform']}/post/{row['post_id']}",
                    "published_date": row["post_timestamp"],
                    "description": row["post_text"],
                    "source_id": "social_media_trending",
                    "source_name": f"{row['platform'].title()} Trending",
                    "categories": ["news"],
                    "is_scrapping_required": False,
                }
                results.append(result)
            return f"Found {len(results)} trending positive news posts. {json.dumps({'results': results}, indent=2)}"
    except Exception as e:
        return f"Error getting trending news: {str(e)}"


if __name__ == "__main__":
    print("here...")
    print(social_media_trending_search(None, 5))