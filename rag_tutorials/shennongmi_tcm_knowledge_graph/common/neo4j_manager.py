"""
Neo4j 图数据库管理模块
=====================

封装与 Neo4j 图数据库的交互，是中医知识图谱的数据访问层（DAL）。

主要功能:
    - Neo4jClient 类: 管理数据库连接、执行 Cypher 查询、元数据导出
    - 惰性初始化: 模块级 neo4j_client 在首次访问时才创建连接，避免在
      Neo4j 未启动时 import 本模块就崩溃
    - 线程安全: 使用双重检查锁定（Double-Checked Locking）保护惰性初始化
    - 安全校验: 对动态拼接的 Cypher 标签名做正则校验，防止 Cypher 注入

典型用法:
    from common.neo4j_manager import neo4j_client

    # 执行只读查询
    result = neo4j_client.run_cypher("MATCH (n:Herb) RETURN n.name LIMIT 10")

    # 获取所有药材名称
    herbs = neo4j_client.get_all_node_names("Herb")

    # 验证 Cypher 语句合法性
    is_valid, error = neo4j_client.valid_cypher(some_query)
"""

from neo4j import GraphDatabase
from common.config import Config
from tqdm import tqdm
import json
import re

# 全局配置实例，读取 Neo4j 连接凭据
conf = Config()


