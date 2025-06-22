from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from datetime import datetime
from services.db_service import sources_db, tracking_db
from models.source_schemas import SourceCreate, SourceUpdate, SourceFeedCreate, PaginatedSources


class SourceService:
    """Service for managing source operations with the new database structure."""

    async def get_sources(
        self, page: int = 1, per_page: int = 10, category: Optional[str] = None, search: Optional[str] = None, include_inactive: bool = False
    ) -> PaginatedSources:
        """Get sources with pagination and filtering."""
        try:
            query_parts = ["SELECT s.id, s.name, s.url, s.description, s.is_active, s.created_at", "FROM sources s", "WHERE 1=1"]
            query_params = []
            if not include_inactive:
                query_parts.append("AND s.is_active = 1")
            if category:
                query_parts.append("""
                    AND EXISTS (
                        SELECT 1 FROM source_categories sc 
                        JOIN categories c ON sc.category_id = c.id
                        WHERE sc.source_id = s.id AND c.name = ?
                    )
                """)
                query_params.append(category)
            if search:
                query_parts.append("AND (s.name LIKE ? OR s.description LIKE ?)")
                search_param = f"%{search}%"
                query_params.extend([search_param, search_param])
            count_query = " ".join(query_parts).replace("SELECT s.id, s.name, s.url, s.description, s.is_active, s.created_at", "SELECT COUNT(*)")
            total_sources = await sources_db.execute_query(count_query, tuple(query_params), fetch=True, fetch_one=True)
            total_count = total_sources.get("COUNT(*)", 0) if total_sources else 0
            query_parts.append("ORDER BY s.name")
            offset = (page - 1) * per_page
            query_parts.append("LIMIT ? OFFSET ?")
            query_params.extend([per_page, offset])
            final_query = " ".join(query_parts)
            sources = await sources_db.execute_query(final_query, tuple(query_params), fetch=True)
            for source in sources:
                source["categories"] = await self.get_source_categories(source["id"])
                source["last_crawled"] = await self.get_source_last_crawled(source["id"])
                source["website"] = source["url"]
                if source["categories"] and isinstance(source["categories"], list):
                    source["category"] = source["categories"][0] if source["categories"] else ""
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            return PaginatedSources(
                items=sources, total=total_count, page=page, per_page=per_page, total_pages=total_pages, has_next=has_next, has_prev=has_prev
            )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching sources: {str(e)}")

    async def get_source(self, source_id: int) -> Dict[str, Any]:
        """Get a specific source by ID."""
        query = """
        SELECT id, name, url, description, is_active, created_at
        FROM sources
        WHERE id = ?
        """
        source = await sources_db.execute_query(query, (source_id,), fetch=True, fetch_one=True)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        source["categories"] = await self.get_source_categories(source["id"])
        source["last_crawled"] = await self.get_source_last_crawled(source["id"])
        source["website"] = source["url"]
        if source["categories"] and isinstance(source["categories"], list):
            source["category"] = source["categories"][0] if source["categories"] else ""
        return source

    async def get_source_categories(self, source_id: int) -> List[str]:
        """Get all categories for a specific source."""
        query = """
        SELECT c.name
        FROM source_categories sc
        JOIN categories c ON sc.category_id = c.id
        WHERE sc.source_id = ?
        ORDER BY c.name
        """
        categories = await sources_db.execute_query(query, (source_id,), fetch=True)
        return [category.get("name", "") for category in categories if category.get("name")]

    async def get_source_last_crawled(self, source_id: int) -> Optional[str]:
        """Get the last crawl time for a source's feeds."""
        query = """
        SELECT MAX(ft.last_processed) as last_crawled
        FROM feed_tracking ft
        WHERE ft.source_id = ?
        """
        result = await tracking_db.execute_query(query, (source_id,), fetch=True, fetch_one=True)
        return result.get("last_crawled") if result else None

    async def get_source_by_name(self, name: str) -> Dict[str, Any]:
        """Get a specific source by name."""
        query = """
        SELECT id, name, url, description, is_active, created_at
        FROM sources
        WHERE name = ?
        """
        source = await sources_db.execute_query(query, (name,), fetch=True, fetch_one=True)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        source["categories"] = await self.get_source_categories(source["id"])
        source["last_crawled"] = await self.get_source_last_crawled(source["id"])
        source["website"] = source["url"]
        if source["categories"] and isinstance(source["categories"], list):
            source["category"] = source["categories"][0] if source["categories"] else ""
        return source

    async def get_source_feeds(self, source_id: int) -> List[Dict[str, Any]]:
        """Get all feeds for a specific source."""
        query = """
        SELECT id, feed_url, feed_type, is_active, created_at, last_crawled
        FROM source_feeds
        WHERE source_id = ?
        ORDER BY feed_type
        """
        feeds = await sources_db.execute_query(query, (source_id,), fetch=True)
        for feed in feeds:
            feed["description"] = feed.get("feed_type", "Main feed").capitalize()
        return feeds

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all source categories."""
        query = """
        SELECT id, name
        FROM categories
        ORDER BY name
        """
        categories = await sources_db.execute_query(query, fetch=True)
        for category in categories:
            category["description"] = f"Articles about {category.get('name', '')}"
        return categories

    async def get_source_by_category(self, category_name: str) -> List[Dict[str, Any]]:
        """Get sources by category using the junction table."""
        query = """
        SELECT s.id, s.name, s.url, s.description, s.is_active
        FROM sources s
        JOIN source_categories sc ON s.id = sc.source_id
        JOIN categories c ON sc.category_id = c.id
        WHERE c.name = ? AND s.is_active = 1
        ORDER BY s.name
        """
        sources = await sources_db.execute_query(query, (category_name,), fetch=True)
        for source in sources:
            source["categories"] = await self.get_source_categories(source["id"])
            source["website"] = source["url"]
            if source["categories"] and isinstance(source["categories"], list):
                source["category"] = source["categories"][0] if source["categories"] else ""
        return sources

    async def create_source(self, source_data: SourceCreate) -> Dict[str, Any]:
        """Create a new source."""
        try:
            source_query = """
            INSERT INTO sources (name, url, description, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
            source_params = (source_data.name, source_data.url, source_data.description, source_data.is_active, datetime.now().isoformat())
            source_id = await sources_db.execute_query(source_query, source_params)
            if source_data.categories:
                for category_name in source_data.categories:
                    await self.add_source_category(source_id, category_name)
            elif hasattr(source_data, "category") and source_data.category:
                await self.add_source_category(source_id, source_data.category)
            if source_data.feeds:
                for feed in source_data.feeds:
                    await self.add_feed_to_source(source_id, feed)
            return await self.get_source(source_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            if "UNIQUE constraint failed" in str(e) and "name" in str(e):
                raise HTTPException(status_code=409, detail="Source with this name already exists")
            raise HTTPException(status_code=500, detail=f"Error creating source: {str(e)}")

    async def add_source_category(self, source_id: int, category_name: str) -> None:
        """Add a category to a source, creating the category if it doesn't exist."""
        category_query = """
        INSERT OR IGNORE INTO categories (name, created_at)
        VALUES (?, ?)
        """
        await sources_db.execute_query(category_query, (category_name, datetime.now().isoformat()))
        get_category_id_query = "SELECT id FROM categories WHERE name = ?"
        category = await sources_db.execute_query(get_category_id_query, (category_name,), fetch=True, fetch_one=True)
        if not category:
            raise HTTPException(status_code=500, detail=f"Failed to find or create category: {category_name}")
        link_query = """
        INSERT OR IGNORE INTO source_categories (source_id, category_id)
        VALUES (?, ?)
        """
        await sources_db.execute_query(link_query, (source_id, category["id"]))

    async def update_source(self, source_id: int, source_data: SourceUpdate) -> Dict[str, Any]:
        """Update an existing source."""
        try:
            await self.get_source(source_id)
            update_fields = []
            update_params = []
            if source_data.name is not None:
                update_fields.append("name = ?")
                update_params.append(source_data.name)
            if source_data.url is not None:
                update_fields.append("url = ?")
                update_params.append(source_data.url)
            if source_data.description is not None:
                update_fields.append("description = ?")
                update_params.append(source_data.description)
            if source_data.is_active is not None:
                update_fields.append("is_active = ?")
                update_params.append(source_data.is_active)
            if update_fields:
                update_params.append(source_id)
                update_query = f"""
                UPDATE sources
                SET {", ".join(update_fields)}
                WHERE id = ?
                """
                await sources_db.execute_query(update_query, tuple(update_params))
            if source_data.categories is not None:
                delete_categories_query = "DELETE FROM source_categories WHERE source_id = ?"
                await sources_db.execute_query(delete_categories_query, (source_id,))
                if source_data.categories:
                    for category_name in source_data.categories:
                        await self.add_source_category(source_id, category_name)
            elif hasattr(source_data, "category") and source_data.category is not None:
                delete_categories_query = "DELETE FROM source_categories WHERE source_id = ?"
                await sources_db.execute_query(delete_categories_query, (source_id,))
                if source_data.category:
                    await self.add_source_category(source_id, source_data.category)
            return await self.get_source(source_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            if "UNIQUE constraint failed" in str(e) and "name" in str(e):
                raise HTTPException(status_code=409, detail="Source with this name already exists")
            raise HTTPException(status_code=500, detail=f"Error updating source: {str(e)}")

    async def delete_source(self, source_id: int) -> Dict[str, Any]:
        """Delete a source (soft delete by setting is_active to false)."""
        try:
            source = await self.get_source(source_id)
            update_query = """
            UPDATE sources
            SET is_active = 0
            WHERE id = ?
            """
            await sources_db.execute_query(update_query, (source_id,))
            feeds_query = """
            UPDATE source_feeds
            SET is_active = 0
            WHERE source_id = ?
            """
            await sources_db.execute_query(feeds_query, (source_id,))
            return {**source, "is_active": False}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error deleting source: {str(e)}")

    async def hard_delete_source(self, source_id: int) -> Dict[str, str]:
        """Permanently delete a source and its feeds."""
        try:
            source = await self.get_source(source_id)
            delete_feeds_query = """
            DELETE FROM source_feeds
            WHERE source_id = ?
            """
            await sources_db.execute_query(delete_feeds_query, (source_id,))
            delete_categories_query = """
            DELETE FROM source_categories
            WHERE source_id = ?
            """
            await sources_db.execute_query(delete_categories_query, (source_id,))
            delete_source_query = """
            DELETE FROM sources
            WHERE id = ?
            """
            await sources_db.execute_query(delete_source_query, (source_id,))
            return {"message": f"Source '{source['name']}' has been permanently deleted"}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error deleting source: {str(e)}")

    async def add_feed_to_source(self, source_id: int, feed_data: SourceFeedCreate) -> Dict[str, Any]:
        """Add a new feed to an existing source."""
        try:
            await self.get_source(source_id)
            check_query = """
            SELECT id, source_id FROM source_feeds WHERE feed_url = ?
            """
            existing_feed = await sources_db.execute_query(check_query, (feed_data.feed_url,), fetch=True, fetch_one=True)
            if existing_feed:
                source_query = """
                SELECT name FROM sources WHERE id = ?
                """
                source = await sources_db.execute_query(source_query, (existing_feed["source_id"],), fetch=True, fetch_one=True)
                source_name = source["name"] if source else "another source"
                raise HTTPException(
                    status_code=409,
                    detail=f"A feed with this URL already exists for {source_name}. Please edit the existing feed (ID: {existing_feed['id']}) instead.",
                )
            feed_query = """
            INSERT INTO source_feeds (source_id, feed_url, feed_type, is_active, created_at)
            VALUES (?, ?, ?, ?, ?)
            """
            feed_params = (source_id, feed_data.feed_url, feed_data.feed_type, feed_data.is_active, datetime.now().isoformat())
            await sources_db.execute_query(feed_query, feed_params)
            return await self.get_source_feeds(source_id)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            if "UNIQUE constraint failed" in str(e) and "feed_url" in str(e):
                raise HTTPException(status_code=409, detail="This feed URL already exists. Please check your existing feeds or try a different URL.")
            raise HTTPException(status_code=500, detail=f"Error adding feed: {str(e)}")

    async def update_feed(self, feed_id: int, feed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing feed."""
        try:
            feed_query = "SELECT id, source_id FROM source_feeds WHERE id = ?"
            feed = await sources_db.execute_query(feed_query, (feed_id,), fetch=True, fetch_one=True)
            if not feed:
                raise HTTPException(status_code=404, detail="Feed not found")
            update_fields = []
            update_params = []
            if "feed_url" in feed_data:
                update_fields.append("feed_url = ?")
                update_params.append(feed_data["feed_url"])
            if "feed_type" in feed_data:
                update_fields.append("feed_type = ?")
                update_params.append(feed_data["feed_type"])
            if "is_active" in feed_data:
                update_fields.append("is_active = ?")
                update_params.append(feed_data["is_active"])
            if not update_fields:
                return await self.get_source_feeds(feed["source_id"])
            update_params.append(feed_id)
            update_query = f"""
            UPDATE source_feeds
            SET {", ".join(update_fields)}
            WHERE id = ?
            """
            await sources_db.execute_query(update_query, tuple(update_params))
            return await self.get_source_feeds(feed["source_id"])
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            if "UNIQUE constraint failed" in str(e) and "feed_url" in str(e):
                raise HTTPException(status_code=409, detail="Feed URL already exists")
            raise HTTPException(status_code=500, detail=f"Error updating feed: {str(e)}")

    async def delete_feed(self, feed_id: int) -> Dict[str, str]:
        """Delete a feed."""
        try:
            feed_query = "SELECT * FROM source_feeds WHERE id = ?"
            feed = await sources_db.execute_query(feed_query, (feed_id,), fetch=True, fetch_one=True)
            if not feed:
                raise HTTPException(status_code=404, detail="Feed not found")
            delete_query = "DELETE FROM source_feeds WHERE id = ?"
            await sources_db.execute_query(delete_query, (feed_id,))
            return {"message": "Feed has been deleted"}
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error deleting feed: {str(e)}")


source_service = SourceService()
