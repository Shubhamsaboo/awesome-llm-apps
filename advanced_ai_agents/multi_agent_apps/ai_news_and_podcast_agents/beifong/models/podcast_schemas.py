from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union


class PodcastBase(BaseModel):
    title: str
    date: str
    audio_generated: bool = False
    banner_img: Optional[str] = None
    identifier: str
    language_code: Optional[str] = "en"
    tts_engine: Optional[str] = "kokoro"


class Podcast(PodcastBase):
    id: int
    created_at: Optional[str] = None
    audio_path: Optional[str] = None

    class Config:
        from_attributes = True


class PodcastContent(BaseModel):
    title: str
    sections: List[Dict[str, Any]]


class PodcastSource(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, str):
            return cls(url=v)
        if isinstance(v, dict):
            return cls(**v)
        raise ValueError("Source must be a string or a dict")


class PodcastDetail(BaseModel):
    podcast: Podcast
    content: PodcastContent
    audio_url: Optional[str] = None
    sources: Optional[List[Union[PodcastSource, str]]] = None
    banner_images: Optional[List[str]] = None


class PodcastCreate(BaseModel):
    title: str
    date: Optional[str] = None
    content: Dict[str, Any]
    sources: Optional[List[Union[Dict[str, str], str]]] = None
    language_code: Optional[str] = "en"
    tts_engine: Optional[str] = "kokoro"


class PodcastUpdate(BaseModel):
    title: Optional[str] = None
    date: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    audio_generated: Optional[bool] = None
    sources: Optional[List[Union[Dict[str, str], str]]] = None
    language_code: Optional[str] = None
    tts_engine: Optional[str] = None


class PaginatedPodcasts(BaseModel):
    items: List[Podcast]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
