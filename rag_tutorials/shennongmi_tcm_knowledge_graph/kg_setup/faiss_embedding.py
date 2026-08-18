"""
FAISS 向量索引构建模块

从 Neo4j 图数据库中获取所有节点名称，使用预训练的文本向量模型
将这些名称编码为向量，并构建 FAISS（Facebook AI Similarity Search）索引，
支持高效的语义相似度搜索。

工作流程：
    1. 从 Neo4j 获取所有节点的 name 属性
    2. 使用文本嵌入模型将节点名称转为向量（L2 归一化）
    3. 构建 FAISS 索引（IndexFlatL2，精确搜索）
    4. 保存 FAISS 索引文件到磁盘
    5. 保存 id → 原始文本的映射关系（pickle 格式）

输出文件：
    - neo4j_embedding_faiss.index: FAISS 向量索引文件
    - neo4j_embedding_faiss_id2text.pkl: id 到原始文本的映射关系

用途：在知识图谱检索场景中，用户输入自然语言查询后，
     通过 FAISS 快速找到最相似的节点名称，进而在图数据库中展开关联查询。
"""
import os
import pickle
import faiss
from common.neo4j_manager import neo4j_client
from common.embedding_model import embedding_model


def build_faiss_index(sentences, index_path="faiss.index", mapping_path="id2text.pkl"):
    """
    基于字符串列表构建 FAISS 索引并保存到磁盘。

    使用预训练的文本向量模型（embedding_model）对输入文本列表进行编码，
    创建基于 L2 距离的精确搜索索引，并将索引和 id→文本映射持久化。

    步骤：
        1. 调用嵌入模型将文本转换为向量（启用 L2 归一化，使内积等价于余弦相似度）
        2. 创建 FAISS IndexFlatL2 索引（基于 L2 距离的精确最近邻搜索）
        3. 将所有向量添加到索引中
        4. 将索引写入磁盘（faiss.write_index）
        5. 构建并保存 id → 原始文本的映射字典（pickle 序列化）

    Args:
        sentences: List[str]，输入的文本列表（每条文本对应一个向量）
        index_path: FAISS 索引保存路径，默认为 "faiss.index"
        mapping_path: id → 原始文本映射保存路径，默认为 "id2text.pkl"
    """
    # 1. 生成向量
    # convert_to_numpy=True: 转换为 NumPy 数组，供 FAISS 使用
    # normalize_embeddings=True: L2 归一化，使向量模长为 1，此时 L2 距离等价于余弦距离
    embeddings = embedding_model.encode(sentences, convert_to_numpy=True, normalize_embeddings=True)

    # 2. 创建 FAISS 索引
    # IndexFlatL2: 使用暴力搜索的精确 L2 距离索引，适合中小规模数据（百万级以内）
    dim = embeddings.shape[1]           # 获取向量维度
    index = faiss.IndexFlatL2(dim)       # 创建 L2 距离索引
    index.add(embeddings)                # 将所有向量加入索引

    # 3. 保存索引到磁盘
    faiss.write_index(index, index_path)

    # 4. 保存 id → 原始文本的映射关系
    # 用于在搜索时根据返回的向量 id 反查原始文本
    id2text = {i: sentence for i, sentence in enumerate(sentences)}
    with open(mapping_path, "wb") as f:
        pickle.dump(id2text, f)

    print(f"✅ 索引已保存到 {index_path}, 映射保存到 {mapping_path}")

# 获取所有节点名称
# get_all_node_names() 从 Neo4j 查询所有节点的 name 属性，
# 返回一个字符串列表，每个元素为一个节点的名称
node_names = neo4j_client.get_all_node_names()

# 将节点名称进行向量化并构建 FAISS 索引
# 脚本所在目录作为索引和映射文件的保存路径
current_dir = os.path.dirname(os.path.abspath(__file__))
build_faiss_index(node_names,
                  index_path=os.path.join(current_dir, "neo4j_embedding_faiss.index"),
                  mapping_path=os.path.join(current_dir, "neo4j_embedding_faiss_id2text.pkl"))
