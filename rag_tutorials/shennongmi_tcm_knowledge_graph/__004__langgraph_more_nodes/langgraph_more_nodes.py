"""
LangGraph 工作流主模块：小红书中医养生内容自动发布 + 中医知识图谱问答

================================================================================
整体架构概览
================================================================================

本模块基于 LangGraph 的 StateGraph 构建了一个包含 14 个节点的有状态工作流图。
工作流从统一的入口（xiaohongshu_publish_intent_node）接收用户输入，根据意图
识别结果分流入三条链路：

  A. 小红书发布链路（用户意图：发布小红书笔记）
     xiaohongshu_publish_intent_node → text_generate_node → image_generator_node
     → check_text_image_node → auto_publish_xiaohongshu_node → generate_markdown_node → END

  B. 中医知识图谱问答链路（用户意图：中医相关问题）
     zhongyi_intent_node → extract_entity_from_user_input_node → match_entity_from_neo4j_node
     → generate_neo4j_cypher_node → check_cypher_node
       ├── 全部合法 → run_cypher_node → neo4j_answer_generate_node → END
       ├── 校验失败 + 未超上限 → 返回 generate_neo4j_cypher_node 重试修正（自修正回路）
       └── 校验失败 + 已达上限 / Cypher 为空 → neo4j_answer_generate_node（LLM 兜底回答）→ END

  C. 非中医兜底链路（用户输入与中医无关）
     zhongyi_intent_node → llm_direct_out_node → END

================================================================================
关键设计要点
================================================================================

1. FAISS 索引预加载：match_entity_from_neo4j_node 在模块加载时初始化 FAISS 索引
   和 PyTorch MPS embedding 模型，必须最先导入以避免与 langchain_openai 的
   httpcore/anyio OpenMP 运行时冲突导致 segmentation fault。

2. Cypher 自修正重试回路：check_cypher_node → generate_neo4j_cypher_node 之间形成
   闭环，校验失败的 Cypher 会带上错误反馈回传给 LLM 重新生成，最多重试
   MAX_CYPHER_RETRIES 次（默认 3 次），防止无限循环。

3. 意图识别本地模型：zhongyi_intent_node 使用 RoBERTa+LoRA 微调的本地模型进行
   中医意图分类，避免额外 LLM 调用；xiaohongshu_publish_intent_node 使用 fastText
   本地模型，仅在不可用时走 LLM 兜底。

4. 流式输出支持：_stream_tokens 运行时字段由末端节点（neo4j_answer_generate_node /
   llm_direct_out_node）收集 token，配合 FastAPI StreamingResponse 实现 SSE 流式
   输送到前端。

================================================================================
流程图参考：graph.jpg / graph1.png
================================================================================

节点串联顺序：

  START
    ↓
  [xiaohongshu_publish_intent_node]  ← 判断用户是否有发小红书的意图
    ├── 是 → [text_generate_node]     ← 进入小红书发布链路
    │         ↓
    │       [image_generator_node]
    │         ↓
    │       [check_text_image_node]
    │         ├── 可以发布 → [auto_publish_xiaohongshu_node]
    │         │                ↓
    │         │              [generate_markdown_node] → END
    │         └── 不可以 → END
    │
    └── 否 → [zhongyi_intent_node]    ← 判断用户输入是否与中医相关
              ├── 是（中医相关）→ [extract_entity_from_user_input_node]  ← 实体抽取
              │                      ↓
              │                    [match_entity_from_neo4j_node]          ← FAISS 实体匹配
              │                      ↓
              │                    [generate_neo4j_cypher_node]            ← 生成 Cypher
              │                      ↓                                     ↑
              │                    [check_cypher_node]                     │ 校验失败 + 未超上限时回环修正
              │                      ├── 全部合法 → [run_cypher_node]      │ (最多 3 次)
              │                      │                ↓                   │
              │                      ├── Cypher 为空 / 达到重试上限 ──→ [neo4j_answer_generate_node] → END
              │                      │                                    ↑
              │                      └── [run_cypher_node] 也汇聚到此
              │
              └── 否（非中医）→ [llm_direct_out_node] → END
"""

from typing import Literal
import sys

from langgraph.graph import StateGraph, START, END

from __004__langgraph_more_nodes.agent_state import AgentState, make_initial_state

# ============================================================
# 导入顺序说明
# ============================================================
# ⚠️ 重要：match_entity_from_neo4j_node 必须最先导入！
# 原因：该模块在加载时会初始化 FAISS 索引和 PyTorch MPS embedding 模型。
#       如果在此之前导入了 langchain_openai（通过 common.llm），
#       其底层 httpcore/anyio 等库会抢先初始化 OpenMP 运行时，
#       导致后续 FAISS 与 PyTorch 的 OpenMP 冲突，发生 segmentation fault。
#       因此所有依赖 common.llm 的节点必须排在此导入之后。
# ============================================================
from __004__langgraph_more_nodes.node.match_entity_from_neo4j_node import (
    match_entity_from_neo4j_node,
)

# —— 小红书发布链路节点 ——
# 这些节点处理从意图识别 → 文案生成 → 配图生成 → 内容校验 → 自动发布 → 结果输出的完整发布流程
from __004__langgraph_more_nodes.node.xiaohongshu_publish_intent_node import (
    xiaohongshu_publish_intent_node,  # 判断用户是否想发小红书（fastText 本地模型 + LLM 兜底）
)
from __004__langgraph_more_nodes.node.text_generate_node import (
    text_generate_node,  # 基于中医知识生成小红书标题和正文（LLM）
)
from __004__langgraph_more_nodes.node.image_generate_node import (
    image_generator_node,  # 调用即梦 AI 生成小红书配图
)
from __004__langgraph_more_nodes.node.check_text_image_node import (
    check_text_image_node,  # 校验标题、正文、图片是否齐全，决定是否可发布
)
from __004__langgraph_more_nodes.node.auto_publish_xiaohongshu_node import (
    auto_publish_xiaohongshu_node,  # 通过 Playwright 自动化发布到小红书
)
from __004__langgraph_more_nodes.node.generate_markdown_node import (
    generate_markdown_node,  # 生成 Markdown 格式的发布结果展示
)

