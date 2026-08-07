"""
神农觅（ChineseMedicalProject）通用模块包
=========================================

本包（common）是整个项目的公共基础设施层，提供以下核心能力：

    - config.py           配置管理（从 .env 读取 LLM / Neo4j / Embedding 等配置）
    - llm.py              LLM 大模型封装（ChatOpenAI + 对话历史格式化）
    - neo4j_manager.py    Neo4j 图数据库客户端（连接、Cypher 执行、元数据导出）
    - embedding_model.py  SentenceTransformer BGE 嵌入模型（文本向量化）
    - session_manager.py  持久化多会话管理（创建、删除、重命名、消息存储）
    - stream_context.py   SSE 流式输出上下文变量（基于 contextvars）
    - output_graph_utils.py  LangGraph 工作流图可视化（导出 PNG）
    - path_utils.py       项目根路径工具（基于 pyproject.toml / .env 定位）

关键模块（如 Neo4j 客户端、TCM 元数据）采用惰性初始化（Lazy Initialization）
优化，避免在 import 阶段因外部服务未就绪而导致程序崩溃。LLM 实例（my_llm /
streaming_llm）和嵌入模型（embedding_model）在 import 时即创建，因为它们
依赖的是网络 API 和本地模型文件，通常在应用启动时已就绪。
"""

# 确保 common 目录被识别为 Python 包
