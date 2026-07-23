"""
Bilibili RAG 知识库系统

知识库路由 - 构建和管理知识库
"""
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends, Response
from loguru import logger
from typing import List, Optional, Callable, Literal
from pydantic import BaseModel
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, get_db_context
from app.models import FavoriteFolder, FavoriteVideo, VideoCache, UserSession, ContentSource, VideoContent
from app.services.bilibili import BilibiliService
from app.services.content_fetcher import ContentFetcher
from app.services.asr import ASRService
from app.services.rag import RAGService
from app.services.markdown_export import build_video_markdown, organize_video_content
from app.services.cancellation import CancelCheck, OperationCancelled, ensure_not_cancelled
from app.routers.auth import get_session

router = APIRouter(prefix="/knowledge", tags=["知识库"])

# 全局 RAG 服务实例
_rag_service: Optional[RAGService] = None

# 构建任务状态
build_tasks = {}

# 单视频导出/入库操作取消状态
active_operations: dict[str, tuple[str, asyncio.Event]] = {}


def get_rag_service() -> RAGService:
    """获取 RAG 服务实例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


class BuildRequest(BaseModel):
    """知识库构建请求"""
    folder_ids: List[int]  # 要处理的收藏夹 ID 列表
    exclude_bvids: Optional[List[str]] = None  # 排除的视频


class BuildStatus(BaseModel):
    """构建状态"""
    task_id: str
    status: str  # pending / running / completed / failed
    progress: int  # 0-100
    current_step: str
    total_videos: int
    processed_videos: int
    total_folders: Optional[int] = None
    processed_folders: Optional[int] = None
    current_folder_id: Optional[int] = None
    current_folder_title: Optional[str] = None
    current_video_title: Optional[str] = None
    message: str


class FolderStatus(BaseModel):
    """收藏夹入库状态"""
    media_id: int
    indexed_count: int
    failed_count: int = 0
    media_count: Optional[int] = None
    last_sync_at: Optional[datetime] = None


class SyncRequest(BaseModel):
    """同步请求"""
    folder_ids: Optional[List[int]] = None


class SyncResult(BaseModel):
    """同步结果"""
    folder_id: int
    total: int
    added: int
    removed: int
    indexed: int
    failed: int = 0
    message: str
    last_sync_at: Optional[datetime] = None


class MarkdownExportRequest(BaseModel):
    """视频 Markdown 导出请求"""
    mode: Literal["original", "ai"] = "original"
    operation_id: Optional[str] = None


class SingleVideoIngestRequest(BaseModel):
    """单视频入库请求"""
    folder_id: int
    operation_id: Optional[str] = None


def _start_operation(operation_id: Optional[str], session_id: str) -> Optional[asyncio.Event]:
    if not operation_id:
        return None
    existing = active_operations.get(operation_id)
    if existing:
        raise HTTPException(status_code=409, detail="操作标识已被占用")
    event = asyncio.Event()
    active_operations[operation_id] = (session_id, event)
    return event


def _finish_operation(operation_id: Optional[str], session_id: str) -> None:
    if not operation_id:
        return
    existing = active_operations.get(operation_id)
    if existing and existing[0] == session_id:
        active_operations.pop(operation_id, None)


async def _get_session_ids_for_user(db: AsyncSession, session_id: str) -> List[str]:
    """获取当前 Session 及同一 B 站账号的历史 Session。"""
    mid = await db.scalar(
        select(UserSession.bili_mid).where(UserSession.session_id == session_id)
    )
    if not mid:
        return [session_id]
    rows = await db.execute(
        select(UserSession.session_id).where(UserSession.bili_mid == mid)
    )
    session_ids = [row[0] for row in rows.fetchall()]
    return session_ids or [session_id]


async def _get_or_create_folder(
    db: AsyncSession,
    session_id: str,
    media_id: int,
    title: Optional[str] = None,
    media_count: Optional[int] = None,
) -> FavoriteFolder:
    """获取或创建收藏夹记录"""
    result = await db.execute(
        select(FavoriteFolder).where(
            FavoriteFolder.session_id == session_id,
            FavoriteFolder.media_id == media_id,
        )
    )
    folder = result.scalar_one_or_none()

    if folder is None:
        folder = FavoriteFolder(
            session_id=session_id,
            media_id=media_id,
            title=title or "",
            media_count=media_count or 0,
            is_selected=True,
        )
        db.add(folder)
        await db.flush()
    else:
        if title:
            folder.title = title
        if media_count is not None:
            folder.media_count = media_count

    return folder


def _extract_video_info(media: dict) -> tuple[str, str, Optional[int]]:
    """抽取视频关键信息"""
    bvid = media.get("bvid") or media.get("bv_id")
    title = media.get("title", bvid)
    cid = None
    ugc = media.get("ugc") or {}
    if ugc.get("first_cid"):
        cid = ugc.get("first_cid")
    else:
        cid = media.get("cid") or media.get("id")
    return bvid, title, cid


async def _upsert_video_cache(db: AsyncSession, bvid: str, meta: dict) -> None:
    """写入或更新视频缓存信息"""
    result = await db.execute(select(VideoCache).where(VideoCache.bvid == bvid))
    cache = result.scalar_one_or_none()

    if cache is None:
        cache = VideoCache(
            bvid=bvid,
            title=meta.get("title") or bvid,
            description=meta.get("intro"),
            owner_name=meta.get("owner_name"),
            owner_mid=meta.get("owner_mid"),
            duration=meta.get("duration"),
            pic_url=meta.get("cover"),
            is_processed=False,
        )
        db.add(cache)
        return

    cache.title = meta.get("title") or cache.title
    if meta.get("intro") is not None:
        cache.description = meta.get("intro")
    if meta.get("owner_name") is not None:
        cache.owner_name = meta.get("owner_name")
    if meta.get("owner_mid") is not None:
        cache.owner_mid = meta.get("owner_mid")
    if meta.get("duration") is not None:
        cache.duration = meta.get("duration")
    if meta.get("cover") is not None:
        cache.pic_url = meta.get("cover")


async def _ingest_single_video(
    db: AsyncSession,
    bili: BilibiliService,
    rag: RAGService,
    content_fetcher: ContentFetcher,
    session_id: str,
    folder_id: int,
    bvid: str,
    cancel_check: CancelCheck = None,
) -> VideoCache:
    """验证收藏关系并将单个视频写入缓存与向量库。"""
    ensure_not_cancelled(cancel_check)
    info_result = await bili.get_favorite_content(folder_id, pn=1, ps=1)
    ensure_not_cancelled(cancel_check)
    folder_info = info_result.get("info", {})
    videos = await bili.get_all_favorite_videos(folder_id)
    ensure_not_cancelled(cancel_check)
    media = next((item for item in videos if (item.get("bvid") or item.get("bv_id")) == bvid), None)
    if media is None:
        raise HTTPException(status_code=404, detail="该视频不在指定收藏夹中")

    title = media.get("title", bvid)
    if media.get("attr", 0) == 9 or title in ["已失效视频", "已删除视频"]:
        raise HTTPException(status_code=409, detail="视频已失效，无法入库")

    _, title, cid = _extract_video_info(media)
    owner = media.get("upper") or {}
    meta = {
        "title": title,
        "cid": cid,
        "intro": media.get("intro"),
        "cover": media.get("cover"),
        "duration": media.get("duration"),
        "owner_name": owner.get("name"),
        "owner_mid": owner.get("mid"),
    }
    folder = await _get_or_create_folder(
        db,
        session_id=session_id,
        media_id=folder_id,
        title=folder_info.get("title"),
        media_count=folder_info.get("media_count", len(videos)),
    )
    ensure_not_cancelled(cancel_check)
    await _upsert_video_cache(db, bvid, meta)
    cache = await db.scalar(select(VideoCache).where(VideoCache.bvid == bvid))
    if cache is None:
        raise RuntimeError("写入视频缓存失败")

    relation = await db.scalar(
        select(FavoriteVideo.id).where(
            FavoriteVideo.folder_id == folder.id,
            FavoriteVideo.bvid == bvid,
        )
    )
    if relation is None:
        db.add(FavoriteVideo(folder_id=folder.id, bvid=bvid, is_selected=True))

    try:
        ensure_not_cancelled(cancel_check)
        has_vectors = await asyncio.to_thread(rag.has_video, bvid)
        ensure_not_cancelled(cancel_check)
        if not (cache.content or "").strip() or not cache.is_processed or not has_vectors:
            content = await content_fetcher.fetch_content(
                bvid,
                cid=meta["cid"],
                title=meta["title"],
                description=meta.get("intro"),
                owner_name=meta.get("owner_name"),
                owner_mid=meta.get("owner_mid"),
                duration=meta.get("duration"),
            )
            ensure_not_cancelled(cancel_check)
            cache.content = content.content
            cache.content_source = content.source.value
            cache.outline_json = content.outline
            if has_vectors:
                await asyncio.to_thread(rag.delete_video, bvid)
                ensure_not_cancelled(cancel_check)
            chunks = await asyncio.to_thread(
                rag.add_video_content,
                content,
                cancel_check,
            )
            ensure_not_cancelled(cancel_check)
            if chunks <= 0:
                raise RuntimeError("未生成可写入的向量文档")
            _set_cache_processing_result(cache)

        folder.last_sync_at = datetime.utcnow()
        ensure_not_cancelled(cancel_check)
        await db.commit()
        return cache
    except OperationCancelled:
        await db.rollback()
        raise
    except Exception as e:
        _set_cache_processing_result(cache, e)
        await db.commit()
        raise


def _set_cache_processing_result(cache: Optional[VideoCache], error: Optional[Exception] = None) -> None:
    """记录内容是否已成功写入向量库。"""
    if cache is None:
        return
    cache.is_processed = error is None
    cache.process_error = str(error) if error else None


async def _sync_folder(
    db: AsyncSession,
    bili: BilibiliService,
    rag: RAGService,
    content_fetcher: ContentFetcher,
    session_id: str,
    folder_id: int,
    exclude_bvids: Optional[set[str]] = None,
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> dict:
    """同步单个收藏夹到向量库"""
    info = {}
    try:
        info_result = await bili.get_favorite_content(folder_id, pn=1, ps=1)
        info = info_result.get("info", {})
    except Exception as e:
        logger.warning(f"获取收藏夹信息失败 [{folder_id}]: {e}")

    videos = await bili.get_all_favorite_videos(folder_id)
    total_in_folder = info.get("media_count", len(videos))

    # 保护：接口异常返回空列表时，避免误删
    if not videos:
        if total_in_folder and total_in_folder > 0:
            raise RuntimeError(
                f"收藏夹 {folder_id} 返回空列表，已中止同步以避免误删"
            )

    video_map = {}
    skipped_invalid = 0
    for media in videos:
        bvid, title, cid = _extract_video_info(media)
        if not bvid:
            continue
        if exclude_bvids and bvid in exclude_bvids:
            continue

        # 过滤失效视频（被删除、下架等）
        # attr 字段: 0=正常, 9=已失效, 1=私密等
        attr = media.get("attr", 0)
        if attr == 9 or title in ["已失效视频", "已删除视频"]:
            skipped_invalid += 1
            logger.debug(f"跳过失效视频: {bvid} - {title}")
            continue

        owner = media.get("upper") or {}
        video_map[bvid] = {
            "title": title,
            "cid": cid,
            "intro": media.get("intro"),
            "cover": media.get("cover"),
            "duration": media.get("duration"),
            "owner_name": owner.get("name"),
            "owner_mid": owner.get("mid"),
        }

    if skipped_invalid > 0:
        logger.info(f"[{folder_id}] 过滤了 {skipped_invalid} 个失效视频")

    # 以有效视频数作为统计口径（过滤失效视频）
    valid_count = len(video_map)
    current_bvids = set(video_map.keys())

    folder = await _get_or_create_folder(
        db,
        session_id=session_id,
        media_id=folder_id,
        title=info.get("title"),
        media_count=valid_count,
    )

    existing_rows = await db.execute(
        select(FavoriteVideo.bvid).where(FavoriteVideo.folder_id == folder.id)
    )
    existing_bvids = {row[0] for row in existing_rows.fetchall()}

    added = current_bvids - existing_bvids
    removed = existing_bvids - current_bvids

    # 写入标题/简介等信息
    for bvid, meta in video_map.items():
        await _upsert_video_cache(db, bvid, meta)

    source_priority = {
        ContentSource.BASIC_INFO.value: 1,
        ContentSource.AI_SUMMARY.value: 2,
        ContentSource.SUBTITLE.value: 3,
        ContentSource.ASR.value: 4,
    }

    def _is_better_source(new_source: str, old_source: Optional[str]) -> bool:
        return source_priority.get(new_source, 0) > source_priority.get(old_source or "", 0)

    def _should_refresh_cache(cache: Optional[VideoCache]) -> bool:
        if not cache:
            return True
        text = (cache.content or "").strip()
        if len(text) < 50:
            return True
        if cache.content_source in (None, "", ContentSource.BASIC_INFO.value):
            return True
        return False

    def _is_asr_cache_usable(cache: Optional[VideoCache]) -> bool:
        if not cache:
            return False
        if cache.content_source != ContentSource.ASR.value:
            return False
        text = (cache.content or "").strip()
        return len(text) >= 50

    # 需要更新的已存在视频（缓存过少或来源较弱）
    update_candidates: set[str] = set()
    vector_presence: dict[str, bool] = {}
    for bvid in current_bvids & existing_bvids:
        if bvid in added:
            continue
        result = await db.execute(select(VideoCache).where(VideoCache.bvid == bvid))
        cache = result.scalar_one_or_none()
        has_vectors = rag.has_video(bvid)
        vector_presence[bvid] = has_vectors
        if cache and cache.is_processed and not has_vectors:
            _set_cache_processing_result(cache, RuntimeError("向量数据缺失，等待重新入库"))
        if _should_refresh_cache(cache) or cache is None or not cache.is_processed or not has_vectors:
            update_candidates.add(bvid)

    # 新增/更新向量与关联
    targets = list(added) + list(update_candidates)
    total_targets = len(targets)
    processed_targets = 0
    failed_targets = 0
    if progress_callback:
        progress_callback("准备处理", processed_targets, total_targets)
    for bvid in targets:
        meta = video_map[bvid]
        cache = None

        # 收藏关系与向量状态分开保存，失败的视频可在下次同步时重试。
        try:
            global_count = await db.scalar(
                select(func.count()).select_from(FavoriteVideo).where(FavoriteVideo.bvid == bvid)
            )
            # 检查缓存内容是否缺失
            result = await db.execute(select(VideoCache).where(VideoCache.bvid == bvid))
            cache = result.scalar_one_or_none()
            old_content = (cache.content or "").strip() if cache else ""
            old_source = cache.content_source if cache else None
            has_vectors = vector_presence.get(bvid)
            if has_vectors is None:
                has_vectors = rag.has_video(bvid)

            needs_fetch = _should_refresh_cache(cache)
            content = None
            should_update_cache = False
            should_reindex = False

            if needs_fetch:
                content = await content_fetcher.fetch_content(
                    bvid,
                    cid=meta["cid"],
                    title=meta["title"],
                    description=meta.get("intro"),
                    owner_name=meta.get("owner_name"),
                    owner_mid=meta.get("owner_mid"),
                    duration=meta.get("duration"),
                )
                new_text = (content.content or "").strip() if content else ""
                new_source = content.source.value if content else None

                if not old_content:
                    should_update_cache = True
                    should_reindex = True
                elif new_source and _is_better_source(new_source, old_source):
                    should_update_cache = True
                    should_reindex = True
                elif new_text and new_text != old_content:
                    should_update_cache = True
                    should_reindex = True

                if cache and should_update_cache:
                    cache.content = content.content
                    cache.content_source = content.source.value
                    cache.outline_json = content.outline
                    logger.info(f"[{bvid}] 已写入缓存: source={cache.content_source}")

            # 需要重建向量：新增/升级/内容变化 或 向量缺失
            if (global_count == 0) or should_reindex or cache is None or not cache.is_processed or not has_vectors:
                if not content:
                    if _is_asr_cache_usable(cache):
                        content = VideoContent(
                            bvid=bvid,
                            title=meta["title"],
                            content=(cache.content or "").strip(),
                            source=ContentSource.ASR,
                            outline=cache.outline_json,
                            description=meta.get("intro"),
                            owner_name=meta.get("owner_name"),
                            owner_mid=meta.get("owner_mid"),
                            duration=meta.get("duration"),
                        )
                        logger.info(f"[{bvid}] 使用缓存 ASR 内容重建向量")
                    else:
                        content = await content_fetcher.fetch_content(
                            bvid,
                            cid=meta["cid"],
                            title=meta["title"],
                            description=meta.get("intro"),
                            owner_name=meta.get("owner_name"),
                            owner_mid=meta.get("owner_mid"),
                            duration=meta.get("duration"),
                        )
                        if cache:
                            cache.content = content.content
                            cache.content_source = content.source.value
                            cache.outline_json = content.outline
                            logger.info(f"[{bvid}] 已写入缓存: source={cache.content_source}")
                try:
                    rag.delete_video(bvid)
                except Exception as e:
                    logger.warning(f"删除旧向量失败 [{bvid}]: {e}")
                chunks = rag.add_video_content(content)
                if chunks <= 0:
                    raise RuntimeError("未生成可写入的向量文档")
                _set_cache_processing_result(cache)
                logger.info(f"[{bvid}] 向量化完成，块数={chunks}")
            else:
                logger.info(f"[{bvid}] 内容未变化或无需升级，跳过向量化")
        except Exception as e:
            failed_targets += 1
            _set_cache_processing_result(cache, e)
            logger.error(f"添加向量失败 [{bvid}]: {e} (收藏关系已保存，可重试)")

        # 无论向量是否添加成功，都写入 FavoriteVideo 记录
        try:
            exists_row = await db.execute(
                select(FavoriteVideo.id).where(
                    FavoriteVideo.folder_id == folder.id,
                    FavoriteVideo.bvid == bvid,
                )
            )
            if exists_row.scalar_one_or_none() is None:
                db.add(FavoriteVideo(folder_id=folder.id, bvid=bvid, is_selected=True))
            processed_targets += 1
            if progress_callback:
                progress_callback(meta["title"], processed_targets, total_targets)
        except Exception as e:
            logger.error(f"写入数据库失败 [{bvid}]: {e}")

    # 删除无效向量
    if removed:
        for bvid in removed:
            other_count = await db.scalar(
                select(func.count())
                .select_from(FavoriteVideo)
                .where(
                    FavoriteVideo.bvid == bvid,
                    FavoriteVideo.folder_id != folder.id,
                )
            )
            if other_count == 0:
                try:
                    rag.delete_video(bvid)
                except Exception as e:
                    logger.warning(f"删除向量失败 [{bvid}]: {e}")

        await db.execute(
            delete(FavoriteVideo).where(
                FavoriteVideo.folder_id == folder.id,
                FavoriteVideo.bvid.in_(removed),
            )
        )

    folder.last_sync_at = datetime.utcnow()

    await db.commit()

    indexed_count = await db.scalar(
        select(func.count(func.distinct(FavoriteVideo.bvid)))
        .select_from(FavoriteVideo)
        .join(VideoCache, VideoCache.bvid == FavoriteVideo.bvid)
        .where(
            FavoriteVideo.folder_id == folder.id,
            VideoCache.is_processed.is_(True),
        )
    )

    message = "同步完成"
    if failed_targets:
        message = f"同步未完成：{failed_targets} 个视频向量入库失败，可重新更新"

    return {
        "folder_id": folder_id,
        "total": valid_count,
        "added": len(added),
        "removed": len(removed),
        "indexed": indexed_count or 0,
        "failed": failed_targets,
        "message": message,
        "last_sync_at": folder.last_sync_at,
    }


@router.get("/stats")
async def get_knowledge_stats():
    """获取知识库统计信息"""
    try:
        rag = get_rag_service()
        stats = rag.get_collection_stats()
        return stats
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders/status", response_model=List[FolderStatus])
async def get_folder_status(
    session_id: str = Query(..., description="会话ID"),
    db: AsyncSession = Depends(get_db),
):
    """获取收藏夹入库状态（跨 Session 查找同一用户的数据）"""

    # 1. 先查当前 Session 对应的用户 MID
    result = await db.execute(
        select(UserSession.bili_mid).where(UserSession.session_id == session_id)
    )
    mid = result.scalar()

    target_session_ids = [session_id]

    if mid:
        # 2. 如果有 MID，查找该用户所有的 Session ID
        result = await db.execute(
            select(UserSession.session_id).where(UserSession.bili_mid == mid)
        )
        target_session_ids = [row[0] for row in result.fetchall()]

    # 3. 查询所有关联 Session 的收藏夹状态
    # 使用 group_by media_id 来去重，取最新的那个
    rows = await db.execute(
        select(FavoriteFolder.id, FavoriteFolder.media_id, FavoriteFolder.last_sync_at)
        .where(FavoriteFolder.session_id.in_(target_session_ids))
        .order_by(FavoriteFolder.updated_at.desc())
    )

    # 手动按 media_id 去重，保留最新的
    folders_map = {}
    for row in rows.fetchall():
        fid, media_id, last_sync = row
        if media_id not in folders_map:
            folders_map[media_id] = (fid, last_sync)

    if not folders_map:
        return []

    folder_ids = [v[0] for v in folders_map.values()]

    # 4. 按 Chroma 实际数据校准并统计入库状态
    relations = await db.execute(
        select(FavoriteVideo.folder_id, FavoriteVideo.bvid, VideoCache)
        .join(VideoCache, VideoCache.bvid == FavoriteVideo.bvid)
        .where(FavoriteVideo.folder_id.in_(folder_ids))
    )
    rag = get_rag_service()
    vector_presence: dict[str, bool] = {}
    indexed_map: dict[int, int] = {}
    failed_map: dict[int, int] = {}
    state_changed = False
    for folder_id, bvid, cache in relations.fetchall():
        has_vectors = vector_presence.get(bvid)
        if has_vectors is None:
            has_vectors = rag.has_video(bvid)
            vector_presence[bvid] = has_vectors
        if not has_vectors and (cache.is_processed or not cache.process_error):
            _set_cache_processing_result(cache, RuntimeError("向量数据缺失，等待重新入库"))
            state_changed = True
        if has_vectors and cache.is_processed:
            indexed_map[folder_id] = indexed_map.get(folder_id, 0) + 1
        if cache.process_error:
            failed_map[folder_id] = failed_map.get(folder_id, 0) + 1

    if state_changed:
        await db.commit()

    result = []
    for media_id, (folder_id, last_sync_at) in folders_map.items():
        # 读取有效视频数（过滤失效后的口径）
        folder_row = await db.execute(
            select(FavoriteFolder.media_count).where(FavoriteFolder.id == folder_id)
        )
        media_count = folder_row.scalar()
        result.append(
            FolderStatus(
                media_id=media_id,
                indexed_count=indexed_map.get(folder_id, 0),
                failed_count=failed_map.get(folder_id, 0),
                media_count=media_count,
                last_sync_at=last_sync_at,
            )
        )
    return result


@router.post("/folders/sync", response_model=List[SyncResult])
async def sync_folders(
    request: SyncRequest,
    session_id: str = Query(..., description="会话ID"),
    db: AsyncSession = Depends(get_db),
):
    """同步收藏夹到向量库"""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")

    cookies = session.get("cookies", {})
    user_info = session.get("user_info", {})

    bili = BilibiliService(
        sessdata=cookies.get("SESSDATA"),
        bili_jct=cookies.get("bili_jct"),
        dedeuserid=cookies.get("DedeUserID"),
    )
    rag = get_rag_service()
    asr_service = ASRService()
    content_fetcher = ContentFetcher(bili, asr_service)

    try:
        folder_ids = request.folder_ids or []
        if not folder_ids:
            mid = user_info.get("mid") or cookies.get("DedeUserID")
            if not mid:
                raise HTTPException(status_code=400, detail="无法获取用户信息")
            folders = await bili.get_user_favorites(mid=mid)
            folder_ids = [folder.get("id") for folder in folders if folder.get("id")]

        results: List[SyncResult] = []
        for folder_id in folder_ids:
            try:
                result = await _sync_folder(
                    db,
                    bili,
                    rag,
                    content_fetcher,
                    session_id,
                    folder_id,
                )
                results.append(SyncResult(**result))
            except Exception as e:
                logger.error(f"同步收藏夹失败 [{folder_id}]: {e}")
                results.append(
                    SyncResult(
                        folder_id=folder_id,
                        total=0,
                        added=0,
                        removed=0,
                        indexed=0,
                        failed=1,
                        message=f"同步失败: {e}",
                        last_sync_at=None,
                    )
                )

        return results
    finally:
        await bili.close()


@router.post("/build")
async def build_knowledge_base(
    request: BuildRequest,
    background_tasks: BackgroundTasks,
    session_id: str = Query(..., description="会话ID"),
):
    """构建知识库（后台任务）"""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")

    import uuid
    task_id = str(uuid.uuid4())

    build_tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "current_step": "初始化中...",
        "total_videos": 0,
        "processed_videos": 0,
        "total_folders": len(request.folder_ids),
        "processed_folders": 0,
        "current_folder_id": None,
        "current_folder_title": None,
        "current_video_title": None,
        "message": "",
    }

    background_tasks.add_task(
        _build_knowledge_base_task,
        task_id,
        session_id,
        session,
        request.folder_ids,
        request.exclude_bvids or [],
    )

    return {"task_id": task_id, "message": "构建任务已启动"}


async def _build_knowledge_base_task(
    task_id: str,
    session_id: str,
    session: dict,
    folder_ids: List[int],
    exclude_bvids: List[str],
):
    """后台构建任务"""
    cookies = session.get("cookies", {})

    try:
        build_tasks[task_id]["status"] = "running"
        build_tasks[task_id]["current_step"] = "同步收藏夹..."

        bili = BilibiliService(
            sessdata=cookies.get("SESSDATA"),
            bili_jct=cookies.get("bili_jct"),
            dedeuserid=cookies.get("DedeUserID"),
        )
        asr_service = ASRService()
        content_fetcher = ContentFetcher(bili, asr_service)
        rag = get_rag_service()

        try:
            total_folders = len(folder_ids)
            build_tasks[task_id]["total_folders"] = total_folders
            if total_folders == 0:
                build_tasks[task_id]["status"] = "completed"
                build_tasks[task_id]["progress"] = 100
                build_tasks[task_id]["message"] = "没有需要处理的收藏夹"
                return

            total_added = 0
            total_removed = 0
            total_failed = 0

            async with get_db_context() as db:
                for idx, folder_id in enumerate(folder_ids, start=1):
                    build_tasks[task_id]["current_step"] = f"同步收藏夹 {folder_id}"
                    build_tasks[task_id]["current_folder_id"] = folder_id
                    build_tasks[task_id]["current_folder_title"] = f"收藏夹 {folder_id}"
                    build_tasks[task_id]["current_video_title"] = None
                    build_tasks[task_id]["processed_folders"] = idx - 1
                    build_tasks[task_id]["processed_videos"] = 0
                    build_tasks[task_id]["total_videos"] = 0

                    def progress_cb(title: str, processed_count: int = 0, total_count: int = 0):
                        build_tasks[task_id]["current_step"] = f"处理: {title}"
                        build_tasks[task_id]["current_video_title"] = title
                        if total_count:
                            build_tasks[task_id]["total_videos"] = total_count
                        if processed_count or processed_count == 0:
                            build_tasks[task_id]["processed_videos"] = processed_count
                            if build_tasks[task_id]["total_videos"]:
                                folder_progress = processed_count / build_tasks[task_id]["total_videos"]
                                build_tasks[task_id]["progress"] = int(
                                    ((idx - 1 + folder_progress) / total_folders) * 100
                                )

                    result = await _sync_folder(
                        db,
                        bili,
                        rag,
                        content_fetcher,
                        session_id,
                        folder_id,
                        exclude_bvids=set(exclude_bvids),
                        progress_callback=progress_cb,
                    )

                    build_tasks[task_id]["processed_folders"] = idx
                    total_added += result["added"]
                    total_removed += result["removed"]
                    total_failed += result.get("failed", 0)

            build_tasks[task_id]["status"] = "failed" if total_failed else "completed"
            build_tasks[task_id]["progress"] = 100
            build_tasks[task_id]["processed_folders"] = total_folders
            build_tasks[task_id]["current_step"] = "失败" if total_failed else "完成"
            build_tasks[task_id]["current_folder_id"] = None
            build_tasks[task_id]["current_folder_title"] = None
            build_tasks[task_id]["current_video_title"] = None
            if total_failed:
                build_tasks[task_id]["message"] = f"同步未完成：{total_failed} 个视频向量入库失败，可重新更新"
            else:
                build_tasks[task_id]["message"] = f"同步完成：新增 {total_added}，移除 {total_removed}"

            logger.info(f"知识库构建结束: 新增 {total_added}，移除 {total_removed}，失败 {total_failed}")
        finally:
            await bili.close()

    except Exception as e:
        logger.error(f"构建任务失败: {e}")
        build_tasks[task_id]["status"] = "failed"
        build_tasks[task_id]["message"] = str(e)


@router.get("/build/status/{task_id}", response_model=BuildStatus)
async def get_build_status(task_id: str):
    """获取构建任务状态"""
    if task_id not in build_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = build_tasks[task_id]
    return BuildStatus(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        current_step=task["current_step"],
        total_videos=task["total_videos"],
        processed_videos=task["processed_videos"],
        total_folders=task.get("total_folders"),
        processed_folders=task.get("processed_folders"),
        current_folder_id=task.get("current_folder_id"),
        current_folder_title=task.get("current_folder_title"),
        current_video_title=task.get("current_video_title"),
        message=task["message"],
    )


@router.delete("/clear")
async def clear_knowledge_base():
    """清空知识库"""
    try:
        rag = get_rag_service()
        rag.clear_collection()
        return {"message": "知识库已清空"}
    except Exception as e:
        logger.error(f"清空知识库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/video/{bvid}")
async def delete_video_from_knowledge(bvid: str):
    """从知识库中删除指定视频"""
    try:
        rag = get_rag_service()
        rag.delete_video(bvid)
        return {"message": f"已删除视频 {bvid}"}
    except Exception as e:
        logger.error(f"删除视频失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/video/{bvid}/export")
async def export_video_markdown(
    bvid: str,
    payload: MarkdownExportRequest,
    session_id: str = Query(..., description="会话ID"),
    db: AsyncSession = Depends(get_db),
):
    """导出当前用户已入库视频的 Markdown 内容。"""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")

    target_session_ids = await _get_session_ids_for_user(db, session_id)
    result = await db.execute(
        select(VideoCache)
        .join(FavoriteVideo, FavoriteVideo.bvid == VideoCache.bvid)
        .join(FavoriteFolder, FavoriteFolder.id == FavoriteVideo.folder_id)
        .where(
            VideoCache.bvid == bvid,
            FavoriteFolder.session_id.in_(target_session_ids),
        )
        .limit(1)
    )
    video = result.scalar_one_or_none()
    if video is None:
        raise HTTPException(status_code=404, detail="视频尚未入库或不属于当前会话")
    if not (video.content or "").strip():
        raise HTTPException(status_code=409, detail="视频尚无可导出的字幕或转写内容")

    cancel_event = _start_operation(payload.operation_id, session_id)
    cancel_check = cancel_event.is_set if cancel_event else None
    try:
        ensure_not_cancelled(cancel_check)
        ai_content = None
        if payload.mode == "ai":
            ai_content = await asyncio.to_thread(
                organize_video_content,
                video.title,
                video.content,
                cancel_check=cancel_check,
            )
        ensure_not_cancelled(cancel_check)
        markdown = build_video_markdown(video, ai_content=ai_content)
        return Response(
            content=markdown,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{bvid}.md"'},
        )
    except OperationCancelled:
        logger.info(f"视频 Markdown 导出已取消 [{bvid}]")
        raise HTTPException(status_code=409, detail="操作已取消")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"导出视频 Markdown 失败 [{bvid}]: {e}")
        raise HTTPException(status_code=500, detail=f"导出失败: {e}")
    finally:
        _finish_operation(payload.operation_id, session_id)


@router.post("/video/{bvid}/ingest")
async def ingest_single_video(
    bvid: str,
    payload: SingleVideoIngestRequest,
    session_id: str = Query(..., description="会话ID"),
    db: AsyncSession = Depends(get_db),
):
    """将当前用户收藏夹中的单个视频写入知识库。"""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")

    cookies = session.get("cookies", {})
    bili = BilibiliService(
        sessdata=cookies.get("SESSDATA"),
        bili_jct=cookies.get("bili_jct"),
        dedeuserid=cookies.get("DedeUserID"),
    )
    cancel_event = _start_operation(payload.operation_id, session_id)
    cancel_check = cancel_event.is_set if cancel_event else None
    try:
        asr_service = ASRService(cancel_check=cancel_check)
        content_fetcher = ContentFetcher(bili, asr_service, cancel_check=cancel_check)
        cache = await _ingest_single_video(
            db,
            bili,
            get_rag_service(),
            content_fetcher,
            session_id,
            payload.folder_id,
            bvid,
            cancel_check,
        )
        return {
            "bvid": cache.bvid,
            "title": cache.title,
            "message": "单视频入库完成",
        }
    except OperationCancelled:
        await db.rollback()
        logger.info(f"单视频入库已取消 [{bvid}]")
        raise HTTPException(status_code=409, detail="操作已取消")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"单视频入库失败 [{bvid}]: {e}")
        raise HTTPException(status_code=500, detail=f"单视频入库失败: {e}")
    finally:
        _finish_operation(payload.operation_id, session_id)
        await bili.close()


@router.post("/operations/{operation_id}/cancel")
async def cancel_operation(
    operation_id: str,
    session_id: str = Query(..., description="会话ID"),
):
    """取消单视频导出或入库操作。"""
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="未登录或会话已过期")

    operation = active_operations.get(operation_id)
    if operation and operation[0] == session_id:
        operation[1].set()
        logger.info(f"收到操作取消请求 [{operation_id}]")
        return {"message": "取消请求已发送"}
    return {"message": "操作已结束或不存在"}
