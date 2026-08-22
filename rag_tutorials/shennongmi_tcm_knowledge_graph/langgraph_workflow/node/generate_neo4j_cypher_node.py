"""
LangGraph 节点：根据用户输入语义 + 匹配到的实体 + 图谱元数据，
调用大模型生成查询 Neo4j 知识图谱的 Cypher 语句。

本节点是 TCM 知识图谱问答链路的"翻译层"——将自然语言问题翻译为
Neo4j 图数据库的 Cypher 查询语言。它综合以下信息生成查询：
    1. 用户原始输入的语义（理解用户真正想问什么）
    2. 匹配到的标准实体名称（从 FAISS 获得，作为查询的锚点）
    3. 知识图谱元数据 / Schema（告知 LLM 有哪些标签、关系类型可用）
    4. 校验失败的反馈信息（用于重试修正）

工作流中的位置：
    实体匹配（FAISS） → [本节点] → Cypher 校验 → Cypher 执行
                              ↑                         |
                              └—— 校验失败时重试 ←———————┘

自修正重试机制：
    当 check_cypher_node 校验失败时，会将 Neo4j 的具体错误信息
    写入 cypher_validation_feedback，本节点检测到该字段非空时
    会自动构建包含错误详情的修正提示词，引导 LLM 根据报错逐一修正。
    重试次数由 cypher_retry_count 追踪，工作流层负责控制重试上限。
"""

import json
import re
from typing import List

from langchain_core.messages import HumanMessage

from langgraph_workflow.agent_state import AgentState
from common.llm import my_llm
from common.config import Config

conf = Config()


# ============================================================
# 辅助函数
# ============================================================

def _collect_matched_entities(state: AgentState) -> dict:
    """
    从 state 中收集所有匹配到的实体（matched_*）和用户输入中的原始实体（user_input_*），
    按类型分组返回。matched 实体是经过 FAISS 校验的标准名称，user_input 实体作为补充上下文。

    返回结构:
        {
            "功效": {"matched": [...], "user_input": [...]},
            "疾病": {"matched": [...], "user_input": [...]},
            ...
        }

    设计意图：
        - matched 列表：LLM 在生成 Cypher 时必须优先使用这些名称，
          因为它们是经过 FAISS 确认存在于知识图谱中的标准名称。
        - user_input 列表（去重后）：仅作为语义参考，帮助 LLM 理解用户意图，
          但不应直接用作 Cypher 查询的锚点实体（FAISS 语义检索未匹配到，
          说明这些实体在知识图谱中很可能不存在，LLM 应返回空查询列表）。
    """
    # 六类实体的 matched 和 user_input 字段名映射
    type_fields = {
        "功效":   ("matched_effects",   "user_input_effects"),
        "疾病":   ("matched_diseases",  "user_input_diseases"),
        "症状":   ("matched_symptoms",  "user_input_symptoms"),
        "方剂":   ("matched_formulas",  "user_input_formulas"),
        "药材":   ("matched_herbs",     "user_input_herbs"),
        "出处":   ("matched_sources",   "user_input_sources"),
    }
    result = {}
    for type_name, (matched_field, user_input_field) in type_fields.items():
        matched = state.get(matched_field, [])
        user_input = state.get(user_input_field, [])
        if matched or user_input:
            result[type_name] = {
                "matched": matched,
                "user_input": [e for e in user_input if e not in matched],  # 去重，只保留未匹配到的
            }
    return result


def _extract_json_from_llm_output(raw_text: str) -> str:
    """
    从 LLM 原始输出中提取 JSON 内容。

    兼容以下情况：
      - 纯 JSON 字符串
      - markdown ```json ... ``` 代码块包裹
      - markdown ``` ... ``` 代码块包裹

    使用正则而非简单字符串切片，能够正确处理嵌套反引号和
    代码块内包含空行的情况。
    """
    text = raw_text.strip()

    # 尝试匹配 ```json ... ``` 或 ``` ... ```
    # re.DOTALL 使 . 能匹配换行符，确保可以捕获多行 JSON
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    return text