# —— 中医知识图谱问答链路节点 ——
# 这些节点处理从中医意图识别 → 实体抽取 → FAISS 匹配 → Cypher 生成与校验 → Neo4j 查询 → 自然语言回答的完整问答流程
from __004__langgraph_more_nodes.node.zhongyi_intent_node import (
    zhongyi_intent_node,  # 判断用户输入是否与中医相关（RoBERTa+LoRA 本地模型）
)
from __004__langgraph_more_nodes.node.llm_direct_out_node import (
    llm_direct_out_node,  # 非中医问题的 LLM 直接回答（兜底）
)
from __004__langgraph_more_nodes.node.extract_entity_from_user_input_node import (
    extract_entity_from_user_input_node,  # LLM 从用户输入中抽取中医实体（症状、方剂、药材等）
)
from __004__langgraph_more_nodes.node.generate_neo4j_cypher_node import (
    generate_neo4j_cypher_node,  # 基于匹配实体生成 Neo4j Cypher 查询语句（LLM）
)
from __004__langgraph_more_nodes.node.check_cypher_node import (
    check_cypher_node,  # 校验 Cypher 语法合法性，生成校验反馈
)
from __004__langgraph_more_nodes.node.run_cypher_node import (
    run_cypher_node,  # 在 Neo4j 数据库中执行校验通过的 Cypher 语句
)
from __004__langgraph_more_nodes.node.neo4j_answer_generate_node import (
    neo4j_answer_generate_node,  # 将 Cypher 查询结果转换为自然语言回答（LLM）
)


# ============================================================
# 配置常量
# ============================================================

# Cypher 校验失败后的最大额外重试次数（不含首次生成）。
# 设为 3 意味着最多 1 次初始生成 + 3 次重试 = 4 次总尝试。
# 重试回路：check_cypher_node → generate_neo4j_cypher_node → check_cypher_node
# 当 cypher_retry_count >= MAX_CYPHER_RETRIES 时，放弃重试并走兜底回答。
MAX_CYPHER_RETRIES = 3

# ============================================================
# 条件路由函数
# ============================================================
# 以下函数均为 LangGraph 的条件边（conditional edge）判断逻辑。
# 每个函数接收当前 state，返回下一个目标节点的名称（字符串）。
# 返回值必须与 add_conditional_edges 中注册的映射键一致，
# 类型注解使用 Literal 以提供编译期检查。
# ============================================================


def decide_after_publish_intent(state: AgentState) -> Literal["text_generate_node", "zhongyi_intent_node"]:
    """
    小红书发布意图识别之后的路由判断。

    该路由在 xiaohongshu_publish_intent_node 执行后触发，根据 is_xiaohongshu_publish_intent
    字段决定进入哪条链路：

      - 是 → text_generate_node（小红书发布链路：生成笔记标题和正文）
      - 否 → zhongyi_intent_node（进入中医意图识别，进一步判断是中医问答还是非中医问题）

    :param state: 当前工作流状态，需包含 is_xiaohongshu_publish_intent 字段
    :return:      下一节点的名称，为 "text_generate_node" 或 "zhongyi_intent_node"
    """
    if state.get("is_xiaohongshu_publish_intent"):
        print("✅ 识别为小红书发布意图，进入文案生成流程")
        return "text_generate_node"
    else:
        print("❌ 非小红书发布意图，进入中医意图识别")
        return "zhongyi_intent_node"


def decide_after_zhongyi_intent(state: AgentState) -> Literal["extract_entity_from_user_input_node", "llm_direct_out_node"]:
    """
    中医意图识别之后的路由判断。

    该路由在 zhongyi_intent_node 执行后触发，根据 is_zhongyi_intent 字段决定
    进入知识图谱问答链路还是 LLM 直接回答兜底：

      - 是（中医相关） → extract_entity_from_user_input_node（知识图谱问答链路：实体抽取）
      - 否（非中医）   → llm_direct_out_node（LLM 直接回答兜底，如"今天天气怎么样"）

    注意：zhongyi_intent_node 使用 RoBERTa+LoRA 本地模型进行预测，不消耗 LLM token。

    :param state: 当前工作流状态，需包含 is_zhongyi_intent 字段
    :return:      下一节点的名称，为 "extract_entity_from_user_input_node" 或 "llm_direct_out_node"
    """
    if state.get("is_zhongyi_intent"):
        print("✅ 识别为中医相关问题，进入知识图谱问答链路")
        return "extract_entity_from_user_input_node"
    else:
        print("❌ 非中医相关问题，使用 LLM 直接回答")
        return "llm_direct_out_node"


def decide_after_check_text_image(state: AgentState) -> Literal["auto_publish_xiaohongshu_node", "__end__"]:
    """
    小红书内容完整性检查之后的路由判断。

    该路由在 check_text_image_node 执行后触发，根据 is_can_publish_xiaohongshu 字段
    决定是否进入自动发布节点：

      - 如果标题、内容、图片都齐全（is_can_publish_xiaohongshu = True）
        → auto_publish_xiaohongshu_node（通过 Playwright 自动发布到小红书）
      - 否则（缺少标题、内容或图片中任意一项）
        → END（直接结束，不执行发布操作）

    :param state: 当前工作流状态，需包含 is_can_publish_xiaohongshu 字段
    :return:      下一节点的名称，或特殊值 END 表示终止
    """
    if state.get("is_can_publish_xiaohongshu"):
        print("✅ 内容完整，进入自动发布流程")
        return "auto_publish_xiaohongshu_node"
    else:
        print("⚠️ 内容不完整，直接结束")
        return END


