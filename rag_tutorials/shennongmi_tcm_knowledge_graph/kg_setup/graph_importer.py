"""
中医知识图谱 Neo4j 导入模块

将 extract_formula_data.json 和 extract_herb_data.json 中的实体、关系、属性数据
导入到 Neo4j 图数据库中，构建可查询的中医知识图谱。

数据流程:
  1. 加载两个 JSON 文件（方剂和药材的提取结果）
  2. 按 (name, type) 去重所有实体，以属性更丰富的为准
  3. 按 (subject, relation, object, subject_type, object_type) 去重所有关系
  4. 批量构建 Cypher 语句（MERGE 节点 + MATCH/MERGE 关系）
  5. 分批写入 Neo4j（先建节点、再建关系）
  6. 验证导入结果（统计各类型节点和关系的数量）

关键设计：
    - MERGE 语义：避免重复创建节点和关系，支持增量导入
    - 批量执行：通过 BATCH_SIZE 控制每批 Cypher 语句数量，减少网络往返
    - 属性合并：同名同类型实体多次出现时，合并属性（新不为空的值覆盖旧的空值）
    - 断点保护：可选清空数据库（通过环境变量 FORCE_CLEAR_NEO4J 控制）

环境变量：
    FORCE_CLEAR_NEO4J=true  → 自动清空数据库后导入
    FORCE_CLEAR_NEO4J=false → 不清空，增量导入（MERGE 模式）
    未设置 → 交互模式（有 tty 时询问用户，否则默认不清空）
"""
import json
import sys
from pathlib import Path
from collections import OrderedDict

# 将项目根目录加入 sys.path，以便导入 common 模块（如 neo4j_manager、path_utils 等）
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from common.neo4j_manager import neo4j_client
from tqdm import tqdm


# ============================================================
# 配置
# ============================================================

# 方剂和药材的提取结果 JSON 文件路径
FORMULA_DATA_PATH = PROJECT_ROOT / "kg_data" / "extract_formula_data.json"
HERB_DATA_PATH = PROJECT_ROOT / "kg_data" / "extract_herb_data.json"

# 每批执行的 Cypher 语句数量，较大的批次可减少网络往返次数但增加单次事务内存开销
BATCH_SIZE = 200  # 每批执行的 Cypher 语句数量


# ============================================================
# 数据加载与合并
# ============================================================

