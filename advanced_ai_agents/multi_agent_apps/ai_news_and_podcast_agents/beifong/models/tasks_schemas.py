from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
from enum import Enum


class TaskType(str, Enum):
    feed_processor = "feed_processor"
    url_crawler = "url_crawler"
    ai_analyzer = "ai_analyzer"
    podcast_generator = "podcast_generator"
    embedding_processor = "embedding_processor"
    faiss_indexer = "faiss_indexer"
    social_x_scraper = "social_x_scraper"
    social_fb_scraper = "social_fb_scraper"


TASK_TYPES = {
    "feed_processor": {
        "name": "Feed Processor",
        "command": "python -m processors.feed_processor",
        "description": "Processes RSS feeds and stores new entries",
    },
    "url_crawler": {"name": "URL Crawler", "command": "python -m processors.url_processor", "description": "Crawls URLs and extracts content"},
    "ai_analyzer": {
        "name": "AI Analyzer",
        "command": "python -m processors.ai_analysis_processor",
        "description": "Analyzes article content using AI",
    },
    "podcast_generator": {
        "name": "Podcast Generator",
        "command": "python -m processors.podcast_generator_processor",
        "description": "Generates podcasts from articles",
    },
    "embedding_processor": {
        "name": "Embedding Processor",
        "command": "python -m processors.embedding_processor",
        "description": "Generates embeddings for processed articles using OpenAI",
    },
    "faiss_indexer": {
        "name": "FAISS Indexer",
        "command": "python -m processors.faiss_indexing_processor",
        "description": "Updates FAISS vector index with new article embeddings",
    },
    "social_x_scraper": {
        "name": "X.com Scraper",
        "command": "python -m processors.x_scraper_processor",
        "description": "Scrapes X.com profiles and analyzes sentiment",
    },
    "social_fb_scraper": {
        "name": "Facebook.com Scraper",
        "command": "python -m processors.fb_scraper_processor",
        "description": "Scrapes Facebook.com profiles and analyzes sentiment",
    },
}


class TaskBase(BaseModel):
    name: str
    task_type: TaskType
    frequency: int
    frequency_unit: str
    description: Optional[str] = None
    enabled: bool = True

    @validator("task_type")
    def set_command_from_type(cls, v):
        if v not in TASK_TYPES:
            raise ValueError(f"Invalid task type: {v}")
        return v


class Task(TaskBase):
    id: int
    command: str
    last_run: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    task_type: Optional[TaskType] = None
    frequency: Optional[int] = None
    frequency_unit: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class TaskExecution(BaseModel):
    id: int
    task_id: int
    task_name: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    output: Optional[str] = None


class PaginatedTaskExecutions(BaseModel):
    items: List[TaskExecution]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class TaskStats(BaseModel):
    tasks: Dict[str, int]
    executions: Dict[str, Any]
