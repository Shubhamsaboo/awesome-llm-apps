from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from services.social_media_service import social_media_service
from models.social_media_schemas import PaginatedPosts, Post
import threading
from tools.social.browser import setup_session_multi

router = APIRouter()


@router.get("/", response_model=PaginatedPosts)
async def read_posts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    platform: Optional[str] = Query(None, description="Filter by platform (e.g., x.com, instagram)"),
    user_handle: Optional[str] = Query(None, description="Filter by user handle"),
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    category: Optional[str] = Query(None, description="Filter by category"),
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search in post text, user display name, or handle"),
):
    """
    Get all social media posts with pagination and filtering.
    """
    return await social_media_service.get_posts(
        page=page,
        per_page=per_page,
        platform=platform,
        user_handle=user_handle,
        sentiment=sentiment,
        category=category,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )


@router.get("/{post_id}", response_model=Post)
async def read_post(post_id: str):
    """
    Get a specific social media post by ID.
    """
    return await social_media_service.get_post(post_id=post_id)


@router.get("/platforms/list", response_model=List[str])
async def read_platforms():
    """Get all available platforms."""
    return await social_media_service.get_platforms()


@router.get("/sentiments/list", response_model=List[Dict[str, Any]])
async def read_sentiments(
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get sentiment distribution with post counts."""
    return await social_media_service.get_sentiments(date_from=date_from, date_to=date_to)


@router.get("/users/top", response_model=List[Dict[str, Any]])
async def read_top_users(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(10, ge=1, le=50, description="Number of top users to return"),
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get top users by post count."""
    return await social_media_service.get_top_users(platform=platform, limit=limit, date_from=date_from, date_to=date_to)


@router.get("/categories/list", response_model=List[Dict[str, Any]])
async def read_categories(
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get all categories with post counts."""
    return await social_media_service.get_categories(date_from=date_from, date_to=date_to)


@router.get("/users/sentiment", response_model=List[Dict[str, Any]])
async def read_user_sentiment(
    limit: int = Query(10, ge=1, le=50, description="Number of users to return"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get users with their sentiment breakdown."""
    return await social_media_service.get_user_sentiment(limit=limit, platform=platform, date_from=date_from, date_to=date_to)


@router.get("/categories/sentiment", response_model=List[Dict[str, Any]])
async def read_category_sentiment(
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get sentiment distribution by category."""
    return await social_media_service.get_category_sentiment(date_from=date_from, date_to=date_to)


@router.get("/topic/trends", response_model=List[Dict[str, Any]])
async def read_trending_topics(
    limit: int = Query(10, ge=1, le=50, description="Number of topics to return"),
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get trending topics with sentiment breakdown."""
    return await social_media_service.get_trending_topics(date_from=date_from, date_to=date_to, limit=limit)


@router.get("/trends/time", response_model=List[Dict[str, Any]])
async def read_sentiment_over_time(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get sentiment trends over time."""
    return await social_media_service.get_sentiment_over_time(date_from=date_from, date_to=date_to, platform=platform)


@router.get("/posts/influential", response_model=List[Dict[str, Any]])
async def read_influential_posts(
    sentiment: Optional[str] = Query(None, description="Filter by sentiment"),
    limit: int = Query(5, ge=1, le=20, description="Number of posts to return"),
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get most influential posts by engagement, optionally filtered by sentiment."""
    return await social_media_service.get_influential_posts(sentiment=sentiment, limit=limit, date_from=date_from, date_to=date_to)


@router.get("/engagement/stats", response_model=Dict[str, Any])
async def read_engagement_stats(
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
):
    """Get overall engagement statistics."""
    return await social_media_service.get_engagement_stats(date_from=date_from, date_to=date_to)


def _run_browser_setup_background(sites: Optional[List[str]] = None):
    """Background task to run browser session setup in separate thread."""
    try:
        if sites and len(sites) > 1:
            setup_session_multi(sites)
        elif sites and len(sites) > 0:
            setup_session_multi(sites)
        else:
            default_sites = ["https://x.com", "https://facebook.com"]
            setup_session_multi(default_sites)
    except Exception as e:
        print(f"Browser setup error: {e}")


@router.post("/session/setup")
async def setup_browser_session(sites: Optional[List[str]] = Query(None, description="List of sites to setup sessions for")):
    """
    Trigger browser session setup in a completely separate thread.
    This will open a browser window for manual login to social media platforms.
    The API immediately returns while the browser setup runs independently.
    """
    thread = threading.Thread(
        target=_run_browser_setup_background,
        args=(sites,),
        daemon=True,
    )
    thread.start()
    return {
        "status": "ok",
        "message": "Browser session setup triggered successfully",
        "note": "Browser window will open shortly for manual authentication",
    }