def load_json(path: Path) -> list:
    """加载 JSON 文件，返回 results 列表。

    从 JSON 文件中读取数据字典，提取 "results" 字段对应的列表。
    每条 result 通常包含 filename 和 extract_dict 两个字段。

    Args:
        path: JSON 文件的路径

    Returns:
        list: results 列表，每个元素为一条提取结果记录
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("results", [])


def collect_all_results(*paths: Path) -> list:
    """加载多个 JSON 文件，合并所有 results。

    遍历传入的所有路径，逐一加载并合并。缺失的文件会打印警告并跳过。

    Args:
        *paths: 可变数量的 JSON 文件路径

    Returns:
        list: 合并后的所有结果记录
    """
    all_results = []
    for path in paths:
        if path.exists():
            data = load_json(path)
            print(f"加载文件: {path}  ({len(data)} 条)")
            all_results.extend(data)
        else:
            print(f"[警告] 文件不存在，跳过: {path}")
    return all_results


def _extract_entities(result: dict) -> list:
    """
    从单条 result 中提取实体列表。

    兼容两种 JSON 格式（LLM 输出可能因版本差异而不同）：
      - extract_dict 为 dict 时: 读取 extract_dict["entities"] 字段
      - extract_dict 为 list 时: 直接将列表作为实体列表返回

    Args:
        result: 单条提取结果记录，包含 extract_dict 字段

    Returns:
        list: 实体列表，每个实体为包含 name、type、attributes 的字典
    """
    ed = result.get("extract_dict", {})
    if isinstance(ed, list):
        return ed
    return ed.get("entities", [])


def _extract_relations(result: dict) -> list:
    """
    从单条 result 中提取关系列表。

    兼容两种 JSON 格式：
      - extract_dict 为 dict 时: 读取 extract_dict["relations"] 字段
      - extract_dict 为 list 时: 该格式不包含关系，返回空列表

    Args:
        result: 单条提取结果记录

    Returns:
        list: 关系列表，每个关系包含 subject、subject_type、relation、object、object_type
    """
    ed = result.get("extract_dict", {})
    if isinstance(ed, list):
        return []
    return ed.get("relations", [])


def merge_entities(results: list) -> dict:
    """
    遍历所有 results，提取实体并按 (name, type) 去重合并。

    去重策略：以 (name, type) 二元组作为实体的唯一标识键。
    若同一实体在多个文件中出现多次，保留 attributes 更丰富的那个。
    具体而言，后出现的非空属性值会覆盖先出现的空属性值。

    Args:
        results: 所有提取结果记录列表

    Returns:
        OrderedDict: 键为 (name, type) 元组，值为 {name, type, attributes} 字典
    """
    entity_map = OrderedDict()

    for result in results:
        for entity in _extract_entities(result):
            # 清洗实体名称和类型（去除首尾空格，过滤空值）
            name = entity.get("name", "").strip()
            etype = entity.get("type", "").strip()
            if not name or not etype:
                continue

            key = (name, etype)
            attrs = entity.get("attributes") or {}

            if key not in entity_map:
                # 首次出现，直接插入
                entity_map[key] = {"name": name, "type": etype, "attributes": attrs}
            else:
                # 已存在，合并属性：新出现的不为空的属性覆盖旧的（特别是覆盖空的旧值）
                existing_attrs = entity_map[key]["attributes"]
                for k, v in attrs.items():
                    if v is not None and (k not in existing_attrs or existing_attrs.get(k) is None):
                        existing_attrs[k] = v
                entity_map[key]["attributes"] = existing_attrs

    return entity_map


def merge_relations(results: list) -> list:
    """
    遍历所有 results，提取关系并按五元组去重。

    去重策略：以 (subject, relation, object, subject_type, object_type) 五元组
    作为关系的唯一标识键。完全相同的关系只保留一条。

    Args:
        results: 所有提取结果记录列表

    Returns:
        list: 去重后的关系字典列表，每个元素包含 subject、subject_type、relation、object、object_type
    """
    relation_set = OrderedDict()

    for result in results:
        for rel in _extract_relations(result):
            # 清洗各字段
            sub = rel.get("subject", "").strip()
            obj = rel.get("object", "").strip()
            rel_type = rel.get("relation", "").strip()
            sub_type = rel.get("subject_type", "").strip()
            obj_type = rel.get("object_type", "").strip()

            # 过滤不完整的关系记录
            if not all([sub, obj, rel_type, sub_type, obj_type]):
                continue

            key = (sub, rel_type, obj, sub_type, obj_type)
            if key not in relation_set:
                relation_set[key] = {
                    "subject": sub,
                    "subject_type": sub_type,
                    "relation": rel_type,
                    "object": obj,
                    "object_type": obj_type,
                }

    return list(relation_set.values())


# ============================================================
# Cypher 语句构建
# ============================================================

def build_node_cypher(entity: dict) -> tuple:
    """
    为单个实体构建 MERGE 节点 + SET 属性的 Cypher 语句。

    使用 MERGE 避免重复创建节点（按 name 属性匹配），
    用 SET 更新（非空的）属性字段。

    Label 处理：对包含特殊字符（如中文、空格）的 Label 使用反引号转义，
    确保 Cypher 语法正确。

    Args:
        entity: 实体字典，包含 name、type、attributes 字段

    Returns:
        tuple: (cypher_string, params_dict)
            - cypher_string: 待执行的 Cypher 语句字符串（Label 通过反引号转义，name 通过 $name 参数化）
            - params_dict: 参数化查询的参数字典（name 值参数化，防止 Cypher 注入；Label 为枚举类型，经反引号转义后安全）
    """
    etype = entity["type"]
    name = entity["name"]
    attrs = entity.get("attributes") or {}

    # 构建参数化查询的参数字典，name 用于 MERGE 匹配
    params = {"name": name}
    set_items = []

    # 遍历属性，仅将非空属性加入 SET 子句
    for attr_key, attr_val in attrs.items():
        if attr_val is not None and attr_val != "":
            param_key = f"attr_{attr_key}"  # 加前缀避免参数名冲突
            params[param_key] = attr_val
            set_items.append(f"n.{attr_key} = ${param_key}")

    # 转义 Cypher label 中的特殊字符（如中文、空格等）
    safe_type = _escape_label(etype)

    # 构建 MERGE ... SET ... 语句
    query = f"MERGE (n:{safe_type} {{name: $name}})"
    if set_items:
        query += " SET " + ", ".join(set_items)

    return query, params


def build_relation_cypher(rel: dict) -> tuple:
    """
    为单条关系构建 MATCH + MERGE 关系的 Cypher 语句。

    先分别 MATCH 主体和客体节点（按 name 属性匹配），
    然后 MERGE 两者之间的关系边。MERGE 确保不重复创建关系。

    Args:
        rel: 关系字典，包含 subject、subject_type、relation、object、object_type

    Returns:
        tuple: (cypher_string, params_dict)
    """
    sub = rel["subject"]
    sub_type = _escape_label(rel["subject_type"])   # 转义主体 Label
    obj = rel["object"]
    obj_type = _escape_label(rel["object_type"])     # 转义客体 Label
    relation = rel["relation"]

    # 参数化查询：主体/客体名称通过 $sub_name/$obj_name 参数化，
    # 防止 Cypher 注入；关系类型为枚举值，经 Pydantic Schema 约束后安全
    params = {
        "sub_name": sub,
        "obj_name": obj,
    }

    # MATCH 两个端点节点，然后 MERGE 关系边
    query = (
        f"MATCH (a:{sub_type} {{name: $sub_name}}) "
        f"MATCH (b:{obj_type} {{name: $obj_name}}) "
        f"MERGE (a)-[:{relation}]->(b)"
    )

    return query, params


def _escape_label(label: str) -> str:
    """对 Neo4j label 进行反引号转义（处理含空格、中文等情况）。

    Neo4j 的 Label 在包含非 ASCII 字母数字字符时需要用反引号包裹。
    例如 "Herb" 不需要转义，但 "中药方剂" 需要转义为 `中药方剂`。

    Args:
        label: 原始的 Neo4j Label 字符串

    Returns:
        str: 转义后的 Label 字符串（如果需要转义则用反引号包裹）
    """
    # 如果 label 只包含字母、数字、下划线，不需要转义
    # 否则用反引号包裹
    if label and not all(c.isalnum() or c == "_" for c in label):
        return f"`{label}`"
    return label


# ============================================================
# 批量执行
# ============================================================

def batch_execute(queries_with_params: list, desc: str = "执行 Cypher"):
    """
    分批执行 Cypher 语句，每批使用一个事务。

    将大量 Cypher 语句按 BATCH_SIZE 分块执行，每块作为一个事务提交，
    既能保证数据一致性，又能避免单次事务过大导致的性能问题。

    Args:
        queries_with_params: (cypher_string, params_dict) 元组列表
        desc: tqdm 进度条的描述文本
    """
    total = len(queries_with_params)
    if total == 0:
        print(f"[{desc}] 无数据需要执行")
        return

    # 按 BATCH_SIZE 分块遍历，每块提交一次事务
    for i in tqdm(range(0, total, BATCH_SIZE), desc=desc):
        batch = queries_with_params[i : i + BATCH_SIZE]
        neo4j_client.run_multiple_cypher(batch)


# ============================================================
# 主流程
# ============================================================

def main():
    """中医知识图谱导入 Neo4j 的主流程函数。

    执行步骤：
        1. 加载 JSON 数据（方剂 + 药材的提取结果）
        2. 合并实体（去重 + 合并相同实体的属性）
        3. 合并关系（五元组去重）
        4. 构建节点 Cypher 语句
        5. 构建关系 Cypher 语句
        6. 清空数据库（可选）并批量写入 Neo4j
        7. 查询统计信息验证导入结果
    """
    print("=" * 60)
    print("中医知识图谱数据导入 Neo4j")
    print("=" * 60)

    # 1. 加载数据
    print("\n[步骤 1] 加载 JSON 数据...")
    all_results = collect_all_results(FORMULA_DATA_PATH, HERB_DATA_PATH)
    print(f"共加载 {len(all_results)} 条结果记录")

    # 2. 合并实体
    print("\n[步骤 2] 合并实体（去重 & 合并属性）...")
    entity_map = merge_entities(all_results)
    entities = list(entity_map.values())
    print(f"去重后实体总数: {len(entities)}")

    # 按实体类型统计数量，便于了解数据分布
    type_counts = {}
    for e in entities:
        type_counts[e["type"]] = type_counts.get(e["type"], 0) + 1
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    # 3. 合并关系
    print("\n[步骤 3] 合并关系（去重）...")
    relations = merge_relations(all_results)
    print(f"去重后关系总数: {len(relations)}")

    # 按关系类型统计数量
    rel_type_counts = {}
    for r in relations:
        rel_type_counts[r["relation"]] = rel_type_counts.get(r["relation"], 0) + 1
    for t, c in sorted(rel_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    # 4. 构建节点 Cypher 语句
    print("\n[步骤 4] 构建节点 Cypher 语句...")
    node_queries = []
    for entity in tqdm(entities, desc="构建节点语句"):
        node_queries.append(build_node_cypher(entity))
    print(f"节点语句数量: {len(node_queries)}")

    # 5. 构建关系 Cypher 语句
    print("\n[步骤 5] 构建关系 Cypher 语句...")
    rel_queries = []
    for rel in tqdm(relations, desc="构建关系语句"):
        rel_queries.append(build_relation_cypher(rel))
    print(f"关系语句数量: {len(rel_queries)}")

    # 6. 写入 Neo4j —— 先处理数据库清空逻辑
    print("\n[步骤 6] 写入 Neo4j 数据库...")

    # ⚠️ 警告：以下操作将清空 Neo4j 数据库中的所有数据！
    # 🔧 修复：支持通过环境变量 FORCE_CLEAR_NEO4J 跳过交互确认，
    # 避免在 CI/CD 或无 tty 环境下因 input() 而卡死。
    import os as _os
    force_clear = _os.getenv("FORCE_CLEAR_NEO4J", "").strip().lower()
    if force_clear == "true":
        # 环境变量明确要求清空
        print("⚠️ FORCE_CLEAR_NEO4J=true，自动清空现有数据...")
        neo4j_client.run_cypher("MATCH (n) DETACH DELETE n")
    elif force_clear == "false":
        # 环境变量明确要求不清空，增量导入
        print("⏭️ FORCE_CLEAR_NEO4J=false，跳过清空，将在现有数据基础上增量导入（MERGE 模式）")
    else:
        # 交互模式：仅在连接了 tty 时询问用户，避免在 CI/CD 中因 input() 卡死
        import sys as _sys
        if _sys.stdin.isatty():
            print("⚠️  即将清空 Neo4j 数据库中的所有数据！此操作不可撤销。")
            confirm = input("确认清空数据库？输入 yes 继续，其他任意键跳过: ").strip().lower()
            if confirm == "yes":
                print("⚠️ 清空现有数据...")
                neo4j_client.run_cypher("MATCH (n) DETACH DELETE n")
            else:
                print("⏭️ 跳过清空，将在现有数据基础上增量导入（MERGE 模式）")
        else:
            # 非交互环境（如管道、CI/CD），默认不清空，安全优先
            print("⏭️ 非交互环境，跳过清空，将在现有数据基础上增量导入（MERGE 模式）")

    # 先建节点（关系依赖节点存在）
    print("创建节点...")
    batch_execute(node_queries, desc="创建节点")

    # 再建关系（MATCH 需要节点已存在）
    print("创建关系...")
    batch_execute(rel_queries, desc="创建关系")

    # 7. 验证导入结果
    print("\n[步骤 7] 验证导入结果...")

    # 查询各类节点的数量
    stats = neo4j_client.run_cypher(
        """
        MATCH (n)
        RETURN labels(n) AS labels, count(n) AS cnt
        ORDER BY cnt DESC
        """
    )
    print("节点统计:")
    for row in stats:
        print(f"  {row['labels']}: {row['cnt']}")

    # 查询各类关系的数量
    rel_stats = neo4j_client.run_cypher(
        """
        MATCH ()-[r]->()
        RETURN type(r) AS rel_type, count(r) AS cnt
        ORDER BY cnt DESC
        """
    )
    print("关系统计:")
    for row in rel_stats:
        print(f"  {row['rel_type']}: {row['cnt']}")

    print("\n" + "=" * 60)
    print("导入完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
