"""
Bilibili RAG 知识库系统
对话路由 - 智能问答
"""
import asyncio
import re
import json
import time
from typing import Callable, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI, OpenAI
from langchain.schema import Document

from app.database import get_db, get_db_context
from app.models import ChatRequest, ChatResponse, FavoriteFolder, FavoriteVideo, VideoCache
from app.config import settings
from app.routers.knowledge import get_rag_service
from app.services.retrieval import (
    build_snippet,
    extract_keywords as extract_retrieval_keywords,
    keyword_score,
    merge_ranked_documents,
)

router = APIRouter(prefix="/chat", tags=["对话"])
ProgressCallback = Optional[Callable[[dict], None]]

def _get_llm_client() -> OpenAI:
    """获取 LLM 客户端"""
    if not settings.chat_api_key:
        raise HTTPException(status_code=400, detail="未配置 LLM API Key")
    return OpenAI(
        api_key=settings.chat_api_key,
        base_url=settings.chat_base_url,
    )

def _get_async_llm_client() -> AsyncOpenAI:
    """获取异步 LLM 客户端，用于流式问答。"""
    if not settings.chat_api_key:
        raise HTTPException(status_code=400, detail="未配置 LLM API Key")
    return AsyncOpenAI(
        api_key=settings.chat_api_key,
        base_url=settings.chat_base_url,
    )

def _emit_progress(callback: ProgressCallback, event_type: str, **payload) -> None:
    if callback:
        callback({"type": event_type, **payload})

def _encode_stream_event(type: str, **payload) -> str:
    """编码一条 NDJSON 流式事件。"""
    return json.dumps({"type": type, **payload}, ensure_ascii=False) + "\n"

def _route_label(route: str) -> str:
    return {
        "direct": "直接回答",
        "db_list": "读取收藏夹清单",
        "db_content": "汇总收藏夹内容",
        "vector": "检索知识库",
    }.get(route, route)

def _build_snippet_event(doc: Document) -> dict:
    meta = doc.metadata or {}
    preview = re.sub(r"\s+", " ", doc.page_content or "").strip()
    if len(preview) > 220:
        preview = preview[:220].rstrip() + "..."
    bvid = meta.get("bvid", "")
    return {
        "bvid": bvid,
        "title": meta.get("title", "") or bvid or "未命名视频",
        "preview": preview,
        "url": meta.get("url") or (f"https://www.bilibili.com/video/{bvid}" if bvid else ""),
    }

