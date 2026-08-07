"""
LangGraph 节点：通过 FAISS 向量相似度将用户实体匹配到 Neo4j 知识图谱标准实体。

本节点是实体处理链路的第二步（紧随实体抽取之后）。它利用 SentenceTransformer
将用户输入的原始实体名称编码为向量，通过 FAISS 索引在 Neo4j 知识图谱的所有实体
中检索语义最相似的标准实体名称，从而桥接"用户用语"与"数据库中的标准名称"。

工作流中的位置：
    实体抽取（LLM） → [本节点] → Cypher 生成 → Cypher 校验 → Cypher 执行

核心技术组件：
    - FAISS 索引：存储知识图谱中所有实体的向量表示
    - id2text 映射：FAISS 内部 ID → 实体标准名称
    - SentenceTransformer：将查询文本编码为同空间向量
    - 余弦相似度阈值：过滤低相似度的假阳性匹配

重要：FAISS 索引必须在 embedding_model 之前加载！！！
原因：embedding_model 使用 PyTorch MPS（Apple Silicon GPU），
      如果 FAISS 索引在 SentenceTransformer 之后才加载，
      会导致 index.search() 时发生 segmentation fault。
      这是 PyTorch MPS 与 FAISS 底层 BLAS 之间的已知兼容性问题。
"""

import os
import pickle
from typing import List, Tuple

import faiss

from __004__langgraph_more_nodes.agent_state import AgentState
from common.config import Config
from common.path_utils import get_file_path


# ============================================================
# 模块级预加载 FAISS 索引和 id2text 映射
# ============================================================
#
# 重要：必须在 embedding_model 之前加载 FAISS 索引！
# 原因：embedding_model 使用 PyTorch MPS（Apple Silicon GPU），
#       如果 FAISS 索引在 SentenceTransformer 之后才加载，
#       会导致 index.search() 时发生 segmentation fault。
#       这是 PyTorch MPS 与 FAISS 底层 BLAS 之间的已知兼容性问题。
#


def _resolve_faiss_paths() -> Tuple[str, str]:
    """
    解析 FAISS 索引和映射文件的路径，兼容配置中的路径拼写错误。

    优先使用 Config 中配置的路径，如果文件不存在则尝试修正拼写错误
    （如 nero4j → neo4j）后的路径，提高系统容错性。

    Returns:
        (index_path, mapping_path) — FAISS 索引文件路径和 id2text 映射文件路径
    """
    config = Config()

    # 优先使用配置中的路径，如果不存在则尝试修正的路径
    index_path = config.ENTITY_INDEX_PATH
    mapping_path = config.ENTITY_ID2TEXT_PATH

    if not os.path.exists(index_path):
        # 兼容 typo: nero4j → neo4j
        fallback_index = get_file_path("__003__create_neo4j_database/neo4j_embedding_faiss.index")
        if os.path.exists(fallback_index):
            index_path = fallback_index

    if not os.path.exists(mapping_path):
        fallback_mapping = get_file_path("__003__create_neo4j_database/neo4j_embedding_faiss_id2text.pkl")
        if os.path.exists(fallback_mapping):
            mapping_path = fallback_mapping

    return index_path, mapping_path


def _eager_load_faiss():
    """
    在模块导入时立即加载 FAISS 索引（eager loading）。

    这种"急加载"策略确保 FAISS 在 PyTorch/SentenceTransformer 之前完成初始化，
    避免 MPS + FAISS 底层 BLAS 冲突导致的 segmentation fault。

    Returns:
        (faiss_index, id2text_dict) — FAISS Index 对象和 {内部ID: 实体名称} 映射字典

    Raises:
        FileNotFoundError: 索引文件或映射文件不存在时抛出，阻止系统在不完整状态下启动
    """
    index_path, mapping_path = _resolve_faiss_paths()

    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS 索引文件不存在: {index_path}")
    if not os.path.exists(mapping_path):
        raise FileNotFoundError(f"FAISS id2text 映射文件不存在: {mapping_path}")

    # 加载 FAISS 索引（内存映射方式，高效且不重复加载）
    idx = faiss.read_index(index_path)
    # 加载 id → 实体名称映射表
    with open(mapping_path, "rb") as f:
        id2text = pickle.load(f)

    print(f"✅ FAISS 索引加载完成，共 {idx.ntotal} 条实体")
    return idx, id2text


