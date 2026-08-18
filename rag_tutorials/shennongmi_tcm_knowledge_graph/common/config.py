"""
配置管理模块
============

负责从项目根目录的 .env 文件加载所有环境变量，并通过 Config 类提供
统一的配置访问接口。所有模块通过 `from common.config import Config` 获取
配置实例，避免在代码中硬编码 API Key、数据库地址等敏感信息。

配置项包括:
    - 大模型 (LLM): API Key、Base URL、模型名称
    - Neo4j: 图数据库连接 URI、用户名、密码
    - Embedding: 本地嵌入模型路径
    - FAISS 索引: 实体向量索引文件路径、ID 到文本映射文件路径
    - TCM 元数据: 知识图谱模式层元数据（惰性加载）

设计要点:
    - load_dotenv() 仅在模块首次 import 时执行一次，使用 get_file_path() 确保
      始终从项目根目录加载 .env，而非从当前工作目录（CWD）误加载同名文件。
    - TCM_METADATA 属性采用惰性加载（Lazy Loading），只有首次访问时才从磁盘读取，
      避免在 Neo4j 数据未导入阶段因文件缺失导致 import 崩溃。
"""

import os
from dotenv import load_dotenv

from common.path_utils import get_file_path

# 只从项目根加载一次 .env，避免从 CWD 误加载同名文件
# get_file_path(".env") 会返回项目根目录下的 .env 绝对路径
load_dotenv(get_file_path(".env"))


class Config:
    """
    全局配置单例类

    首次实例化时从环境变量读取所有配置项并缓存在实例属性中。
    通常在模块级别创建一个实例（如 `conf = Config()`），
    其他模块通过 import 该实例来共享同一份配置。

    Attributes:
        MODEL_API_KEY (str): 大模型 API 密钥
        MODEL_BASE_URL (str): 大模型 API 服务地址（兼容 OpenAI 协议的 endpoint）
        MODEL_NAME (str): 大模型名称（如 gpt-4o, deepseek-chat 等）
        NEO4J_URI (str): Neo4j 图数据库 Bolt 协议连接地址
        NEO4J_USER (str): Neo4j 用户名
        NEO4J_PASSWORD (str): Neo4j 密码
        EMBEDDING_MODEL_PATH (str): 本地 SentenceTransformer 嵌入模型路径
        ENTITY_INDEX_PATH (str): FAISS 实体向量索引文件路径
        ENTITY_ID2TEXT_PATH (str): FAISS ID 到实体文本的映射文件路径
    """

    def __init__(self):
        # ========== 大模型相关 ==========
        # 用于调用 ChatOpenAI（兼容 OpenAI API 协议）的配置
        self.MODEL_API_KEY = os.getenv("MODEL_API_KEY")
        self.MODEL_BASE_URL = os.getenv("MODEL_BASE_URL")
        self.MODEL_NAME = os.getenv("MODEL_NAME")

        # ========== Neo4j 图数据库相关 ==========
        # 连接中医知识图谱所需的 Neo4j 凭据
        self.NEO4J_URI = os.getenv("NEO4J_URI")
        self.NEO4J_USER = os.getenv("NEO4J_USER")
        self.NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

        # ========== Embedding 嵌入模型相关 ==========
        # BGE 中文嵌入模型的本地存储路径
        self.EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH")

        # ========== FAISS 向量索引路径 ==========
        # 这两个文件由 kg_setup 流程生成，
        # 用于基于向量相似度的实体检索
        self.ENTITY_INDEX_PATH = get_file_path("kg_setup/neo4j_embedding_faiss.index")
        self.ENTITY_ID2TEXT_PATH = get_file_path("kg_setup/neo4j_embedding_faiss_id2text.pkl")

        # ========== 即梦 AI 相关 ==========
        # （已移除，精简版不包含小红书配图功能）

        # ========== TCM 知识图谱元数据 ==========
        # 🔧 修复：元数据改为惰性加载，避免 import 时文件不存在导致崩溃。
        # tcm_metadata.json 由 kg_setup/export_metadata.py 在 Neo4j 数据导入后生成，
        # 在此之前导入本模块不应该因此失败。
        # _tcm_metadata 为 None 表示尚未从磁盘加载；首次访问 TCM_METADATA 属性时触发加载。
        self._tcm_metadata = None

    @property
    def TCM_METADATA(self) -> str:
        """
        惰性读取知识图谱模式层元数据（tcm_metadata.json 文件内容）。

        首次访问时从磁盘加载 JSON 文件内容并缓存到 _tcm_metadata，
        后续访问直接返回缓存值，避免重复 I/O。

        Returns:
            str: tcm_metadata.json 文件的完整 JSON 字符串。
                 可用于作为 LLM prompt 中的 schema 上下文，
                 告知模型知识图谱中有哪些节点类型、关系类型和属性。

        Raises:
            FileNotFoundError: 当元数据文件不存在时抛出，提示用户先运行
                               Neo4j 数据导入和元数据导出流程。
        """
        if self._tcm_metadata is None:
            # 首次访问：从磁盘加载并缓存
            metadata_path = get_file_path("kg_setup/tcm_metadata.json")
            if not os.path.exists(metadata_path):
                raise FileNotFoundError(
                    f"图谱元数据文件不存在: {metadata_path}\n"
                    f"请先运行 Neo4j 数据导入和元数据导出流程。"
                )
            with open(metadata_path, "r", encoding="utf-8") as f:
                self._tcm_metadata = f.read()
        return self._tcm_metadata
