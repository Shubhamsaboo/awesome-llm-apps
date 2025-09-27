from fastapi import APIRouter, Query, Path, Body, status
from typing import List
from models.podcast_config_schemas import PodcastConfig, PodcastConfigCreate, PodcastConfigUpdate
from services.podcast_config_service import podcast_config_service


router = APIRouter()


@router.get("/", response_model=List[PodcastConfig])
async def get_podcast_configs(
    active_only: bool = Query(False, description="Include only active podcast configs"),
):
    """
    Get all podcast configurations with optional filtering.

    - **active_only**: If true, includes only active podcast configurations
    """
    return await podcast_config_service.get_all_configs(active_only=active_only)


@router.get("/{config_id}", response_model=PodcastConfig)
async def get_podcast_config(
    config_id: int = Path(..., description="The ID of the podcast config to retrieve"),
):
    """
    Get a specific podcast configuration by ID.

    - **config_id**: The ID of the podcast configuration to retrieve
    """
    return await podcast_config_service.get_config(config_id=config_id)


@router.post("/", response_model=PodcastConfig, status_code=status.HTTP_201_CREATED)
async def create_podcast_config(config_data: PodcastConfigCreate = Body(...)):
    """
    Create a new podcast configuration.

    - **config_data**: Data for the new podcast configuration
    """
    return await podcast_config_service.create_config(
        name=config_data.name,
        prompt=config_data.prompt,
        description=config_data.description,
        time_range_hours=config_data.time_range_hours,
        limit_articles=config_data.limit_articles,
        is_active=config_data.is_active,
        tts_engine=config_data.tts_engine,
        language_code=config_data.language_code,
        podcast_script_prompt=config_data.podcast_script_prompt,
        image_prompt=config_data.image_prompt,
    )


@router.put("/{config_id}", response_model=PodcastConfig)
async def update_podcast_config(
    config_id: int = Path(..., description="The ID of the podcast config to update"),
    config_data: PodcastConfigUpdate = Body(...),
):
    """
    Update an existing podcast configuration.

    - **config_id**: The ID of the podcast configuration to update
    - **config_data**: Updated data for the podcast configuration
    """
    updates = {k: v for k, v in config_data.dict().items() if v is not None}
    return await podcast_config_service.update_config(config_id=config_id, updates=updates)


@router.delete("/{config_id}")
async def delete_podcast_config(
    config_id: int = Path(..., description="The ID of the podcast config to delete"),
):
    """
    Delete a podcast configuration.

    - **config_id**: The ID of the podcast configuration to delete
    """
    return await podcast_config_service.delete_config(config_id=config_id)


@router.post("/{config_id}/enable", response_model=PodcastConfig)
async def enable_podcast_config(
    config_id: int = Path(..., description="The ID of the podcast config to enable"),
):
    """
    Enable a podcast configuration.

    - **config_id**: The ID of the podcast configuration to enable
    """
    return await podcast_config_service.toggle_config(config_id=config_id, enable=True)


@router.post("/{config_id}/disable", response_model=PodcastConfig)
async def disable_podcast_config(
    config_id: int = Path(..., description="The ID of the podcast config to disable"),
):
    """
    Disable a podcast configuration.

    - **config_id**: The ID of the podcast configuration to disable
    """
    return await podcast_config_service.toggle_config(config_id=config_id, enable=False)
