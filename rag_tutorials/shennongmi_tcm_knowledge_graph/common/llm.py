"""
LLM 大模型封装模块
=================

本模块封装了与 LLM（大语言模型）交互的核心功能，基于 LangChain 的 ChatOpenAI
实现，兼容所有 OpenAI API 协议的模型服务（如 DeepSeek、Qwen、GLM 等）。

主要功能:
    1. 对话历史格式化 — 将多轮对话消息列表转换为 prompt 中可用的文本段落，
       支持按轮数截断以控制上下文窗口长度。
    2. 普通 LLM 实例 (my_llm) — 用于单次同步调用，如工具调用、结构化输出等。
    3. 流式 LLM 实例 (streaming_llm) — 开启 streaming=True，配合 LangGraph 的
       astream_events() 实现 token 级别的实时流式输出（SSE）。

设计要点:
    - 两个 LLM 实例在模块级别创建（全局单例），所有函数复用同一连接。
    - 配置从 common.config.Config 统一读取，不硬编码 API 信息。
    - 流式 LLM 与 common.stream_context 配合使用，使 Agent 工作流中的
      每个 LLM 节点都能将生成 token 实时推送到前端。
"""

from typing import List, Dict, Optional

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from common.config import Config

# 全局配置实例，读取 .env 中的 LLM 相关设置
conf = Config()


# ============================================================
# 对话历史格式化工具
# ============================================================

def format_conversation_history(
    messages: List[Dict[str, str]],
    max_turns: Optional[int] = None,
) -> str:
    """将对话历史消息列表格式化为 prompt 中可用的文本段落。

    用于在多轮对话中为 LLM 提供历史上下文，使模型能记住同一会话中的
    之前对话内容，从而实现连贯的多轮对话。调用方可将返回的文本拼接到
    当前用户消息之前的 system prompt 或 user prompt 中。

    参数:
        messages: 对话消息列表，每条消息为一个字典，格式为:
                  {"role": "user" | "assistant", "content": "消息文本"}
                  消息按时间顺序排列（最早的在前面）。
        max_turns: 最多保留最近几轮对话（一轮 = 用户 + 助手各一条消息）。
                   为 None 时保留全部历史；设置后可避免 prompt 过长
                   超出模型的上下文窗口限制（如 128K tokens）。

    返回:
        str: 格式化后的对话历史文本，包含 "## 对话历史" 标题，
             每条消息以 "用户：" 或 "助手：" 前缀标记。
             如果 messages 为空则返回空字符串。

    示例:
        >>> messages = [
        ...     {"role": "user", "content": "四君子汤有哪些药材？"},
        ...     {"role": "assistant", "content": "四君子汤由人参、白术、茯苓、甘草组成。"},
        ... ]
        >>> print(format_conversation_history(messages))
        ## 对话历史
        用户：四君子汤有哪些药材？
        助手：四君子汤由人参、白术、茯苓、甘草组成。
    """
    if not messages:
        return ""

    # 如果指定了最大轮数，只保留最近的 N 轮对话
    # 每轮 = 1 user + 1 assistant = 2 条消息，所以 max_messages = max_turns * 2
    if max_turns is not None and max_turns > 0:
        max_messages = max_turns * 2
        messages = messages[-max_messages:]  # 从末尾截取最近的消息

    # 构建格式化的对话历史文本
    lines = ["## 对话历史"]
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lines.append(f"用户：{content}")
        elif role == "assistant":
            lines.append(f"助手：{content}")

    return "\n".join(lines)


# ============================================================
# LLM 实例（全局单例）
# ============================================================

# ============ 普通 LLM — 用于同步调用 ============
# 适用于不需要流式输出的场景，如：
#   - 工具调用 / Function Calling
#   - 结构化输出（JSON mode）
#   - 简单的单次问答
#   - 意图识别、实体提取等
my_llm = ChatOpenAI(
    api_key=conf.MODEL_API_KEY,
    base_url=conf.MODEL_BASE_URL,
    model=conf.MODEL_NAME,
)

# ============ 流式输出 LLM — 用于实时 token 级别流式输出 ============
# streaming=True 使底层 API 调用开启 SSE（Server-Sent Events）流式传输，
# 配合 LangGraph 的 astream_events() 可捕获每个 token 的 on_chat_model_stream 事件。
#
# 使用场景：
#   - 用户聊天界面中逐字显示 AI 回复
#   - Agent 工作流中实时展示思考过程
#
# 工作流程：
#   1. 前端发起 SSE 连接请求
#   2. FastAPI 端点设置 stream_queue ContextVar
#   3. LangGraph Agent 使用 streaming_llm 执行节点
#   4. astream_events() 捕获 on_chat_model_stream 事件
#   5. 每个 token 通过 stream_queue 推送到 SSE 通道
#   6. 前端实时渲染接收到的 token
streaming_llm = ChatOpenAI(
    api_key=conf.MODEL_API_KEY,
    base_url=conf.MODEL_BASE_URL,
    model=conf.MODEL_NAME,
    streaming=True,
)

# ============================================================
# 模块自测
# ============================================================

if __name__ == '__main__':
    # 构造一条简单的对话消息，测试 LLM 连接是否正常
    messages = [
        HumanMessage(content="用一句话介绍一下你自己")
    ]
    # 调用模型（同步方式，等待完整响应）
    response = my_llm.invoke(messages)
    print(response.content)