# 在 embedding_model 导入之前立即加载 FAISS（避免 MPS + FAISS 冲突导致 segfault）
_faiss_index, _id2text = _eager_load_faiss()

# FAISS 索引已就绪，现在可以安全加载 embedding_model
# noqa: E402 — 此 import 有意放在模块级代码之后，确保 FAISS 先于 PyTorch 初始化
from common.embedding_model import embedding_model  # noqa: E402 (import after module-level code is intentional)


# ============================================================
# 检索函数
# ============================================================

def batch_search_similar_entities(
    queries: List[str],
    top_k: int = 3,
    threshold: float = 0.85,
) -> List[List[Tuple[str, float]]]:
    """
    批量在 FAISS 索引中搜索与 queries 最相似的实体名称。

    工作原理：
        - 将所有 queries 一次性编码为向量矩阵 (n, dim)
        - 一次性在 FAISS 索引中检索，返回 (n, top_k) 的距离和索引矩阵
        - 按行处理，每行对应一个 query 的 top_k 个匹配结果
        - 将 L2 距离精确转换为余弦相似度 (cos = 1 - L2²/2)，过滤低于阈值的结果

    批量检索的优势：
        相比逐条检索，批量编码和批量搜索显著减少了 Python ↔ C++ 的跨语言调用次数，
        同时利用了 FAISS 内部的矩阵运算优化（如 OpenMP 并行），性能提升明显。

    :param queries:   待匹配的实体名称列表，如 ["咳嗽", "四君子汤", "补气血"]
    :param top_k:     每个 query 返回的最相似实体数量
    :param threshold: 余弦相似度阈值 ∈ [0, 1]，只有 cos >= threshold 的结果才会被保留。
                      向量已归一化，等价 L2 距离对照：
                        cos≥0.95 → L2≤0.316
                        cos≥0.85 → L2≤0.548
                        cos≥0.70 → L2≤0.775
                        cos≥0.50 → L2≤1.0
                      默认 0.85，兼顾召回与精确。
    :return:          List[List[(实体名称, 相似度得分)]]
                      queries[i] 的匹配结果在 result[i] 中，按相似度降序排列
    """
    if not queries:
        return []

    # 批量编码：一次 encode，shape = (len(queries), dim)
    # normalize_embeddings=True 确保向量被归一化到单位长度，
    # 这样 L2 距离与余弦相似度之间存在精确的数学转换关系
    query_embeddings = embedding_model.encode(
        queries, convert_to_numpy=True, normalize_embeddings=True
    )

    # 批量检索：一次 FAISS search，shape = (len(queries), top_k)
    # distances: L2 距离矩阵，值越小表示越相似
    # indices: FAISS 内部索引矩阵，可通过 _id2text 映射回实体名称
    distances, indices = _faiss_index.search(query_embeddings, top_k)

    # 按行处理，distances[i] / indices[i] 对应 queries[i] 的 top_k 个匹配
    all_results: List[List[Tuple[str, float]]] = []
    for dist_row, idx_row in zip(distances, indices):
        row_results: List[Tuple[str, float]] = []
        for dist, idx in zip(dist_row, idx_row):
            if idx == -1:  # FAISS 返回的无效索引（当实际结果少于 top_k 时）
                continue
            entity_name = _id2text.get(int(idx))
            if entity_name is None:
                continue
            # 归一化向量下 L2 距离 → 余弦相似度精确转换：cos = 1 - L2²/2
            # 推导：对于归一化向量 a, b，L2² = ||a-b||² = 2 - 2cos(a,b)
            #       所以 cos = 1 - L2²/2
            similarity = 1.0 - (dist * dist) / 2.0
            if similarity >= threshold:
                row_results.append((entity_name, float(similarity)))
        all_results.append(row_results)

    return all_results


# ============================================================
# LangGraph 节点函数
# ============================================================