def _build_matched_entities_section(entities_info: dict) -> str:
    """
    将匹配到的实体及用户输入原始实体格式化为提示词中的一段文本。

    此函数将结构化的实体信息转为 LLM 易于理解的自然语言描述，
    区分"已匹配"（知识图谱中存在）和"未匹配"（仅供参考）两类实体。

    :param entities_info: _collect_matched_entities 的返回值，
                          结构: {类型名: {"matched": [...], "user_input": [...]}}
    :return: 格式化后的实体描述文本，可直接嵌入提示词
    """
    if not entities_info:
        # 无任何实体信息：提示 LLM 不要凭空推测，返回空查询列表
        return "（无匹配实体，知识图谱中不存在用户问题涉及的实体，请返回空的 cypher_queries 列表 `[]`，不要推测名称）"

    # 中文类型名 → Neo4j Label 名映射
    type_to_label = {
        "功效": "Effect",
        "疾病": "Disease",
        "症状": "Symptom",
        "方剂": "Formula",
        "药材": "Herb",
        "出处": "Source",
    }

    lines = ["以下是与用户问题相关的实体信息，请优先使用【已匹配】的标准名称构造 Cypher 查询："]
    for type_name, info in entities_info.items():
        label = type_to_label.get(type_name, type_name)
        matched = info.get("matched", [])
        user_input = info.get("user_input", [])

        if matched:
            lines.append(f"- {type_name} (label: {label})【已匹配】: {', '.join(matched)}")
        if user_input:
            lines.append(f"- {type_name} (label: {label})【未匹配，仅供参考】: {', '.join(user_input)}")

    return "\n".join(lines)


# ============================================================
# 构建提示词
# ============================================================

