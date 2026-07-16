"""
Bilibili RAG 知识库系统

RAG 服务模块 - 向量存储与问答
"""
from typing import Callable, List, Optional
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from app.config import settings
from app.models import VideoContent
from app.services.cancellation import OperationCancelled, ensure_not_cancelled


class RAGService:
    """
    RAG 服务

    负责：
    1. 向量存储管理
    2. 文档添加与检索
    3. 问答功能
    """

    def __init__(self, collection_name: str = "bilibili_videos"):
        """
        初始化 RAG 服务

        Args:
            collection_name: 向量集合名称
        """
        self.collection_name = collection_name

        # 初始化 Embeddings (使用 DashScope 原生支持)
        try:
            from langchain_community.embeddings import DashScopeEmbeddings
        except ImportError as exc:
            logger.error("缺少 langchain-community，无法初始化 DashScope Embedding")
            raise RuntimeError(
                "DashScope Embedding 初始化失败，请运行 pip install -r requirements.txt"
            ) from exc

        self.embeddings = DashScopeEmbeddings(
            dashscope_api_key=settings.dashscope_api_key,
            model=settings.embedding_model
        )
        logger.info("使用 DashScopeEmbeddings 初始化成功")

        # 初始化向量存储
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=settings.chroma_persist_directory
        )

        # 初始化 LLM
        self.llm = ChatOpenAI(
            api_key=settings.chat_api_key,
            base_url=settings.chat_base_url,
            model=settings.llm_model,
            temperature=0.5
        )

        # 文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "]
        )

        # 问答提示模板
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个知识库助手，专门基于用户收藏的 B站视频内容来回答问题。

请遵循以下规则：
1. 根据提供的视频内容来回答问题
2. 回答要自然、友好、有条理
3. 可以引用相关的视频标题作为来源
4. 如果多个视频涉及相同话题，请综合它们的内容

视频内容：
{context}
"""),
            ("human", "{question}")
        ])

        # 无内容时的通用回复模板
        self.fallback_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个友好的助手。用户在使用一个B站收藏夹知识库系统。

当前情况：知识库中没有找到与用户问题相关的内容。

请：
1. 友好地回应用户的问题
2. 如果能根据常识简单回答，可以简要回答
3. 建议用户构建更多收藏夹内容，或者换个问法
4. 保持自然、不要死板
"""),
            ("human", "{question}")
        ])

        # 摘要提示模板
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个内容总结专家。请对以下视频字幕内容进行总结。

要求：
1. 提取核心要点（3-5个）
2. 生成一段简洁的总结（100-200字）
3. 保持原意，不要添加额外信息

