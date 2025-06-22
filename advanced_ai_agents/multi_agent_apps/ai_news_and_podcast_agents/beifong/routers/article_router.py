from fastapi import APIRouter, Query
from typing import List, Optional, Dict, Any
from models.article_schemas import Article, PaginatedArticles
from services.article_service import article_service

router = APIRouter()


@router.get("/", response_model=PaginatedArticles)
async def read_articles(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    source: Optional[str] = Query(None, description="Filter by source name"),
    category: Optional[str] = Query(None, description="Filter by category"),
    date_from: Optional[str] = Query(None, description="Filter by start date (format: YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by end date (format: YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search in title and summary"),
):
    """
    Get all articles with pagination and filtering.

    - **page**: Page number (starting from 1)
    - **per_page**: Number of items per page (max 100)
    - **source**: Filter by source name
    - **category**: Filter by category
    - **date_from**: Filter by start date (format: YYYY-MM-DD)
    - **date_to**: Filter by end date (format: YYYY-MM-DD)
    - **search**: Search in title and summary
    """
    return await article_service.get_articles(
        page=page, per_page=per_page, source=source, category=category, date_from=date_from, date_to=date_to, search=search
    )


@router.get("/{article_id}", response_model=Article)
async def read_article(article_id: int):
    """
    Get a specific article by ID.

    - **article_id**: ID of the article to retrieve
    """
    return await article_service.get_article(article_id=article_id)


@router.get("/sources/list", response_model=List[str])
async def read_sources():
    """Get all available sources."""
    return await article_service.get_sources()


@router.get("/categories/list", response_model=List[Dict[str, Any]])
async def read_categories():
    """Get all available categories with article counts."""
    return await article_service.get_categories()