def _build_cypher_generation_prompt(
    user_input: str,
    matched_entities: dict,
    metadata: str,
    validation_feedback: str = "",
    retry_count: int = 0,
) -> str:
    """
    构建用于生成 Cypher 语句的完整提示词。

    提示词设计策略：
        1. Role（角色定位）：将 LLM 定位为 Neo4j Cypher 专家
        2. Context（上下文）：提供用户问题、匹配实体、图谱 Schema
        3. Constraints（约束）：明确命名规则、格式要求、边界条件
        4. Examples（示例）：提供常见查询模式作为参考（few-shot 学习）
        5. Feedback（反馈修正）：重试时嵌入 Neo4j 的具体错误信息

    :param user_input:          用户原始输入
    :param matched_entities:    匹配到的标准实体（按类型分组）
    :param metadata:            图谱元数据 JSON 字符串（包含 labels / relationships / triples）
    :param validation_feedback: 上一次校验失败的错误详情（重试时传入，首次生成为空）
    :param retry_count:         当前是第几次重试（0 表示首次生成）
    :return: 完整的提示词字符串，可直接发送给 LLM
    """
    matched_section = _build_matched_entities_section(matched_entities)

    # 如果是重试，构建修正指导段落
    retry_section = ""
    if validation_feedback:
        retry_section = f"""
## ⚠️ 上一次生成的 Cypher 校验失败（第 {retry_count} 次重试）

以下是 Neo4j 数据库返回的具体错误信息，请仔细阅读并根据报错逐一修正：

{validation_feedback}

### 修正要求
1. **标签名（Label）**：检查是否与 Schema 中的标签完全一致（区分大小写），常见错误如 `Herb` 写成 `Herbs`、`Formula` 写成 `Formla`
2. **关系类型**：确认关系类型是否存在于 Schema 中，常见错误如混淆 `HAS_EFFECT` 和 `HAS_SYMPTOM`
3. **属性名**：确认属性名是否正确，当前图谱使用 `name` 作为主匹配属性
4. **语法问题**：检查引号配对、括号匹配、变量名拼写等
5. 如果 Neo4j 提示某标签或关系不存在，请从 Schema 中查找正确的替代名称
6. 修正后重新生成，确保每条语句都能通过 EXPLAIN 校验
"""

    prompt = f"""你是一名 Neo4j Cypher 查询专家，负责根据用户问题生成查询中医知识图谱的 Cypher 语句。

## 用户问题
{user_input}

## 匹配到的实体
{matched_section}

## 知识图谱元数据（Schema）
{metadata}
{retry_section}
## 任务要求
1. 根据用户问题的语义、匹配到的实体以及图谱 Schema，生成一个或多个 Cypher 查询语句来回答用户问题。
2. 查询中使用的实体名称必须严格来自【匹配到的实体】中的【已匹配】标准名称。标记为【未匹配】的实体说明 FAISS 语义检索未在知识图谱中找到对应记录，很可能不存在于 Neo4j 数据库中，请不要使用。如果用户问题涉及的关键实体全部未匹配，请返回空的 cypher_queries 列表 `[]`，由下游节点告知用户"暂未收录相关信息"。
3. 所有节点均使用 `name` 属性作为匹配条件（如 `{{name: "xxx"}}`）。
4. 查询应尽可能一次返回用户需要的信息，同时保持语句清晰可读。
5. 如果用户问题涉及多个子问题，可以为每个子问题分别生成一条查询。
6. 优先使用简单的 MATCH...RETURN 查询，避免不必要的复杂嵌套。

## 常见查询模式参考
- 查询某药材（Herb）的详细信息：
  MATCH (h:Herb {{name: "人参"}}) RETURN h
- 查询某方剂（Formula）由哪些药材组成：
  MATCH (f:Formula {{name: "四君子汤"}})-[:HAS_INGREDIENT]->(h:Herb) RETURN f.name, h.name
- 查询哪些药材具有某功效（Effect）：
  MATCH (h:Herb)-[:HAS_EFFECT]->(e:Effect {{name: "清热解毒"}}) RETURN h.name
- 查询某方剂的功效和主治：
  MATCH (f:Formula {{name: "桂枝汤"}})-[:HAS_EFFECT]->(e:Effect)
  MATCH (f)-[:TREATS_DISEASE]->(d:Disease)
  RETURN f.name, collect(DISTINCT e.name) AS effects, collect(DISTINCT d.name) AS diseases
- 查询某疾病（Disease）有哪些症状（Symptom）：
  MATCH (d:Disease {{name: "风寒感冒"}})-[:HAS_SYMPTOM]->(s:Symptom) RETURN s.name
- 查询哪些方剂可以治疗某疾病：
  MATCH (f:Formula)-[:TREATS_DISEASE]->(d:Disease {{name: "咳嗽"}}) RETURN f.name
- 查询某文献出处（Source）包含的方剂：
  MATCH (f:Formula)-[:FROM_SOURCE]->(s:Source {{name: "伤寒论"}}) RETURN f.name

## 输出格式
- 严格输出 JSON 格式，不要输出任何解释或其他文字。
- JSON 结构如下：
{{
    "cypher_queries": [
        "MATCH ... RETURN ...",
        "MATCH ... RETURN ..."
    ],
    "reasoning": "简要说明每条查询的目的（一句话即可）"
}}

## 注意事项
- 如果用户问题是纯闲聊或不涉及图谱查询，请返回空的 cypher_queries 列表 `[]`。
- 确保 Cypher 语法正确，标签（如 Herb, Formula）和关系类型（如 HAS_INGREDIENT, TREATS_DISEASE）必须严格来自元数据。
- 节点标签（Label）和关系类型（Relationship Type）区分大小写。
"""
    return prompt


# ============================================================
# LangGraph 节点函数
# ============================================================