def _build_overview_messages(context: str, question: str) -> list[dict]:
    system = (
        "你是一个收藏夹知识库助手。用户想要了解他们收藏夹的整体内容。\n"
        "请根据以下视频信息回答用户的问题。回答要：\n"
        "1. 自然、友好、有条理\n"
        "2. 可以总结、分类、提炼要点\n"
        "3. 如果内容较多，挑选代表性的进行介绍\n\n"
        f"收藏夹内容：\n{context}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

def _build_rag_messages(context: str, question: str) -> list[dict]:
    system = (
        "你是一个知识库助手，基于用户收藏的视频内容回答问题。\n"
        "请根据以下检索到的视频内容回答：\n"
        "1. 直接回答问题，引用相关内容\n"
        "2. 回答要自然、有条理\n"
        "3. 可以引用视频标题作为来源\n\n"
        f"相关内容：\n{context}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

def _build_fallback_messages(context: str, question: str) -> list[dict]:
    system = (
        "你是一个收藏夹知识库助手。\n"
        "用户的问题在现有知识库中没有检索到直接内容。\n"
        "以下是用户收藏夹中的视频概览（如果为空说明用户还没入库）：\n"
        f"{context}\n\n"
        "请根据以上信息（如果有）：\n"
        "1. 尝试回答用户问题\n"
        "2. 如果没有任何视频信息，礼貌地告诉用户需要先在左侧选择收藏夹并点击「入库」或者「更新」\n"
        "3. 保持像真人助手一样的语气，不要显示这是\"备选方案\""
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

def _build_direct_messages(question: str) -> list[dict]:
    """通用回答（不查库）"""
    system = (
        "你是一个知识库问答助手。\n"
        "请直接回答用户问题，避免引入收藏夹或知识库内容。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

def _build_direct_messages_with_context(context: str, question: str) -> list[dict]:
    """带收藏夹上下文的通用回答（引导用户提问）"""
    system = (
        "你是一个知识库问答助手。\n"
        "以下是用户收藏夹的概览（收藏夹名称与视频标题）：\n"
        f"{context}\n\n"
        "请先回答用户问题，再根据收藏夹内容引导用户提出与收藏相关的问题。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

def _log_final_payload(route: str, messages: list[dict], sources: list[dict]) -> None:
    """记录最终发送给 LLM 的内容与来源"""
    logger.info(f"最终路由: {route}")
    logger.info(f"最终消息: {messages}")
    logger.info(f"最终来源数量: {len(sources)}")

def _build_db_list_messages(context: str, question: str) -> list[dict]:
    """仅用标题/简介回答列表类问题"""
    system = (
        "你是一个收藏夹知识库助手。\n"
        "用户需要清单/列表类答案，请基于以下视频标题与简介回答。\n"
        "回答要：\n"
        "1. 按收藏夹或主题分组\n"
        "2. 只输出与问题相关的条目\n"
        "3. 简洁清晰\n\n"
        f"收藏夹内容：\n{context}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

def _build_db_summary_messages(context: str, question: str) -> list[dict]:
    """仅用数据库内容回答总结类问题"""
    system = (
        "你是一个收藏夹知识库助手。\n"
        "用户需要总结/提炼，请基于以下视频内容回答。\n"
        "回答要：\n"
        "1. 提炼重点与要点\n"
        "2. 结构清晰、可快速理解\n"
        "3. 必要时引用视频标题作为来源\n\n"
        f"收藏夹内容：\n{context}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question},
    ]

def _is_list_question(question: str) -> bool:
    """列表/清单类问题"""
    list_terms = ["有哪些", "有什么", "列表", "清单", "目录", "都有哪些", "列出", "罗列", "多少个", "几个"]
    return any(term in question for term in list_terms)

def _is_summary_question(question: str) -> bool:
    """总结/概括类问题"""
    summary_terms = ["总结", "概述", "概括", "分析", "梳理", "提炼", "回顾", "复盘", "要点", "重点", "关键点", "核心", "讲了什么", "讲些什么"]
    return any(term in question for term in summary_terms)

def _is_general_question(question: str) -> bool:
    """通用闲聊/与收藏无关的问题"""
    general_terms = [
        "你好", "嗨", "哈喽", "hello", "hi", "ok", "在吗", "你是谁", "你能做什么",
        "谢谢", "好的", "好", "收到", "明白", "可以", "嗯", "嗯嗯", "晚安", "早安", "早上好",
    ]
    cleaned = re.sub(r"[\W_]+", "", question, flags=re.UNICODE)
    lowered = cleaned.lower()
    residual = lowered
    for term in general_terms:
        residual = residual.replace(term.lower(), "")
    return residual == ""

def _is_collection_intent(question: str) -> bool:
    """是否显式指向收藏/视频/知识库"""
    terms = ["收藏", "收藏夹", "视频", "合集", "up主", "BV", "bv", "分P", "字幕", "知识库", "入库", "同步", "向量", "检索"]
    return any(term in question for term in terms)

def _is_overview_question(question: str) -> bool:
    """概览类问题（列表或总结）"""
    return _is_list_question(question) or _is_summary_question(question)

def _route_with_rules(question: str, is_collection_intent: bool, related: bool) -> str:
    """规则路由兜底"""
    if _is_general_question(question):
        return "direct"
    if _is_list_question(question):
        return "db_list"
    if _is_summary_question(question):
        return "db_content"
    if not related and not is_collection_intent:
        return "direct"
    return "vector"

def _route_with_llm(question: str) -> tuple[Optional[str], str]:
    """使用 LLM 进行路由判断"""
    try:
        client = _get_llm_client()
        system = (
            "你是一个路由器，只输出以下之一：direct, db_list, db_content, vector。\n"
            "规则：\n"
            "- direct：寒暄/闲聊/与收藏无关的问题\n"
            "- db_list：清单/列表/目录/有哪些\n"
            "- db_content：明确要求“全部/所有/整体/概览/全库”内容的总结\n"
            "- vector：具体主题问题或需要“先检索再总结”的问题\n"
            "示例：\n"
            "Q: 中西方文化的差异是什么，简单总结 -> vector\n"
            "Q: 概览我收藏夹里所有王德峰相关内容 -> db_content\n"
            "只输出一个词，不要解释。"
        )
        resp = client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
            temperature=0,
        )
        text = (resp.choices[0].message.content or "").strip()
        match = re.search(r"(direct|db_list|db_content|vector)", text)
        return (match.group(1) if match else None), text
    except Exception as e:
        logger.warning(f"LLM 路由失败: {e}")
        return None, ""

def _extract_keywords(question: str) -> List[str]:
    """提取用于过滤的关键词"""
    return extract_retrieval_keywords(question)

def _filter_docs_by_keywords(docs: List[Document], question: str) -> List[Document]:
    """根据关键词过滤召回内容，减少噪声"""
    keywords = _extract_keywords(question)
    if not keywords:
        return []
    filtered: List[Document] = []
    for doc in docs:
        meta = doc.metadata or {}
        title = meta.get("title", "") or ""
        content = doc.page_content or ""
        if any(kw in title for kw in keywords) or any(kw in content for kw in keywords):
            filtered.append(doc)
    return filtered

def _rank_sources_by_question(sources: List[dict], question: str) -> List[dict]:
    """让总结类回答的来源优先指向标题命中的视频。"""
    keywords = _extract_keywords(question)
    if not keywords:
        return sources
    ranked = []
    for index, source in enumerate(sources):
        score = keyword_score(keywords, title=source.get("title", "") or "")
        if score > 0:
            ranked.append((score, index, source))
    if not ranked:
        return sources
    ranked.sort(key=lambda item: (-item[0], item[1]))
    best_score = ranked[0][0]
    ranked = [item for item in ranked if item[0] >= best_score * 0.5]
    return [source for _, _, source in ranked]

def _build_keyword_document(
    *,
    bvid: str,
    title: str,
    description: Optional[str],
    content: Optional[str],
    owner_name: Optional[str],
    keywords: List[str],
    score: float,
) -> Document:
    """Build one DB keyword recall document for a video."""
    parts = [f"视频标题：{title}"]
    if owner_name:
        parts.append(f"UP主：{owner_name}")
    if description:
        parts.append(f"视频简介：{description}")
    if content:
        parts.append("相关片段：" + build_snippet(content, keywords))

    return Document(
        page_content="\n".join(parts),
        metadata={
            "bvid": bvid,
            "title": title,
            "owner_name": owner_name or "",
            "url": f"https://www.bilibili.com/video/{bvid}",
            "doc_type": "keyword",
            "chunk_index": -2,
            "keyword_score": score,
        },
    )

async def _keyword_search_docs(
    db: AsyncSession,
    folder_ids: List[int],
    question: str,
    limit: int,
) -> List[Document]:
    """Recall videos from SQLite by weighted keyword matches."""
    if not folder_ids or limit <= 0:
        return []
    keywords = _extract_keywords(question)
    if not keywords:
        return []

    like_conds = []
    for kw in keywords:
        pattern = f"%{kw}%"
        like_conds.extend([
            VideoCache.bvid.ilike(pattern),
            VideoCache.title.ilike(pattern),
            VideoCache.description.ilike(pattern),
            VideoCache.content.ilike(pattern),
            VideoCache.owner_name.ilike(pattern),
        ])

    stmt = (
        select(
            VideoCache.bvid,
            VideoCache.title,
            VideoCache.description,
            VideoCache.content,
            VideoCache.owner_name,
        )
        .join(FavoriteVideo, FavoriteVideo.bvid == VideoCache.bvid)
        .where(FavoriteVideo.folder_id.in_(folder_ids))
        .where(or_(*like_conds))
        .limit(max(limit * 4, 40))
    )
    rows = await db.execute(stmt)

    docs_by_bvid: dict[str, Document] = {}
    scores_by_bvid: dict[str, float] = {}
    for bvid, title, description, content, owner_name in rows.fetchall():
        if not bvid or not title:
            continue
        score = keyword_score(
            keywords,
            title=title or "",
            description=description or "",
            content=content or "",
            owner_name=owner_name or "",
        )
        if score <= 0:
            continue
        if score <= scores_by_bvid.get(bvid, 0):
            continue
        scores_by_bvid[bvid] = score
        docs_by_bvid[bvid] = _build_keyword_document(
            bvid=bvid,
            title=title,
            description=description,
            content=content,
            owner_name=owner_name,
            keywords=keywords,
            score=score,
        )

    return sorted(
        docs_by_bvid.values(),
        key=lambda doc: doc.metadata.get("keyword_score", 0),
        reverse=True,
    )[:limit]

async def _is_related_to_collection(db: AsyncSession, folder_ids: List[int], question: str) -> bool:
    """判断问题是否与收藏夹内容有关"""
    if not folder_ids:
        return False
    keywords = _extract_keywords(question)
    if not keywords:
        return False
    like_conds = []
    for kw in keywords:
        pattern = f"%{kw}%"
        like_conds.append(VideoCache.title.ilike(pattern))
        like_conds.append(VideoCache.description.ilike(pattern))
        like_conds.append(VideoCache.content.ilike(pattern))
    stmt = (
        select(func.count())
        .select_from(VideoCache)
        .join(FavoriteVideo, FavoriteVideo.bvid == VideoCache.bvid)
        .where(FavoriteVideo.folder_id.in_(folder_ids))
        .where(or_(*like_conds))
    )
    count = await db.scalar(stmt)
    return (count or 0) > 0

async def _get_folder_ids_for_session(db: AsyncSession, session_id: str, media_ids: Optional[List[int]]) -> List[int]:
    """根据 session 和 media_id 获取内部 folder_id（支持跨 session 查找同用户数据）"""
    from app.models import UserSession
    # 1. 尝试获取当前 session 的 mid
    mid_result = await db.execute(select(UserSession.bili_mid).where(UserSession.session_id == session_id))
    mid = mid_result.scalar()
    target_session_ids = [session_id]
    if mid:
        # 查找该用户所有的 Session ID
        sessions_result = await db.execute(select(UserSession.session_id).where(UserSession.bili_mid == mid))
        target_session_ids = [row[0] for row in sessions_result.fetchall()]
    # 构建查询：按 media_id 去重，只保留最新的一条
    stmt = (
        select(FavoriteFolder.id, FavoriteFolder.media_id, FavoriteFolder.updated_at)
        .where(FavoriteFolder.session_id.in_(target_session_ids))
        .order_by(FavoriteFolder.updated_at.desc())
    )
    if media_ids:
        stmt = stmt.where(FavoriteFolder.media_id.in_(media_ids))
    rows = await db.execute(stmt)
    dedup: dict[int, int] = {}
    for folder_id, media_id, _updated_at in rows.fetchall():
        if media_id not in dedup:
            dedup[media_id] = folder_id
    return list(dedup.values())

async def _get_bvids_by_folder_ids(db: AsyncSession, folder_ids: List[int]) -> List[str]:
    """获取指定收藏夹的视频 BV 列表"""
    if not folder_ids:
        return []
    rows = await db.execute(select(FavoriteVideo.bvid).where(FavoriteVideo.folder_id.in_(folder_ids)))
    bvids = []
    seen = set()
    for (bvid,) in rows.fetchall():
        if not bvid or bvid in seen:
            continue
        seen.add(bvid)
        bvids.append(bvid)
    return bvids

async def _get_video_context(db: AsyncSession, folder_ids: List[int], include_content: bool = False, limit: Optional[int] = 50) -> tuple[str, List[dict]]:
    """获取视频上下文信息"""
    if not folder_ids:
        return "", []
    # 查询视频信息
    query = (
        select(
            FavoriteFolder.title.label("folder_title"),
            VideoCache.bvid,
            VideoCache.title,
            VideoCache.description,
            VideoCache.content if include_content else VideoCache.description,
        )
        .join(FavoriteVideo, FavoriteVideo.folder_id == FavoriteFolder.id)
        .join(VideoCache, VideoCache.bvid == FavoriteVideo.bvid, isouter=True)
        .where(FavoriteFolder.id.in_(folder_ids))
    )
    if limit is not None:
        query = query.limit(limit)
    result = await db.execute(query)
    records = result.fetchall()
    if not records:
        return "", []
    # 按收藏夹分组（对 bvid 去重，避免同一视频重复出现）
    grouped = {}
    sources = []
    seen_bvids = set()
    for folder_title, bvid, title, desc, content in records:
        if not bvid or not title:
            continue
        if bvid in seen_bvids:
            continue
        folder_name = folder_title or "默认收藏夹"
        if folder_name not in grouped:
            grouped[folder_name] = []
        video_info = f"- 《{title}》"
        if include_content and content:
            video_info += f"\n  摘要: {content}"
        elif desc:
            short_desc = desc[:100] + "..." if len(desc) > 100 else desc
            video_info += f" ({short_desc})"
        grouped[folder_name].append(video_info)
        seen_bvids.add(bvid)
        sources.append({"bvid": bvid, "title": title, "url": f"https://www.bilibili.com/video/{bvid}"})
    # 构建上下文文本
    context_parts = [f"【{folder_name}】\n" + "\n".join(videos) for folder_name, videos in grouped.items()]
    context = "\n\n".join(context_parts)
    return context, sources

async def _get_video_titles_context(db: AsyncSession, folder_ids: List[int], limit: int = 50) -> str:
    """获取收藏夹名称与视频标题（用于引导问题）"""
    if not folder_ids:
        return ""
    query = (
        select(FavoriteFolder.title.label("folder_title"), VideoCache.bvid, VideoCache.title)
        .join(FavoriteVideo, FavoriteVideo.folder_id == FavoriteFolder.id)
        .join(VideoCache, VideoCache.bvid == FavoriteVideo.bvid, isouter=True)
        .where(FavoriteFolder.id.in_(folder_ids))
        .limit(limit)
    )
    result = await db.execute(query)
    records = result.fetchall()
    if not records:
        return ""
    grouped = {}
    seen_bvids = set()
    for folder_title, bvid, title in records:
        if not title or not bvid:
            continue
        if bvid in seen_bvids:
            continue
        seen_bvids.add(bvid)
        folder_name = folder_title or "默认收藏夹"
        grouped.setdefault(folder_name, []).append(f"- 《{title}》")
    context_parts = [f"【{folder_name}】\n" + "\n".join(videos) for folder_name, videos in grouped.items()]
    return "\n\n".join(context_parts)

async def _prepare_messages(
    request: ChatRequest,
    db: AsyncSession,
    progress_callback: ProgressCallback = None,
) -> tuple[list[dict], List[dict], str]:
    """准备 LLM 消息与来源信息"""
    prepare_started = time.perf_counter()
    question = request.question.strip()
    folder_ids = []
    if request.session_id:
        folder_ids = await _get_folder_ids_for_session(db, request.session_id, request.folder_ids)
        logger.info(f"Session: {request.session_id}, 关联 FolderIDs: {folder_ids}")
    bvids = await _get_bvids_by_folder_ids(db, folder_ids) if folder_ids else []
    _emit_progress(
        progress_callback,
        "scope",
        stage="scope",
        folder_count=len(folder_ids),
        video_count=len(bvids),
        message=f"已确定检索范围：{len(folder_ids)} 个收藏夹，共 {len(bvids)} 个视频",
    )
    has_data = len(bvids) > 0
    is_collection_intent = _is_collection_intent(question)
    is_general = _is_general_question(question)
    if request.folder_ids and not is_general:
        is_collection_intent = True
    # 1) 默认使用规则路由，避免每次回答前额外等待一轮 LLM。
    route_started = time.perf_counter()
    logger.info(f"路由输入: question={question} folder_ids={folder_ids} has_data={has_data} is_collection_intent={is_collection_intent}")
    related: Optional[bool] = None
    route: Optional[str] = None
    route_source = "RULE"
    if settings.chat_use_llm_router and not is_general:
        route, _route_raw = await asyncio.to_thread(_route_with_llm, question)
        if route:
            route_source = "LLM"
    if not route:
        route = _route_with_rules(question, is_collection_intent, related=False)
        route_source = "RULE"
    logger.info(f"路由策略: {route_source} => {route}，耗时={time.perf_counter() - route_started:.2f}s")
    _emit_progress(
        progress_callback,
        "status",
        stage="routing",
        route=route,
        message=f"问题处理方式：{_route_label(route)}",
    )
    # 纠偏
    if is_general:
        route = "direct"
    # 2) 无数据时处理
    if not has_data:
        if is_collection_intent:
            context, sources = await _get_video_context(db, folder_ids, include_content=False, limit=50)
            if not context:
                context = "（暂无已入库的视频信息，请提醒用户可能需要先进行入库操作）"
            messages = _build_fallback_messages(context, question)
            return messages, sources, question
        messages = _build_direct_messages(question)
        return messages, [], question
    # 3) 直接回答。非寒暄问题如果能在库里命中关键词，转入检索，避免被路由误杀。
    if route == "direct":
        if is_general:
            return _build_direct_messages(question), [], question
        if is_collection_intent:
            route = "vector"
            _emit_progress(
                progress_callback,
                "status",
                stage="routing",
                route=route,
                message=f"问题处理方式：{_route_label(route)}",
            )
        else:
            _emit_progress(
                progress_callback,
                "status",
                stage="relatedness",
                message="正在检查问题与知识库内容的关联",
            )
            related = await _is_related_to_collection(db, folder_ids, question)
            if related:
                route = "vector"
                _emit_progress(
                    progress_callback,
                    "status",
                    stage="routing",
                    route=route,
                    message=f"问题处理方式：{_route_label(route)}",
                )
            else:
                title_context = await _get_video_titles_context(db, folder_ids, limit=50)
                messages = _build_direct_messages_with_context(title_context, question) if title_context else _build_direct_messages(question)
                return messages, [], question

    if route == "direct":
        title_context = await _get_video_titles_context(db, folder_ids, limit=50)
        messages = _build_direct_messages_with_context(title_context, question) if title_context else _build_direct_messages(question)
        return messages, [], question
    # 4) 列表类问题
    if route == "db_list":
        _emit_progress(progress_callback, "status", stage="retrieval", message="正在读取收藏夹视频清单")
        if related is None and not is_collection_intent:
            related = await _is_related_to_collection(db, folder_ids, question)
        if not related and not is_collection_intent:
            return _build_direct_messages(question), [], question
        context, sources = await _get_video_context(db, folder_ids, include_content=False, limit=50)
        _emit_progress(
            progress_callback,
            "retrieval",
            stage="retrieval",
            final_count=len(sources),
            message=f"已读取 {len(sources)} 个相关视频条目",
        )
        if not context:
            return _build_fallback_messages("（暂无信息，请入库）", question), sources, question
        return _build_db_list_messages(context, question), sources, question
    # 5) 总结类问题
    if route == "db_content":
        _emit_progress(progress_callback, "status", stage="retrieval", message="正在汇总已入库视频内容")
        if related is None and not is_collection_intent:
            related = await _is_related_to_collection(db, folder_ids, question)
        if not related and not is_collection_intent:
            return _build_direct_messages(question), [], question
        context, sources = await _get_video_context(db, folder_ids, include_content=True, limit=None)
        _emit_progress(
            progress_callback,
            "retrieval",
            stage="retrieval",
            final_count=len(sources),
            message=f"已读取 {len(sources)} 个视频的入库内容",
        )
        if not context:
            return _build_fallback_messages("（暂无信息，请入库）", question), sources, question
        sources = _rank_sources_by_question(sources, question)
        return _build_db_summary_messages(context, question), sources, question
    # 6) 检查相关性。vector 路由本身就是语义检索意图，不再用关键词 LIKE 提前拦截。
    if route != "vector":
        if related is None:
            related = await _is_related_to_collection(db, folder_ids, question)
        if not related and not is_collection_intent:
            return _build_direct_messages(question), [], question
    # 7) 混合检索：向量 MMR + SQLite 关键词召回，再用 RRF 融合。
    docs: List[Document] = []
    try:
        rag = get_rag_service()
        recall_started = time.perf_counter()
        _emit_progress(
            progress_callback,
            "status",
            stage="retrieval",
            message="正在并发执行向量检索与关键词检索",
        )
        top_k = max(1, settings.retrieval_top_k)
        candidate_k = max(top_k, settings.retrieval_candidate_k)
        vector_task = asyncio.to_thread(
            rag.search,
            question,
            k=candidate_k,
            bvids=bvids if bvids else None,
            fetch_k=max(candidate_k, settings.retrieval_mmr_fetch_k),
        )
        keyword_task = _keyword_search_docs(db, folder_ids, question, limit=candidate_k)
        vector_docs, keyword_docs = await asyncio.gather(vector_task, keyword_task)
        docs = merge_ranked_documents(
            {"vector": vector_docs, "keyword": keyword_docs},
            top_k=top_k,
            channel_weights={"vector": 1.0, "keyword": 0.9},
            per_video_limit=2,
        )
        logger.info(
            f"混合检索完成：vector={len(vector_docs)} keyword={len(keyword_docs)} final={len(docs)}，耗时={time.perf_counter() - recall_started:.2f}s"
        )
        _emit_progress(
            progress_callback,
            "retrieval",
            stage="retrieval",
            vector_count=len(vector_docs),
            keyword_count=len(keyword_docs),
            final_count=len(docs),
            elapsed_ms=round((time.perf_counter() - recall_started) * 1000),
            message=f"检索完成：筛选出 {len(docs)} 个相关片段",
        )
        for doc in docs[:5]:
            _emit_progress(progress_callback, "snippet", stage="retrieval", **_build_snippet_event(doc))
    except Exception as e:
        logger.error(f"混合检索失败: {e}")
        raise RuntimeError("知识库检索失败") from e
    if docs:
        context_parts, sources, seen_bvids = [], [], set()
        for doc in docs:
            bvid, title, content = doc.metadata.get("bvid", ""), doc.metadata.get("title", ""), doc.page_content.strip()
            if content: context_parts.append(f"【{title}】\n{content}")
            if bvid and bvid not in seen_bvids:
                seen_bvids.add(bvid)
                sources.append({"bvid": bvid, "title": title, "url": f"https://www.bilibili.com/video/{bvid}"})
        logger.info(f"准备问答上下文完成，耗时={time.perf_counter() - prepare_started:.2f}s")
        return _build_rag_messages("\n\n---\n\n".join(context_parts), question), sources, question
    # 兜底
    context, sources = await _get_video_context(db, folder_ids, include_content=False, limit=50)
    return _build_fallback_messages(context or "（暂无入库信息）", question), sources, question

@router.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """智能问答"""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    try:
        messages, sources, _ = await _prepare_messages(request, db)
        client = _get_llm_client()
        response = client.chat.completions.create(model=settings.llm_model, messages=messages, temperature=0.5)
        return ChatResponse(answer=response.choices[0].message.content or "", sources=sources[:5])
    except HTTPException: raise
    except Exception as e:
        logger.error(f"问答失败: {e}")
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")

@router.post("/ask/stream")
async def ask_question_stream(request: ChatRequest):
    """以 NDJSON 事件流返回执行过程与答案。"""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    async def generate():
        yield _encode_stream_event("status", stage="routing", message="正在分析问题")
        progress_queue: asyncio.Queue[dict] = asyncio.Queue()
        prepare_task: Optional[asyncio.Task] = None

        def report(event: dict) -> None:
            progress_queue.put_nowait(event)

        try:
            async with get_db_context() as stream_db:
                try:
                    prepare_task = asyncio.create_task(
                        _prepare_messages(request, stream_db, progress_callback=report)
                    )
                    while not prepare_task.done():
                        try:
                            event = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                            yield _encode_stream_event(**event)
                        except asyncio.TimeoutError:
                            continue
                    while not progress_queue.empty():
                        yield _encode_stream_event(**progress_queue.get_nowait())
                    messages, sources, _ = await prepare_task
                finally:
                    if prepare_task and not prepare_task.done():
                        prepare_task.cancel()
                        await asyncio.gather(prepare_task, return_exceptions=True)

            yield _encode_stream_event("sources", items=sources[:5])
            yield _encode_stream_event("status", stage="generation", message="正在基于检索结果生成回答")

            client = _get_async_llm_client()
            stream = await client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                temperature=0.5,
                stream=True,
            )
            emitted_content = False
            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    emitted_content = True
                    yield _encode_stream_event("token", content=delta.content)
            if not emitted_content:
                raise RuntimeError("AI 回答返回空结果")
            yield _encode_stream_event("done")
        except Exception as e:
            logger.error(f"流式问答失败: {e}")
            yield _encode_stream_event("error", message=f"问答失败: {e}")

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson; charset=utf-8",
        headers={"X-Accel-Buffering": "no"},
    )

@router.post("/search")
async def search_videos(query: str, k: int = 5):
    """搜索相关视频片段"""
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="查询不能为空")
    try:
        rag = get_rag_service()
        docs = rag.search(query, k=k)
        results, seen_bvids = [], set()
        for doc in docs:
            bvid = doc.metadata.get("bvid", "")
            if bvid in seen_bvids: continue
            seen_bvids.add(bvid)
            results.append({
                "bvid": bvid,
                "title": doc.metadata.get("title", ""),
                "url": doc.metadata.get("url", ""),
                "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
            })
        return {"results": results}
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")
