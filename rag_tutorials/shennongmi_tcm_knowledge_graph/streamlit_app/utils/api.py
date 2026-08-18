"""
FastAPI 后端客户端 — 封装对中医知识图谱服务的 HTTP 请求
=============================================

功能：
  - 非流式 API 调用: query_tcm_knowledge() → /process 端点
  - 流式 SSE 调用:   stream_tcm_knowledge() → /process/stream 端点
  - 健康检查:        check_fastapi_health() → TCP Socket 端口检测
  - 进度消息清理:    strip_stream_progress() → 剥离进度提示，保留纯正文

设计考量：
  - 健康检查使用 TCP Socket 而非 HTTP /process，因为 /process 会触发完整
    LangGraph 工作流（LLM 推理 + 图谱查询），耗时 10-30 秒，无法用于快速检测
  - 流式调用通过 SSE (Server-Sent Events) 协议接收实时事件，
    直接返回生成器，可传入 st.write_stream() 实现渐进式渲染
  - 进度消息剥离采用精确匹配（完整字符串），避免误删 LLM 正文中
    以 > 开头的 Markdown 引用块
"""

import json
import re
import socket
import time
from typing import Generator, Optional

import requests
import streamlit as st

# ============================================================
# 配置常量
# ============================================================

# FastAPI 服务的绑定地址和端口（与服务端 uvicorn.run 参数保持一致）
API_HOST = "127.0.0.1"
API_PORT = 8000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
PROCESS_ENDPOINT = f"{API_BASE_URL}/process"       # 非流式端点
STREAM_ENDPOINT = f"{API_BASE_URL}/process/stream"  # 流式 SSE 端点
REQUEST_TIMEOUT = 120       # HTTP 请求超时（秒），LangGraph 工作流可能耗时较长
SOCKET_CHECK_TIMEOUT = 2    # TCP 端口检测超时（秒），快速判断服务是否在线


# ============================================================
# 缓存状态 — 健康检查
# ============================================================


@st.cache_data(ttl=30, show_spinner=False)
def check_fastapi_health() -> tuple[bool, str]:
    """
    快速检测 FastAPI 服务是否在线。

    使用 TCP Socket 直连检测端口是否在监听，**不**调用 /process 端点。
    因为 /process 会触发完整的 LangGraph 工作流（LLM 推理 + 图谱查询），
    耗时 10-30 秒，无法用于快速健康检查。

    缓存策略：使用 st.cache_data 缓存结果 30 秒，避免每次渲染都检测端口。

    返回:
        tuple[bool, str]:
          - bool: 服务是否在线（端口可连接）
          - str:  状态描述信息（成功时："服务端口已监听"，
                  失败时包含具体失败原因如超时/端口未开放/主机名解析失败等）
    """
    # 创建 TCP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(SOCKET_CHECK_TIMEOUT)  # 设置 2 秒超时，避免长时间阻塞
    try:
        # connect_ex 返回 0 表示连接成功，非 0 表示连接失败（errno 值）
        result = sock.connect_ex((API_HOST, API_PORT))
        if result == 0:
            return True, "服务端口已监听"
        return False, f"端口 {API_PORT} 未开放（connect_ex={result}）"
    except socket.timeout:
        return False, f"连接 {API_HOST}:{API_PORT} 超时"
    except socket.gaierror:
        # 主机名解析失败（getaddrinfo error）
        return False, f"无法解析主机地址: {API_HOST}"
    except Exception as e:
        return False, f"连接检测异常: {str(e)}"
    finally:
        # 确保 Socket 连接被关闭，避免资源泄漏
        sock.close()


def clear_health_cache():
    """清除健康检查缓存。

    典型使用场景：用户点击「刷新连接状态」按钮后调用，
    确保下次 check_fastapi_health() 重新实际检测端口状态。
    """
    check_fastapi_health.clear()


# ============================================================
# 响应清理工具 — 进度消息剥离
# ============================================================


# 已知的进度消息文本（来自 FastAPI 的 NODE_PROGRESS_MAP），
# 用于精确匹配和剥离，避免误删 LLM 正文中的 Markdown 引用块（> 开头的行）。
# 注意：这些消息需要与 fastapi_app/main.py 中的 NODE_PROGRESS_MAP 保持同步。
_KNOWN_PROGRESS_MESSAGES = [
    "🔍 正在判断问题类型...",
    "📋 正在提取中医实体...",
    "🔗 正在匹配知识图谱实体...",
    "💻 正在生成图谱查询语句...",
    "🔎 正在校验查询语句...",
    "⚡ 正在执行知识图谱查询...",
    "🤖 正在生成回答...",
]
# 预编译：将每个进度消息转为完整的 "\n\n> {message}" 字符串，用于精确替换
# 格式来源：stream_tcm_knowledge() 中 yield f"\n\n> {message}"
_PROGRESS_PATTERNS = [f"\n\n> {msg}" for msg in _KNOWN_PROGRESS_MESSAGES]


