from fastapi import APIRouter, HTTPException, File, UploadFile, Body, Query, Path
from fastapi.responses import FileResponse
from typing import List, Optional
import os
from datetime import datetime
from models.podcast_schemas import Podcast, PodcastDetail, PodcastCreate, PodcastUpdate, PaginatedPodcasts
from services.podcast_service import podcast_service

router = APIRouter()


@router.get("/", response_model=PaginatedPodcasts)
async def get_podcasts(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in title"),
    date_from: Optional[str] = Query(None, description="Filter by date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (YYYY-MM-DD)"),
    language_code: Optional[str] = Query(None, description="Filter by language code"),
    tts_engine: Optional[str] = Query(None, description="Filter by TTS engine"),
    has_audio: Optional[bool] = Query(None, description="Filter by audio availability"),
):
    """
    Get a paginated list of podcasts with optional filtering.
    """
    return await podcast_service.get_podcasts(
        page=page,
        per_page=per_page,
        search=search,
        date_from=date_from,
        date_to=date_to,
        language_code=language_code,
        tts_engine=tts_engine,
        has_audio=has_audio,
    )


@router.get("/formats", response_model=List[str])
async def get_podcast_formats():
    """
    Get a list of available podcast formats for filtering.
    """
    return await podcast_service.get_podcast_formats()


@router.get("/language-codes", response_model=List[str])
async def get_language_codes():
    """
    Get a list of available language codes for filtering.
    """
    return await podcast_service.get_language_codes()


@router.get("/tts-engines", response_model=List[str])
async def get_tts_engines():
    """
    Get a list of available TTS engines for filtering.
    """
    return await podcast_service.get_tts_engines()


@router.get("/{podcast_id}", response_model=PodcastDetail)
async def get_podcast(podcast_id: int = Path(..., description="The ID of the podcast to retrieve")):
    """
    Get detailed information about a specific podcast.

    Parameters:
    - **podcast_id**: The ID of the podcast to retrieve

    Returns the podcast metadata and content.
    """
    podcast = await podcast_service.get_podcast(podcast_id)
    content = await podcast_service.get_podcast_content(podcast_id)
    audio_url = await podcast_service.get_podcast_audio_url(podcast)
    sources = podcast.get("sources", [])
    if "sources" in podcast:
        del podcast["sources"]
    banner_images = podcast.get("banner_images", [])
    if "banner_images" in podcast:
        del podcast["banner_images"]
    return {"podcast": podcast, "content": content, "audio_url": audio_url, "sources": sources, "banner_images": banner_images}


@router.get("/by-identifier/{identifier}", response_model=PodcastDetail)
async def get_podcast_by_identifier(identifier: str = Path(..., description="The unique identifier of the podcast")):
    """
    Get detailed information about a specific podcast using string identifier.

    Parameters:
    - **identifier**: The unique identifier of the podcast to retrieve

    Returns the podcast metadata and content.
    """
    podcast = await podcast_service.get_podcast_by_identifier(identifier)
    podcast_id = int(podcast["id"])
    content = await podcast_service.get_podcast_content(podcast_id)
    audio_url = await podcast_service.get_podcast_audio_url(podcast)
    sources = podcast.get("sources", [])
    if "sources" in podcast:
        del podcast["sources"]
    banner_images = podcast.get("banner_images", [])
    if "banner_images" in podcast:
        del podcast["banner_images"]
    return {"podcast": podcast, "content": content, "audio_url": audio_url, "sources": sources, "banner_images": banner_images}


@router.post("/", response_model=Podcast)
async def create_podcast(podcast_data: PodcastCreate = Body(...)):
    """
    Create a new podcast.

    Parameters:
    - **podcast_data**: Podcast data including title, date, content, sources, language_code, and tts_engine

    Returns the created podcast metadata.
    """
    date = podcast_data.date or datetime.now().strftime("%Y-%m-%d")
    return await podcast_service.create_podcast(
        title=podcast_data.title,
        date=date,
        content=podcast_data.content,
        sources=podcast_data.sources,
        language_code=podcast_data.language_code,
        tts_engine=podcast_data.tts_engine,
    )


@router.put("/{podcast_id}", response_model=Podcast)
async def update_podcast(podcast_id: int = Path(..., description="The ID of the podcast to update"), podcast_data: PodcastUpdate = Body(...)):
    """
    Update an existing podcast's metadata and/or content.

    Parameters:
    - **podcast_id**: The ID of the podcast to update
    - **podcast_data**: Updated data for the podcast

    Returns the updated podcast metadata.
    """
    update_data = {k: v for k, v in podcast_data.dict().items() if v is not None}
    return await podcast_service.update_podcast(podcast_id, update_data)


@router.delete("/{podcast_id}")
async def delete_podcast(podcast_id: int = Path(..., description="The ID of the podcast to delete")):
    """
    Delete a podcast.

    Parameters:
    - **podcast_id**: The ID of the podcast to delete

    Returns a success message.
    """
    success = await podcast_service.delete_podcast(podcast_id)
    if success:
        return {"message": f"Podcast {podcast_id} deleted successfully"}
    return {"message": "No podcast was deleted"}


@router.post("/{podcast_id}/audio", response_model=Podcast)
async def upload_audio(podcast_id: int = Path(..., description="The ID of the podcast"), file: UploadFile = File(...)):
    """
    Upload an audio file for a podcast.

    Parameters:
    - **podcast_id**: The ID of the podcast to attach the audio to
    - **file**: The audio file to upload

    Returns the updated podcast.
    """
    return await podcast_service.upload_podcast_audio(podcast_id, file)


@router.post("/{podcast_id}/banner", response_model=Podcast)
async def upload_banner(podcast_id: int = Path(..., description="The ID of the podcast"), file: UploadFile = File(...)):
    """
    Upload a banner image for a podcast.

    Parameters:
    - **podcast_id**: The ID of the podcast to attach the banner to
    - **file**: The image file to upload

    Returns the updated podcast.
    """
    return await podcast_service.upload_podcast_banner(podcast_id, file)


@router.get("/audio/{filename}")
async def get_audio_file(filename: str = Path(..., description="The filename of the audio file")):
    """
    Get the audio file for a podcast.

    Parameters:
    - **filename**: The filename of the audio file to retrieve

    Returns the audio file as a download.
    """
    audio_path = os.path.join("podcasts", "audio", filename)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(audio_path)
