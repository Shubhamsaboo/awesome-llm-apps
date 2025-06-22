import sqlite3
from typing import List, Union
from agno.agent import Agent
from db.config import get_tracking_db_path
import json


def search_articles(agent: Agent, terms: Union[str, List[str]]) -> str:
    """
    Search for articles related to a podcast topic using direct SQL queries.
    The agent can pass either a string topic or a list of search terms.

    Args:
        agent: The agent instance
        terms: Either a single topic string or a list of search terms

    Returns:
        A formatted string response with the search results
    """
    print(f"Search Internal Articles terms: {terms}")
    search_terms = terms if isinstance(terms, list) else [terms]
    limit = 3
    db_path = get_tracking_db_path()
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
            results = execute_simple_search(conn, search_terms, limit)
            if not results:
                return "No relevant articles found in our database. Would you like to try a different topic or provide specific URLs?"
            for article in results:
                article["categories"] = get_article_categories(conn, article["id"])
                article["source_name"] = article.get("source_id", "Unknown Source")
            return f"is_scrapping_required: False, Found {len(results)}, {json.dumps(results, indent=2)} potential sources that might be relevant to your topic careful my search is text bassed do quality check and ignore invalid resutls."
    except Exception as e:
        print(f"Error searching articles: {e}")
        return "I encountered a database error while searching. Would you like to try a different approach?"


def execute_simple_search(conn, terms, limit):
    base_query = """
        SELECT DISTINCT ca.id, ca.title, ca.url, ca.published_date, 
               COALESCE(ca.summary, ca.content) as content,
               ca.source_id, ca.feed_id
        FROM crawled_articles ca
        WHERE ca.processed = 1 
          AND (
    """
    clauses = []
    params = []
    for term in terms:
        like_term = f"%{term}%"
        clauses.append("(ca.title LIKE ? OR ca.content LIKE ? OR ca.summary LIKE ?)")
        params.extend([like_term, like_term, like_term])

    query = base_query + " OR ".join(clauses) + ") ORDER BY ca.published_date DESC LIMIT ?"
    params.append(limit)
    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def get_article_categories(conn, article_id):
    try:
        cursor = conn.execute("SELECT category_name FROM article_categories WHERE article_id = ?", (article_id,))
        return [row["category_name"] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching article categories: {e}")
        return []