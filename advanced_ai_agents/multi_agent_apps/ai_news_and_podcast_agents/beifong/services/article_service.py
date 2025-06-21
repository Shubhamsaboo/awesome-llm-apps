from typing import List, Optional, Dict, Any
from fastapi import HTTPException
import json
from services.db_service import tracking_db, sources_db
from models.article_schemas import Article, PaginatedArticles


class ArticleService:
    """Service for managing article operations with the new database structure."""

    async def get_articles(
        self,
        page: int = 1,
        per_page: int = 10,
        source: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
    ) -> PaginatedArticles:
        """Get articles with pagination and filtering."""
        try:
            offset = (page - 1) * per_page
            query_parts = [
                "SELECT ca.id, ca.title, ca.url, ca.published_date, ca.summary, ca.feed_id",
                "FROM crawled_articles ca",
                "WHERE ca.processed = 1 AND ca.ai_status = 'success'",
            ]
            query_params = []
            if source:
                source_id_query = "SELECT id FROM sources WHERE name = ?"
                source_id_result = await sources_db.execute_query(source_id_query, (source,), fetch=True, fetch_one=True)
                if source_id_result and source_id_result.get("id"):
                    feed_ids_query = "SELECT id FROM source_feeds WHERE source_id = ?"
                    feed_ids_result = await sources_db.execute_query(feed_ids_query, (source_id_result["id"],), fetch=True)
                    if feed_ids_result:
                        feed_ids = [item["id"] for item in feed_ids_result]
                        placeholders = ",".join(["?" for _ in feed_ids])
                        query_parts.append(f"AND ca.feed_id IN ({placeholders})")
                        query_params.extend(feed_ids)
            if category:
                query_parts.append("""
                    AND EXISTS (
                        SELECT 1 FROM article_categories ac 
                        WHERE ac.article_id = ca.id AND ac.category_name = ?
                    )
                """)
                query_params.append(category.lower())
            if date_from:
                query_parts.append("AND datetime(ca.published_date) >= datetime(?)")
                query_params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(ca.published_date) <= datetime(?)")
                query_params.append(date_to)
            if search:
                query_parts.append("AND (ca.title LIKE ? OR ca.summary LIKE ?)")
                search_param = f"%{search}%"
                query_params.extend([search_param, search_param])
            count_query = " ".join(query_parts).replace(
                "SELECT ca.id, ca.title, ca.url, ca.published_date, ca.summary, ca.feed_id",
                "SELECT COUNT(*)",
            )
            total_articles = await tracking_db.execute_query(count_query, tuple(query_params), fetch=True, fetch_one=True)
            total_count = total_articles.get("COUNT(*)", 0) if total_articles else 0
            query_parts.append("ORDER BY datetime(ca.published_date) DESC, ca.id DESC")
            query_parts.append("LIMIT ? OFFSET ?")
            query_params.extend([per_page, offset])
            articles_query = " ".join(query_parts)
            articles = await tracking_db.execute_query(articles_query, tuple(query_params), fetch=True)
            feed_ids = [article["feed_id"] for article in articles if article.get("feed_id")]
            source_names = {}
            if feed_ids:
                feed_ids_str = ",".join("?" for _ in feed_ids)
                source_query = f"""
                SELECT sf.id as feed_id, s.name as source_name
                FROM source_feeds sf
                JOIN sources s ON sf.source_id = s.id
                WHERE sf.id IN ({feed_ids_str})
                """
                sources_result = await sources_db.execute_query(source_query, tuple(feed_ids), fetch=True)
                source_names = {item["feed_id"]: item["source_name"] for item in sources_result}
            for article in articles:
                feed_id = article.get("feed_id")
                article["source_name"] = source_names.get(feed_id, "Unknown Source")
                article.pop("feed_id", None)
                article["categories"] = await self.get_article_categories(article["id"])
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            return PaginatedArticles(
                items=articles,
                total=total_count,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching articles: {str(e)}")

    async def get_article(self, article_id: int) -> Article:
        """Get a specific article by ID."""
        try:
            article_query = """
            SELECT id, title, url, published_date, content, summary, feed_id,
                   metadata, ai_status
            FROM crawled_articles
            WHERE id = ? AND processed = 1
            """
            article = await tracking_db.execute_query(article_query, (article_id,), fetch=True, fetch_one=True)
            if not article:
                raise HTTPException(status_code=404, detail="Article not found")
            if article.get("feed_id"):
                source_query = """
                SELECT s.name as source_name
                FROM source_feeds sf
                JOIN sources s ON sf.source_id = s.id
                WHERE sf.id = ?
                """
                source_result = await sources_db.execute_query(source_query, (article["feed_id"],), fetch=True, fetch_one=True)
                if source_result:
                    article["source_name"] = source_result["source_name"]
                else:
                    article["source_name"] = "Unknown Source"
            else:
                article["source_name"] = "Unknown Source"
            article.pop("feed_id", None)
            if article.get("metadata"):
                try:
                    article["metadata"] = json.loads(article["metadata"])
                except json.JSONDecodeError:
                    article["metadata"] = {}
            article["categories"] = await self.get_article_categories(article_id)
            return article
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching article: {str(e)}")

    async def get_article_categories(self, article_id: int) -> List[str]:
        """Get categories for a specific article."""
        query = """
        SELECT category_name
        FROM article_categories
        WHERE article_id = ?
        """
        categories = await tracking_db.execute_query(query, (article_id,), fetch=True)
        return [category.get("category_name", "") for category in categories]

    async def get_sources(self) -> List[str]:
        """Get all available active sources."""
        query = """
        SELECT DISTINCT name FROM sources 
        WHERE is_active = 1
        ORDER BY name
        """
        result = await sources_db.execute_query(query, fetch=True)
        return [row.get("name", "") for row in result if row.get("name")]

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all categories with article counts."""
        query = """
        SELECT category_name, COUNT(DISTINCT article_id) as article_count
        FROM article_categories
        GROUP BY category_name
        ORDER BY article_count DESC
        """
        return await tracking_db.execute_query(query, fetch=True)


article_service = ArticleService()