def decide_after_check_cypher(state: AgentState) -> Literal["run_cypher_node", "generate_neo4j_cypher_node", "neo4j_answer_generate_node"]:
    """
    Cypher 校验之后的路由判断（带自修正重试回路）。

    该路由在 check_cypher_node 执行后触发，是工作流中最复杂的路由逻辑。
    根据 Cypher 校验结果和重试次数，决定三条分支之一：

      ┌─ 全部通过校验（is_all_validate_cypher = True 且 cypher_query 非空）
      │  → run_cypher_node（在 Neo4j 中执行校验通过的 Cypher 语句）
      │
      ├─ Cypher 列表为空（通常是因为没有匹配到任何实体，无法生成有效查询）
      │  → neo4j_answer_generate_node（无查询可执行，直接走 LLM 兜底回答）
      │
      ├─ 未通过校验 AND 重试次数 < MAX_CYPHER_RETRIES
      │  → generate_neo4j_cypher_node（带上 cypher_validation_feedback 错误反馈，
      │    让 LLM 根据错误信息修正 Cypher，同时 cypher_retry_count 自增 1）
      │
      └─ 未通过校验 AND 重试次数 >= MAX_CYPHER_RETRIES
         → neo4j_answer_generate_node（放弃重试，直接走 LLM 兜底回答，
           避免无限循环消耗 LLM token）

    重试回路：check_cypher → generate_neo4j_cypher → check_cypher → ...
    最多循环 MAX_CYPHER_RETRIES 次（默认 3 次），由 cypher_retry_count 计数器控制。

    :param state: 当前工作流状态，需包含 is_all_validate_cypher、cypher_query、
                  cypher_retry_count 字段
    :return:      下一节点的名称，为 "run_cypher_node"、"generate_neo4j_cypher_node"
                  或 "neo4j_answer_generate_node" 之一
    """
    # 情况 1：Cypher 全部校验通过且非空 → 执行查询
    if state.get("is_all_validate_cypher") and state.get("cypher_query"):
        print("✅ Cypher 校验通过，进入执行节点")
        return "run_cypher_node"

    # 情况 2：Cypher 列表为空（通常因实体匹配失败导致）
    # 直接走兜底回答，不浪费 LLM 调用做无意义的空查询重试
    if not state.get("cypher_query"):
        print("⚠️ Cypher 查询列表为空，直接进入兜底回答节点")
        return "neo4j_answer_generate_node"

    # 情况 3 和 4：根据重试次数决定是修正还是放弃
    retry_count = state.get("cypher_retry_count", 0)
    if retry_count < MAX_CYPHER_RETRIES:
        # 未达重试上限 → 回传给 LLM 修正 Cypher
        print(f"🔄 Cypher 校验未通过，返回生成节点修正（第 {retry_count + 1}/{MAX_CYPHER_RETRIES} 次重试）")
        return "generate_neo4j_cypher_node"
    else:
        # 已达重试上限 → 放弃修正，走兜底回答
        print(f"⚠️ Cypher 校验已重试 {MAX_CYPHER_RETRIES} 次仍未通过，放弃修正，直接生成回答")
        return "neo4j_answer_generate_node"


# ============================================================
# 构建 LangGraph 工作流
# ============================================================


