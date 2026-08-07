"""
小红书发布意图识别节点（fastText 版本）
============================================

角色定位:
    LangGraph 工作流中的"路由分支"节点。位于用户输入解析之后，
    负责判断用户是否有在小红书平台发布笔记/内容的意图。
    根据判断结果，LangGraph 会将请求分流到"中医问答链路"或"小红书发布链路"。

核心功能:
    1. 优先使用本地 fastText 模型进行意图二分类（发布/非发布）
       - 速度快（毫秒级推理）
       - 零 API 成本
       - 离线可用
    2. 若 fastText 模型文件不存在，自动降级为 LLM 调用（兜底策略）
    3. 若 fastText 推理过程中出现其他异常（如依赖缺失），也降级为 LLM

技术选型理由:
    fastText 是 Facebook 开源的高效文本分类库，使用 n-gram 特征和
    hierarchical softmax，在 CPU 上即可达到毫秒级推理速度，
    非常适合意图识别这种轻量级文本分类任务。

模型文件:
    __007__fine_tune/model/fasttext_xhs_intent.bin

训练脚本:
    __007__fine_tune/fasttext_xiaohongshu_recognition/train_fasttext_intent.py

依赖:
    - fastText (本地模型推理)
    - jieba (中文分词)
    - common.llm.my_llm (LLM 兜底)
    - AgentState: LangGraph 全局状态
"""

from __004__langgraph_more_nodes.agent_state import AgentState


def xiaohongshu_publish_intent_node(state: AgentState):
    """
    识别用户输入是否具有小红书发布意图。

    优先使用本地 fastText 模型进行推理（速度快、零 API 成本），
    若 fastText 模型文件不存在则自动降级为 LLM 调用。

    参数:
        state (AgentState): LangGraph 全局状态，包含:
            - input: 用户原始输入文本

    返回:
        AgentState: 更新后的状态，新增字段:
            - is_xiaohongshu_publish_intent: bool
                True  → 用户有发布小红书笔记的意图，后续走发布链路
                False → 用户无发布意图，走中医问答链路

    写入 AgentState:
        - is_xiaohongshu_publish_intent: True/False
    """
    print("🔍 开始识别是否有发小红书的意图（fastText）")

    user_input = state["input"]

    try:
        # —— 策略1: 优先使用 fastText 本地模型 ——
        # fastText 推理速度快（< 10ms），零 API 成本，适合高频调用
        is_publish, confidence = _predict_with_fasttext(user_input)
        state["is_xiaohongshu_publish_intent"] = is_publish
        label = "发布" if is_publish else "非发布"
        print(f"🔍 小红书意图识别结果: [{label}] 置信度: {confidence:.4f}")

    except FileNotFoundError as e:
        # —— 策略2: fastText 模型文件不存在，降级为 LLM ——
        # 可能原因: 模型尚未训练、模型文件被删除、路径配置错误
        print(f"⚠️ fastText 模型不可用: {e}")
        print("   降级为 LLM 调用...")
        state = _predict_with_llm(state, user_input)

    except Exception as e:
        # —— 策略3: fastText 其他异常（如 jieba 分词库未安装），降级为 LLM ——
        # 可能原因: 依赖缺失、模型文件损坏、内存不足等
        print(f"❌ fastText 推理异常: {e}")
        print("   降级为 LLM 调用...")
        state = _predict_with_llm(state, user_input)

    print("✅ 完成识别是否有发小红书的意图")
    return state


# ============================================================
# fastText 推理
# ============================================================

def _predict_with_fasttext(user_input: str):
    """
    使用 fastText 模型进行意图识别。

    内部调用训练好的 fastText 预测器，对用户输入进行二分类:
      - __label__publish:    有发布意图
      - __label__not_publish: 无发布意图

    参数:
        user_input (str): 用户原始输入文本

    返回:
        tuple: (is_publish: bool, confidence: float)
            - is_publish: True 表示有发布意图
            - confidence: fastText 模型输出的预测置信度 (0.0 ~ 1.0)

    异常:
        FileNotFoundError: fastText 模型文件 (.bin) 不存在
        其他异常: 推理过程中出现的依赖或运行时错误
    """
    from __007__fine_tune.fasttext_xiaohongshu_recognition.fasttext_predictor import (
        predict_xhs_intent,
    )
    return predict_xhs_intent(user_input)


