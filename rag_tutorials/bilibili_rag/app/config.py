"""
Bilibili RAG 知识库系统

核心配置模块
"""
from pydantic_settings import BaseSettings
from pydantic import Field, AliasChoices
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""

    # OpenAI / LLM 配置
    openai_api_key: str = Field(
        default="",
        validation_alias="OPENAI_API_KEY",
    )
    nebius_api_key: str = Field(default="", validation_alias="NEBIUS_API_KEY")
    openai_base_url: str = Field(default="", validation_alias="OPENAI_BASE_URL")
    llm_model: str = Field(default="gpt-4-turbo", env="LLM_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    chat_use_llm_router: bool = Field(default=False, env="CHAT_USE_LLM_ROUTER")

    # DashScope ASR
    dashscope_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("DASHSCOPE_API_KEY", "OPENAI_API_KEY"),
    )
    dashscope_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1",
        env="DASHSCOPE_BASE_URL"
    )
    asr_model: str = Field(default="paraformer-v2", env="ASR_MODEL")
    asr_timeout: int = Field(default=600, env="ASR_TIMEOUT")
    asr_model_local: str = Field(default="paraformer-realtime-v2", env="ASR_MODEL_LOCAL")
    asr_input_format: str = Field(default="pcm", env="ASR_INPUT_FORMAT")

    # 应用配置
    app_host: str = Field(default="0.0.0.0", env="APP_HOST")
    app_port: int = Field(default=8000, env="APP_PORT")
    debug: bool = Field(default=True, env="DEBUG")

    # 数据库
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/bilibili_rag.db",
        env="DATABASE_URL"
    )

    # ChromaDB
    chroma_persist_directory: str = Field(
        default="./data/chroma_db",
        env="CHROMA_PERSIST_DIRECTORY"
    )

    # Retrieval
    retrieval_candidate_k: int = Field(default=24, env="RETRIEVAL_CANDIDATE_K")
    retrieval_top_k: int = Field(default=8, env="RETRIEVAL_TOP_K")
    retrieval_mmr_fetch_k: int = Field(default=32, env="RETRIEVAL_MMR_FETCH_K")
    retrieval_mmr_lambda: float = Field(default=0.55, env="RETRIEVAL_MMR_LAMBDA")

    @property
    def chat_api_key(self) -> str:
        """Return the configured key for OpenAI-compatible chat calls."""
        return self.nebius_api_key or self.openai_api_key or self.dashscope_api_key

    @property
    def chat_base_url(self) -> str:
        """Resolve the chat endpoint without changing DashScope SDK endpoints."""
        if self.openai_base_url:
            return self.openai_base_url
        if self.nebius_api_key:
            return "https://api.tokenfactory.nebius.com/v1"
        if self.dashscope_api_key and not self.openai_api_key:
            return "https://dashscope.aliyuncs.com/compatible-mode/v1"
        return "https://api.openai.com/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# 全局配置实例
settings = Settings()


def ensure_directories():
    """确保必要的目录存在"""
    dirs = [
        "data",
        settings.chroma_persist_directory,
        "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
