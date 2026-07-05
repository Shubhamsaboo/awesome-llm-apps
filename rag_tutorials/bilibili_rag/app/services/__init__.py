"""
Bilibili RAG 知识库系统

服务模块初始化
"""

__all__ = [
    "BilibiliService",
    "ContentFetcher",
    "ASRService",
    "RAGService",
    "wbi_signer"
]


def __getattr__(name):
    """Lazy-load service classes to avoid importing optional clients unnecessarily."""
    if name == "BilibiliService":
        from app.services.bilibili import BilibiliService
        return BilibiliService
    if name == "ContentFetcher":
        from app.services.content_fetcher import ContentFetcher
        return ContentFetcher
    if name == "ASRService":
        from app.services.asr import ASRService
        return ASRService
    if name == "RAGService":
        from app.services.rag import RAGService
        return RAGService
    if name == "wbi_signer":
        from app.services.wbi import wbi_signer
        return wbi_signer
    raise AttributeError(f"module 'app.services' has no attribute {name!r}")