def generate_neo4j_cypher_node(state: AgentState) -> AgentState:
    """
    Cypher 语句生成节点：根据用户输入语义、匹配到的实体及图谱元数据，
    调用大模型生成查询 Neo4j 知识图谱的 Cypher 语句。

    支持自修正重试：当上游 check_cypher_node 校验失败并回传
    cypher_validation_feedback 时，会将错误信息嵌入提示词，
    引导 LLM 根据 Neo4j 的具体报错进行修正。

    输入（来自上游节点的 state 字段）：
        - input                     → 用户原始输入
        - matched_effects/diseases/symptoms/formulas/herbs/sources → 匹配到的标准实体
        - cypher_validation_feedback → 校验失败的错误详情（重试时由 check_cypher_node 回传）
        - cypher_retry_count         → 当前重试次数

    输出（写入 state）：
        - cypher_query → 生成的 Cypher 查询语句列表
        - cypher_retry_count → 递增后的重试次数
          （语句合法性校验由下游 check_cypher_node 负责）

    容错机制：
        1. JSON 解析失败 → 从原始输出中用正则提取 MATCH 语句作为后备
        2. 后备提取也无结果 → 将 cypher_query 置空，下游会走兜底回答
        3. LLM 调用异常 → 同上，置空 cypher_query
    """
    print("=" * 50)
    print("🔧 开始生成 Neo4j Cypher 查询语句")
    print("=" * 50)

    # —— 第一步：收集所需信息 ——
    user_input = state.get("input", "")
    entities_info = _collect_matched_entities(state)
    validation_feedback = state.get("cypher_validation_feedback", "")
    retry_count = state.get("cypher_retry_count", 0)

    # —— 第二步：处理重试状态 ——
    # 如果是重试，递增计数器
    if validation_feedback:
        retry_count += 1
        state["cypher_retry_count"] = retry_count
        print(f"🔄 第 {retry_count} 次重试，将根据校验反馈修正 Cypher...")
    else:
        # 首次执行也确保 cypher_retry_count 字段存在于 state 中
        state.setdefault("cypher_retry_count", 0)

    # —— 第三步：打印实体概况日志（便于调试和追踪） ——
    if entities_info:
        total_matched = sum(len(v.get("matched", [])) for v in entities_info.values())
        total_user_input = sum(len(v.get("user_input", [])) for v in entities_info.values())
        print(f"📌 实体概况: {total_matched} 个已匹配, {total_user_input} 个未匹配")
        for type_name, info in entities_info.items():
            matched = info.get("matched", [])
            ui = info.get("user_input", [])
            if matched:
                print(f"   [{type_name}] 已匹配: {matched}")
            if ui:
                print(f"   [{type_name}] 未匹配: {ui}")
    else:
        print("⚠️ 未接收到任何实体信息，将指示 LLM 返回空查询列表")

    # —— 第四步：构建提示词（含重试反馈） ——
    metadata = conf.TCM_METADATA
    prompt = _build_cypher_generation_prompt(
        user_input, entities_info, metadata,
        validation_feedback=validation_feedback,
        retry_count=retry_count,
    )

    # —— 第五步：调用大模型并解析结果 ——
    try:
        # 调用大模型
        response = my_llm.invoke([HumanMessage(content=prompt)])
        raw_output = response.content.strip()
        print(f"\n📝 LLM 原始输出:\n{raw_output[:500]}{'...' if len(raw_output) > 500 else ''}")

        # 提取 JSON 并解析
        json_str = _extract_json_from_llm_output(raw_output)
        result = json.loads(json_str)
        cypher_queries: List[str] = result.get("cypher_queries", [])
        reasoning = result.get("reasoning", "")

        print(f"\n📊 生成结果: {len(cypher_queries)} 条 Cypher 语句")
        if reasoning:
            print(f"💡 生成思路: {reasoning}")
        for i, q in enumerate(cypher_queries, 1):
            print(f"   [{i}] {q[:120]}{'...' if len(q) > 120 else ''}")

        state["cypher_query"] = cypher_queries
        print(f"\n✅ 成功解析 {len(cypher_queries)} 条 Cypher 语句（校验由下游 check_cypher_node 负责）")

    except json.JSONDecodeError as e:
        # —— 容错路径 A：JSON 解析失败 ——
        # LLM 可能返回了非 JSON 格式（虽然提示词要求了 JSON）
        # 尝试用正则从原始文本中提取 MATCH 语句作为后备方案
        print(f"\n❌ JSON 解析失败: {e}")
        print(f"   原始输出: {raw_output[:300]}")
        # 解析失败时，尝试从原始输出中提取 MATCH 语句作为后备
        fallback_queries = re.findall(
            r"(?:MATCH|OPTIONAL\s+MATCH).*?(?:RETURN|YIELD).*?(?=(?:MATCH|OPTIONAL\s+MATCH|$))",
            raw_output,
            re.DOTALL | re.IGNORECASE,
        )
        if fallback_queries:
            # 🔧 修复：不再用 split('\n\n')[0] 截断多行语句。
            # 改用更精确的策略：逐条语句收集，遇到空行时仅在后面还有新的 MATCH 时才认为结束。
            # 同时去除尾部非 Cypher 文本（如 LLM 的注释说明）。
            cleaned_queries = []
            cypher_keywords = ("MATCH", "OPTIONAL", "CREATE", "MERGE", "RETURN", "WHERE", "WITH", "UNWIND")
            for q in fallback_queries:
                lines = q.strip().split('\n')
                # 从后往前扫描：去掉尾部不以 Cypher 关键字开头的行（LLM 注释行）
                while lines and not any(lines[-1].strip().upper().startswith(kw) for kw in cypher_keywords):
                    lines.pop()
                q = '\n'.join(lines).strip()
                if q:
                    cleaned_queries.append(q)
            fallback_queries = cleaned_queries
            print(f"⚠️ 已从原始输出中提取 {len(fallback_queries)} 条 MATCH 语句作为后备")
            state["cypher_query"] = fallback_queries
        else:
            state["cypher_query"] = []

    except Exception as e:
        # —— 容错路径 B：LLM 调用异常（网络问题、API 限流等） ——
        print(f"\n❌ 生成 Cypher 语句时发生异常: {e}")
        state["cypher_query"] = []

    print(f"\n{'=' * 50}")
    print(f"🔧 Cypher 语句生成完成")
    print(f"{'=' * 50}")

    return state


