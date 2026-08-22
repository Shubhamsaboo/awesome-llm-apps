"""
流式输出上下文变量（SSE Streaming Context）
==========================================

使用 Python contextvars 模块将当前 HTTP 请求的 asyncio.Queue 从 FastAPI 端点
传递到 LangGraph Agent 的 LLM 节点中，实现跨调用栈的无侵入上下文传递。

核心原理:
    contextvars.ContextVar 是 Python 3.7+ 标准库提供的协程安全的上下文变量，
    类似于线程本地存储（threading.local）但对于 asyncio 协程是安全的。
    每个请求拥有独立的上下文副本，不同请求之间不会互相干扰。

工作流程:
    1. FastAPI SSE 端点创建 asyncio.Queue 实例
    2. 通过 stream_queue.set(queue) 将队列绑定到当前请求的 context 中
    3. LangGraph Agent 的各 LLM 节点通过 stream_queue.get(None) 获取队列
    4. 节点在 streaming_llm.astream() 迭代时，将每个 token 通过
       await queue.put(...) 推入队列
    5. SSE event_generator 从队列中取出 token 并封装为 SSE 事件发送给前端
    6. 请求结束时通过 stream_queue.reset(token) 清理上下文

降级模式:
    当 _stream_queue 为 None 时（如非流式的 /process 端点），
    LLM 节点自动退化为 state["_stream_tokens"] 列表收集模式，
    在请求完成后一次性返回全部 token 列表。

使用方式（生产者端 — FastAPI endpoint）:
    import contextvars
    from common.stream_context import stream_queue

    # 设置当前请求的流式队列
    token = stream_queue.set(queue)
    try:
        # 执行 Agent 工作流 ...
        await agent.astream(...)
    finally:
        # 清理上下文，避免内存泄漏
        stream_queue.reset(token)

使用方式（消费者端 — LLM 节点）:
    from common.stream_context import stream_queue

    queue = stream_queue.get(None)
    if queue is not None:
        # 流式模式：实时推送每个 token
        await queue.put({"type": "token", "content": token_text})
"""

import contextvars

# ContextVar 用于在同一个 asyncio 请求的协程树中传递流式队列
# default=None 表示：如果当前上下文未设置队列，get() 返回 None
# 调用方可据此判断当前是流式模式（有队列）还是批量模式（无队列）
stream_queue: contextvars.ContextVar = contextvars.ContextVar('stream_queue', default=None)
