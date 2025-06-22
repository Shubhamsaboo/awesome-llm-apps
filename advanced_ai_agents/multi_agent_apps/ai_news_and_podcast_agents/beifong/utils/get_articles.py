import sqlite3
import openai
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

TOPIC_EXTRACTION_MODEL = "gpt-4o-mini"


def extract_search_terms(prompt: str, api_key: str, max_terms: int = 10) -> list:
    client = openai.OpenAI(api_key=api_key)
    system_msg = (
        "analyze the user's request and extract up to "
        f"{max_terms} key search terms or phrases (focus on nouns and concepts). "
        "Include broad variations and synonyms to increase match chances. "
        "For very specific topics, add general category terms too. "
        "output only a json object following this exact schema: "
        "{'terms': ['term1','term2',...]}. no additional keys or text."
    )
    try:
        resp = client.chat.completions.create(
            model=TOPIC_EXTRACTION_MODEL,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        parsed = json.loads(resp.choices[0].message.content.strip())
        if isinstance(parsed, dict) and isinstance(parsed.get("terms"), list):
            return parsed["terms"]
    except Exception as e:
        print(f"Error extracting search terms: {e}")
    return [prompt.strip()]


def search_articles(
    prompt: str,
    db_path: str,
    api_key: str,
    operator: str = "OR",
    limit: int = 20,
    from_date: str = None,
    use_categories: bool = True,
    fallback_to_broader: bool = True,
) -> List[Dict[str, Any]]:
    if from_date is None:
        from_date = (datetime.now() - timedelta(hours=48)).isoformat()
    terms = extract_search_terms(prompt, api_key)
    if not terms:
        return []
    print(f"Search terms: {terms}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    results = []
    try:
        results = _execute_search(cursor, terms, from_date, operator, limit, use_categories)
        if fallback_to_broader and len(results) < min(5, limit):
            print(f"Initial search returned only {len(results)} results. Trying broader search...")
            if operator == "AND":
                broader_results = _execute_search(
                    cursor,
                    terms,
                    from_date,
                    "OR",
                    limit,
                    use_categories=True,
                )
                if len(broader_results) > len(results):
                    print(f"Broader search found {len(broader_results)} results")
                    results = broader_results
        if results:
            _add_source_names(cursor, results)
        for article in results:
            article["categories"] = _get_article_categories(cursor, article["id"])
    except Exception as e:
        print(f"Error searching articles: {e}")
    finally:
        conn.close()
    return results


def _execute_search(
    cursor,
    terms,
    from_date,
    operator,
    limit,
    use_categories=True,
    partial_match=False,
    days_fallback=0,
):
    if days_fallback > 0:
        try:
            from_date_obj = datetime.fromisoformat(from_date.replace("Z", "").split("+")[0])
            adjusted_date = (from_date_obj - timedelta(days=days_fallback)).isoformat()
            from_date = adjusted_date
        except Exception as e:
            print(f"Warning: Could not adjust date with fallback: {e}")
    base_query = """
        SELECT DISTINCT ca.id, ca.title, ca.url, ca.published_date, ca.summary as content, 
               ca.source_id, ca.feed_id
        FROM crawled_articles ca
        WHERE ca.processed = 1 AND ca.published_date >= ?
    """
    if use_categories:
        base_query = """
            SELECT DISTINCT ca.id, ca.title, ca.url, ca.published_date, ca.summary as content,
                   ca.source_id, ca.feed_id
            FROM crawled_articles ca
            LEFT JOIN article_categories ac ON ca.id = ac.article_id
            WHERE ca.processed = 1 AND ca.published_date >= ?
        """
    clauses, params = [], [from_date]
    for term in terms:
        term_clauses = []
        like = f"%{term}%"
        term_clauses.append("(ca.title LIKE ? OR ca.content LIKE ? OR ca.summary LIKE ?)")
        params.extend([like, like, like])
        if use_categories:
            term_clauses.append("(ac.category_name LIKE ?)")
            params.append(like)
        if term_clauses:
            clauses.append(f"({' OR '.join(term_clauses)})")
    where = f" {operator} ".join(clauses)
    sql = f"{base_query} AND ({where}) ORDER BY ca.published_date DESC LIMIT {limit}"
    cursor.execute(sql, params)
    return [dict(row) for row in cursor.fetchall()]


def _add_source_names(cursor, articles):
    source_ids = {a.get("source_id") for a in articles if a.get("source_id")}
    feed_ids = {a.get("feed_id") for a in articles if a.get("feed_id")}
    if not source_ids and not feed_ids:
        return
    source_names = {}
    if source_ids:
        source_ids = [id for id in source_ids if id is not None]
        if source_ids:
            placeholders = ",".join(["?"] * len(source_ids))
            try:
                cursor.execute(
                    f"SELECT id, name FROM sources WHERE id IN ({placeholders})",
                    list(source_ids),
                )
                for row in cursor.fetchall():
                    source_names[row["id"]] = row["name"]
            except Exception as e:
                print(f"Error fetching source names: {e}")
    if feed_ids:
        feed_ids = [id for id in feed_ids if id is not None]
        if feed_ids:
            placeholders = ",".join(["?"] * len(feed_ids))
            try:
                cursor.execute(
                    f"""
                    SELECT sf.id, s.name 
                    FROM source_feeds sf
                    JOIN sources s ON sf.source_id = s.id
                    WHERE sf.id IN ({placeholders})
                """,
                    list(feed_ids),
                )
                for row in cursor.fetchall():
                    source_names[row["id"]] = row["name"]
            except Exception as e:
                print(f"Error fetching feed source names: {e}")
    for article in articles:
        source_id = article.get("source_id")
        feed_id = article.get("feed_id")
        if source_id and source_id in source_names:
            article["source_name"] = source_names[source_id]
        elif feed_id and feed_id in source_names:
            article["source_name"] = source_names[feed_id]
        else:
            article["source_name"] = "Unknown Source"


def _get_article_categories(cursor, article_id):
    try:
        cursor.execute(
            "SELECT category_name FROM article_categories WHERE article_id = ?",
            (article_id,),
        )
        return [row["category_name"] for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error fetching article categories: {e}")
        return []
