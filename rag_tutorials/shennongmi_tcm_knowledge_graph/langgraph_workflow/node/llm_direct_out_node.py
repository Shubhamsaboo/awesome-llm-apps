"""
LLM 直接回答节点（异步流式版本）
=====================================

角色定位:
    LangGraph 工作流中的"兜底回答"节点，当用户问题被判定为**非中医问题**时
    （is_zhongyi_intent=False），跳过知识图谱查询链路，直接由 LLM 生成回答。

核心功能:
    1. 接收用户输入和对话历史
    2. 构建通用知识助手 prompt（保留中医专业背景能力）
    3. 调用 streaming_llm.astream() 实现 token 级别流式输出
    4. 每个 token 实时推送到 stream_queue（真流式）供 SSE 消费，
       同时存入 state["_stream_tokens"]（向后兼容非流式端点）

与 neo4j_answer_generate_node 的区别:
    - neo4j_answer_generate_node: 有 Cypher 查询结果作为上下文 → 知识图谱增强回答
    - llm_direct_out_node: 无图谱上下文 → 纯 LLM 通用回答（但仍可调用中医知识）

使用场景:
    - 用户问"今天天气怎么样" → 非中医，走此节点
    - 用户问"劳动仲裁怎么申请" → 非中医，走此节点
    - 用户用代词指代之前聊过的中医话题 → 结合历史上下文回答

依赖:
    - common.llm.streaming_llm: 流式大模型实例
    - common.llm.format_conversation_history: 对话历史格式化工具
    - common.stream_context.stream_queue: 线程安全的流式消息队列
    - AgentState: LangGraph 全局状态
"""

from langgraph_workflow.agent_state import AgentState
from langchain_core.messages import HumanMessage
from common.llm import streaming_llm, format_conversation_history
from common.stream_context import stream_queue


async def llm_direct_out_node(state: AgentState) -> AgentState:
    """
    非中医问题直接回答（异步流式版本）。

    当 LangGraph 路由判定用户输入不是中医问题时（is_zhongyi_intent=False），
    由本节点接管并用 LLM 生成直接回答，不经过实体提取/Cypher 生成/图谱查询链路。

    流式输出机制:
      - 每个 token 存入 state["_stream_tokens"]，供 FastAPI /process 端点
        在 astream_events 循环结束后逐 token 发送到前端。
      - 同时推入 stream_queue，供 FastAPI /process/stream 端点
        以 SSE 方式实时推送。

    参数:
        state (AgentState): LangGraph 全局状态，包含:
            - input: 用户原始输入
            - messages: 对话历史消息列表

    返回:
        AgentState: 更新后的状态，新增/修改字段:
            - direct_out: LLM 直接生成的回答
            - output: 最终输出（与 direct_out 相同）
            - _stream_tokens: token 列表（流式输出用）
    """
    print("开始生成直接用户回答")
    user_input = state["input"]
    messages = state.get("messages", [])
    # 初始化流式 token 缓存列表（每次调用重新开始）
    state["_stream_tokens"] = []

    # 构建对话历史文本（保留最近 5 轮，避免 prompt 过长超出上下文窗口）
    history_section = format_conversation_history(messages, max_turns=5)

    # 组装 prompt: 通用知识助手 + 中医专业背景 + 对话历史
    # 要求 LLM 根据问题类型灵活回答，不要强行套用中医术语
    prompt = f"""
{history_section}

    用户当前输入: {user_input}

    你是一名通用知识助手，同时具备中医专业知识背景。
    要求：
    - 根据用户问题类型，给出准确、简洁的回答。
    - 如果问题涉及中医相关内容（如症状、方剂、中药材、功效、经络、典籍等），可从中医角度回答。
    - 如果问题与中医无关，直接给出常规回答，不要强行套用中医术语。
    - 输出时只给出最终答案，不要解释你是如何推理的。
    - 如果对话历史中有涉及的相关内容，请结合历史上下文理解用户的意图（如代词指代、延续讨论等）。
    """

    # 获取当前请求的流式队列（仅 /process/stream 端点会设置）
    # 如果未设置，queue 为 None，后续跳过队列推送
    queue = stream_queue.get(None)

    try:
        full_response = ""
        # astream() 是 LangChain 的异步流式方法，yield 每个 token chunk
        async for chunk in streaming_llm.astream([HumanMessage(content=prompt)]):
            token = chunk.content
            if token:
                full_response += token
                state["_stream_tokens"].append(token)
                # 真流式：token 产生瞬间推入队列，由 SSE event_generator 即时消费
                if queue is not None:
                    await queue.put({"type": "token", "content": token})
        model_answer = full_response.strip()
    except Exception as e:
        # LLM 调用异常处理：网络超时、API 限流、服务不可用等
        print(f"❌ LLM 直接回答调用失败: {e}")
        model_answer = "抱歉，暂时无法处理您的问题，请稍后重试。"
        state["_stream_tokens"] = [model_answer]
        if queue is not None:
            await queue.put({"type": "token", "content": model_answer})

    # 更新状态: 将 LLM 直接回答写入 direct_out 和 output 字段
    state["direct_out"] = model_answer
    state["output"] = model_answer
    print("完成生成直接用户回答")
    return state
