"""
Neo4j 图谱答案生成节点（异步流式版本）
============================================

角色定位:
    LangGraph 工作流中的"答案生成"节点，位于 Cypher 查询执行之后。
    将 Neo4j 知识图谱的查询结果（结构化 JSON）作为上下文，由大模型
    (LLM) 生成自然语言回答。

核心功能:
    1. 接收上游节点传来的 Cypher 查询结果列表 (cypher_results)
    2. 构建包含对话历史、用户问题和图谱查询结果的 prompt
    3. 调用 streaming_llm.astream() 实现 token 级别流式输出
    4. 每个 token 实时推送到 stream_queue（真流式）供 SSE 消费，
       同时存入 state["_stream_tokens"]（向后兼容非流式 /process 端点）

空结果处理策略:
    当 cypher_results 为空时，根据上游失败原因分三类给出不同提示:
      a) 实体未匹配 → 知识库未收录（无 Cypher 查询语句生成）
      b) Cypher 校验全部失败 → 语法/标签问题（有查询语句但校验不通过）
      c) LLM 生成异常 → 有实体匹配但未产出查询语句

依赖:
    - common.llm.streaming_llm: 流式大模型实例
    - common.llm.format_conversation_history: 对话历史格式化工具
    - common.stream_context.stream_queue: 线程安全的流式消息队列
    - AgentState: LangGraph 全局状态
"""

from langchain_core.messages import HumanMessage

from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import streaming_llm, format_conversation_history
from common.stream_context import stream_queue
import json


