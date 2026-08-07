"""
小红书文案生成节点
======================

角色定位:
    LangGraph 小红书发布链路中的第一步。当用户意图被判定为"发布小红书"后，
    本节点负责根据用户输入生成适合小红书平台发布的中医养生类文案。

核心功能:
    1. 使用 PydanticOutputParser 约束 LLM 输出格式（title + content）
    2. 调用 LLM 生成吸引人的标题（<= 19 字）和社交化正文
    3. 解析 LLM 输出为结构化的 XiaohongshuTCMPostOutput 对象
    4. 将生成的标题和正文写入 AgentState，供下游节点使用

Pydantic 结构化输出策略:
    使用 PydanticOutputParser 让 LLM 按照指定 JSON schema 输出，
    解析器会自动校验字段类型和必填项，解析失败时返回空字符串，
    由下游 check_text_image_node 负责拦截不完整的发布。

数据流向:
    用户输入 → text_generate_node → xiaohongshu_tcm_post_title
                                      xiaohongshu_tcm_post_content
                                     → image_generate_node (生成配图)
                                     → check_text_image_node (完整性校验)

依赖:
    - langchain_core.output_parsers.PydanticOutputParser: 结构化输出解析
    - pydantic.BaseModel: 输出数据模型定义
    - common.llm.my_llm: LLM 实例
"""

from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from __004__langgraph_more_nodes.agent_state import AgentState
from common.llm import my_llm


class XiaohongshuTCMPostOutput(BaseModel):
    """
    小红书中医养生帖子的结构化输出数据模型。

    Attributes:
        title (str): 帖子标题，要求 <= 19 个中文字符，简短有吸引力。
        content (str): 帖子正文，具有分享性和实用性，语气自然亲切。
    """
    title: str
    content: str


def generate_xiaohongshu_text(input: str):
    """
    调用 LLM 生成小红书标题和正文。

    使用 PydanticOutputParser 作为 LangChain 输出解析器，
    通过 format_instructions 告知 LLM 按照 JSON schema 输出，
    然后由 parser.parse() 校验并反序列化为 Python 对象。

    参数:
        input (str): 用户提供的小红书发布主题或需求描述

    返回:
        tuple: (title: str, content: str)
            - 解析成功时返回标题和正文
            - 解析失败时返回 ("", "")，由下游节点拦截

    容错策略:
        LLM 可能输出不符合 JSON 格式的文本，导致 parser.parse() 失败。
        此时捕获异常并返回空字符串，不会中断整个 LangGraph 工作流。
    """
    # 初始化 Pydantic 输出解析器，并获取格式化指令
    parser = PydanticOutputParser(pydantic_object=XiaohongshuTCMPostOutput)
    format_instructions = parser.get_format_instructions()

    # 组装消息: SystemMessage 设定小编角色 + HumanMessage 传入用户需求
    messages = [
        SystemMessage(content=(
            "你是一个专门为小红书平台撰写中医养生内容的文案助手。\n"
            "请根据用户提供的主题或需求，生成一条适合小红书发布的中医养生类内容，要求包含：\n"
            "1. 吸引人的标题（title）：不超过19个中文字符，简短有吸引力\n"
            "2. 内容正文，具有分享性和实用性，语气自然亲切，适合社交媒体（content）\n"
            "请你严格按照以下格式返回结果：\n"
            f"{format_instructions}"
        )),
        HumanMessage(content=input)
    ]

    try:
        # 调用 LLM 生成文案，获取原始输出
        raw_output = my_llm.invoke(messages).content.strip()
        # 使用 PydanticOutputParser 解析结构化输出
        parsed_output = parser.parse(raw_output)
        return parsed_output.title, parsed_output.content
    except Exception as e:
        # LLM 输出格式不符合 schema 或调用失败时，返回空字符串
        # 下游 check_text_image_node 会检测到标题/内容为空并阻止发布
        print(f"❌ 小红书文案生成或解析失败: {e}")
        return "", ""


def text_generate_node(state: AgentState) -> AgentState:
    """
    根据用户输入生成中医养生类的小红书文案（标题、内容）。

    LangGraph 节点函数，从小红书发布链路调用。
    生成的标题和正文存入 AgentState，供 image_generate_node 生成配图
    和 auto_publish_xiaohongshu_node 自动发布使用。

    参数:
        state (AgentState): LangGraph 全局状态，包含:
            - input: 用户原始输入文本

    返回:
        AgentState: 更新后的状态，新增/修改字段:
            - xiaohongshu_tcm_post_title: 生成的帖子标题
            - xiaohongshu_tcm_post_content: 生成的帖子正文
            （若生成失败，这两个字段可能为空字符串）
    """
    print("开始生成小红书标题和内容")
    title, content = generate_xiaohongshu_text(state['input'])

    # 将生成的标题和正文写入状态
    state['xiaohongshu_tcm_post_title'] = title
    state['xiaohongshu_tcm_post_content'] = content

    # 如果标题或内容为空，提示下游校验节点将拦截发布
    if not title or not content:
        print("⚠️ 文案生成不完整（标题或内容为空），下游校验节点将拦截发布")
    print("完成生成小红书标题和内容")
    return state


if __name__ == '__main__':
    title, content = generate_xiaohongshu_text("写一篇文章，关于吃西瓜。")
    print(title)
    print(content)
