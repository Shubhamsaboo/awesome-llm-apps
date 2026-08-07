"""
工作流状态定义模块

定义了 LangGraph 工作流中流转的 AgentState TypedDict，作为图中所有节点之间传递
数据的统一载体。每个节点从 state 中读取所需字段，处理后将结果写回 state，供下游
节点或最终输出使用。

AgentState 字段按功能分为以下几组：

  1. 输入输出字段         —— 用户输入、对话历史、最终输出
  2. 意图识别字段         —— 小红书发布意图、中医相关性判断
  3. 小红书发布链路字段   —— 标题、正文、图片路径、发布状态、Markdown 输出
  4. 实体抽取与匹配字段   —— LLM 抽取的实体 / FAISS 匹配的实体（病症、方剂、药材等）
  5. Cypher 查询字段      —— 生成的 Cypher 语句、校验结果、重试控制
  6. Neo4j 结果字段       —— 查询结果、自然语言回答
  7. LLM 直接回答兜底字段 —— 非中医问题的 LLM 直接回答
  8. 运行时辅助字段       —— 流式 token 收集（_stream_tokens，以 _ 前缀标识内部使用）

本模块同时提供 make_initial_state() 工厂函数，统一管理 AgentState 的默认值，
消除多处重复的硬编码初始化。当 AgentState 新增字段时，只需在此函数中补充即可
保证所有调用方一致。
"""

from typing import TypedDict, List, Dict


class AgentState(TypedDict):
    """
    LangGraph 工作流的状态字典类型。

    该 TypedDict 定义了工作流图中所有节点共享的状态结构。每个节点函数接受
    AgentState 作为输入参数，返回更新后的 AgentState 字典（部分字段更新）。

    LangGraph 会自动合并节点返回的更新，无需手动处理状态合并逻辑。

    字段说明（按功能分组）：

    ── 输入输出 ──
    - input:              用户原始输入文本
    - messages:           对话历史消息列表，格式为 [{"role": "user/assistant", "content": "..."}]
                          用于在多轮对话中保持上下文连贯性
    - output:             最终输出文本，由末端节点（neo4j_answer_generate_node / llm_direct_out_node
                          / generate_markdown_node）写入

    ── 意图识别 ──
    - is_xiaohongshu_publish_intent: 用户是否具有发小红书的意图
    - is_zhongyi_intent:             用户输入是否与中医相关

    ── 小红书发布链路 ──
    - xiaohongshu_tcm_post_title:     生成的小红书笔记标题
    - xiaohongshu_tcm_post_content:   生成的小红书笔记正文
    - xiaohongshu_image_path_list:    生成的配图本地路径列表
    - xiaohongshu_tcm_tip:            发布状态提示信息（成功/失败原因）
    - is_can_publish_xiaohongshu:     内容完整性检查结果，True 表示标题、正文、图片均齐全
    - xiaohongshu_markdown_output:    最终 Markdown 格式的输出结果

    ── 实体抽取（LLM 从用户输入中提取） ──
    - user_input_effects:   抽取的功效实体（如"止泻"、"清热"）
    - user_input_diseases:  抽取的疾病实体（如"感冒"、"头痛"）
    - user_input_symptoms:  抽取的症状实体（如"腹泻"、"恶心"）
    - user_input_formulas:  抽取的方剂实体（如"藿香正气散"）
    - user_input_herbs:     抽取的药材实体（如"藿香"、"陈皮"）
    - user_input_sources:   抽取的来源实体（如"伤寒论"）

    ── 实体匹配（FAISS 向量检索匹配到知识图谱中的实体） ──
    - matched_effects:   匹配成功的功效实体名称
    - matched_diseases:  匹配成功的疾病实体名称
    - matched_symptoms:  匹配成功的症状实体名称
    - matched_formulas:  匹配成功的方剂实体名称
    - matched_herbs:     匹配成功的药材实体名称
    - matched_sources:   匹配成功的来源实体名称

    ── Cypher 查询 ──
    - cypher_query:              生成的 Cypher 查询语句列表，每条为一个独立的查询
    - is_all_validate_cypher:    是否所有 Cypher 语句都通过语法校验
    - cypher_validation_feedback: Cypher 校验失败时的错误详情，用于回传 LLM 修正
    - cypher_retry_count:         Cypher 生成重试次数计数器，防止无限循环（上限见 MAX_CYPHER_RETRIES）

    ── Neo4j 查询结果 ──
    - cypher_results:  执行 Cypher 查询后返回的结果列表，每个元素为一条查询的结果
    - neo4j_answer:    基于 Cypher 结果生成的最终自然语言回答

    ── LLM 直接回答兜底 ──
    - direct_out:      非中医问题由 LLM 直接生成的回答文本，由 llm_direct_out_node 写入；
                       同时也会写入 output 字段作为最终输出

    ── 运行时辅助 ──
    - _stream_tokens:  流式输出的 token 缓冲区（以 _ 前缀标识为内部运行时字段，
                       由 neo4j_answer_generate_node / llm_direct_out_node 产生）
    """

    # ── 输入输出 ──
    input: str
    messages: List[Dict[str, str]]
    output: str

    # ── 意图识别 ──
    is_xiaohongshu_publish_intent: bool
    is_zhongyi_intent: bool

    # ── 小红书发布链路 ──
    xiaohongshu_tcm_post_title: str
    xiaohongshu_tcm_post_content: str
    xiaohongshu_image_path_list: List[str]
    xiaohongshu_tcm_tip: str
    is_can_publish_xiaohongshu: bool
    xiaohongshu_markdown_output: str

    # ── 实体抽取（LLM 从用户输入中提取） ──
    user_input_effects: List[str]
    user_input_diseases: List[str]
    user_input_symptoms: List[str]
    user_input_formulas: List[str]
    user_input_herbs: List[str]
    user_input_sources: List[str]

    # ── 实体匹配（FAISS 向量检索） ──
    matched_effects: List[str]
    matched_diseases: List[str]
    matched_symptoms: List[str]
    matched_formulas: List[str]
    matched_herbs: List[str]
    matched_sources: List[str]

    # ── Cypher 查询 ──
    cypher_query: List[str]
    is_all_validate_cypher: bool
    cypher_validation_feedback: str
    cypher_retry_count: int

    # ── Neo4j 查询结果 ──
    cypher_results: List[dict]
    neo4j_answer: str

    # ── LLM 直接回答兜底 ──
    direct_out: str

    # ── 运行时辅助（内部字段，以 _ 前缀标识） ──
    _stream_tokens: List[str]


