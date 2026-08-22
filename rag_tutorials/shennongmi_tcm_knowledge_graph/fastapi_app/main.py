"""
中医知识图谱 FastAPI 服务端
=============================================

功能：
  - /process 端点：接收用户输入，通过 LangGraph 工作流进行意图识别和路由分发
  - /process/stream 端点：SSE 流式接口，实时推送工作流进度和 LLM 生成 token

LangGraph 工作流路由：
  - 中医相关问题 → 意图识别 → 实体抽取 → FAISS 语义匹配 → Cypher 查询 → Neo4j 回答
  - 非中医问题 → LLM 直接回答

启动方式：
  python fastapi_app/main.py
"""

import json
import traceback
import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from langgraph_workflow.langgraph_more_nodes import zhongyi_response, graph
from langgraph_workflow.agent_state import AgentState, make_initial_state
from common.path_utils import get_file_path
from common.stream_context import stream_queue

# 创建 FastAPI 应用实例
app = FastAPI()
# 将项目根目录下的 picture 文件夹挂载为静态文件服务，通过 URL 路径 /picture 对外提供访问。
# 例如：图片 /path/to/picture/abc.png 可通过 http://host:8000/picture/abc.png 访问
app.mount("/picture", StaticFiles(directory=get_file_path("picture")))


# ============================================================
# 节点名称 → 中文进度描述 映射表
# ============================================================
# 用于将 LangGraph 内部节点名转换为用户可读的进度提示。
# 当 astream_events 捕获到 on_chain_start 事件时，查找此表发送对应的中文进度。

NODE_PROGRESS_MAP = {
    # —— TCM Knowledge Graph Q&A pipeline ——
    "zhongyi_intent_node": "正在判断问题类型...",
    "extract_entity_from_user_input_node": "正在提取中医实体...",
    "match_entity_from_neo4j_node": "正在匹配知识图谱实体...",
    "generate_neo4j_cypher_node": "正在生成图谱查询语句...",
    "check_cypher_node": "正在校验查询语句...",
    "run_cypher_node": "正在执行知识图谱查询...",
    "neo4j_answer_generate_node": "正在生成回答...",
    # —— Non-TCM fallback ——
    "llm_direct_out_node": "正在生成回答...",
}


def _build_initial_state(user_input: str, messages: list = None) -> AgentState:
    """构造 LangGraph 工作流的初始状态。

    参数:
        user_input: 用户输入文本
        messages:   对话历史消息列表，
                    格式: [{"role": "user", "content": "..."}, ...]

    返回:
        AgentState: LangGraph 工作流的初始状态对象
    """
    return make_initial_state(user_input, messages)


@app.post("/process")
async def process(request: Request):
    """处理用户请求的主端点（非流式，保留向后兼容）。

    接收用户输入文本，通过 LangGraph 工作流进行意图识别和路由分发：
    
      - 中医相关问题 → 实体抽取 → FAISS 匹配 → Cypher 查询 → Neo4j 回答
      - 非中医问题 → LLM 直接回答

    参数:
        request: FastAPI Request 对象，body 为 JSON：
                 {"input": str, "messages"?: list}

    返回:
        JSONResponse: {"input": str, "output": str}
    """
    # 解析请求体 JSON
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            content={"input": "", "output": "请求体格式错误，请提供有效的 JSON 数据"},
            status_code=400,
        )

    # 提取用户输入并做空值校验
    user_input = (data.get("input", "") or "").strip()
    if not user_input:
        return JSONResponse(
            content={"input": "", "output": "请输入您的问题或指令"},
            status_code=400,
        )

    # 提取对话历史（可选参数，用于多轮对话上下文）
    messages = data.get("messages", None)

    # 执行 LangGraph 工作流，获取处理结果
    try:
        output = await zhongyi_response(user_input, messages=messages)
        return JSONResponse(content={"input": user_input, "output": output})
    except Exception:
        traceback.print_exc()
        return JSONResponse(
            content={"input": user_input, "output": "系统出错了，请重试！"},
            status_code=500,
        )


# ============================================================
# 流式 SSE 端点
# ============================================================

