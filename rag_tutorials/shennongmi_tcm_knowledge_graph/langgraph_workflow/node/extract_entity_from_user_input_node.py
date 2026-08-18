"""
LangGraph 节点：从用户输入中抽取中医实体。

本节点是实体处理链路的第一步。它调用大模型（LLM）从用户原始输入中识别并抽取出
六类中医实体：症状（Symptom）、疾病（Disease）、方剂（Formula）、药材（Herb）、
功效（Effect）、出处（Source）。

工作流中的位置：
    中医意图识别（通过） → [本节点] → 实体匹配（FAISS） → Cypher 生成 → ...

设计要点：
    1. 对话历史上下文：保留最近 3 轮对话历史，用于代词指代消解（如"它"、"这个"），
       但不过度干扰实体抽取的精准度。
    2. 容错机制：LLM 返回非法 JSON 或调用失败时，将所有字段置空，
       保证流程不中断，下游节点会收到空列表并走兜底回答。
    3. Markdown 兼容：自动去除 LLM 可能包裹的 ```json ... ``` 代码块标记。
    4. 输出格式：严格 JSON，六类实体各对应一个字符串列表。
"""

import json

from langchain_core.messages import HumanMessage

from langgraph_workflow.agent_state import AgentState
from common.llm import my_llm, format_conversation_history


def extract_entity_from_user_input_node(state: AgentState) -> AgentState:
    """
    从用户输入中抽取中医相关实体（症状、疾病、方剂、药材、功效、出处）。

    通过精心设计的提示词（prompt）引导 LLM 严格按照六类实体进行分类抽取。
    支持利用对话历史进行代词指代消解，解析诸如"它的功效是什么"中的"它"
    指代的是上一轮提到的哪个方剂或药材。

    输入 state 字段：
        - input    → 用户当前输入的文本
        - messages → 对话历史消息列表（用于上下文理解）

    输出 state 字段：
        - user_input_symptoms  → 抽取到的症状实体列表
        - user_input_diseases  → 抽取到的疾病实体列表
        - user_input_formulas  → 抽取到的方剂实体列表
        - user_input_herbs     → 抽取到的药材实体列表
        - user_input_effects   → 抽取到的功效实体列表
        - user_input_sources   → 抽取到的出处实体列表

    异常处理：
        - LLM 返回非法 JSON → 所有字段置空，打印原始输出便于排查
        - LLM 调用异常（网络、API 等）→ 所有字段置空，下游走兜底回答
    """
    print("开始抽取用户输入中的实体...")

    # 获取用户输入和对话历史
    user_input = state["input"]
    messages = state.get("messages", [])

    # 构建对话历史文本（保留最近 3 轮，用于代词指代消解，避免过度干扰实体抽取）
    history_section = format_conversation_history(messages, max_turns=3)

    # 构建实体抽取提示词
    # 提示词设计要点：
    #   - 明确定义六类实体的范围和示例，帮助 LLM 精准分类
    #   - 强调"只抽取明确出现的实体，不要凭空编造"，避免幻觉
    #   - 指示 LLM 利用对话历史解析代词（如"它"→最近提到的方剂/药材）
    #   - 要求严格输出 JSON，方便程序化解析
    prompt = f"""
{history_section}

用户当前输入: {user_input}

你是一个中医实体抽取器。请从【用户当前输入】中抽取出以下六类实体：

1. Symptom（症状）：如咳嗽、腹痛、发热、失眠、头痛等
2. Disease（疾病）：如感冒、肺炎、肾虚、风寒感冒、脾虚泄泻等
3. Formula（方剂）：如四君子汤、桂枝汤、六味地黄丸、麻黄汤等
4. Herb（药材）：如人参、黄芪、丁香、当归、甘草、白术等
5. Effect（功效）：如补气、活血、祛湿、止痛、清热、解毒等
6. Source（出处）：如《本草纲目》《伤寒论》《金匮要略》等

【任务要求】
- 只抽取【用户当前输入】中明确出现或直接相关的实体，不要凭空编造。
- 对话历史仅用于理解上下文（如代词"它"、"这个"指代的是什么），帮助你准确识别当前输入中的实体。
- 如果用户使用了代词（如"它的功效是什么"），请根据对话历史中最近提到的方剂/药材来解析指代对象，并将解析后的实体名填入对应字段。
- 如果某类实体没有匹配到，对应的列表保持为空。
- 尽可能精准，避免将普通词汇误识别为中医实体。

【输出要求】
- 严格输出 JSON 格式，不要输出任何解释或其他文字。
- JSON 结构如下：
{{
    "symptoms": ["..."],
    "diseases": ["..."],
    "formulas": ["..."],
    "herbs": ["..."],
    "effects": ["..."],
    "sources": ["..."]
}}
"""

    # 🔧 修复：在 try 块外初始化为 None，避免 LLM invoke 失败时
    # except json.JSONDecodeError 中引用未绑定变量 model_answer
    model_answer = None
    try:
        # 调用大模型进行实体抽取
        response = my_llm.invoke([HumanMessage(content=prompt)])
        model_answer = response.content.strip()

        # 尝试解析 LLM 返回的 JSON
        # 兼容可能被 markdown 代码块包裹的情况
        if model_answer.startswith("```"):
            # 去掉 ```json 或 ``` 标记
            lines = model_answer.split("\n")
            # 去掉首行 ``` 和末行 ```
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            model_answer = "\n".join(lines)

        # 解析 JSON 并提取各类实体
        result = json.loads(model_answer)

        # 将抽取结果写入 state
        # 使用 .get() 安全取值，避免 JSON 中缺少某字段时 KeyError
        state["user_input_symptoms"] = result.get("symptoms", [])
        state["user_input_diseases"] = result.get("diseases", [])
        state["user_input_formulas"] = result.get("formulas", [])
        state["user_input_herbs"] = result.get("herbs", [])
        state["user_input_effects"] = result.get("effects", [])
        state["user_input_sources"] = result.get("sources", [])

        print(f"实体抽取完成: symptoms={state['user_input_symptoms']}, "
              f"diseases={state['user_input_diseases']}, "
              f"formulas={state['user_input_formulas']}, "
              f"herbs={state['user_input_herbs']}, "
              f"effects={state['user_input_effects']}, "
              f"sources={state['user_input_sources']}")

    except json.JSONDecodeError as e:
        # JSON 解析失败：可能是 LLM 返回了非标准格式
        # 将所有字段置空，保证流程不中断
        print(f"JSON 解析失败: {e}, 原始输出: {model_answer}")
        # 解析失败时将所有字段置空，保证流程不中断
        state["user_input_symptoms"] = []
        state["user_input_diseases"] = []
        state["user_input_formulas"] = []
        state["user_input_herbs"] = []
        state["user_input_effects"] = []
        state["user_input_sources"] = []

    except Exception as e:
        # LLM 调用异常：可能是网络问题、API 限流等
        # 将所有字段置空，下游匹配节点收到空列表后会走兜底回答
        print(f"❌ 实体抽取 LLM 调用失败: {e}")
        # LLM 不可用时将所有字段置空，保证流程不中断，下游会走兜底回答
        state["user_input_symptoms"] = []
        state["user_input_diseases"] = []
        state["user_input_formulas"] = []
        state["user_input_herbs"] = []
        state["user_input_effects"] = []
        state["user_input_sources"] = []

    return state