def make_initial_state(
    user_input: str = "",
    messages: List[Dict[str, str]] = None,
) -> AgentState:
    """
    创建带有安全默认值的新 AgentState 实例。

    统一的初始状态工厂函数，消除多处重复的硬编码默认值。
    当 AgentState 新增字段时，只需修改此函数即可保证所有调用方一致。

    :param user_input: 用户输入的文本内容，默认为空字符串
    :param messages:   对话历史消息列表，格式为 [{"role": "user/assistant", "content": "..."}]
                       默认为空列表，确保后续节点处理 messages 时不会遇到 None 值
    :return:           初始化完成的 AgentState TypedDict

    默认值约定：
      - 所有字符串字段初始化为空字符串 ""
      - 所有列表字段初始化为空列表 []
      - 所有布尔字段初始化为 False
      - 计数器（cypher_retry_count）初始化为 0
    """
    return AgentState(
        # ── 输入输出 ──
        input=user_input,
        messages=messages or [],
        output="",

        # ── 意图识别 ──
        is_xiaohongshu_publish_intent=False,
        is_zhongyi_intent=False,

        # ── 小红书发布链路 ──
        xiaohongshu_tcm_post_title="",
        xiaohongshu_tcm_post_content="",
        xiaohongshu_image_path_list=[],
        xiaohongshu_tcm_tip="",
        is_can_publish_xiaohongshu=False,
        xiaohongshu_markdown_output="",

        # ── 实体抽取（LLM 从用户输入中提取） ──
        user_input_effects=[],
        user_input_diseases=[],
        user_input_symptoms=[],
        user_input_formulas=[],
        user_input_herbs=[],
        user_input_sources=[],

        # ── 实体匹配（FAISS 向量检索） ──
        matched_effects=[],
        matched_diseases=[],
        matched_symptoms=[],
        matched_formulas=[],
        matched_herbs=[],
        matched_sources=[],

        # ── Cypher 查询 ──
        cypher_query=[],
        is_all_validate_cypher=False,
        cypher_validation_feedback="",
        cypher_retry_count=0,

        # ── Neo4j 查询结果 ──
        cypher_results=[],
        neo4j_answer="",

        # ── LLM 直接回答兜底 ──
        direct_out="",

        # ── 运行时辅助 ──
        _stream_tokens=[],
    )