# ============================================================
# 调试入口
# ============================================================

if __name__ == "__main__":
    from unittest.mock import patch, MagicMock

    # 当脚本直接运行时，模块名为 __main__，需要 patch __main__ 中的 my_llm 引用
    # （而非包路径 langgraph_workflow.node.generate_neo4j_cypher_node）
    _PATCH_TARGET = "__main__.my_llm"

    def _make_mock_llm_response(json_str: str):
        """构造一个模拟的 LLM 响应对象"""
        mock_msg = MagicMock()
        mock_msg.content = json_str
        mock_response = MagicMock()
        mock_response.content = mock_msg.content
        return mock_response

    def _build_state(
        user_input: str,
        matched_effects: list = None,
        matched_diseases: list = None,
        matched_symptoms: list = None,
        matched_formulas: list = None,
        matched_herbs: list = None,
        matched_sources: list = None,
        user_input_effects: list = None,
        user_input_diseases: list = None,
        user_input_symptoms: list = None,
        user_input_formulas: list = None,
        user_input_herbs: list = None,
        user_input_sources: list = None,
    ) -> AgentState:
        """
        构建测试用 AgentState。
        matched_*   — FAISS 匹配到的标准实体名称
        user_input_* — LLM 从用户输入中抽取的原始实体名称
        两者可以独立设置，模拟「匹配成功」和「匹配失败」两种场景。
        """
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
            "user_input_effects": user_input_effects or [],
            "user_input_diseases": user_input_diseases or [],
            "user_input_symptoms": user_input_symptoms or [],
            "user_input_formulas": user_input_formulas or [],
            "user_input_herbs": user_input_herbs or [],
            "user_input_sources": user_input_sources or [],
            "matched_effects": matched_effects or [],
            "matched_diseases": matched_diseases or [],
            "matched_symptoms": matched_symptoms or [],
            "matched_formulas": matched_formulas or [],
            "matched_herbs": matched_herbs or [],
            "matched_sources": matched_sources or [],
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
    # 测试1：查询方剂组成
    # ============================================================
    print("=" * 60)
    print("测试1: 查询方剂组成（四君子汤）")
    print("=" * 60)
    state1 = _build_state(
        user_input="四君子汤由哪些药材组成？",
        matched_formulas=["四君子汤"],
    )

    mock_json1 = json.dumps({
        "cypher_queries": [
            "MATCH (f:Formula {name: '四君子汤'})-[:HAS_INGREDIENT]->(h:Herb) RETURN f.name, h.name",
            "MATCH (f:Formula {name: '四君子汤'})-[:HAS_EFFECT]->(e:Effect) RETURN f.name, e.name",
        ],
        "reasoning": "查询四君子汤的组成药材和功效"
    }, ensure_ascii=False)

    with patch(_PATCH_TARGET) as mock_llm:
        mock_llm.invoke.return_value = _make_mock_llm_response(mock_json1)
        result1 = generate_neo4j_cypher_node(state1)

    print(f"\n输入: {state1['input']}")
    print(f"匹配方剂: {state1['matched_formulas']}")
    print(f"生成的 Cypher 语句 ({len(result1['cypher_query'])} 条):")
    for i, q in enumerate(result1['cypher_query'], 1):
        print(f"  [{i}] {q}")
    print(f"✅ 成功生成 {len(result1['cypher_query'])} 条 Cypher 语句")
    print()

    # ============================================================
    # 测试2：查询药材功效
    # ============================================================
    print("=" * 60)
    print("测试2: 查询药材功效和主治（人参）")
    print("=" * 60)
    state2 = _build_state(
        user_input="人参有什么功效？能治什么病？",
        matched_herbs=["人参"],
    )

    mock_json2 = json.dumps({
        "cypher_queries": [
            "MATCH (h:Herb {name: '人参'})-[:HAS_EFFECT]->(e:Effect) RETURN e.name",
            "MATCH (h:Herb {name: '人参'})-[:TREATS_DISEASE]->(d:Disease) RETURN d.name",
        ],
        "reasoning": "分别查询人参的功效和主治疾病"
    }, ensure_ascii=False)

    with patch(_PATCH_TARGET) as mock_llm:
        mock_llm.invoke.return_value = _make_mock_llm_response(mock_json2)
        result2 = generate_neo4j_cypher_node(state2)

    print(f"\n输入: {state2['input']}")
    print(f"匹配药材: {state2['matched_herbs']}")
    print(f"生成的 Cypher 语句 ({len(result2['cypher_query'])} 条):")
    for i, q in enumerate(result2['cypher_query'], 1):
        print(f"  [{i}] {q}")
    print(f"✅ 成功生成 {len(result2['cypher_query'])} 条 Cypher 语句")
    print()

    # ============================================================
    # 测试3：查询治疗某疾病的方剂
    # ============================================================
    print("=" * 60)
    print("测试3: 查询治疗某疾病的方剂（风寒感冒）")
    print("=" * 60)
    state3 = _build_state(
        user_input="治疗风寒感冒有哪些方剂？",
        matched_diseases=["风寒感冒"],
    )

    mock_json3 = json.dumps({
        "cypher_queries": [
            "MATCH (f:Formula)-[:TREATS_DISEASE]->(d:Disease {name: '风寒感冒'}) RETURN f.name",
            "MATCH (h:Herb)-[:TREATS_DISEASE]->(d:Disease {name: '风寒感冒'}) RETURN h.name",
        ],
        "reasoning": "查询治疗风寒感冒的方剂和药材"
    }, ensure_ascii=False)

    with patch(_PATCH_TARGET) as mock_llm:
        mock_llm.invoke.return_value = _make_mock_llm_response(mock_json3)
        result3 = generate_neo4j_cypher_node(state3)

    print(f"\n输入: {state3['input']}")
    print(f"匹配疾病: {state3['matched_diseases']}")
    print(f"生成的 Cypher 语句 ({len(result3['cypher_query'])} 条):")
    for i, q in enumerate(result3['cypher_query'], 1):
        print(f"  [{i}] {q}")
    print(f"✅ 成功生成 {len(result3['cypher_query'])} 条 Cypher 语句")
    print()

    # ============================================================
    # 测试4：多实体复杂查询
    # ============================================================
    print("=" * 60)
    print("测试4: 多实体复杂查询（咳嗽 + 止嗽散）")
    print("=" * 60)
    state4 = _build_state(
        user_input="止嗽散能治咳嗽吗？里面有哪些药材？出自哪里？",
        matched_symptoms=["咳嗽"],
        matched_formulas=["止嗽散"],
    )

    mock_json4 = json.dumps({
        "cypher_queries": [
            "MATCH (f:Formula {name: '止嗽散'})-[:TREATS_DISEASE]->(d:Disease) RETURN d.name",
            "MATCH (f:Formula {name: '止嗽散'})-[:HAS_INGREDIENT]->(h:Herb) RETURN h.name",
            "MATCH (f:Formula {name: '止嗽散'})-[:FROM_SOURCE]->(s:Source) RETURN s.name",
        ],
        "reasoning": "分别查询止嗽散的主治疾病、组成药材和文献出处"
    }, ensure_ascii=False)

    with patch(_PATCH_TARGET) as mock_llm:
        mock_llm.invoke.return_value = _make_mock_llm_response(mock_json4)
        result4 = generate_neo4j_cypher_node(state4)

    print(f"\n输入: {state4['input']}")
    print(f"匹配症状: {state4['matched_symptoms']}")
    print(f"匹配方剂: {state4['matched_formulas']}")
    print(f"生成的 Cypher 语句 ({len(result4['cypher_query'])} 条):")
    for i, q in enumerate(result4['cypher_query'], 1):
        print(f"  [{i}] {q}")
    print(f"✅ 成功生成 {len(result4['cypher_query'])} 条 Cypher 语句")
    print()

    # ============================================================
    # 测试5：非中医/闲聊问题（应返回空列表）
    # ============================================================
    print("=" * 60)
    print("测试5: 非中医闲聊问题（应返回空列表）")
    print("=" * 60)
    state5 = _build_state(user_input="今天天气怎么样？")

    mock_json5 = json.dumps({
        "cypher_queries": [],
        "reasoning": "用户问题与中医无关，无需查询知识图谱"
    }, ensure_ascii=False)

    with patch(_PATCH_TARGET) as mock_llm:
        mock_llm.invoke.return_value = _make_mock_llm_response(mock_json5)
        result5 = generate_neo4j_cypher_node(state5)

    print(f"\n输入: {state5['input']}")
    print(f"生成的 Cypher 语句: {result5['cypher_query']}")
    # 验证：空列表也应正常返回
    assert result5['cypher_query'] == [], f"应返回空列表，实际: {result5['cypher_query']}"
    print("✅ 空列表（闲聊问题）验证通过")
    print()

    # ============================================================
    # 测试6：无匹配实体 — 应返回空列表
    # ============================================================
    print("=" * 60)
    print("测试6: 无匹配实体（应返回空列表，不推测名称）")
    print("=" * 60)
    state6 = _build_state(user_input="什么药材能清热解毒？")

    # 新行为：无匹配实体时 LLM 应返回空列表，而不是凭空推测实体名称
    mock_json6 = json.dumps({
        "cypher_queries": [],
        "reasoning": "用户问药材功效，但没有任何实体匹配到，知识图谱中可能无相关记录"
    }, ensure_ascii=False)

    with patch(_PATCH_TARGET) as mock_llm:
        mock_llm.invoke.return_value = _make_mock_llm_response(mock_json6)
        result6 = generate_neo4j_cypher_node(state6)

    print(f"\n输入: {state6['input']}")
    print(f"匹配实体: (无)")
    print(f"生成的 Cypher 语句: {result6['cypher_query']}")
    assert result6['cypher_query'] == [], f"无匹配实体时应返回空列表，实际: {result6['cypher_query']}"
    print("✅ 无匹配实体 → 返回空列表，验证通过")
    print()

    # ============================================================
    # 测试7：JSON 解析失败 — 后备提取
    # ============================================================
    print("=" * 60)
    print("测试7: LLM 返回非法 JSON（后备提取测试）")
    print("=" * 60)
    state7 = _build_state(
        user_input="当归有什么功效？",
        matched_herbs=["当归"],
    )

    # 模拟 LLM 返回非 JSON 但包含 MATCH 语句的输出
    mock_raw_output = """
    好的，以下是为您生成的查询语句：

    MATCH (h:Herb {name: '当归'})-[:HAS_EFFECT]->(e:Effect) RETURN e.name
    MATCH (h:Herb {name: '当归'})-[:TREATS_DISEASE]->(d:Disease) RETURN d.name

    以上查询可以帮您了解当归的功效和主治。
    """

    with patch(_PATCH_TARGET) as mock_llm:
        mock_llm.invoke.return_value = _make_mock_llm_response(mock_raw_output)
        result7 = generate_neo4j_cypher_node(state7)

    print(f"\n输入: {state7['input']}")
    print(f"生成的 Cypher 语句 ({len(result7['cypher_query'])} 条):")
    for i, q in enumerate(result7['cypher_query'], 1):
        print(f"  [{i}] {q}")
    print(f"✅ 成功从后备提取 {len(result7['cypher_query'])} 条 Cypher 语句")
    print()

    # ============================================================
    # 测试8：FAISS 匹配全部失败 — 应返回空列表
    # ============================================================
    print("=" * 60)
    print("测试8: FAISS 匹配全部失败（关键实体全未匹配，应返回空列表）")
    print("=" * 60)
    state8 = _build_state(
        user_input="柴葛解肌汤能治阳明经证吗？",
        # FAISS 匹配失败（方剂名不存在于知识图谱中）
        matched_formulas=[],
        # LLM 实体抽取成功但 FAISS 未匹配
        user_input_formulas=["柴葛解肌汤"],
        user_input_diseases=["阳明经证"],
    )

    # 新行为：关键实体全未匹配，LLM 应返回空列表，不推测名称
    mock_json8 = json.dumps({
        "cypher_queries": [],
        "reasoning": "柴葛解肌汤和阳明经证均未在知识图谱中匹配到，暂无法查询"
    }, ensure_ascii=False)

    with patch(_PATCH_TARGET) as mock_llm:
        mock_llm.invoke.return_value = _make_mock_llm_response(mock_json8)
        result8 = generate_neo4j_cypher_node(state8)

    print(f"\n输入: {state8['input']}")
    print(f"匹配方剂（matched）: {state8['matched_formulas']}（空，匹配失败）")
    print(f"抽取方剂（user_input）: {state8['user_input_formulas']}（有值但未匹配）")
    print(f"匹配疾病（matched）: {state8['matched_diseases']}")
    print(f"抽取疾病（user_input）: {state8['user_input_diseases']}")
    print(f"生成的 Cypher 语句: {result8['cypher_query']}")
    # 验证：关键实体全未匹配时，应返回空列表而非凭空推测
    assert result8['cypher_query'] == [], f"关键实体全未匹配时应返回空列表，实际: {result8['cypher_query']}"
    print("✅ FAISS 匹配失败 → 返回空列表，验证通过")
    print()

    print("=" * 60)
    print("全部测试完成 ✓")
    print("=" * 60)
