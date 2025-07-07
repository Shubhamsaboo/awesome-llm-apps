import json
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from services.db_service import social_media_db
from models.social_media_schemas import PaginatedPosts, Post
from datetime import datetime, timedelta


class SocialMediaService:
    """Service for managing social media posts."""

    async def get_posts(
        self,
        page: int = 1,
        per_page: int = 10,
        platform: Optional[str] = None,
        user_handle: Optional[str] = None,
        sentiment: Optional[str] = None,
        category: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
    ) -> PaginatedPosts:
        """Get social media posts with pagination and filtering."""
        try:
            offset = (page - 1) * per_page
            query_parts = [
                "SELECT * FROM posts",
                "WHERE 1=1",
            ]
            query_params = []
            if platform:
                query_parts.append("AND platform = ?")
                query_params.append(platform)
            if user_handle:
                query_parts.append("AND user_handle = ?")
                query_params.append(user_handle)
            if sentiment:
                query_parts.append("AND sentiment = ?")
                query_params.append(sentiment)
            if category:
                query_parts.append("AND categories LIKE ?")
                query_params.append(f'%"{category}"%')
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                query_params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                query_params.append(date_to)
            if search:
                query_parts.append("AND (post_text LIKE ? OR user_display_name LIKE ? OR user_handle LIKE ?)")
                search_param = f"%{search}%"
                query_params.extend([search_param, search_param, search_param])
            count_query = " ".join(query_parts).replace("SELECT *", "SELECT COUNT(*)")
            total_posts = await social_media_db.execute_query(count_query, tuple(query_params), fetch=True, fetch_one=True)
            total_count = total_posts.get("COUNT(*)", 0) if total_posts else 0
            query_parts.append("ORDER BY datetime(post_timestamp) DESC, post_id DESC")
            query_parts.append("LIMIT ? OFFSET ?")
            query_params.extend([per_page, offset])
            posts_query = " ".join(query_parts)
            posts_data = await social_media_db.execute_query(posts_query, tuple(query_params), fetch=True)
            posts = []
            for post in posts_data:
                post_dict = dict(post)
                if post_dict.get("media"):
                    try:
                        post_dict["media"] = json.loads(post_dict["media"])
                    except json.JSONDecodeError:
                        post_dict["media"] = []
                if post_dict.get("categories"):
                    try:
                        post_dict["categories"] = json.loads(post_dict["categories"])
                    except json.JSONDecodeError:
                        post_dict["categories"] = []
                if post_dict.get("tags"):
                    try:
                        post_dict["tags"] = json.loads(post_dict["tags"])
                    except json.JSONDecodeError:
                        post_dict["tags"] = []
                post_dict["engagement"] = {
                    "replies": post_dict.pop("engagement_reply_count", 0),
                    "retweets": post_dict.pop("engagement_retweet_count", 0),
                    "likes": post_dict.pop("engagement_like_count", 0),
                    "bookmarks": post_dict.pop("engagement_bookmark_count", 0),
                    "views": post_dict.pop("engagement_view_count", 0),
                }
                posts.append(post_dict)
            total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            return PaginatedPosts(
                items=posts,
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
            raise HTTPException(status_code=500, detail=f"Error fetching social media posts: {str(e)}")

    async def get_post(self, post_id: str) -> Dict[str, Any]:
        """Get a specific post by ID."""
        try:
            query = "SELECT * FROM posts WHERE post_id = ?"
            post = await social_media_db.execute_query(query, (post_id,), fetch=True, fetch_one=True)
            if not post:
                raise HTTPException(status_code=404, detail="Post not found")
            post_dict = dict(post)
            if post_dict.get("media"):
                try:
                    post_dict["media"] = json.loads(post_dict["media"])
                except json.JSONDecodeError:
                    post_dict["media"] = []
            if post_dict.get("categories"):
                try:
                    post_dict["categories"] = json.loads(post_dict["categories"])
                except json.JSONDecodeError:
                    post_dict["categories"] = []
            if post_dict.get("tags"):
                try:
                    post_dict["tags"] = json.loads(post_dict["tags"])
                except json.JSONDecodeError:
                    post_dict["tags"] = []
            post_dict["engagement"] = {
                "replies": post_dict.pop("engagement_reply_count", 0),
                "retweets": post_dict.pop("engagement_retweet_count", 0),
                "likes": post_dict.pop("engagement_like_count", 0),
                "bookmarks": post_dict.pop("engagement_bookmark_count", 0),
                "views": post_dict.pop("engagement_view_count", 0),
            }
            return post_dict
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching social media post: {str(e)}")

    async def get_platforms(self) -> List[str]:
        """Get all platforms that have posts."""
        query = "SELECT DISTINCT platform FROM posts ORDER BY platform"
        result = await social_media_db.execute_query(query, fetch=True)
        return [row.get("platform", "") for row in result if row.get("platform")]

    async def get_sentiments(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sentiment distribution with post counts."""
        try:
            query_parts = [
                """
                SELECT 
                    sentiment, COUNT(*) as post_count 
                FROM posts 
                WHERE sentiment IS NOT NULL
                """
            ]
            params = []
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)
            query_parts.append("GROUP BY sentiment ORDER BY post_count DESC")
            query = " ".join(query_parts)
            return await social_media_db.execute_query(query, tuple(params), fetch=True)
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching sentiments: {str(e)}")

    async def get_top_users(
        self, 
        platform: Optional[str] = None,
        limit: int = 10,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get top users by post count."""
        query_parts = ["SELECT user_handle, user_display_name, COUNT(*) as post_count", "FROM posts", "WHERE user_handle IS NOT NULL"]
        params = []
        if platform:
            query_parts.append("AND platform = ?")
            params.append(platform)
        if date_from:
            query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
            params.append(date_from)
        if date_to:
            query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
            params.append(date_to)
        query_parts.extend(["GROUP BY user_handle", "ORDER BY post_count DESC", "LIMIT ?"])
        params.append(limit)
        query = " ".join(query_parts)
        return await social_media_db.execute_query(query, tuple(params), fetch=True)

    async def get_categories(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all categories with post counts."""
        try:
            query_parts = ["SELECT categories FROM posts WHERE categories IS NOT NULL"]
            params = []
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to) 
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            category_counts = {}
            for row in result:
                if row.get("categories"):
                    try:
                        categories = json.loads(row["categories"])
                        for category in categories:
                            if category in category_counts:
                                category_counts[category] += 1
                            else:
                                category_counts[category] = 1
                    except json.JSONDecodeError:
                        pass
            return [{"category": category, "post_count": count} for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)]
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

    async def get_user_sentiment(
        self,
        limit: int = 10,
        platform: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get users with their sentiment breakdown."""
        try:
            query_parts = [
                """
                SELECT 
                    user_handle, 
                    user_display_name,
                    COUNT(*) as total_posts,
                    SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                    SUM(CASE WHEN sentiment = 'critical' THEN 1 ELSE 0 END) as critical_count
                FROM posts
                WHERE user_handle IS NOT NULL
                """
            ]
            params = []
            if platform:
                query_parts.append("AND platform = ?")
                params.append(platform)
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)
            query_parts.extend(["GROUP BY user_handle, user_display_name", "ORDER BY total_posts DESC", "LIMIT ?"])
            params.append(limit)
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            for user in result:
                total = user["total_posts"]
                user["positive_percent"] = (user["positive_count"] / total) * 100 if total > 0 else 0
                user["negative_percent"] = (user["negative_count"] / total) * 100 if total > 0 else 0
                user["neutral_percent"] = (user["neutral_count"] / total) * 100 if total > 0 else 0
                user["critical_percent"] = (user["critical_count"] / total) * 100 if total > 0 else 0
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching user sentiment: {str(e)}")

    async def get_category_sentiment(self, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sentiment distribution by category."""
        try:
            date_filter = ""
            params = []
            if date_from or date_to:
                date_filter = "WHERE "
                if date_from:
                    date_filter += "datetime(p.post_timestamp) >= datetime(?)"
                    params.append(date_from)
                    if date_to:
                        date_filter += " AND "
                if date_to:
                    date_filter += "datetime(p.post_timestamp) <= datetime(?)"
                    params.append(date_to)
            query = f"""
            WITH category_data AS (
                SELECT 
                    json_each.value as category,
                    sentiment,
                    COUNT(*) as count
                FROM 
                    posts p,
                    json_each(p.categories)
                {date_filter}
                GROUP BY 
                    json_each.value, sentiment
            )
            SELECT 
                category,
                SUM(count) as total_count,
                SUM(CASE WHEN sentiment = 'positive' THEN count ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment = 'negative' THEN count ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment = 'neutral' THEN count ELSE 0 END) as neutral_count,
                SUM(CASE WHEN sentiment = 'critical' THEN count ELSE 0 END) as critical_count
            FROM 
                category_data
            GROUP BY 
                category
            ORDER BY 
                total_count DESC
            """
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            for category in result:
                total = category["total_count"]
                category["positive_percent"] = (category["positive_count"] / total) * 100 if total > 0 else 0
                category["negative_percent"] = (category["negative_count"] / total) * 100 if total > 0 else 0
                category["neutral_percent"] = (category["neutral_count"] / total) * 100 if total > 0 else 0
                category["critical_percent"] = (category["critical_count"] / total) * 100 if total > 0 else 0
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching category sentiment: {str(e)}")

    async def get_trending_topics(
        self, 
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending topics with sentiment breakdown."""
        try:
            query_parts = [
                """
                WITH topic_data AS (
                    SELECT 
                        json_each.value as topic,
                        sentiment,
                        COUNT(*) as count
                    FROM 
                        posts,
                        json_each(posts.tags)
                    WHERE tags IS NOT NULL
                """
            ]
            params = []
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)  
            query_parts.append(
                """
                GROUP BY 
                    json_each.value, sentiment
                )
                SELECT 
                    topic,
                    SUM(count) as total_count,
                    SUM(CASE WHEN sentiment = 'positive' THEN count ELSE 0 END) as positive_count,
                    SUM(CASE WHEN sentiment = 'negative' THEN count ELSE 0 END) as negative_count,
                    SUM(CASE WHEN sentiment = 'neutral' THEN count ELSE 0 END) as neutral_count,
                    SUM(CASE WHEN sentiment = 'critical' THEN count ELSE 0 END) as critical_count
                FROM 
                    topic_data
                GROUP BY 
                    topic
                ORDER BY 
                    total_count DESC
                LIMIT ?
                """
            )
            params.append(limit)
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            for topic in result:
                total = topic["total_count"]
                topic["positive_percent"] = (topic["positive_count"] / total) * 100 if total > 0 else 0
                topic["negative_percent"] = (topic["negative_count"] / total) * 100 if total > 0 else 0
                topic["neutral_percent"] = (topic["neutral_count"] / total) * 100 if total > 0 else 0
                topic["critical_percent"] = (topic["critical_count"] / total) * 100 if total > 0 else 0
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching trending topics: {str(e)}")

    async def get_sentiment_over_time(
        self, 
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        platform: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get sentiment trends over time."""
        try:
            date_range_query = ""
            if date_from and date_to:
                date_range_query = f"""
                WITH RECURSIVE date_range(date) AS (
                    SELECT date('{date_from}')
                    UNION ALL
                    SELECT date(date, '+1 day')
                    FROM date_range
                    WHERE date < date('{date_to}')
                )
                SELECT date as post_date FROM date_range
                """
            else:
                days_ago = (datetime.now() - timedelta(days=30)).isoformat()
                date_range_query = f"""
                WITH RECURSIVE date_range(date) AS (
                    SELECT date('{days_ago}')
                    UNION ALL
                    SELECT date(date, '+1 day')
                    FROM date_range
                    WHERE date < date('now')
                )
                SELECT date as post_date FROM date_range
                """
            query_parts = [
                f"""
                WITH dates AS (
                    {date_range_query}
                )
                SELECT 
                    dates.post_date,
                    COALESCE(SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END), 0) as positive_count,
                    COALESCE(SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END), 0) as negative_count,
                    COALESCE(SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END), 0) as neutral_count,
                    COALESCE(SUM(CASE WHEN sentiment = 'critical' THEN 1 ELSE 0 END), 0) as critical_count,
                    COUNT(posts.post_id) as total_count
                FROM 
                    dates
                LEFT JOIN 
                    posts ON date(posts.post_timestamp) = dates.post_date
                """
            ]
            params = []
            if platform:
                query_parts.append("AND posts.platform = ?")
                params.append(platform)
            query_parts.append("GROUP BY dates.post_date ORDER BY dates.post_date")
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            for day in result:
                total = day["total_count"]
                day["positive_percent"] = (day["positive_count"] / total) * 100 if total > 0 else 0
                day["negative_percent"] = (day["negative_count"] / total) * 100 if total > 0 else 0
                day["neutral_percent"] = (day["neutral_count"] / total) * 100 if total > 0 else 0
                day["critical_percent"] = (day["critical_count"] / total) * 100 if total > 0 else 0
            return result
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching sentiment over time: {str(e)}")

    async def get_influential_posts(
        self, 
        sentiment: Optional[str] = None,
        limit: int = 5,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get most influential posts by engagement, optionally filtered by sentiment."""
        try:
            query_parts = [
                """
                SELECT *,
                    (COALESCE(engagement_reply_count, 0) + 
                    COALESCE(engagement_retweet_count, 0) + 
                    COALESCE(engagement_like_count, 0) + 
                    COALESCE(engagement_bookmark_count, 0)) as total_engagement
                FROM posts
                WHERE 1=1
                """
            ]
            params = []
            if sentiment:
                query_parts.append("AND sentiment = ?")
                params.append(sentiment)  
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)
            query_parts.extend(["ORDER BY total_engagement DESC", "LIMIT ?"])
            params.append(limit)
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True)
            processed_posts = []
            for post in result:
                post_dict = dict(post)
                if post_dict.get("media"):
                    try:
                        post_dict["media"] = json.loads(post_dict["media"])
                    except json.JSONDecodeError:
                        post_dict["media"] = []
                if post_dict.get("categories"):
                    try:
                        post_dict["categories"] = json.loads(post_dict["categories"])
                    except json.JSONDecodeError:
                        post_dict["categories"] = []
                if post_dict.get("tags"):
                    try:
                        post_dict["tags"] = json.loads(post_dict["tags"])
                    except json.JSONDecodeError:
                        post_dict["tags"] = []
                post_dict["engagement"] = {
                    "replies": post_dict.pop("engagement_reply_count", 0),
                    "retweets": post_dict.pop("engagement_retweet_count", 0),
                    "likes": post_dict.pop("engagement_like_count", 0),
                    "bookmarks": post_dict.pop("engagement_bookmark_count", 0),
                    "views": post_dict.pop("engagement_view_count", 0),
                }
                processed_posts.append(post_dict)
            return processed_posts
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching influential posts: {str(e)}")

    async def get_engagement_stats(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get overall engagement statistics."""
        try:
            query_parts = [
                """
                SELECT 
                    AVG(COALESCE(engagement_reply_count, 0)) as avg_replies,
                    AVG(COALESCE(engagement_retweet_count, 0)) as avg_retweets,
                    AVG(COALESCE(engagement_like_count, 0)) as avg_likes,
                    AVG(COALESCE(engagement_bookmark_count, 0)) as avg_bookmarks,
                    AVG(COALESCE(engagement_view_count, 0)) as avg_views,
                    MAX(COALESCE(engagement_reply_count, 0)) as max_replies,
                    MAX(COALESCE(engagement_retweet_count, 0)) as max_retweets,
                    MAX(COALESCE(engagement_like_count, 0)) as max_likes,
                    MAX(COALESCE(engagement_bookmark_count, 0)) as max_bookmarks,
                    MAX(COALESCE(engagement_view_count, 0)) as max_views,
                    COUNT(*) as total_posts,
                    COUNT(DISTINCT user_handle) as unique_authors
                FROM posts
                WHERE 1=1
                """
            ]
            params = []
            if date_from:
                query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
                params.append(date_from)
            if date_to:
                query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
                params.append(date_to)
            query = " ".join(query_parts)
            result = await social_media_db.execute_query(query, tuple(params), fetch=True, fetch_one=True)
            if not result:
                return {"avg_engagement": 0, "total_posts": 0, "unique_authors": 0}
            result_dict = dict(result)
            result_dict["avg_engagement"] = (
                result_dict["avg_replies"] + result_dict["avg_retweets"] + result_dict["avg_likes"] + result_dict["avg_bookmarks"]
            )
            platform_query_parts = [
                """
                SELECT 
                    platform, 
                    COUNT(*) as post_count
                FROM posts
                WHERE 1=1
                """
            ]
            if date_from:
                platform_query_parts.append("AND datetime(post_timestamp) >= datetime(?)")
            if date_to:
                platform_query_parts.append("AND datetime(post_timestamp) <= datetime(?)")
            platform_query_parts.extend([
                "GROUP BY platform",
                "ORDER BY post_count DESC",
                "LIMIT 10"
            ])
            platforms = await social_media_db.execute_query(
                " ".join(platform_query_parts), 
                tuple(params), 
                fetch=True
            )
            result_dict["platforms"] = platforms
            return result_dict
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error fetching engagement stats: {str(e)}")


social_media_service = SocialMediaService()