def match_entity_from_neo4j_node(state: AgentState) -> AgentState:
    """
    实体匹配节点：将从用户输入中抽取的中医实体，通过 FAISS 向量检索，
    匹配到 Neo4j 知识图谱中的标准实体名称。

    输入（来自 extract_entity_from_user_input_node 的输出）：
        - user_input_effects   → 用户提到的功效
        - user_input_diseases  → 用户提到的疾病
        - user_input_symptoms  → 用户提到的症状
        - user_input_formulas  → 用户提到的方剂
        - user_input_herbs     → 用户提到的药材
        - user_input_sources   → 用户提到的出处

    输出（写入 state）：
        - matched_effects / matched_diseases / matched_symptoms /
          matched_formulas / matched_herbs / matched_sources
          每个字段存储匹配到的 Neo4j 标准实体名称列表

    匹配策略：
        - 对每个抽取的实体，在 FAISS 索引中检索 top-3 最相似实体
        - 取相似度最高且超过阈值的结果作为匹配
        - 若无满足阈值的结果，该实体视为未匹配，跳过
        - 未匹配的实体会在 generate_neo4j_cypher_node 中作为
          "仅供参考"信息传递给 LLM，但不强制使用
    """
    print("=" * 50)
    print("🔍 开始实体匹配：用户输入实体 → Neo4j 知识图谱实体")
    print("=" * 50)

    # 定义六类实体的输入/输出字段映射
    # key: 实体中文类型名（用于日志输出）
    # value: (state中的输入字段名, state中的输出字段名)
    entity_type_mapping = {
        "功效": ("user_input_effects", "matched_effects"),
        "疾病": ("user_input_diseases", "matched_diseases"),
        "症状": ("user_input_symptoms", "matched_symptoms"),
        "方剂": ("user_input_formulas", "matched_formulas"),
        "药材": ("user_input_herbs", "matched_herbs"),
        "出处": ("user_input_sources", "matched_sources"),
    }

    total_matched = 0  # 成功匹配的实体总数（跨所有类型）

    for type_name, (input_field, output_field) in entity_type_mapping.items():
        # 从 state 中读取该类型的原始抽取实体
        extracted_entities = state.get(input_field, [])
        if not extracted_entities:
            # 该类型无抽取实体，输出字段置空
            state[output_field] = []
            continue

        print(f"\n📌 匹配【{type_name}】类实体 (共 {len(extracted_entities)} 个):")

        # 批量检索：一次 encode + 一次 FAISS search 处理该类型的所有实体
        # top_k=3 表示每个实体取前 3 个候选，取第一个（相似度最高）作为匹配结果
        batch_results = batch_search_similar_entities(extracted_entities, top_k=3)

        matched = []
        for entity, similar_list in zip(extracted_entities, batch_results):
            if similar_list:
                # similar_list 已按相似度降序排列，取第一个（最相似的）
                best_name, best_score = similar_list[0]
                matched.append(best_name)
                total_matched += 1
                print(f"  ✅ '{entity}' → '{best_name}' (相似度: {best_score:.4f})")
            else:
                # 无满足阈值的候选项，可能原因：
                #   1. 用户描述的实体在知识图谱中不存在
                #   2. 用户描述与标准名称差异过大（如口语化表述 vs 学术名）
                print(f"  ❌ '{entity}' → 未找到匹配实体（无满足阈值的候选项）")

        state[output_field] = matched

    print(f"\n{'=' * 50}")
    print(f"✅ 实体匹配完成: 共匹配 {total_matched} 个实体")
    print(f"{'=' * 50}")

    return state


# ============================================================
# 调试入口
# ============================================================

if __name__ == "__main__":
    # 测试批量 FAISS 检索
    # FAISS 索引已在模块加载时由 _eager_load_faiss() 预加载，无需再手动加载

    test_queries = ["咳嗽", "四君子汤", "补气血", "感冒", "人参","数学"]
    results = batch_search_similar_entities(test_queries, top_k=3)

    for q, matches in zip(test_queries, results):
        print(f"\n🔎 搜索: '{q}'")
        if matches:
            for name, score in matches:
                print(f"    {name} (相似度: {score:.4f})")
        else:
            print("    (无匹配)")