字幕内容："""),
            ("human", "{content}")
        ])

    def _build_metadata_document(self, video: VideoContent) -> Optional[Document]:
        """Build a compact searchable metadata document for title/intro recall."""
        parts = [f"视频标题：{video.title or '未知标题'}"]
        if video.owner_name:
            parts.append(f"UP主：{video.owner_name}")
        if video.description:
            parts.append(f"视频简介：{video.description}")
        if video.duration:
            parts.append(f"视频时长：{video.duration} 秒")
        if video.outline:
            outline_titles = []
            for item in video.outline:
                title = (item.get("title") or "").strip() if isinstance(item, dict) else ""
                if title:
                    outline_titles.append(title)
            if outline_titles:
                parts.append("内容提纲：" + "；".join(outline_titles[:8]))

        content = "\n".join(part for part in parts if part).strip()
        if len(content) < 10:
            return None

        return Document(
            page_content=content,
            metadata={
                "bvid": video.bvid,
                "title": video.title or "未知标题",
                "source": video.source.value,
                "doc_type": "metadata",
                "chunk_index": -1,
                "url": f"https://www.bilibili.com/video/{video.bvid}",
            },
        )

    def add_video_content(
        self,
        video: VideoContent,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> int:
        """
        添加单个视频内容到向量库

        Args:
            video: VideoContent 对象

        Returns:
            添加的文档块数量
        """
        # 构建完整内容（正文不带标题，避免标题相似度主导召回）
        title = video.title or "未知标题"
        content_parts: List[str] = []

        if video.content and video.content.strip():
            content_parts.append(video.content.strip())

        # 如果有分段提纲，添加结构化信息
        if video.outline:
            outline_text = "\n## 内容提纲\n"
            for item in video.outline:
                item_title = item.get('title', '') or ''
                outline_text += f"\n### {item_title}\n"
                for point in item.get("points", []):
                    point_content = point.get('content', '') or ''
                    if point_content:
                        outline_text += f"- {point_content}\n"
            if outline_text.strip() != "## 内容提纲":
                content_parts.append(outline_text)

        full_content = "\n\n".join(content_parts).strip()

        # 验证内容不为空
        if not full_content or len(full_content.strip()) < 10:
            logger.warning(f"[{video.bvid}] 内容太少，跳过")
            return 0

        # 分块
        chunks = self.text_splitter.split_text(full_content)

        if not chunks:
            logger.warning(f"[{video.bvid}] 没有生成文档块")
            return 0

        # 过滤空内容块
        valid_chunks = [c for c in chunks if c and c.strip() and len(c.strip()) > 5]
        if not valid_chunks:
            logger.warning(f"[{video.bvid}] 没有有效的文档块")
            return 0

        # 创建文档。额外加入一条元信息文档，提升标题/简介/UP主类问题召回率。
        documents = []
        metadata_doc = self._build_metadata_document(video)
        if metadata_doc:
            documents.append(metadata_doc)

        for i, chunk in enumerate(valid_chunks):
            doc = Document(
                page_content=chunk.strip(),  # 确保是干净的字符串
                metadata={
                    "bvid": video.bvid,
                    "title": title,
                    "source": video.source.value,
                    "doc_type": "chunk",
                    "chunk_index": i,
                    "url": f"https://www.bilibili.com/video/{video.bvid}"
                }
            )
            documents.append(doc)

        # 添加到向量库
        added_ids: List[str] = []
        try:
            batch_size = 10
            for idx in range(0, len(documents), batch_size):
                ensure_not_cancelled(cancel_check)
                added_ids.extend(self.vectorstore.add_documents(documents[idx:idx + batch_size]))
                ensure_not_cancelled(cancel_check)
            logger.info(f"[{video.bvid}] 添加了 {len(documents)} 个文档块")
        except OperationCancelled:
            if added_ids:
                try:
                    self.vectorstore._collection.delete(ids=added_ids)
                except Exception as cleanup_error:
                    logger.error(f"[{video.bvid}] 取消后清理向量失败: {cleanup_error}")
            raise
        except Exception as e:
            logger.error(f"[{video.bvid}] 添加到向量库失败: {e}")
            if added_ids:
                try:
                    self.vectorstore._collection.delete(ids=added_ids)
                    logger.warning(f"[{video.bvid}] 已清理 {len(added_ids)} 个未完成向量")
                except Exception as cleanup_error:
                    logger.error(f"[{video.bvid}] 清理未完成向量失败: {cleanup_error}")
            raise

        return len(documents)

    def add_videos_batch(self, videos: List[VideoContent], progress_callback=None) -> dict:
        """
        批量添加视频到向量库

        Args:
            videos: VideoContent 列表
            progress_callback: 进度回调 callback(current, total, title)

        Returns:
            {"success": 成功数, "failed": 失败数, "chunks": 总块数}
        """
        success = 0
        failed = 0
        total_chunks = 0

        for i, video in enumerate(videos):
            try:
                chunks = self.add_video_content(video)
                total_chunks += chunks
                success += 1

                if progress_callback:
                    progress_callback(i + 1, len(videos), video.title)

            except Exception as e:
                logger.error(f"添加视频失败 [{video.bvid}]: {e}")
                failed += 1

        return {
            "success": success,
            "failed": failed,
            "chunks": total_chunks
        }

    def search(
        self,
        query: str,
        k: int = 5,
        bvids: Optional[List[str]] = None,
        fetch_k: Optional[int] = None,
        use_mmr: bool = True,
    ) -> List[Document]:
        """
        检索相关内容
        """
        if not query or not query.strip():
            logger.warning("检索查询为空")
            return []

        try:
            requested_k = max(1, k)
            candidate_k = max(fetch_k or settings.retrieval_mmr_fetch_k, requested_k)
            search_filter = {"bvid": {"$in": bvids}} if bvids else None
            docs: List[Document] = []

            if use_mmr:
                try:
                    docs = self.vectorstore.max_marginal_relevance_search(
                        query,
                        k=requested_k,
                        fetch_k=candidate_k,
                        lambda_mult=settings.retrieval_mmr_lambda,
                        filter=search_filter,
                    )
                except Exception as e:
                    logger.warning(f"MMR 检索失败，降级 similarity_search: {e}")

            if not docs:
                if search_filter:
                    docs = self.vectorstore.similarity_search(query, k=requested_k, filter=search_filter)
                else:
                    docs = self.vectorstore.similarity_search(query, k=requested_k)

            logger.info(f"检索完成：query='{query}'，召回={len(docs)}")
            for idx, doc in enumerate(docs):
                meta = doc.metadata or {}
                title = meta.get("title", "")
                bvid = meta.get("bvid", "")
                chunk_index = meta.get("chunk_index", "")
                preview = doc.page_content[:120].replace("\n", " ").strip()
                logger.info(f"召回[{idx+1}] {bvid} #{chunk_index} {title} | {preview}")

            return docs
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            raise RuntimeError("向量检索失败") from e

    async def _fallback_answer(self, question: str, reason: str = "") -> dict:
        """
        当没有检索到内容时，让 AI 自然回复

        Args:
            question: 用户问题
            reason: 原因说明

        Returns:
            回答结果
        """
        try:
            chain = (
                {"question": RunnablePassthrough()}
                | self.fallback_prompt
                | self.llm
                | StrOutputParser()
            )

            answer = await chain.ainvoke(question)
            return {
                "answer": answer,
                "sources": []
            }
        except Exception as e:
            logger.error(f"Fallback 回复失败: {e}")
            return {
                "answer": f"抱歉，{reason}。您可以尝试构建更多收藏夹内容，或者换个问法试试。",
                "sources": []
            }

    async def answer_question(self, question: str, k: int = 5, bvids: Optional[List[str]] = None) -> dict:
        """
        回答问题

        Args:
            question: 用户问题
            k: 检索文档数量
            bvids: 可选，限制在这些视频范围内搜索

        Returns:
            {
                "answer": 回答内容,
                "sources": 来源视频列表
            }
        """
        # 先检查向量库是否有内容
        stats = self.get_collection_stats()
        if stats["total_chunks"] == 0:
            # 知识库为空时，使用 fallback 让 AI 自然回复
            return await self._fallback_answer(question, "知识库目前还没有内容")

        # 检索相关文档
        try:
            docs = self.search(
                question,
                k=max(k, settings.retrieval_top_k),
                bvids=bvids if bvids else None,
                fetch_k=settings.retrieval_mmr_fetch_k,
            )
        except Exception as e:
            logger.error(f"检索失败: {e}")
            raise

        if not docs:
            # 没检索到内容时，也让 AI 自然回复
            return await self._fallback_answer(question, "没有找到相关内容")

        # 构建上下文
        context_parts = []
        seen_bvids = set()
        sources = []

        for doc in docs:
            bvid = doc.metadata.get("bvid", "")
            title = doc.metadata.get("title", "未知标题")
            content = doc.page_content.strip()

            if content:  # 只添加有内容的文档
                context_parts.append(f"【{title}】\n{content}")

            if bvid and bvid not in seen_bvids:
                seen_bvids.add(bvid)
                sources.append({
                    "bvid": bvid,
                    "title": title,
                    "url": doc.metadata.get("url", f"https://www.bilibili.com/video/{bvid}")
                })

        # 如果没有有效内容
        if not context_parts:
            return {
                "answer": "检索到了相关视频，但没有找到有效的文本内容。可能是视频还未完成内容提取。",
                "sources": sources
            }

        context = "\n\n---\n\n".join(context_parts)

        # 确保 context 不为空
        if not context.strip():
            return {
                "answer": "没有找到可用的内容来回答您的问题。",
                "sources": sources
            }

        # 构建链并执行
        try:
            chain = (
                {"context": lambda _: context, "question": RunnablePassthrough()}
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )

            answer = await chain.ainvoke(question)

            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return {
                "answer": f"AI 回答时发生错误: {str(e)}",
                "sources": sources
            }

    async def summarize_content(self, content: str) -> str:
        """
        使用 LLM 总结内容（用于字幕内容）

        Args:
            content: 原始内容（字幕文本）

        Returns:
            总结后的内容
        """
        # 如果内容太长，先截断
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "\n...(内容已截断)"

        chain = (
            {"content": RunnablePassthrough()}
            | self.summary_prompt
            | self.llm
            | StrOutputParser()
        )

        return await chain.ainvoke(content)

    def get_collection_stats(self) -> dict:
        """
        获取向量库统计信息

        Returns:
            统计信息字典
        """
        try:
            collection = self.vectorstore._collection
            count = collection.count()

            # 获取唯一视频数
            result = collection.get(include=["metadatas"])
            bvids = set()
            for meta in result.get("metadatas", []):
                if meta and "bvid" in meta:
                    bvids.add(meta["bvid"])

            return {
                "total_chunks": count,
                "total_videos": len(bvids),
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_chunks": 0,
                "total_videos": 0,
                "collection_name": self.collection_name
            }

    def has_video(self, bvid: str) -> bool:
        """检查指定视频是否实际存在于向量库。"""
        try:
            result = self.vectorstore._collection.get(where={"bvid": bvid}, limit=1)
            return bool(result.get("ids"))
        except Exception as e:
            logger.error(f"查询视频向量失败 [{bvid}]: {e}")
            raise RuntimeError(f"查询视频向量失败 [{bvid}]") from e

    def clear_collection(self):
        """清空向量库"""
        try:
            self.vectorstore._collection.delete(where={})
            logger.info(f"已清空向量库: {self.collection_name}")
        except Exception as e:
            logger.error(f"清空向量库失败: {e}")
            raise

    def delete_video(self, bvid: str):
        """
        删除指定视频的所有文档块

        Args:
            bvid: 视频 BV 号
        """
        try:
            self.vectorstore._collection.delete(where={"bvid": bvid})
            logger.info(f"已删除视频: {bvid}")
        except Exception as e:
            logger.error(f"删除视频失败 [{bvid}]: {e}")
            raise