class Neo4jClient:
    """
    Neo4j 图数据库客户端

    封装与 Neo4j 数据库的完整交互逻辑，包括连接管理、Cypher 查询执行、
    元数据导出等功能。使用 Neo4j 官方 Python 驱动（neo4j 包）实现。

    每个实例通过 self.driver 持有一条数据库连接。建议在应用生命周期内
    复用同一个实例，而非频繁创建/销毁连接。

    Attributes:
        driver: neo4j.GraphDatabase.driver 实例，管理 Bolt 协议连接池。
    """

    def __init__(self, uri, user, password):
        """
        初始化 Neo4j 数据库连接。

        Args:
            uri (str): Bolt 协议连接地址，如 bolt://localhost:7687
            user (str): 数据库用户名，通常为 neo4j
            password (str): 数据库密码
        """
        # GraphDatabase.driver() 创建连接池，不立即建立连接
        # 实际连接在首次执行查询时建立（惰性连接）
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """
        显式关闭驱动连接和连接池。

        应在应用退出时调用，释放网络资源。关闭后 driver 设为 None，
        防止后续误用。再次使用需要重新创建 Neo4jClient 实例。
        """
        if self.driver is not None:
            self.driver.close()
            self.driver = None

    def run_cypher(self, query, parameters=None):
        """
        执行一条 Cypher 查询语句并返回结果列表。

        自动管理 session 的生命周期（with 语句），查询完成后自动
        关闭 session 归还到连接池。

        Args:
            query (str): Cypher 查询语句，支持 $param 参数占位符
            parameters (dict, optional): 参数字典，键为参数名（不含 $ 前缀），
                                         值为参数值。Neo4j 会自动做类型转换和
                                         注入防护。默认为 None（无参数）。

        Returns:
            list[dict]: 查询结果列表，每条记录为一个字典，键为 RETURN 子句中
                        的变量名，值为对应的 Neo4j 数据类型。
                        例如 [{"name": "人参", "category": "补气药"}, ...]

        Example:
            >>> result = neo4j_client.run_cypher(
            ...     "MATCH (n:Herb {name: $name}) RETURN n",
            ...     {"name": "人参"}
            ... )
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            # record.data() 将 Neo4j Record 对象转为 Python dict
            return [record.data() for record in result]

    def run_multiple_cypher(self, queries_with_params):
        """
        执行多条 Cypher 语句，使用事务保证原子性，并显示 tqdm 进度条。

        所有语句在同一个写事务（execute_write）中执行，任一条失败则全部回滚。
        适用于批量数据导入 / 批量更新等场景，通过 tqdm 实时显示执行进度。

        Args:
            queries_with_params (List[Tuple[str, Dict]]):
                查询-参数对列表，每条为 (cypher_query, params_dict) 元组。
                例如: [("CREATE (n:Herb {name: $name})", {"name": "人参"}), ...]

        Example:
            >>> queries = [
            ...     ("CREATE (n:Herb {name: $name})", {"name": name})
            ...     for name in ["人参", "白术", "茯苓"]
            ... ]
            >>> neo4j_client.run_multiple_cypher(queries)
        """
        with self.driver.session() as session:
            # 定义事务逻辑函数，接收事务对象 tx 作为参数
            def transaction_logic(tx):
                for query, params in tqdm(queries_with_params, desc="执行 Cypher 语句"):
                    tx.run(query, params or {})

            # execute_write 自动管理事务提交/回滚
            session.execute_write(transaction_logic)

    def export_tcm_metadata_to_json(self, output_path="tcm_metadata.json"):
        """
        导出知识图谱模式层元数据为 JSON 文件。

        自动扫描数据库中所有的：
            1. 节点标签（Node Labels）及其属性
            2. 关系类型（Relationship Types）及其属性
            3. 三元组结构（头实体标签 → 关系类型 → 尾实体标签）

        生成的 JSON 文件可作为 LLM prompt 的 schema 上下文，告知模型
        知识图谱的结构信息（有哪些实体类型、关系类型和属性）。

        Args:
            output_path (str): 输出 JSON 文件路径，默认为 "tcm_metadata.json"

        Returns:
            str: 输出文件的路径，同 output_path 参数

        输出 JSON 结构示例:
            {
                "labels": [
                    {"name": "Herb", "description": "", "properties": [
                        {"name": "name", "description": ""}, ...
                    ]}
                ],
                "relationships": [
                    {"type": "TREATS", "description": "", "properties": [...]}
                ],
                "triples": [
                    {"from": "Herb", "rel_type": "TREATS", "to": "Disease", "description": ""}
                ]
            }
        """
        with self.driver.session() as session:

            # 1. 获取所有节点标签（如 Herb, Disease, Symptom, Effect 等）
            #    UNWIND 展开每个节点的多标签，DISTINCT 去重
            label_query = """
            MATCH (n)
            UNWIND labels(n) AS label
            RETURN DISTINCT label
            """
            labels = [record["label"] for record in session.run(label_query)]

            # 2. 获取所有关系类型（如 TREATS, CONTAINS, HAS_SYMPTOM 等）
            #    使用无向匹配 (n)-[r]-() 可匹配任意方向的关系
            rel_query = """
            MATCH (n)-[r]-()
            RETURN DISTINCT type(r) AS rel_type
            """
            rel_types = [record["rel_type"] for record in session.run(rel_query)]

            # 3. 获取所有三元组结构（schema 级别的，非实例级别）
            #    head(labels(n)) 取节点的第一个标签作为代表标签
            triple_query = """
            MATCH (n)-[r]->(m)
            WITH head(labels(n)) AS from_label, type(r) AS rel_type, head(labels(m)) AS to_label
            RETURN DISTINCT from_label, rel_type, to_label
            """
            triples = [{
                "from": record["from_label"],
                "rel_type": record["rel_type"],
                "to": record["to_label"],
                "description": ""  # 预留描述字段，供后续人工补充
            } for record in session.run(triple_query)]

            # 4. 获取每个节点标签下的所有属性键
            #    UNWIND keys(n) 将属性键展开为行，DISTINCT 去重
            node_props_query = """
            MATCH (n)
            UNWIND labels(n) AS label
            UNWIND keys(n) AS prop
            RETURN DISTINCT label, prop
            ORDER BY label, prop
            """
            label_props = {}
            for record in session.run(node_props_query):
                label = record["label"]
                prop = record["prop"]
                if prop == "project":  # 忽略内部使用的 project 字段
                    continue
                # setdefault 确保键存在，默认值为空列表
                label_props.setdefault(label, []).append({
                    "name": prop,
                    "description": ""  # 预留描述字段
                })

            # 5. 获取每种关系类型下的所有属性键
            rel_props_query = """
            MATCH (n)-[r]->(m)
            UNWIND keys(r) AS prop
            RETURN DISTINCT type(r) AS rel_type, prop
            ORDER BY rel_type, prop
            """
            rel_type_props = {}
            for record in session.run(rel_props_query):
                rel_type = record["rel_type"]
                prop = record["prop"]
                rel_type_props.setdefault(rel_type, []).append({
                    "name": prop,
                    "description": ""  # 预留描述字段
                })

            # 6. 组装 JSON 对象
            json_obj = {
                "labels": [
                    {
                        "name": label,
                        "description": "",
                        "properties": label_props.get(label, [])
                    } for label in labels
                ],
                "relationships": [
                    {
                        "type": rel,
                        "description": "",
                        "properties": rel_type_props.get(rel, [])
                    } for rel in rel_types
                ],
                "triples": triples
            }

            # 7. 写入 JSON 文件（UTF-8 编码，缩进 2 空格，不转义中文）
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_obj, f, ensure_ascii=False, indent=2)

            return output_path

    def get_all_node_names(self, label: str = None):
        """
        获取指定标签下所有节点的 name 属性。

        常用于构建下拉选项列表（如所有药材名、所有病症名），供前端
        搜索建议或表单选择使用。

        Args:
            label (str, optional): 节点标签，如 'Herb'、'Disease'、'Symptom'。
                                   为 None 时返回所有节点的 name 属性。

        Returns:
            List[str]: 节点名称列表，按字母顺序排序。过滤掉 name 为 None
                       或空字符串的节点。

        Raises:
            ValueError: 当 label 参数不符合 Neo4j 标签命名规范时抛出。
                        Neo4j 标签必须以字母开头，仅包含字母、数字、下划线，
                        长度不超过 256 字符。

        Security:
            使用正则表达式校验 label 参数，防止 Cypher 注入攻击。
            因为 Neo4j 不支持参数化标签名（只能参数化属性值），
            动态拼接标签名时必须先做安全校验。
        """
        # 🔧 修复：用正则校验 label，防止 Cypher 注入。
        # Neo4j label 只能包含字母、数字、下划线，且以字母开头。
        if label is not None:
            if not re.match(r'^[A-Za-z][A-Za-z0-9_]{0,255}$', label):
                raise ValueError(f"无效的 Neo4j 标签: {label!r}")
            # 经过正则校验后才安全拼入（Neo4j 不支持参数化标签名）
            query = (
                f"MATCH (n:`{label}`) "
                "RETURN DISTINCT n.name AS name "
                "ORDER BY name"
            )
        else:
            # 无标签过滤：查询所有节点的 name 属性
            query = (
                "MATCH (n) "
                "RETURN DISTINCT n.name AS name "
                "ORDER BY name"
            )
        with self.driver.session() as session:
            result = session.run(query)
            # 过滤掉 name 为 None 的节点
            return [record["name"] for record in result if record["name"]]

    def valid_cypher(self, query: str) -> tuple:
        """
        验证一条 Cypher 查询语句是否语法合法。

        使用 Neo4j 的 EXPLAIN 命令在不实际执行查询的情况下检查语法。
        EXPLAIN 只做查询计划和语法分析，不会修改数据，因此安全无副作用。

        常用于 Agent 工具调用场景：LLM 生成的 Cypher 语句在执行前
        先通过此方法校验，防止非法语句导致运行时错误。

        Args:
            query (str): 待验证的 Cypher 查询语句

        Returns:
            tuple: (is_valid: bool, error_msg: str)
                   - is_valid=True 表示语句合法，error_msg 为空字符串 ""
                   - is_valid=False 表示语句不合法，error_msg 包含具体错误描述

        Example:
            >>> is_valid, error = neo4j_client.valid_cypher("MATCH (n) RETURN n")
            >>> print(is_valid)  # True
            >>> is_valid, error = neo4j_client.valid_cypher("MATCH (n RETRN n")
            >>> print(error)     # 具体语法错误信息
        """
        try:
            with self.driver.session() as session:
                # EXPLAIN 前缀让 Neo4j 只分析语法和查询计划，不实际执行
                session.run(f"EXPLAIN {query}")
            return True, ""
        except Exception as e:
            error_msg = str(e)
            print(f"Cypher 校验失败: {error_msg}")
            return False, error_msg


# ============================================================
# 惰性初始化机制（Lazy Initialization）
# ============================================================
#
# 🔧 修复：使用惰性初始化，避免在 import 时因 Neo4j 未启动而崩溃。
# 旧行为：neo4j_client = Neo4jClient(...) 在模块导入时立即连接。
# 新行为：首次访问时才创建连接。
#
# 设计原理:
#   1. 使用模块级私有变量 _neo4j_client 存储单例实例
#   2. 使用 threading.Lock 保证线程安全
#   3. 使用双重检查锁定（DCL）模式：先无锁检查是否为 None，
#      如果为 None 则加锁后再次检查，避免多线程同时创建多个实例
#   4. 通过 __getattr__ 模块级钩子拦截对 neo4j_client 的访问，
#      自动触发惰性初始化，对调用方完全透明

import threading

# 模块级私有变量，存储 Neo4jClient 单例
_neo4j_client = None
# 线程锁，保护惰性初始化过程
_neo4j_client_lock = threading.Lock()


def _get_neo4j_client() -> Neo4jClient:
    """
    惰性获取 Neo4j 客户端（线程安全，双重检查锁定）。

    首次调用时创建 Neo4jClient 实例并缓存到模块级变量 _neo4j_client，
    后续调用直接返回缓存的实例。使用双重检查锁定（Double-Checked Locking）
    模式保证多线程环境下的安全性和性能。

    Returns:
        Neo4jClient: 全局唯一的 Neo4j 客户端实例

    Thread Safety:
        使用 threading.Lock 和双重检查模式，确保即使多个线程同时
        首次调用，也只会创建一个 Neo4jClient 实例。
    """
    global _neo4j_client
    # 第一次检查（无锁）：快速路径，大多数情况下实例已存在
    if _neo4j_client is None:
        with _neo4j_client_lock:
            # 第二次检查（有锁）：防止竞态条件下重复创建连接
            # 场景：线程 A 和 B 同时通过第一次检查，A 获得锁创建实例，
            #       B 等待锁，获得锁后再次检查发现已不为 None，跳过创建
            if _neo4j_client is None:
                _neo4j_client = Neo4jClient(conf.NEO4J_URI, conf.NEO4J_USER, conf.NEO4J_PASSWORD)
    return _neo4j_client


def __getattr__(name):
    """
    模块级属性代理（PEP 562 模块 __getattr__）。

    当外部代码访问 `neo4j_client` 时自动调用惰性初始化。
    兼容所有使用 `from common.neo4j_manager import neo4j_client` 的代码，
    使惰性加载对调用方完全透明。

    Args:
        name (str): 被访问的属性名

    Returns:
        Neo4jClient: 当 name == "neo4j_client" 时返回惰性初始化的客户端实例

    Raises:
        AttributeError: 当访问的属性名不是 "neo4j_client" 时抛出
    """
    if name == "neo4j_client":
        return _get_neo4j_client()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ============================================================
# 模块自测
# ============================================================

if __name__ == '__main__':
    # 获取 Neo4j 客户端（惰性初始化）
    neo4j_client = _get_neo4j_client()
    # 测试连接是否正常（只读查询，不修改数据）
    result = neo4j_client.run_cypher("MATCH (n) RETURN count(n) AS count LIMIT 1")
    print(f"Neo4j 连接成功，节点总数: {result[0]['count'] if result else 0}")
