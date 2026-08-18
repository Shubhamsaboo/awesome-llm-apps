"""
LangGraph 节点：Cypher 语句执行。

本节点是 TCM 知识图谱问答链路的最后一个数据节点。它接收经过校验的
Cypher 查询语句列表，逐条在 Neo4j 图数据库中执行，并将结果收集汇总。

工作流中的位置：
    Cypher 生成 → Cypher 校验（通过）→ [本节点] → 结果汇总/回答生成

执行策略：
    - 逐条执行：每条 Cypher 语句独立执行，互不影响
    - 容错处理：某条语句执行失败时不影响其他语句，
      错误信息随查询结果一起记录，供下游节点判断和处理
    - 结果保留：每条语句的查询语句原文和执行结果（或错误）
      成对保留在 cypher_results 中，便于前端展示和 LLM 总结

输入 state 字段：
    - cypher_query → 已通过校验的 Cypher 查询语句列表

输出 state 字段：
    - cypher_results → 查询结果列表，每项结构为：
        {
            'query': str,           # 执行的 Cypher 语句原文
            'result': list[dict],   # Neo4j 返回的记录列表（成功时）
        }
        或
        {
            'query': str,           # 执行的 Cypher 语句原文
            'error': str,           # 异常信息（失败时）
        }
"""

from common.neo4j_manager import neo4j_client
from langgraph_workflow.agent_state import AgentState


def run_cypher_node(state: AgentState) -> AgentState:
    """
    执行 Cypher 语句节点：逐条在 Neo4j 中执行已校验通过的 Cypher 查询，
    并将所有结果收集到 state 中供下游节点（如结果摘要、LLM 回答生成）使用。

    执行流程：
        1. 从 state 中获取 Cypher 语句列表
        2. 逐条在 Neo4j 中执行
        3. 每条语句的成功结果或错误信息按统一格式存入 cypher_results
        4. 返回更新后的 state

    :param state: AgentState，包含 cypher_query 字段（Cypher 语句列表）
    :return: 更新后的 AgentState，cypher_results 字段被填充

    异常处理：
        - 单条语句执行异常时，异常被捕获并记录在该条语句的 error 字段中，
          不会中断整个节点的执行流程
        - 异常不会导致其他 Cypher 语句被跳过
    """
    # 阶段一：获取待执行的 Cypher 语句列表
    print("开始执行cypher语句")
    cypher_query_list = state.get("cypher_query", [])
    query_results = []  # 存储每条语句的执行结果（成功或失败）

    # 阶段二：逐条执行 Cypher 语句
    # 每条语句独立执行，互不影响。某条失败不会阻止后续语句的执行。
    for cypher_query in cypher_query_list:
        try:
            # 调用 Neo4j 客户端执行查询
            # run_cypher 返回 Neo4j Record 对象的列表，
            # 每条 Record 可通过 dict(record) 或 record.data() 转为字典
            result_list = neo4j_client.run_cypher(cypher_query)
            # 成功：同时记录查询原文和返回结果
            query_results.append({
                'query': cypher_query,
                'result': result_list
            })
        except Exception as e:
            # 失败：记录查询原文和异常信息
            # 常见失败原因：
            #   1. Cypher 语法错误（理论上已被 check_cypher_node 拦截，但 CHECK 非 100% 可靠）
            #   2. Neo4j 数据库连接问题
            #   3. 查询超时
            query_results.append({
                'query': cypher_query,
                'error': str(e)
            })
            print(f"执行cypher语句失败: {e}")

    # 阶段三：将执行结果写入 state，供下游节点使用
    # cypher_results 结构：
    #   [{'query': 'MATCH ...', 'result': [...]},      # 成功
    #    {'query': 'MATCH ...', 'error': '...'}]        # 失败
    state['cypher_results'] = query_results
    print("完成执行所有Cypher语句")
    return state
