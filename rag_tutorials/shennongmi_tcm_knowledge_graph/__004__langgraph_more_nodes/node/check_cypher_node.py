"""
LangGraph 节点：Cypher 语法校验。

本节点位于 Cypher 生成节点之后、Cypher 执行节点之前，是整个工作流中
"质量守门人"的角色。它逐条调用 Neo4j 的 EXPLAIN 命令来验证 Cypher
语句的语法合法性，确保只有通过校验的语句才会被实际执行。

工作流中的位置：
    Cypher 生成 → [本节点] → 全部通过 → Cypher 执行
                           → 有失败 → 返回 Cypher 生成节点重试（最多 N 次）

EXPLAIN 校验原理：
    Neo4j 的 EXPLAIN 命令会在不实际执行查询的情况下进行语法分析、
    语义检查和查询计划生成。如果语句有语法错误（标签不存在、关系类型
    拼写错误等），EXPLAIN 会直接抛出异常并给出具体错误信息。

自修正重试机制：
    当校验失败时，本节点会将 Neo4j 的详细错误信息写入
    cypher_validation_feedback，工作流路由器检测到 is_all_validate_cypher
    为 False 后会路由回 generate_neo4j_cypher_node，后者将错误信息
    嵌入提示词，引导 LLM 根据具体报错进行修正。

失败处理策略：
    - 全部通过 → is_all_validate_cypher = True，进入 Cypher 执行
    - 部分失败 → is_all_validate_cypher = False，反馈错误详情，
      工作流层控制是否重试或退出
    - 查询列表为空 → is_all_validate_cypher = False，反馈提示信息，
      工作流层将跳过 Cypher 执行，直接给出"暂无收录信息"的兜底回答
"""

from __004__langgraph_more_nodes.agent_state import AgentState
from common.neo4j_manager import neo4j_client


def check_cypher_node(state: AgentState) -> AgentState:
    """
    校验 Cypher 语句的语法合法性。

    通过 Neo4j 的 EXPLAIN 命令逐条验证 cypher_query 列表中的每条语句。
    EXPLAIN 不会实际执行查询，仅做语法和语义分析，因此安全性高、性能开销低。

    逻辑：
      - 逐条调用 Neo4j 的 EXPLAIN 校验每条 Cypher 语句
      - 全部通过 → is_all_validate_cypher = True
      - 有一条不通过 → is_all_validate_cypher = False，
        并将具体错误信息写入 cypher_validation_feedback，
        供下游 generate_neo4j_cypher_node 重试时参考修正

    输入 state 字段：
        - cypher_query → 待校验的 Cypher 语句列表
        - cypher_retry_count → 当前重试次数（保留原值，不做修改）

    输出 state 字段：
        - is_all_validate_cypher    → 是否全部通过校验（布尔值）
        - cypher_validation_feedback → 校验失败的详细错误信息（通过时为空字符串）
    """
    print("=" * 50)
    print("🔍 开始校验 Cypher 语句")
    print("=" * 50)

    # 从 state 中获取待校验的 Cypher 语句列表
    cypher_query_list = state.get("cypher_query", [])

    # 初始化校验状态：默认全部通过
    state["is_all_validate_cypher"] = True
    state["cypher_validation_feedback"] = ""

    # 特殊处理：Cypher 查询列表为空
    # 这可能发生在以下场景：
    #   1. 用户问题不涉及知识图谱查询（闲聊）
    #   2. 所有关键实体都未在 FAISS 中匹配到
    #   3. Cypher 生成节点遇到异常
    # 此时标记为未通过，由工作流层决定是否跳过执行
    if not cypher_query_list:
        state["is_all_validate_cypher"] = False
        state["cypher_validation_feedback"] = "Cypher 查询列表为空，没有可校验的语句。"
        print("⚠️ Cypher 查询列表为空")
        return state

    # 逐条校验每条 Cypher 语句
    errors = []
    for i, cypher_query in enumerate(cypher_query_list, 1):
        print(f"\n[{i}/{len(cypher_query_list)}] 校验: {cypher_query[:100]}...")

        # 调用 Neo4j EXPLAIN 进行语法/语义校验
        # is_valid: True 表示语法正确，False 表示有错误
        # error_msg: 错误详情（Neo4j 返回的具体报错信息）
        is_valid, error_msg = neo4j_client.valid_cypher(cypher_query)

        if is_valid:
            print(f"  ✅ 通过")
        else:
            # 校验失败：记录错误详情以便后续修正
            print(f"  ❌ 失败: {error_msg}")
            state["is_all_validate_cypher"] = False
            errors.append(f"语句[{i}]: {cypher_query}\n  错误: {error_msg}")

    # 汇总所有失败信息，构建结构化的反馈文本
    # 这段文本会直接嵌入 LLM 的重试提示词中，因此格式需要便于 LLM 理解
    if errors:
        state["cypher_validation_feedback"] = (
            f"以下 {len(errors)} 条 Cypher 语句校验失败，请根据 Neo4j 的报错信息修正：\n\n"
            + "\n\n".join(errors)
        )

    print(f"\n{'=' * 50}")
    print(f"🔍 校验结果: {'全部通过 ✅' if state['is_all_validate_cypher'] else f'有 {len(errors)} 条失败 ❌'}")
    print(f"{'=' * 50}")

    return state


if __name__ == "__main__":
    # 快速测试：需要 Neo4j 连接
    from unittest.mock import patch, MagicMock

    def _build_state(cypher_query, retry_count=0):
        """
        构建测试用 state。

        :param cypher_query: 待校验的 Cypher 语句列表
        :param retry_count: 模拟的当前重试次数
        """
        return {
            "cypher_query": cypher_query,
            "is_all_validate_cypher": False,
            "cypher_validation_feedback": "",
            "cypher_retry_count": retry_count,
        }

    # 测试1：模拟全部通过
    print("=" * 60)
    print("测试1: 全部 Cypher 通过校验")
    print("=" * 60)
    state1 = _build_state(["MATCH (h:Herb {name: '人参'}) RETURN h"])
    with patch.object(neo4j_client, "valid_cypher", return_value=(True, "")):
        result1 = check_cypher_node(state1)
    print(f"  is_all_validate_cypher: {result1['is_all_validate_cypher']}")
    print(f"  feedback: '{result1.get('cypher_validation_feedback', '')}'")
    print()

    # 测试2：模拟部分失败
    print("=" * 60)
    print("测试2: 部分 Cypher 校验失败")
    print("=" * 60)
    state2 = _build_state([
        "MATCH (h:Herb {name: '人参'}) RETURN h",
        "MATCH (f:Formla {name: '四君子汤'}) RETURN f",  # Formla 拼写错误
    ])
    responses = [
        (True, ""),
        (False, "Label 'Formla' does not exist in the graph. Did you mean 'Formula'?"),
    ]
    with patch.object(neo4j_client, "valid_cypher", side_effect=responses):
        result2 = check_cypher_node(state2)
    print(f"  is_all_validate_cypher: {result2['is_all_validate_cypher']}")
    print(f"  feedback:\n{result2.get('cypher_validation_feedback', '')}")
    print()

    # 测试3：空列表
    print("=" * 60)
    print("测试3: 空 Cypher 列表")
    print("=" * 60)
    state3 = _build_state([])
    result3 = check_cypher_node(state3)
    print(f"  is_all_validate_cypher: {result3['is_all_validate_cypher']}")
    print(f"  feedback: '{result3.get('cypher_validation_feedback', '')}'")