async def neo4j_answer_generate_node(state: AgentState) -> AgentState:
    """
    生成自然语言回答（异步流式版本）。

    使用 streaming_llm.astream() 实现 token 级别流式输出:
      - 每个 token 存入 state["_stream_tokens"]，供 FastAPI /process 端点
        在 astream_events 循环结束后逐 token 发送到前端。
      - 同时推入 stream_queue，供 FastAPI /process/stream 端点
        以 SSE (Server-Sent Events) 方式实时推送到前端。

    参数:
        state (AgentState): LangGraph 全局状态，包含:
            - input: 用户原始输入
            - cypher_results: Neo4j 执行后的查询结果列表
            - messages: 对话历史消息列表
            - cypher_query: 生成的 Cypher 查询语句列表
            - is_all_validate_cypher: 是否全部通过语法校验
            - matched_* 系列字段: 匹配到的实体列表

    返回:
        AgentState: 更新后的状态，新增/修改字段:
            - neo4j_answer: LLM 生成的自然语言回答
            - output: 最终输出（与 neo4j_answer 相同）
            - _stream_tokens: token 列表（流式输出用）
    """
    print("开始生成大模型的回答")
    user_input = state.get("input", "")
    cypher_results = state.get("cypher_results", [])
    messages = state.get("messages", [])
    # 初始化流式 token 缓存列表（每次调用重新开始）
    state["_stream_tokens"] = []

    # 获取当前请求的流式队列（仅 /process/stream 端点会设置）
    # 如果未设置（非流式端点调用），queue 为 None，后续跳过推送
    queue = stream_queue.get(None)

    # ================================================================
    # 空结果分支: 根据失败原因给出差异化提示
    # ================================================================
    # 🔧 修复：根据失败原因给出不同提示，而非统一返回"未能查询到相关信息"。
    # 可能的空结果原因：
    #   a) 无匹配实体 → cypher_query 为空（知识库未收录）
    #   b) Cypher 校验全部失败 → cypher_query 非空但 is_all_validate_cypher=False（语法正确性问题）
    #   c) LLM 生成异常 → cypher_query 为空但有异常记录
    if not cypher_results:
        cypher_query = state.get("cypher_query", [])
        is_valid = state.get("is_all_validate_cypher", False)

        if cypher_query and not is_valid:
            # 情况b: 有查询语句但校验都不通过 → 语法/标签问题
            # 可能原因: LLM 生成的 Cypher 语句语法有误，或用了不存在的节点标签/关系类型
            no_result_msg = (
                "抱歉，系统生成了知识图谱查询语句但未能通过语法校验，"
                "暂时无法回答您的问题。请尝试换一种方式提问，或检查是否输入了正确的方剂/药材名称。"
            )
        elif not cypher_query:
            # 情况a 或 c: 没有生成任何查询 → 实体未匹配或 LLM 未产出
            # 统计所有实体匹配字段中被匹配到的实体总数
            matched_count = sum(len(state.get(k, [])) for k in (
                "matched_effects", "matched_diseases", "matched_symptoms",
                "matched_formulas", "matched_herbs", "matched_sources",
            ))
            if matched_count == 0:
                # 情况a: 实体提取阶段未匹配到任何知识图谱实体 → 知识库未收录
                no_result_msg = (
                    "抱歉，未能在中医知识图谱中找到与您问题相关的实体信息，"
                    "无法回答您的问题。请尝试使用更具体的方剂名、药材名或症状名提问。"
                )
            else:
                # 情况c: 有实体匹配但 LLM 未成功生成 Cypher 语句 → 生成异常
                no_result_msg = (
                    "抱歉，虽然匹配到了一些相关实体，但未能成功生成知识图谱查询语句，"
                    "暂时无法回答您的问题。请稍后重试或换一种方式提问。"
                )
        else:
            # 兜底（cypher_query 非空且校验通过但 run_cypher 未产生结果，极少见）
            # 可能原因: Neo4j 连接异常、数据库为空等
            no_result_msg = "抱歉，未能从知识图谱中查询到相关信息，无法回答您的问题。"

        # 将提示消息写入状态，同时作为流式输出推送给前端
        state["neo4j_answer"] = no_result_msg
        state["output"] = no_result_msg
        state["_stream_tokens"] = [no_result_msg]
        # 流式模式下也需推送此消息，让用户看到提示
        if queue is not None:
            await queue.put({"type": "token", "content": no_result_msg})
        print("没有 Cypher 查询结果，直接返回提示信息")
        return state

    # ================================================================
    # 正常流程: 有 Cypher 查询结果，构建 prompt 调用 LLM 生成回答
    # ================================================================

    # 将 Cypher 查询结果序列化为格式化的 JSON 字符串（保留中文，缩进 4 格）
    cypher_results_json = json.dumps(cypher_results, ensure_ascii=False, indent=4)

    # 构建对话历史文本（保留最近 5 轮，避免 prompt 过长超出上下文窗口）
    history_section = format_conversation_history(messages, max_turns=5)

    # 组装 prompt: 角色设定 + 对话历史 + 用户问题 + 图谱查询结果
    prompt = f"""
    你是一个中医知识图谱问答助手。
{history_section}

    用户当前提出了问题：{user_input}

    我已经在 Neo4j 图数据库中执行了查询，查询结果如下：
    {cypher_results_json}

    请你根据这些查询结果，结合对话历史上下文，用简洁、清晰、自然的中文回答用户的问题。
    如果用户当前问题涉及对话历史中的内容（如用"它"、"这个"等代词指代之前提到的方剂/药材），请结合历史上下文理解用户意图。
    如果查询结果无法回答用户的问题，请如实告知用户没有找到相关答案。
    如果查询结果中包含错误信息（error 字段），请告知用户查询过程中出现了错误，并尽量基于成功的查询结果作答。
    """

    # ================================================================
    # 流式输出: 调用 streaming_llm.astream()
    # ================================================================
    # astream() 是 LangChain 的异步流式方法，yield 每个 token chunk。
    # 每个 token 同时做两件事:
    #   1. 追加到 state["_stream_tokens"] → 非流式 /process 端点用
    #   2. 推入 stream_queue → 真流式 SSE /process/stream 端点用
    try:
        full_response = ""
        async for chunk in streaming_llm.astream([HumanMessage(content=prompt)]):
            token = chunk.content
            if token:
                full_response += token
                state["_stream_tokens"].append(token)
                # 真流式：token 产生瞬间推入队列，由 SSE event_generator 即时消费
                if queue is not None:
                    await queue.put({"type": "token", "content": token})
        answer = full_response.strip()
    except Exception as e:
        # LLM 调用异常（网络超时、API 限流、服务不可用等）
        print(f"调用大模型生成回答失败: {e}")
        answer = "抱歉，在生成回答时遇到了技术问题，请稍后重试。"
        state["_stream_tokens"] = [answer]
        if queue is not None:
            await queue.put({"type": "token", "content": answer})

    # 更新状态: 将生成的回答写入 neo4j_answer 和 output 字段
    state["neo4j_answer"] = answer
    state["output"] = answer
    print("完成 Neo4j 数据输入大模型，回答已生成")

    return state