# ============================================================
# LLM 兜底推理（保留原有逻辑）
# ============================================================

def _predict_with_llm(state: AgentState, user_input: str) -> AgentState:
    """
    使用 LLM 进行意图识别（兜底策略）。

    当 fastText 模型不可用时调用，通过 few-shot prompt 让 LLM
    判断用户是否有小红书发布意图。

    参数:
        state (AgentState): 当前 LangGraph 状态
        user_input (str): 用户原始输入文本

    返回:
        AgentState: 更新后的状态，设置 is_xiaohongshu_publish_intent 字段

    容错设计:
        - LLM 返回"是"→ 判定为有发布意图
        - LLM 返回"否/不/不是/非/无/没有"→ 判定为无发布意图
        - LLM 返回无法解析的内容 → 保守处理，默认视为非发布意图（走中医问答）
        - LLM 调用异常 → 保守处理，默认视为非发布意图（走中医问答）
    """
    from langchain_core.messages import HumanMessage
    from common.llm import my_llm

    # 构建意图判断 prompt: 用 few-shot 示例 + 明确规则引导 LLM 输出
    prompt = f"""你是一个意图分类器，判断用户是否有在"小红书平台发笔记/发内容"的意图。

【判断规则】
- 用户明确提到"发小红书"、"写一篇小红书"、"发布笔记"、"帮我写一篇帖子"等 → 是
- 用户只是询问中医知识、描述症状、求医问药，没有提到发布或分享 → 否
- 用户想分享养生经验、中医知识到小红书平台 → 是
- 用户仅是日常聊天、提问、求助（不含发布意图） → 否

---
用户输入：{user_input}

请回答（只能输出一个字，是或否）："""

    try:
        # 调用 LLM 进行意图分类（非流式，只需要最终结果）
        response = my_llm.invoke([HumanMessage(content=prompt)])
        model_answer = response.content.strip()
        print(f"🔍 小红书意图识别原始输出(LLM): '{model_answer}'")

        # 解析 LLM 输出: 先检测否定词，避免"不是"误匹配"是"
        if model_answer.startswith("否") or model_answer in ("不", "不是", "非", "无", "没有"):
            state["is_xiaohongshu_publish_intent"] = False
        elif "是" in model_answer:
            state["is_xiaohongshu_publish_intent"] = True
        else:
            # 无法解析时默认不发布，走中医问答链路（保守策略）
            print(f"⚠️ 小红书意图识别输出无法解析: '{model_answer}'，默认视为非发布意图")
            state["is_xiaohongshu_publish_intent"] = False
    except Exception as e:
        # LLM 调用异常时的容错处理
        print(f"❌ 小红书发布意图识别 LLM 调用失败: {e}")
        # LLM 不可用时保守处理：当作非小红书意图，走中医问答链路
        state["is_xiaohongshu_publish_intent"] = False

    return state


# ============================================================
# 测试代码
# ============================================================

if __name__ == '__main__':
    test_cases = [
        "帮我写一篇小红书笔记，分享枸杞养生茶的做法",  # 明确发布意图
        "感冒了吃什么中药",                           # 中医咨询（无发布意图）
        "我要发小红书，内容是艾灸养生",               # 明确发布意图
        "四君子汤由哪些药材组成",                     # 中医知识问答（无发布意图）
        "写一篇科普帖发小红书上",                      # 明确发布意图
        "劳动仲裁怎么申请",                           # 完全非中医、非发布
        "帮我写一篇养生分享",         # 隐式发布意图（需模型推理）
        "最近失眠严重中医有什么办法",  # 症状咨询（无发布意图）
    ]

    print("=" * 60)
    print("🧪 小红书发布意图识别测试")
    print("=" * 60)

    for text in test_cases:
        state = AgentState(input=text)
        result = xiaohongshu_publish_intent_node(state=state)
        label = "发布" if result["is_xiaohongshu_publish_intent"] else "非发布"
        print(f"  [{label}] {text}")

    print("=" * 60)