if __name__ == "__main__":
    from unittest.mock import patch, MagicMock

    def _make_mock_response(json_str: str):
        """构造一个模拟的 LLM 响应对象"""
        mock_msg = MagicMock()
        mock_msg.content = json_str
        mock_response = MagicMock()
        mock_response.content = mock_msg.content
        return mock_response

    def _build_state(user_input: str) -> AgentState:
        """构建一个最小可用的 AgentState"""
        return {
            "input": user_input,
            "messages": [],
            "is_xiaohongshu_publish_intent": False,
            "xiaohongshu_tcm_post_title": "",
            "xiaohongshu_tcm_post_content": "",
            "xiaohongshu_image_path_list": [],
            "xiaohongshu_tcm_tip": "",
            "is_can_publish_xiaohongshu": False,
            "xiaohongshu_markdown_output": "",
            "is_zhongyi_intent": False,
            "direct_out": "",
            "user_input_effects": [],
            "user_input_diseases": [],
            "user_input_symptoms": [],
            "user_input_formulas": [],
            "user_input_herbs": [],
            "user_input_sources": [],
            "matched_effects": [],
            "matched_diseases": [],
            "matched_symptoms": [],
            "matched_formulas": [],
            "matched_herbs": [],
            "matched_sources": [],
            "cypher_query": [],
            "is_all_validate_cypher": False,
            "cypher_validation_feedback": "",
            "cypher_retry_count": 0,
            "cypher_results": [],
            "neo4j_answer": "",
            "output": "",
            "_stream_tokens": [],
        }

    # ============================================================
    # 测试1：正常抽取 — 用户输入包含症状、方剂、药材
    # ============================================================
    print("=" * 60)
    print("测试1: 正常实体抽取（症状 + 方剂 + 药材）")
    print("=" * 60)
    state1 = _build_state("我最近咳嗽头痛，想用人参和黄芪调理，可以喝四君子汤吗？")

    mock_json1 = json.dumps({
        "symptoms": ["咳嗽", "头痛"],
        "diseases": [],
        "formulas": ["四君子汤"],
        "herbs": ["人参", "黄芪"],
        "effects": [],
        "sources": []
    }, ensure_ascii=False)

    with patch("langgraph_workflow.node.extract_entity_from_user_input_node.my_llm") as mock_llm:
        mock_llm.invoke.return_value = _make_mock_response(mock_json1)
        result1 = extract_entity_from_user_input_node(state1)

    print(f"输入: {state1['input']}")
    print(f"symptoms : {result1['user_input_symptoms']}")
    print(f"diseases : {result1['user_input_diseases']}")
    print(f"formulas : {result1['user_input_formulas']}")
    print(f"herbs    : {result1['user_input_herbs']}")
    print(f"effects  : {result1['user_input_effects']}")
    print(f"sources  : {result1['user_input_sources']}")
    print()

    # ============================================================
    # 测试2：LLM 返回 markdown 代码块包裹的 JSON
    # ============================================================
    print("=" * 60)
    print("测试2: Markdown 代码块包裹的 JSON")
    print("=" * 60)
    state2 = _build_state("《伤寒论》里记载的麻黄汤能治疗风寒感冒，有发汗解表的功效")

    mock_content2 = '```json\n{\n  "symptoms": [],\n  "diseases": ["风寒感冒"],\n  "formulas": ["麻黄汤"],\n  "herbs": [],\n  "effects": ["发汗解表"],\n  "sources": ["伤寒论"]\n}\n```'

    with patch("langgraph_workflow.node.extract_entity_from_user_input_node.my_llm") as mock_llm:
        mock_llm.invoke.return_value = _make_mock_response(mock_content2)
        result2 = extract_entity_from_user_input_node(state2)

    print(f"输入: {state2['input']}")
    print(f"symptoms : {result2['user_input_symptoms']}")
    print(f"diseases : {result2['user_input_diseases']}")
    print(f"formulas : {result2['user_input_formulas']}")
    print(f"herbs    : {result2['user_input_herbs']}")
    print(f"effects  : {result2['user_input_effects']}")
    print(f"sources  : {result2['user_input_sources']}")
    print()

    # ============================================================
    # 测试3：用户输入不包含任何中医实体
    # ============================================================
    print("=" * 60)
    print("测试3: 无中医实体的输入")
    print("=" * 60)
    state3 = _build_state("今天天气真好，适合出去玩")

    mock_json3 = json.dumps({
        "symptoms": [],
        "diseases": [],
        "formulas": [],
        "herbs": [],
        "effects": [],
        "sources": []
    }, ensure_ascii=False)

    with patch("langgraph_workflow.node.extract_entity_from_user_input_node.my_llm") as mock_llm:
        mock_llm.invoke.return_value = _make_mock_response(mock_json3)
        result3 = extract_entity_from_user_input_node(state3)

    print(f"输入: {state3['input']}")
    print(f"symptoms : {result3['user_input_symptoms']}")
    print(f"diseases : {result3['user_input_diseases']}")
    print(f"formulas : {result3['user_input_formulas']}")
    print(f"herbs    : {result3['user_input_herbs']}")
    print(f"effects  : {result3['user_input_effects']}")
    print(f"sources  : {result3['user_input_sources']}")
    print()

    # ============================================================
    # 测试4：JSON 解析失败 — 容错处理
    # ============================================================
    print("=" * 60)
    print("测试4: LLM 返回非法 JSON（容错测试）")
    print("=" * 60)
    state4 = _build_state("当归补血汤里的当归和黄芪有什么功效？")

    with patch("langgraph_workflow.node.extract_entity_from_user_input_node.my_llm") as mock_llm:
        mock_llm.invoke.return_value = _make_mock_response("这不是一个合法的 JSON 字符串...")
        result4 = extract_entity_from_user_input_node(state4)

    print(f"输入: {state4['input']}")
    print(f"symptoms : {result4['user_input_symptoms']}")
    print(f"diseases : {result4['user_input_diseases']}")
    print(f"formulas : {result4['user_input_formulas']}")
    print(f"herbs    : {result4['user_input_herbs']}")
    print(f"effects  : {result4['user_input_effects']}")
    print(f"sources  : {result4['user_input_sources']}")
    print("（解析失败时所有字段应为空列表，流程不中断）")
    print()

    # ============================================================
    # 测试5：全部六类实体覆盖
    # ============================================================
    print("=" * 60)
    print("测试5: 全部六类实体覆盖")
    print("=" * 60)
    state5 = _build_state(
        "根据《金匮要略》记载，甘麦大枣汤用甘草、小麦、大枣治疗脏躁，"
        "症见悲伤欲哭、烦躁不安，有养心安神的功效"
    )

    mock_json5 = json.dumps({
        "symptoms": ["悲伤欲哭", "烦躁不安"],
        "diseases": ["脏躁"],
        "formulas": ["甘麦大枣汤"],
        "herbs": ["甘草", "小麦", "大枣"],
        "effects": ["养心安神"],
        "sources": ["金匮要略"]
    }, ensure_ascii=False)

    with patch("langgraph_workflow.node.extract_entity_from_user_input_node.my_llm") as mock_llm:
        mock_llm.invoke.return_value = _make_mock_response(mock_json5)
        result5 = extract_entity_from_user_input_node(state5)

    print(f"输入: {state5['input']}")
    print(f"symptoms : {result5['user_input_symptoms']}")
    print(f"diseases : {result5['user_input_diseases']}")
    print(f"formulas : {result5['user_input_formulas']}")
    print(f"herbs    : {result5['user_input_herbs']}")
    print(f"effects  : {result5['user_input_effects']}")
    print(f"sources  : {result5['user_input_sources']}")
    print()

    print("=" * 60)
    print("全部测试完成 ✓")
    print("=" * 60)