@app.post("/process/stream")
async def process_stream(request: Request):
    """流式 SSE（Server-Sent Events）端点。

    与 /process 端点完成相同的 LangGraph 工作流，
    但通过 SSE 实时推送以下事件类型：
      - progress: 当前正在执行的节点（中文描述），让用户了解进度
      - token:    LLM 实时生成的文本 token，实现逐字/词组渲染
      - done:     工作流完成（包含完整输出，用作无 token 场景的 fallback）
      - error:    错误信息

    SSE 数据格式: data: {"type": "...", ...}\n\n

    参数:
        request: FastAPI Request 对象，body 为 JSON：
                 {"input": str, "messages"?: list}

    返回:
        StreamingResponse: text/event-stream 类型的流式响应
    """
    # 解析请求体 JSON
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            content={"input": "", "output": "请求体格式错误，请提供有效的 JSON 数据"},
            status_code=400,
        )

    # 提取用户输入并做空值校验
    user_input = (data.get("input", "") or "").strip()
    if not user_input:
        return JSONResponse(
            content={"input": "", "output": "请输入您的问题或指令"},
            status_code=400,
        )

    # 提取对话历史
    messages = data.get("messages", None)

    async def event_generator():
        """异步生成器：产出 SSE 格式的事件流。

        该生成器是 /process/stream 的核心，通过以下机制实现流式推送：
        1. 创建 asyncio.Queue 作为事件管道
        2. 通过 contextvars 将 queue 注入 LLM 节点（LLM 节点将 token 推入此 queue）
        3. 后台任务跑 LangGraph astream_events，捕获节点进度和最终输出
        4. 主循环从 queue 消费事件，转为 SSE 格式 yield 给客户端
        """
        # 构造 LangGraph 初始状态
        initial_state = _build_initial_state(user_input, messages=messages)
        # 最终输出（在无 token 场景下用作 fallback）
        final_output = ""
        # 已发送过进度的节点集合，避免重复推送同一节点的进度
        shown_progress: set = set()

        # 为本请求创建独立的 asyncio.Queue，通过 contextvars 传递给 LLM 节点
        # LLM 节点通过 stream_queue.get() 获取此 queue 并将 token 推入
        queue: asyncio.Queue = asyncio.Queue()
        ctx_token = stream_queue.set(queue)

        # ============================================================
        # 后台任务：执行 LangGraph 工作流，将进度/完成/错误事件推入 queue
        # ============================================================
        async def run_graph():
            """后台协程：运行 LangGraph 工作流并推送事件到 queue。

            通过 graph.astream_events(initial_state, version="v2") 监听：
              - on_chain_start: 节点开始执行 → 推送 progress 事件
              - on_chain_end:   节点执行完毕 → 捕获最终输出作为 fallback

            异常会被捕获并以 error 事件推送到 queue。
            """
            nonlocal final_output
            try:
                # 使用 astream_events v2 API 遍历工作流事件
                async for event in graph.astream_events(initial_state, version="v2"):
                    kind = event.get("event", "")
                    name = event.get("name", "")

                    # 节点开始执行 → 推送进度事件
                    if kind == "on_chain_start" and name in NODE_PROGRESS_MAP:
                        message = NODE_PROGRESS_MAP[name]
                        # 每个节点只在首次进入时推送一次进度
                        if name not in shown_progress:
                            shown_progress.add(name)
                            await queue.put({
                                "type": "progress",
                                "node": name,
                                "message": message,
                            })

                    # 节点执行结束 → 捕获最终输出作为 fallback
                    # 当 LLM 节点没有通过 stream_queue 推送 token 时（例如
                    # 没有 Cypher 结果、LLM 调用失败等场景），前端可以通过
                    # done 事件的 output 字段获取最终答案
                    elif kind == "on_chain_end" and name in NODE_PROGRESS_MAP:
                        node_output = event.get("data", {}).get("output", {})
                        if isinstance(node_output, dict):
                            out_val = node_output.get("output", "")
                            if out_val:
                                final_output = out_val
            except Exception as e:
                traceback.print_exc()
                await queue.put({
                    "type": "error",
                    "message": f"工作流执行异常: {str(e)}",
                })
                return

            # 图执行完毕，发送 done 信号（携带 final_output 作为 fallback）
            await queue.put({
                "type": "done",
                "output": final_output,
            })

        try:
            # asyncio.create_task 会自动复制当前 context（含 stream_queue），
            # 因此 LLM 节点能通过 stream_queue.get() 拿到此 queue 并实时推送 token
            graph_task = asyncio.create_task(run_graph())

            # ============================================================
            # 主循环：从 queue 消费所有事件（progress / token / done / error）
            # ============================================================
            while True:
                # 阻塞等待 queue 中的下一条消息（后台任务推送）
                msg = await queue.get()
                event_type = msg.get("type", "")

                # progress / token 事件 → 推送 SSE 后继续循环
                if event_type in ("progress", "token"):
                    # 使用 ensure_ascii=False 保留中文字符，避免转义为 \\uXXXX
                    yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

                # done 事件 → 推送最终 SSE 后退出循环
                elif event_type == "done":
                    yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                    break

                # error 事件 → 推送错误 SSE 后退出循环
                elif event_type == "error":
                    yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                    break

            # 确保后台任务已完成（正常情况此时已完成，这里是双重保险）
            await graph_task

        finally:
            # 恢复 context var 的默认值，避免跨请求污染
            # （asyncio 中的 contextvars 是协程级别隔离的，但主动重置是最佳实践）
            stream_queue.reset(ctx_token)

    # 返回 SSE 流式响应
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            # 禁止缓存，确保客户端始终获取实时数据
            "Cache-Control": "no-cache",
            # 保持长连接
            "Connection": "keep-alive",
            # 禁用 Nginx 代理缓冲（若通过 Nginx 反向代理），确保事件实时推送
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================
# 启动入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    # 启动 Uvicorn ASGI 服务器，监听所有网卡，端口 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
