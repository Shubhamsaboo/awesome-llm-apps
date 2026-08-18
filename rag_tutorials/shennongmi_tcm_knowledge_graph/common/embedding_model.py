"""
嵌入模型（Embedding Model）模块
===============================

基于 SentenceTransformer 的中文文本向量化模块，用于将自然语言文本（如中草药名、
病症描述、功效说明等）转换为固定维度的稠密向量（Embedding），以支持向量相似度搜索。

主要功能:
    - EmbeddingModel 类: 封装 SentenceTransformer BGE 模型的加载和推理
    - 自动设备选择: 优先使用 Apple Silicon MPS 加速，不可用时回退到 CPU
    - 灵活的模型加载: 优先从本地路径加载，路径无效时自动从 HuggingFace 下载
    - 模块级单例: embedding_model 实例在 import 时创建，全局共享

技术选型:
    - 模型: BAAI/bge-large-zh-v1.5（BGE 中文大规模嵌入模型，1024 维向量）
    - 框架: SentenceTransformer（封装了 HuggingFace Transformers，提供简洁 API）
    - 加速: PyTorch MPS 后端（Apple Silicon GPU）或 CPU

注意事项:
    - PyTorch MPS 与 FAISS 各自链接了不同版本的 libomp.dylib，可能出现
      OpenMP 重复初始化的问题。如遇 segfault（段错误），可设置环境变量
      KMP_DUPLICATE_LIB_OK=TRUE 作为临时 workaround，或改回 device = "cpu"。

典型用法:
    from common.embedding_model import embedding_model

    # 对单条文本编码
    vector = embedding_model.encode(["人参"])

    # 对多条文本批量编码
    vectors = embedding_model.encode(["人参", "白术", "茯苓"])
"""

from typing import List
import torch
from sentence_transformers import SentenceTransformer
from common.config import Config
import os

# ============================================================
# 设备选择
# ============================================================

# 使用 MPS（Apple Silicon GPU）加速 embedding 计算。
# torch.backends.mps.is_available() 检测当前环境是否支持 MPS。
# macOS 12.3+ 且 Apple Silicon 芯片（M1/M2/M3/M4）上为 True。
#
# 注意事项：PyTorch MPS 与 FAISS 各自链接了不同版本的 libomp.dylib，
#           可能出现 OpenMP 重复初始化的问题。如遇 segfault，可设
#           KMP_DUPLICATE_LIB_OK=TRUE 环境变量作为临时 workaround，
#           或改回 device = "cpu"。
device = "mps" if torch.backends.mps.is_available() else "cpu"


class EmbeddingModel:
    """
    文本嵌入模型封装类

    基于 SentenceTransformer 框架，加载 BGE 中文嵌入模型，
    提供文本向量化（encode）功能。支持单条和批量文本编码。

    Attributes:
        model (SentenceTransformer): 加载好的 SentenceTransformer 模型实例。
                                     可通过 model.get_sentence_embedding_dimension()
                                     获取输出向量维度（1024）。

    模型加载优先级:
        1. 如果 EMBEDDING_MODEL_PATH 指向存在的本地目录/文件，从本地加载
        2. 如果 EMBEDDING_MODEL_PATH 已设置但路径不存在，将其视为
           HuggingFace 模型名称尝试下载
        3. 如果 EMBEDDING_MODEL_PATH 未配置，从 HuggingFace 自动下载
           BAAI/bge-large-zh-v1.5 模型
    """

    def __init__(self):
        """
        初始化嵌入模型。

        加载逻辑:
            1. 读取 Config 中的 EMBEDDING_MODEL_PATH 配置
            2. 如果配置的路径有效（文件存在），从本地加载（速度更快）
            3. 如果 EMBEDDING_MODEL_PATH 已设置但路径不存在，将其视为
               HuggingFace 模型名称尝试下载
            4. 如果配置未设置（None/空），从 HuggingFace Hub 下载默认模型
               BAAI/bge-large-zh-v1.5（约 1.3GB，首次需下载）
        """
        config = Config()
        if config.EMBEDDING_MODEL_PATH and os.path.exists(config.EMBEDDING_MODEL_PATH):
            # 本地路径有效，直接加载（无需网络，速度更快）
            self.model = SentenceTransformer(config.EMBEDDING_MODEL_PATH, device=device)
        else:
            # 🔧 修复：移除硬编码路径。优先使用 HuggingFace 模型名称自动下载。
            # 若环境变量 EMBEDDING_MODEL_PATH 未正确设置，则尝试从 HuggingFace 加载。
            model_name = config.EMBEDDING_MODEL_PATH or "BAAI/bge-large-zh-v1.5"
            print(f"⚠️ 配置路径无效，尝试从 HuggingFace 加载模型: {model_name}")
            self.model = SentenceTransformer(model_name, device=device)

    def encode(
        self,
        texts: List[str],
        convert_to_numpy: bool = False,
        normalize_embeddings: bool = False
    ) -> List[List[float]]:
        """
        将文本列表转换为向量表示（Embedding）。

        这是 embedding 模型的核心推理方法，将自然语言文本映射到
        高维向量空间。语义相近的文本在向量空间中距离更近，
        可用于相似度搜索、聚类、分类等下游任务。

        Args:
            texts (List[str]): 待编码的文本列表，如 ["人参", "补气健脾"]
            convert_to_numpy (bool): 是否返回 NumPy 数组格式。
                                     False 时返回 Python list（默认），
                                     True 时返回 numpy.ndarray。
            normalize_embeddings (bool): 是否对输出向量做 L2 归一化。
                                         归一化后向量模长为 1，此时内积
                                         等价于余弦相似度，适合 FAISS 索引。

        Returns:
            List[List[float]]: 嵌入向量列表，每个文本对应一个向量。
                               向量维度取决于模型（BGE-large 为 1024 维）。
                               例如：[[0.123, -0.456, ...], [0.789, ...]]

        Example:
            >>> model = EmbeddingModel()
            >>> vectors = model.encode(["人参", "白术"])
            >>> len(vectors)         # 2（两条文本）
            >>> len(vectors[0])      # 1024（向量维度）
        """
        return self.model.encode(
            texts,
            convert_to_numpy=convert_to_numpy,
            normalize_embeddings=normalize_embeddings
        )


# ============================================================
# 模块级单例
# ============================================================

# 在 import 时创建全局嵌入模型实例，整个应用共享同一份模型。
# 避免重复加载模型文件（BGE-large 约 1.3GB），节省内存。
# 注意：模型加载需要一定时间（首次可能需下载），import 本模块时会有延迟。
embedding_model = EmbeddingModel()


# ============================================================
# 模块自测
# ============================================================

if __name__ == "__main__":
    # 创建测试用的嵌入模型实例
    embedding_model = EmbeddingModel()
    # 打印模型信息
    print(embedding_model)
    # 测试单条文本编码
    print(embedding_model.encode(["你好"]))
    # 打印模型输出向量维度（BGE-large 为 1024）
    print(embedding_model.model.get_sentence_embedding_dimension())
    # 测试批量文本编码（取消注释以测试）
    # print(embedding_model.encode(["你好", "世界"]))