def strip_stream_progress(text: str) -> str:
    """从流式响应中移除进度消息和连接提示，只保留正文内容。

    st.write_stream 会将所有 yield 的文本拼接返回，包括：
      - 初始连接提示: "⏳ 正在连接知识服务..."
      - 进度消息:     "\\n\\n> 🔍 正在判断问题类型..."
      - 分隔换行:     "\\n\\n"
      - 正文 token:   逐个字符/词组

    此函数移除前两类，返回干净的正文内容，用于存入聊天历史或展示。

    设计要点：
      使用精确的完整字符串匹配（而非正则），避免误删 LLM 正文中以 > 开头的
      Markdown 引用块（例如 LLM 回答中可能包含 "> 这是引用内容"）。

    参数:
        text: st.write_stream 返回的完整拼接文本（含进度消息）

    返回:
        str: 去除进度消息后的纯正文内容
    """
    if not text:
        return text
    # 移除初始连接提示（流式响应第一个 yield 的文本）
    text = text.replace("⏳ 正在连接知识服务...", "")
    # 精确移除已知的进度消息行（用完整字符串匹配，避免误删正文中的 Markdown 引用）
    for pattern in _PROGRESS_PATTERNS:
        text = text.replace(pattern, "")
    # 去除首尾多余的空白行
    return text.strip()


# ============================================================
# API 调用（非流式，保留向后兼容）
# ============================================================


@st.cache_data(ttl=300, show_spinner=False)
def query_tcm_knowledge(user_input: str, messages: list = None) -> dict:
    """
    调用 FastAPI /process 端点进行中医知识图谱查询。

    LangGraph 工作流会自动判断用户意图并路由：
      - 中医相关问题 → 意图识别 → 实体抽取 → FAISS 匹配 → Cypher 查询 → 回答
      - 非中医问题 → LLM 直接回答

    缓存策略：相同输入（user_input + messages）的结果缓存 5 分钟，
    避免重复触发耗时的 LangGraph 工作流。

    参数:
        user_input: 用户输入文本
        messages:   对话历史消息列表，
                    格式: [{"role": "user", "content": "..."}, ...]

    返回:
        dict:
            {
                "input": str,       # 原始输入
                "output": str,      # 工作流处理结果
                "success": bool,    # 是否成功
                "elapsed": float,   # 耗时（秒）
                "error": str | None # 错误信息（仅在失败时）
            }
    """
    # 记录请求开始时间，用于计算耗时
    start = time.time()
    # 构建返回结果的基础结构
    result = {
        "input": user_input,
        "output": "",
        "success": False,
        "elapsed": 0.0,
        "error": None,
    }

    # 构造请求体
    payload = {"input": user_input}
    if messages:
        payload["messages"] = messages

    try:
        # 发送 POST 请求到 /process 端点
        resp = requests.post(
            PROCESS_ENDPOINT,
            json=payload,
            timeout=REQUEST_TIMEOUT,  # 120 秒超时
        )
        # 检查 HTTP 状态码，非 2xx 时抛出 HTTPError
        resp.raise_for_status()
        data = resp.json()
        result["output"] = data.get("output", "")
        result["success"] = True

    except requests.exceptions.ConnectionError:
        # 连接被拒绝：FastAPI 服务未启动或端口不可达
        result["error"] = (
            "❌ 无法连接到中医知识服务。\n\n"
            "请确认 FastAPI 服务已启动：\n"
            "```bash\n"
            "cd ShenNongMi\n"
            "python fastapi_app/main.py\n"
            "```"
        )
    except requests.exceptions.Timeout:
        # 请求超时：LangGraph 工作流执行超过 120 秒
        result["error"] = (
            "⏱️ 请求超时（120秒），工作流可能耗时过长或服务负载过高，请稍后重试。"
        )
    except requests.exceptions.HTTPError as e:
        # HTTP 错误：尝试从响应体获取详细错误信息
        try:
            error_detail = resp.json()
            result["error"] = error_detail.get("output", f"服务端错误: {e}")
        except Exception:
            result["error"] = f"服务端返回错误: {e}"
    except Exception as e:
        # 其他未预期的异常
        result["error"] = f"请求异常: {str(e)}"

    # 计算并记录请求总耗时（精确到 0.01 秒）
    result["elapsed"] = round(time.time() - start, 2)
    return result


# ============================================================
# 流式 API 调用 — SSE (Server-Sent Events)
# ============================================================