def build_workflow() -> StateGraph:
    """
    构建完整的 LangGraph 工作流图（StateGraph）。

    该函数完成以下工作：
      1. 创建以 AgentState 为状态类型的 StateGraph 实例
      2. 注册全部 14 个节点到图中
      3. 添加边：普通边（固定流转）和条件边（根据状态动态路由）

    返回的 StateGraph 尚未编译（未调用 .compile()），调用方可根据需要
    进一步定制（如替换节点函数进行 mock 测试）后再编译。

    节点注册清单（共 14 个）：

      小红书发布链路（6 个）：
        - xiaohongshu_publish_intent_node  意图识别（统一入口）
        - text_generate_node               文案生成（标题 + 正文）
        - image_generator_node             配图生成（即梦 AI）
        - check_text_image_node            内容完整性校验
        - auto_publish_xiaohongshu_node    自动发布（Playwright）
        - generate_markdown_node           Markdown 结果输出

      中医知识图谱问答链路（7 个）：
        - zhongyi_intent_node              中医意图识别（RoBERTa+LoRA）
        - extract_entity_from_user_input_node  实体抽取（LLM）
        - match_entity_from_neo4j_node         FAISS 实体匹配
        - generate_neo4j_cypher_node           Cypher 生成（LLM）
        - check_cypher_node                    Cypher 语法校验
        - run_cypher_node                      Neo4j 查询执行
        - neo4j_answer_generate_node           自然语言回答（LLM）

      兜底链路（1 个）：
        - llm_direct_out_node              LLM 直接回答

    边连接清单：

      START → xiaohongshu_publish_intent_node（统一入口）
      xiaohongshu_publish_intent_node → text_generate_node（小红书链路）/ zhongyi_intent_node（否）
      text_generate_node → image_generator_node
      image_generator_node → check_text_image_node
      check_text_image_node → auto_publish_xiaohongshu_node / END
      auto_publish_xiaohongshu_node → generate_markdown_node
      generate_markdown_node → END
      zhongyi_intent_node → extract_entity_from_user_input_node / llm_direct_out_node
      extract_entity_from_user_input_node → match_entity_from_neo4j_node
      match_entity_from_neo4j_node → generate_neo4j_cypher_node
      generate_neo4j_cypher_node → check_cypher_node（进入校验 → 重试回路）
      check_cypher_node → run_cypher_node / generate_neo4j_cypher_node（重试）/ neo4j_answer_generate_node（兜底）
      run_cypher_node → neo4j_answer_generate_node
      neo4j_answer_generate_node → END
      llm_direct_out_node → END

    三条主链路：

      A. 小红书发布链路（xiaohongshu_publish_intent → 是）
         xiaohongshu_publish_intent_node → text_generate_node → image_generator_node
         → check_text_image_node → auto_publish_xiaohongshu_node → generate_markdown_node → END

      B. 中医知识图谱问答链路（xiaohongshu_publish_intent → 否 → zhongyi_intent → 是）
         zhongyi_intent_node → extract_entity_from_user_input_node → match_entity_from_neo4j_node
         → generate_neo4j_cypher_node → check_cypher_node
           ├── 全部合法 → run_cypher_node → neo4j_answer_generate_node → END
           ├── 校验失败 + 未超上限 → 返回 generate_neo4j_cypher_node 重试修正
           └── 校验失败 + 已达上限 / Cypher 为空 → neo4j_answer_generate_node（LLM 兜底回答）→ END

      C. 非中医兜底链路（xiaohongshu_publish_intent → 否 → zhongyi_intent → 否）
         zhongyi_intent_node → llm_direct_out_node → END

    :return: 未编译的 StateGraph 实例
    """
    workflow = StateGraph(AgentState)

    # ==============================
    # 第 1 步：注册全部 14 个节点到图中
    # ==============================

    # —— 小红书发布链路节点（6 个） ——
    workflow.add_node("xiaohongshu_publish_intent_node", xiaohongshu_publish_intent_node)
    workflow.add_node("text_generate_node", text_generate_node)
    workflow.add_node("image_generator_node", image_generator_node)
    workflow.add_node("check_text_image_node", check_text_image_node)
    workflow.add_node("auto_publish_xiaohongshu_node", auto_publish_xiaohongshu_node)
    workflow.add_node("generate_markdown_node", generate_markdown_node)

    # —— 中医知识图谱问答链路节点（7 个） ——
    workflow.add_node("zhongyi_intent_node", zhongyi_intent_node)
    workflow.add_node("llm_direct_out_node", llm_direct_out_node)  # 兜底节点，也属于此链路
    workflow.add_node("extract_entity_from_user_input_node", extract_entity_from_user_input_node)
    workflow.add_node("match_entity_from_neo4j_node", match_entity_from_neo4j_node)
    workflow.add_node("generate_neo4j_cypher_node", generate_neo4j_cypher_node)
    workflow.add_node("check_cypher_node", check_cypher_node)
    workflow.add_node("run_cypher_node", run_cypher_node)
    workflow.add_node("neo4j_answer_generate_node", neo4j_answer_generate_node)

    # ==============================
    # 第 2 步：连接边，定义节点间的流转关系
    # ==============================

    # —— 入口 ——
    # 所有用户输入统一从 xiaohongshu_publish_intent_node 进入
    # START 是 LangGraph 内置的特殊起始节点
    workflow.add_edge(START, "xiaohongshu_publish_intent_node")

    # —— 小红书意图 → 条件分支 ——
    #   是（is_xiaohongshu_publish_intent = True）  → text_generate_node（进入小红书发布链路）
    #   否（is_xiaohongshu_publish_intent = False） → zhongyi_intent_node（进入中医意图分类）
    #   条件函数：decide_after_publish_intent
    workflow.add_conditional_edges(
        "xiaohongshu_publish_intent_node",
        decide_after_publish_intent,
        {
            "text_generate_node": "text_generate_node",
            "zhongyi_intent_node": "zhongyi_intent_node",
        },
    )

    # ==============================
    # A. 小红书发布链路
    # 节点依次串联：文案生成 → 图片生成 → 内容检查 → 发布 → Markdown 输出
    # ==============================

    # 文案生成 → 图片生成（固定边，无需条件判断）
    workflow.add_edge("text_generate_node", "image_generator_node")

    # 图片生成 → 内容完整性检查（固定边）
    workflow.add_edge("image_generator_node", "check_text_image_node")

    # 完整性检查 → 条件分支
    #   可以发布（is_can_publish_xiaohongshu = True）  → auto_publish_xiaohongshu_node
    #   不可以（is_can_publish_xiaohongshu = False）    → END（直接终止）
    #   条件函数：decide_after_check_text_image
    workflow.add_conditional_edges(
        "check_text_image_node",
        decide_after_check_text_image,
        {
            "auto_publish_xiaohongshu_node": "auto_publish_xiaohongshu_node",
            END: END,
        },
    )

    # 自动发布 → 生成 Markdown 结果页（固定边）
    workflow.add_edge("auto_publish_xiaohongshu_node", "generate_markdown_node")

    # Markdown 输出 → 结束（固定边）
    workflow.add_edge("generate_markdown_node", END)

    # ==============================
    # B. 中医知识图谱问答链路
    # 节点依次串联：中医意图 → 实体抽取 → FAISS 匹配 → Cypher 生成 → 校验（带重试回路） → 执行 → 回答
    # ==============================

    # 中医意图识别 → 条件分支
    #   是（中医相关） → extract_entity_from_user_input_node（进入知识图谱问答链路）
    #   否（非中医）   → llm_direct_out_node（LLM 直接回答兜底）
    #   条件函数：decide_after_zhongyi_intent
    workflow.add_conditional_edges(
        "zhongyi_intent_node",
        decide_after_zhongyi_intent,
        {
            "extract_entity_from_user_input_node": "extract_entity_from_user_input_node",
            "llm_direct_out_node": "llm_direct_out_node",
        },
    )

    # 实体抽取 → 实体匹配（固定边）
    # extract_entity_from_user_input_node 产出 user_input_effects/diseases/symptoms 等字段，
    # match_entity_from_neo4j_node 读取这些字段进行 FAISS 向量检索匹配
    workflow.add_edge("extract_entity_from_user_input_node", "match_entity_from_neo4j_node")

    # 实体匹配 → 生成 Cypher 查询语句（固定边）
    # match_entity_from_neo4j_node 产出 matched_effects/diseases/symptoms 等字段，
    # generate_neo4j_cypher_node 基于匹配实体生成 Cypher 查询
    workflow.add_edge("match_entity_from_neo4j_node", "generate_neo4j_cypher_node")

    # Cypher 生成 → Cypher 语法校验（固定边，进入校验 → 重试回路）
    workflow.add_edge("generate_neo4j_cypher_node", "check_cypher_node")

    # Cypher 校验 → 条件分支（带自修正重试回路）
    #   全部通过           → run_cypher_node（执行 Cypher，结果存入 cypher_results）
    #   未通过 + 未超上限  → generate_neo4j_cypher_node（带着 cypher_validation_feedback 回传给 LLM 修正）
    #   未通过 + 已达上限  → neo4j_answer_generate_node（放弃重试，LLM 兜底回答）
    #   条件函数：decide_after_check_cypher
    #
    #   重试回路示意：
    #     check_cypher ──(未通过+可重试)──→ generate_neo4j_cypher ──→ check_cypher ──→ ...
    #     最多循环 MAX_CYPHER_RETRIES 次后，强制走 neo4j_answer_generate_node 兜底
    workflow.add_conditional_edges(
        "check_cypher_node",
        decide_after_check_cypher,
        {
            "run_cypher_node": "run_cypher_node",
            "generate_neo4j_cypher_node": "generate_neo4j_cypher_node",
            "neo4j_answer_generate_node": "neo4j_answer_generate_node",
        },
    )

    # 执行 Cypher → 生成自然语言回答（固定边）
    # run_cypher_node 产出 cypher_results 查询结果列表，
    # neo4j_answer_generate_node 将其转换为自然语言回答并写入 neo4j_answer 和 output
    workflow.add_edge("run_cypher_node", "neo4j_answer_generate_node")

    # 自然语言回答 → 结束（固定边）
    workflow.add_edge("neo4j_answer_generate_node", END)

    # ==============================
    # C. 非中医兜底链路
    # 非中医问题直接由 LLM 回答，不经过知识图谱查询
    # ==============================

    # LLM 直接回答 → 结束（固定边）
    # llm_direct_out_node 将回答写入 direct_out 和 output 字段
    workflow.add_edge("llm_direct_out_node", END)

    # 返回未编译的 StateGraph，调用方可根据需要进一步定制后再编译
    return workflow


# ============================================================
# 编译图（模块级别，方便直接导入使用）
# ============================================================
# 在模块加载时预编译工作流图，避免每次调用时重复编译开销。
# 如需 mock 测试，可在 __main__ 中重新调用 build_workflow().compile() 获得新实例。

graph = build_workflow().compile()


# ============================================================
# 同步运行入口
# ============================================================

