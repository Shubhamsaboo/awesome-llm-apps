from fastapi import APIRouter, Body, Path, status
from typing import List, Optional, Dict, Any
from models.source_schemas import Source, SourceWithFeeds, Category, PaginatedSources, SourceCreate, SourceUpdate, SourceFeedCreate
from services.source_service import source_service

router = APIRouter()


@router.get("/", response_model=PaginatedSources)
async def read_sources(
    page: int = 1, per_page: int = 10, category: Optional[str] = None, search: Optional[str] = None, include_inactive: bool = False
):
    """
    Get sources with pagination and filtering.

    - **page**: Page number (starting from 1)
    - **per_page**: Number of items per page
    - **category**: Filter by source category
    - **search**: Search in name and description
    - **include_inactive**: Include inactive sources
    """
    return await source_service.get_sources(page=page, per_page=per_page, category=category, search=search, include_inactive=include_inactive)


@router.get("/categories", response_model=List[Category])
async def read_categories():
    """Get all available source categories."""
    return await source_service.get_categories()


@router.get("/by-category/{category_name}", response_model=List[Source])
async def read_sources_by_category(category_name: str):
    """
    Get sources by category name.

    - **category_name**: Name of the category to filter by
    """
    return await source_service.get_source_by_category(category_name=category_name)


@router.get("/{source_id}", response_model=SourceWithFeeds)
async def read_source(source_id: int = Path(..., gt=0)):
    """
    Get detailed information about a specific source.

    - **source_id**: ID of the source to retrieve
    """
    source = await source_service.get_source(source_id=source_id)
    feeds = await source_service.get_source_feeds(source_id=source_id)
    source_with_feeds = {**source, "feeds": feeds}
    return source_with_feeds


@router.get("/by-name/{name}", response_model=SourceWithFeeds)
async def read_source_by_name(name: str):
    """
    Get detailed information about a specific source by name.

    - **name**: Name of the source to retrieve
    """
    source = await source_service.get_source_by_name(name=name)
    feeds = await source_service.get_source_feeds(source_id=source["id"])
    source_with_feeds = {**source, "feeds": feeds}
    return source_with_feeds


@router.post("/", response_model=SourceWithFeeds, status_code=status.HTTP_201_CREATED)
async def create_source(source_data: SourceCreate):
    """
    Create a new source.

    - **source_data**: Data for the new source
    """
    source = await source_service.create_source(source_data)
    feeds = await source_service.get_source_feeds(source_id=source["id"])
    source_with_feeds = {**source, "feeds": feeds}
    return source_with_feeds


@router.put("/{source_id}", response_model=SourceWithFeeds)
async def update_source(source_data: SourceUpdate, source_id: int = Path(..., gt=0)):
    """
    Update an existing source.

    - **source_id**: ID of the source to update
    - **source_data**: Updated data for the source
    """
    source = await source_service.update_source(source_id, source_data)
    feeds = await source_service.get_source_feeds(source_id=source["id"])
    source_with_feeds = {**source, "feeds": feeds}
    return source_with_feeds


@router.delete("/{source_id}", response_model=Dict[str, Any])
async def delete_source(source_id: int = Path(..., gt=0), permanent: bool = False):
    """
    Delete a source.

    - **source_id**: ID of the source to delete
    - **permanent**: If true, permanently deletes the source; otherwise, performs a soft delete
    """
    if permanent:
        return await source_service.hard_delete_source(source_id)
    return await source_service.delete_source(source_id)


@router.post("/{source_id}/feeds", response_model=List[Dict[str, Any]])
async def add_feed(feed_data: SourceFeedCreate, source_id: int = Path(..., gt=0)):
    """
    Add a new feed to a source.

    - **source_id**: ID of the source to add the feed to
    - **feed_data**: Data for the new feed
    """
    return await source_service.add_feed_to_source(source_id, feed_data)


@router.put("/feeds/{feed_id}", response_model=Dict[str, Any])
async def update_feed(feed_data: Dict[str, Any] = Body(...), feed_id: int = Path(..., gt=0)):
    """
    Update an existing feed.

    - **feed_id**: ID of the feed to update
    - **feed_data**: Updated data for the feed
    """
    return await source_service.update_feed(feed_id, feed_data)


@router.delete("/feeds/{feed_id}", response_model=Dict[str, str])
async def delete_feed(feed_id: int = Path(..., gt=0)):
    """
    Delete a feed.

    - **feed_id**: ID of the feed to delete
    """
    return await source_service.delete_feed(feed_id)