def stream_tcm_knowledge(user_input: str, messages: list = None) -> Generator[str, None, None]:
    """流式调用 FastAPI /process/stream 端点，返回文本生成器。

    通过 SSE (Server-Sent Events) 协议接收 LangGraph 工作流的实时事件：
      - progress 事件 → 生成进度提示文本（"> 🔍 正在判断问题类型..."）
      - token 事件   → 生成 LLM 实时输出的文本 token
      - done 事件     → 流结束（含 fallback output，用于无 token 场景）
      - error 事件    → 生成错误提示

    此生成器可直接传入 Streamlit 的 st.write_stream() 实现渐进式渲染。

    SSE 协议要点：
      - 每个事件以 "data: " 开头，后面跟 JSON 数据
      - 事件之间以空行分隔
      - 使用 iter_lines() 逐行读取响应流

    参数:
        user_input: 用户输入文本
        messages:   对话历史消息列表，
                    格式: [{"role": "user", "content": "..."}, ...]

    用法示例:
        with st.chat_message("assistant"):
            response = st.write_stream(stream_tcm_knowledge(user_input))
        # response 是拼接后的完整文本（含进度提示），需用 strip_stream_progress 清理
    """
    # 记录已显示的进度消息，避免重复推送同一节点的进度
    shown_progress: set = set()
    # 当前是否已经开始输出 LLM token（用于在进度提示和正文之间插入分隔换行）
    started_tokens = False

    # 构造请求体
    payload = {"input": user_input}
    if messages:
        payload["messages"] = messages

    try:
        # 🔧 修复：先 yield 一个初始提示，让用户立即看到反馈，
        # 避免在建立 HTTP 连接和首节点执行期间的空白等待（首次连接约 2-5 秒）。
        yield "⏳ 正在连接知识服务..."

        # 发送流式 POST 请求
        resp = requests.post(
            STREAM_ENDPOINT,
            json=payload,
            stream=True,             # 启用流式传输，不等待完整响应
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        # 逐行读取 SSE 事件流
        # iter_lines(decode_unicode=True) 将字节行自动解码为 Unicode 字符串
        for line in resp.iter_lines(decode_unicode=True):
            # SSE 空行表示事件边界分隔，跳过
            if not line:
                continue
            # 只处理以 "data: " 开头的行（SSE 协议规范）
            if not line.startswith("data: "):
                continue

            # 解析 JSON 数据
            # line[6:] 跳过 "data: " 前缀（6 个字符）
            try:
                data = json.loads(line[6:])
            except json.JSONDecodeError:
                # JSON 解析失败（可能是中间传输损坏），跳过该事件
                continue

            # 获取事件类型，根据类型做不同处理
            event_type = data.get("type", "")

            # —— 进度事件 ——
            # 将节点开始信息转换为中文进度提示，每个节点只显示一次
            if event_type == "progress":
                message = data.get("message", "")
                node = data.get("node", "")
                if node not in shown_progress:
                    shown_progress.add(node)
                    # 使用 Markdown 引用格式展示进度（"> 进度描述"）
                    # 前置 \n\n 确保与前面的内容分隔开来
                    yield f"\n\n> {message}"

            # —— Token 事件 ——
            # LLM 实时生成的文本片段，直接 yield 给 write_stream 渲染
            elif event_type == "token":
                # 首次收到 token 时，在进度提示和正文之间插入分隔换行
                if not started_tokens:
                    started_tokens = True
                    yield "\n\n"
                yield data.get("content", "")

            # —— 完成事件 ——
            # 如果之前没有流式 token 输出（例如无 Cypher 结果、LLM 调用失败
            # 等场景），从 done 事件的 output 字段获取最终答案作为回退。
            elif event_type == "done":
                fallback_output = data.get("output", "")
                if fallback_output and not started_tokens:
                    # 无 token 场景：使用 fallback 输出
                    yield f"\n\n{fallback_output}"
                break

            # —— 错误事件 ——
            # 工作流执行异常，将错误信息展示给用户
            elif event_type == "error":
                error_msg = data.get("message", "未知错误")
                yield f"\n\n❌ **错误**: {error_msg}"
                break

    except requests.exceptions.ConnectionError:
        # 连接失败：FastAPI 服务未启动
        yield (
            "\n\n❌ 无法连接到中医知识服务。\n\n"
            "请确认 FastAPI 服务已启动：\n"
            "```bash\n"
            "cd ShenNongMi\n"
            "python fastapi_app/main.py\n"
            "```"
        )
    except requests.exceptions.Timeout:
        # 请求超时
        yield "\n\n⏱️ 请求超时（120秒），工作流可能耗时过长，请稍后重试。"
    except requests.exceptions.HTTPError as e:
        # HTTP 错误：尝试从响应体获取详细错误信息
        try:
            error_body = resp.json()
            detail = error_body.get("output", str(e))
        except Exception:
            detail = str(e)
        yield f"\n\n❌ 服务端错误: {detail}"
    except Exception as e:
        # 其他未预期的异常
        yield f"\n\n❌ 请求异常: {str(e)}"