def run_workflow(user_input: str, messages: list = None) -> AgentState:
    """
    同步运行 LangGraph 工作流。

    内部调用 graph.invoke() 执行完整的同步工作流，返回最终的 AgentState。
    适用于脚本、测试等同步场景。

    :param user_input: 用户输入的文本内容
    :param messages:   对话历史消息列表（可选），
                       格式为 [{"role": "user", "content": "..."},
                              {"role": "assistant", "content": "..."}]
                       传入 None 或空列表均视为新对话
    :return: 工作流执行完毕后的最终 AgentState，可通过 result["output"] 获取最终回答
    """
    initial_state = make_initial_state(user_input, messages)
    result = graph.invoke(initial_state)
    return result


# ============================================================
# 异步运行入口（FastAPI 专用）
# ============================================================

async def zhongyi_response(user_input: str, messages: list = None) -> str:
    """
    FastAPI 异步入口：异步执行 LangGraph 工作流，返回最终输出字符串。

    与 run_workflow() 的区别：
      - 使用 graph.ainvoke() 实现非阻塞异步执行，适配 FastAPI 的 async handler
      - 避免同步 invoke() 阻塞事件循环影响并发能力
      - 直接返回 output 字符串而非整个 AgentState，减少冗余数据传输

    典型用法（FastAPI 路由）：
      @app.post("/chat")
      async def chat(request: ChatRequest):
          answer = await zhongyi_response(request.message, request.history)
          return {"answer": answer}

    :param user_input: 用户输入的文本内容
    :param messages:   对话历史消息列表（可选），
                       格式为 [{"role": "user", "content": "..."},
                              {"role": "assistant", "content": "..."}]
    :return: 工作流最终的 output 字符串（即最终回答文本）
    """
    initial_state = make_initial_state(user_input, messages)
    result = await graph.ainvoke(initial_state)
    return result["output"]


# ============================================================
# 集成测试（仅在直接运行本模块时执行）
# ============================================================
# 覆盖两条主链路：
#   Test 1 — 中医知识图谱问答链路：用户问诊 → 实体抽取 → FAISS 匹配 → Cypher 生成
#           → Neo4j 查询 → 自然语言回答
#   Test 2 — 小红书发布链路：用户请求发布 → 文案生成 → 图片生成 → 内容校验
#           → 自动发布 → Markdown 结果输出
#
# 注意事项：
#   - 测试使用 unittest.mock.patch 对 LLM / Neo4j / FAISS / 即梦 AI / Playwright
#     等外部依赖进行 mock，确保测试可离线运行且结果可复现
#   - 如果 FAISS 索引文件存在，实体匹配节点会返回真实的语义匹配结果；
#     如果不存在，测试会 mock FAISS 匹配以保障可运行性
#   - 意图识别节点（zhongyi_intent_node）已改用 RoBERTa+LoRA 本地模型，
#     因此测试中 mock predict_tcm_intent 函数而非 LLM
#   - 小红书发布意图节点（xiaohongshu_publish_intent_node）优先使用 fastText 本地模型，
#     因此只在 fastText 不可用时才走 LLM 兜底
# ============================================================

