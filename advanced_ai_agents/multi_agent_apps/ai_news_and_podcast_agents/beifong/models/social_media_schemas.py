from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class PostBase(BaseModel):
    post_id: str
    platform: str
    user_display_name: Optional[str] = None
    user_handle: Optional[str] = None
    user_profile_pic_url: Optional[str] = None
    post_timestamp: Optional[str] = None
    post_display_time: Optional[str] = None
    post_url: Optional[str] = None
    post_text: Optional[str] = None
    post_mentions: Optional[str] = None

class PostEngagement(BaseModel):
    replies: Optional[int] = None
    retweets: Optional[int] = None
    likes: Optional[int] = None
    bookmarks: Optional[int] = None
    views: Optional[int] = None

class MediaItem(BaseModel):
    type: str 
    url: str

class Post(PostBase):
    engagement: Optional[PostEngagement] = None
    media: Optional[List[MediaItem]] = None
    media_count: Optional[int] = 0
    is_ad: Optional[bool] = False
    sentiment: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    analysis_reasoning: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PaginatedPosts(BaseModel):
    items: List[Post]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PostFilterParams(BaseModel):
    platform: Optional[str] = None
    user_handle: Optional[str] = None
    sentiment: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    search: Optional[str] = None