if __name__ == "__main__":
    import json
    import os
    from unittest.mock import patch, MagicMock

    # ================================================================
    # 工具函数
    # ================================================================

    def _make_llm_response(content: str):
        """
        构造模拟的 LLM 响应对象。

        兼容 langchain_core.messages 的 content 属性，
        使得 mock 的 ChatOpenAI.invoke() 返回值可以被下游节点正常读取。

        :param content: 模拟的 LLM 返回文本内容
        :return:        MagicMock 对象，其 .content 属性为传入的 content 值
        """
        mock_msg = MagicMock()
        mock_msg.content = content
        mock_response = MagicMock()
        mock_response.content = mock_msg.content
        return mock_response

    # ================================================================
    # Test 1: 中医知识图谱问答链路
    # ================================================================
    #   完整路由路径：
    #     START
    #       → xiaohongshu_publish_intent_node  （意图判断：非小红书发布意图）
    #       → zhongyi_intent_node              （中医意图识别：是中医问题）
    #       → extract_entity_from_user_input_node  （LLM 实体抽取）
    #       → match_entity_from_neo4j_node         （FAISS 向量匹配）
    #       → generate_neo4j_cypher_node           （LLM 生成 Cypher）
    #       → check_cypher_node                    （Cypher 语法校验）
    #       → run_cypher_node                      （Neo4j 执行查询）
    #       → neo4j_answer_generate_node           （LLM 生成自然语言回答）
    #       → END
    #
    #   依赖 mock：
    #     - langchain_openai.ChatOpenAI.invoke   → 模拟 LLM 返回（按调用顺序排列）
    #     - zhongyi_intent_node.predict_tcm_intent → 模拟为返回 True（中医问题）
    #     - match_entity_from_neo4j_node.batch_search_similar_entities → 模拟 FAISS 匹配结果
    #     - common.neo4j_manager.neo4j_client.valid_cypher → 模拟为校验通过
    #     - common.neo4j_manager.neo4j_client.run_cypher    → 模拟 Neo4j 查询结果
    # ================================================================

    print("\n" + "=" * 70)
    print("\U0001f9ea Test 1: 中医知识图谱问答链路")
    print("=" * 70)

    tcm_input = "我最近拉肚子、恶心想吐，有什么中药方剂可以缓解症状？"
    print(f"\U0001f4dd 用户输入: {tcm_input}")

    # — 准备 LLM mock 响应（按工作流执行时的 LLM 调用顺序排列） —
    # 注意：zhongyi_intent_node 已改用 RoBERTa+LoRA 本地模型，不再调用 LLM，
    #       因此 LLM mock 中不再包含中医意图识别的调用。
    #
    # 第1次 LLM 调用：xiaohongshu_publish_intent_node → 返回"否"
    #   （仅在 fastText 模型不可用时触发 LLM 兜底）
    llm_response_no_publish = _make_llm_response("否")

    # 第2次 LLM 调用：extract_entity_from_user_input_node → 返回实体 JSON
    #   LLM 从用户输入中抽取中医相关实体（症状、方剂、药材、功效等）
    llm_response_entities = _make_llm_response(json.dumps({
        "symptoms": ["腹泻", "恶心", "呕吐"],
        "diseases": [],
        "formulas": ["藿香正气散"],
        "herbs": ["藿香", "陈皮", "白术"],
        "effects": ["止泻", "止呕", "化湿"],
        "sources": []
    }, ensure_ascii=False))

    # 第3次 LLM 调用：generate_neo4j_cypher_node → 返回 Cypher JSON
    #   LLM 基于匹配到的实体生成 Neo4j Cypher 查询语句
    llm_response_cypher = _make_llm_response(json.dumps({
        "cypher_queries": [
            "MATCH (f:Formula {name: '藿香正气散'})-[:HAS_INGREDIENT]->(h:Herb) RETURN f.name, h.name",
            "MATCH (f:Formula {name: '藿香正气散'})-[:HAS_EFFECT]->(e:Effect) RETURN e.name",
            "MATCH (h:Herb)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['止泻', '止呕', '化湿'] RETURN h.name, e.name",
        ],
        "reasoning": "查询藿香正气散的组成、功效，以及具有止泻止呕功效的药材"
    }, ensure_ascii=False))

    # 第4次 LLM 调用：neo4j_answer_generate_node → 返回自然语言回答
    #   LLM 将 Cypher 查询结果整合为流畅的中文自然语言回答
    llm_response_answer = _make_llm_response(
        "根据中医知识图谱查询结果，藿香正气散是治疗您所述症状（腹泻、恶心、呕吐）的常用方剂。"
        "其主要由藿香、陈皮、白术等药材组成，具有化湿止泻、理气和中的功效。"
        "此外，藿香、白术等药材也具有止呕、止泻的作用。建议在中医师指导下使用。"
    )

    # LLM 调用顺序（必须与实际执行顺序严格一致）
    #   1. xiaohongshu_publish_intent_node（仅 fastText 不可用时）
    #   2. extract_entity_from_user_input_node
    #   3. generate_neo4j_cypher_node
    #   4. neo4j_answer_generate_node
    llm_side_effect_tcm = [
        llm_response_no_publish,   # 1. xiaohongshu_publish_intent_node（LLM 兜底）
        llm_response_entities,     # 2. extract_entity_from_user_input_node
        llm_response_cypher,       # 3. generate_neo4j_cypher_node
        llm_response_answer,       # 4. neo4j_answer_generate_node
    ]

    # — Mock FAISS 实体匹配 —
    # 模拟 batch_search_similar_entities 的行为：
    # 输入实体名称列表，返回 [(匹配名称, 相似度), ...] 列表
    def mock_batch_search(queries, top_k=3, threshold=0.85):
        """
        模拟 FAISS 批量语义检索，返回可控的匹配结果。

        :param queries:   待检索的实体名称列表
        :param top_k:     返回每个查询的 top-k 匹配（mock 中未使用）
        :param threshold: 相似度阈值（mock 中未使用）
        :return:          匹配结果列表，每个元素为 [(名称, 相似度), ...] 或空列表
        """
        # 预定义的映射表：输入实体 → [(匹配名称, 相似度)]
        # 相似度 > 0.85 视为匹配成功，实际由 match_entity_from_neo4j_node 内部判断
        mapping = {
            "腹泻": [("腹泻", 0.99)],
            "恶心": [("恶心", 0.98)],
            "呕吐": [("呕吐", 0.97)],
            "藿香正气散": [("藿香正气散", 0.99)],
            "藿香": [("藿香", 0.96)],
            "陈皮": [("陈皮", 0.97)],
            "白术": [("白术", 0.98)],
            "止泻": [("止泻", 0.95)],
            "止呕": [("止呕", 0.94)],
            "化湿": [("化湿", 0.93)],
        }
        results = []
        for q in queries:
            if q in mapping:
                results.append(mapping[q])
            else:
                results.append([])  # 未匹配，返回空列表
        return results

    # — Mock Neo4j Cypher 执行结果 —
    # 模拟 run_cypher_node 依次执行 3 条 Cypher 语句后的返回结果
    mock_cypher_results = [
        {
            "query": "MATCH (f:Formula {name: '藿香正气散'})-[:HAS_INGREDIENT]->(h:Herb) RETURN f.name, h.name",
            "result": [
                {"f.name": "藿香正气散", "h.name": "藿香"},
                {"f.name": "藿香正气散", "h.name": "陈皮"},
                {"f.name": "藿香正气散", "h.name": "白术"},
            ]
        },
        {
            "query": "MATCH (f:Formula {name: '藿香正气散'})-[:HAS_EFFECT]->(e:Effect) RETURN e.name",
            "result": [
                {"e.name": "化湿"},
                {"e.name": "止泻"},
                {"e.name": "止呕"},
            ]
        },
        {
            "query": "MATCH (h:Herb)-[:HAS_EFFECT]->(e:Effect) WHERE e.name IN ['止泻', '止呕', '化湿'] RETURN h.name, e.name",
            "result": [
                {"h.name": "藿香", "e.name": "止呕"},
                {"h.name": "白术", "e.name": "止泻"},
                {"h.name": "陈皮", "e.name": "化湿"},
            ]
        },
    ]

    # — 组装所有 mock 并运行工作流 —
    # patch.multiple 在 with 块内生效，退出时自动恢复原始实现
    with (
        # mock LLM 调用：按 llm_side_effect_tcm 顺序依次返回模拟响应
        patch("langchain_openai.ChatOpenAI.invoke", side_effect=llm_side_effect_tcm) as mock_llm,
        # mock 中医意图预测：zhongyi_intent_node 使用 RoBERTa+LoRA 本地模型，
        # 直接 mock 其 predict_tcm_intent 函数返回 True（表示是中医问题）
        patch(
            "__004__langgraph_more_nodes.node.zhongyi_intent_node.predict_tcm_intent",
            return_value=True,
        ) as mock_zhongyi_intent,
        # mock FAISS 向量检索：替换 batch_search_similar_entities 函数
        patch(
            "__004__langgraph_more_nodes.node.match_entity_from_neo4j_node.batch_search_similar_entities",
            side_effect=mock_batch_search,
        ) as mock_faiss,
        # mock Cypher 语法校验：始终返回 (True, "") 表示校验通过
        patch(
            "common.neo4j_manager.neo4j_client.valid_cypher",
            return_value=(True, ""),
        ) as mock_valid,
        # mock Cypher 执行：按顺序返回 3 条查询的结果
        patch(
            "common.neo4j_manager.neo4j_client.run_cypher",
            side_effect=[
                mock_cypher_results[0]["result"],
                mock_cypher_results[1]["result"],
                mock_cypher_results[2]["result"],
            ],
        ) as mock_run,
    ):
        result_state = run_workflow(tcm_input)

    # — 打印测试结果 —
    # 展示工作流各节点处理后的中间状态，便于验证链路正确性
    print("\n" + "-" * 50)
    print("\U0001f4ca Test 1 执行结果")
    print("-" * 50)
    print(f"  小红书发布意图:  {'✅ 是（进入发布链路）' if result_state.get('is_xiaohongshu_publish_intent') else '❌ 否（进入中医意图判断）'}")
    print(f"  中医相关问题:    {'✅ 是（进入知识图谱问答）' if result_state.get('is_zhongyi_intent') else '❌ 否（走 LLM 兜底）'}")
    print(f"  抽取症状:        {result_state.get('user_input_symptoms', [])}")
    print(f"  抽取方剂:        {result_state.get('user_input_formulas', [])}")
    print(f"  抽取药材:        {result_state.get('user_input_herbs', [])}")
    print(f"  抽取功效:        {result_state.get('user_input_effects', [])}")
    print(f"  FAISS 匹配症状:  {result_state.get('matched_symptoms', [])}")
    print(f"  FAISS 匹配方剂:  {result_state.get('matched_formulas', [])}")
    print(f"  FAISS 匹配药材:  {result_state.get('matched_herbs', [])}")
    print(f"  FAISS 匹配功效:  {result_state.get('matched_effects', [])}")
    print(f"  生成 Cypher 条数: {len(result_state.get('cypher_query', []))}")
    for i, cq in enumerate(result_state.get('cypher_query', []), 1):
        print(f"    [{i}] {cq[:100]}{'...' if len(cq) > 100 else ''}")
    print(f"  Cypher 全部校验通过: {'✅ 是' if result_state.get('is_all_validate_cypher') else '❌ 否'}")
    print(f"  Cypher 执行结果数: {len(result_state.get('cypher_results', []))}")
    print(f"  Neo4j 答案: {result_state.get('neo4j_answer', '')[:120]}...")
    print(f"  最终输出: {result_state.get('output', '')[:120]}...")
    print("-" * 50)
    print("✅ Test 1 通过：中医知识图谱问答链路完整走通")
    print("=" * 70)

    # — 断言验证 —
    # 确保每个关键节点都产生了预期输出，任一项失败即表示链路断裂
    assert result_state.get("is_xiaohongshu_publish_intent") is False, "应为非小红书发布意图"
    assert result_state.get("is_zhongyi_intent") is True, "应为中医相关问题"
    assert len(result_state.get("user_input_symptoms", [])) > 0, "应抽取到症状实体"
    assert len(result_state.get("matched_formulas", [])) > 0, "应匹配到方剂实体"
    assert len(result_state.get("cypher_query", [])) > 0, "应生成 Cypher 查询"
    assert result_state.get("is_all_validate_cypher") is True, "Cypher 应全部校验通过"
    assert len(result_state.get("cypher_results", [])) > 0, "应有 Cypher 执行结果"
    assert len(result_state.get("neo4j_answer", "")) > 0, "应生成自然语言回答"
    print("\U0001f389 所有断言验证通过！\n")

    # ================================================================
    # Test 2: 小红书发布链路
    # ================================================================
    #   完整路由路径：
    #     START
    #       → xiaohongshu_publish_intent_node  （意图判断：是小红书发布意图）
    #       → text_generate_node               （LLM 生成标题和正文）
    #       → image_generator_node             （即梦 AI 生成配图）
    #       → check_text_image_node            （内容完整性校验）
    #       → auto_publish_xiaohongshu_node    （Playwright 自动发布到小红书）
    #       → generate_markdown_node           （生成 Markdown 结果展示）
    #       → END
    #
    #   依赖 mock：
    #     - langchain_openai.ChatOpenAI.invoke                        → 模拟 LLM 返回
    #     - image_generate_node.xiaohongshu_image_generator           → 模拟图片生成（创建临时 PNG）
    #     - auto_publish_xiaohongshu_node（__main__ 命名空间中）            → 模拟发布操作
    #
    #   特殊处理：
    #     - auto_publish_xiaohongshu_node 需要 patch.object(__main__, ...)
    #       因为测试在当前模块的命名空间中运行，而 build_workflow() 中的函数引用
    #       指向的是当前模块的全局命名空间，不是原始模块的引用。
    #     - 因此需将 auto_publish_xiaohongshu_node 替换为 mock 版本后，
    #       重新调用 build_workflow().compile() 得到使用 mock 节点的新图。
    # ================================================================

    print("\n" + "=" * 70)
    print("\U0001f9ea Test 2: 小红书发布链路")
    print("=" * 70)

    xhs_input = "帮我写一篇小红书笔记，分享枸杞养生茶的做法和好处，要吸引人一点"
    print(f"\U0001f4dd 用户输入: {xhs_input}")

    # — 准备 LLM mock 响应（按工作流执行时的 LLM 调用顺序排列） —
    # 第1次 LLM 调用：xiaohongshu_publish_intent_node → 返回"是"
    llm_response_yes_publish = _make_llm_response("是")

    # 第2次 LLM 调用：text_generate_node → 返回 PydanticOutputParser 能解析的 JSON
    #   JSON 格式必须匹配 TextGenerateOutput 的 schema：{"title": "...", "content": "..."}
    xhs_title = "枸杞养生茶的3大好处，打工人必看！"
    xhs_content = (
        "今天来给大家分享一个超简单的中医养生小知识～\n\n"
        "枸杞，大家都不陌生吧？但是你真的会吃枸杞吗？\n\n"
        "\U0001f375 枸杞泡水的3大好处：\n\n"
        "1️⃣ 养肝明目\n"
        "枸杞入肝经，能滋补肝血。每天对着电脑的姐妹们，坚持喝枸杞水，眼睛会舒服很多！\n\n"
        "2️⃣ 补肾益精\n"
        "枸杞甘平，归肾经。经常熬夜、腰酸的朋友，可以试试枸杞泡水～\n\n"
        "3️⃣ 延缓衰老\n"
        "枸杞富含枸杞多糖和抗氧化成分，是天然的「抗老食材」！\n\n"
        "⚠️ 小贴士：\n"
        "• 每天10-15粒即可，不要贪多\n"
        "• 用60°C温水冲泡，不要用沸水\n"
        "• 上火期间暂时不要吃哦\n\n"
        "#中医养生 #枸杞 #养生日常 #打工人养生"
    )
    llm_response_text = _make_llm_response(json.dumps({
        "title": xhs_title,
        "content": xhs_content,
    }, ensure_ascii=False))

    # LLM 调用顺序（小红书链路比中医链路少，只有 2 次 LLM 调用）
    llm_side_effect_xhs = [
        llm_response_yes_publish,  # 1. xiaohongshu_publish_intent_node
        llm_response_text,         # 2. text_generate_node
    ]

    # — Mock 图片生成：直接创建一个临时图片文件 —
    # 替代即梦 AI 的真实图片生成，避免网络调用和 API 消耗
    def mock_image_generator(_title, _content):
        """
        模拟图片生成器，返回一个真实存在的临时 PNG 文件路径。

        替代即梦 AI 的 xiaohongshu_image_generator 函数，
        创建一个最小的 1x1 像素 PNG 文件作为"生成的配图"。

        :param _title:   小红书标题（mock 中未使用）
        :param _content: 小红书正文（mock 中未使用）
        :return:         临时 PNG 文件的绝对路径
        """
        tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "picture")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_file = os.path.join(tmp_dir, "test_xhs_mock_image.png")
        # 创建一个最小的 1x1 PNG 文件（合法的 PNG 二进制数据）
        with open(tmp_file, "wb") as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
        return tmp_file

    # — Mock 自动发布节点（避免启动真实浏览器进行 Playwright 自动化） —
    def mock_auto_publish(state):
        """
        模拟小红书自动发布，直接设置发布成功状态。

        替换真实的 auto_publish_xiaohongshu_node 函数，
        避免在测试环境中启动 Playwright 浏览器进行真实发布操作。

        :param state: 当前工作流状态
        :return:      更新后的状态（标记发布成功）
        """
        state["is_can_publish_xiaohongshu"] = True
        state["xiaohongshu_tcm_tip"] = "发布成功（\U0001f9ea 测试模式：未实际发布到小红书）"
        print("\U0001f9ea Mock 发布: 模拟发布成功（跳过真实浏览器操作）")
        return state

    # — 组装 mock 并重新编译图 —
    # 注意：当前脚本以 __main__ 运行，所有函数引用在 __main__ 命名空间中。
    #       patch.object(__main__, ...) 可以精准替换 build_workflow() 将要使用的函数引用，
    #       重新调用 build_workflow().compile() 即可得到使用 mock 节点的新图。
    _main_module = sys.modules["__main__"]

    with (
        # mock LLM 调用：按 llm_side_effect_xhs 顺序依次返回模拟响应
        patch("langchain_openai.ChatOpenAI.invoke", side_effect=llm_side_effect_xhs) as mock_llm_xhs,
        # mock 图片生成：创建临时 PNG 文件替代即梦 AI 的真实图片生成
        patch(
            "__004__langgraph_more_nodes.node.image_generate_node.xiaohongshu_image_generator",
            side_effect=mock_image_generator,
        ) as mock_img,
        # mock 自动发布：patch.object 替换 __main__ 中的函数引用
        # 因为 build_workflow() 从当前模块的全局命名空间获取 auto_publish_xiaohongshu_node
        patch.object(
            _main_module, "auto_publish_xiaohongshu_node", mock_auto_publish,
        ),
    ):
        # 重新编译图：build_workflow() 会使用 mock 后的 auto_publish_xiaohongshu_node
        # 这是必要的，因为模块级别的 graph 已经在 mock 前编译好了
        test_workflow = build_workflow()
        test_graph = test_workflow.compile()
        initial_state = make_initial_state(xhs_input, [])
        result_state = test_graph.invoke(initial_state)

    # — 清理测试图片 —
    # 测试完成后删除临时创建的 mock PNG 文件，避免污染本地文件系统
    tmp_image = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "picture", "test_xhs_mock_image.png")
    if os.path.exists(tmp_image):
        os.remove(tmp_image)

    # — 打印测试结果 —
    # 展示小红书发布链路各节点的输出，便于验证内容生成和发布流程
    print("\n" + "-" * 50)
    print("\U0001f4ca Test 2 执行结果")
    print("-" * 50)
    print(f"  小红书发布意图:  {'✅ 是（进入发布链路）' if result_state.get('is_xiaohongshu_publish_intent') else '❌ 否'}")
    print(f"  生成标题:        {result_state.get('xiaohongshu_tcm_post_title', '')}")
    print(f"  生成内容长度:    {len(result_state.get('xiaohongshu_tcm_post_content', ''))} 字")
    print(f"  内容预览:        {result_state.get('xiaohongshu_tcm_post_content', '')[:60]}...")
    print(f"  图片路径列表:    {result_state.get('xiaohongshu_image_path_list', [])}")
    print(f"  图片提示:        {result_state.get('xiaohongshu_tcm_tip', '')}")
    print(f"  内容完整性检查:  {'✅ 可以发布' if result_state.get('is_can_publish_xiaohongshu') else '❌ 不完整'}")
    print(f"  发布状态:        {result_state.get('xiaohongshu_tcm_tip', '')}")
    markdown_out = result_state.get('xiaohongshu_markdown_output', '')
    print(f"  Markdown 输出:   {'✅ 已生成' if markdown_out else '❌ 未生成'} ({len(markdown_out)} 字符)")
    print(f"  最终输出长度:    {len(result_state.get('output', ''))} 字符")
    print("-" * 50)
    print("✅ Test 2 通过：小红书发布链路完整走通")
    print("=" * 70)

    # — 断言验证 —
    # 确保小红书发布链路每个关键步骤都产生了预期结果
    assert result_state.get("is_xiaohongshu_publish_intent") is True, "应为小红书发布意图"
    assert len(result_state.get("xiaohongshu_tcm_post_title", "")) > 0, "应生成标题"
    assert len(result_state.get("xiaohongshu_tcm_post_content", "")) > 0, "应生成内容"
    assert len(result_state.get("xiaohongshu_image_path_list", [])) > 0, "应有图片路径"
    assert result_state.get("is_can_publish_xiaohongshu") is True, "应可以发布"
    assert len(result_state.get("xiaohongshu_markdown_output", "")) > 0, "应生成 Markdown 输出"
    print("\U0001f389 所有断言验证通过！\n")

    # ================================================================
    # 测试总结
    # ================================================================
    print("=" * 70)
    print("\U0001f3c1 全部集成测试完成")
    print("=" * 70)
    print("  ✅ Test 1 — 中医知识图谱问答链路：START → 意图识别 → 实体抽取 → FAISS → Cypher → Neo4j → 回答 → END")
    print("  ✅ Test 2 — 小红书发布链路：START → 意图识别 → 文案生成 → 图片生成 → 校验 → 发布 → Markdown → END")
    print("=" * 70)
