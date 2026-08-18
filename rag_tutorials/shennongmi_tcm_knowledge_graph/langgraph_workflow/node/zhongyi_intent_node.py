"""
LangGraph 节点：中医意图识别。

本节点是整个 TCM 知识图谱问答链路的第一道闸门。它使用 LoRA 微调后的
Chinese-RoBERTa-wwm-ext 模型对用户输入进行二分类，判断是否属于中医相关问题。

工作流中的位置：
    用户输入 → [本节点] → 是中医问题 → 实体抽取 → ... → 知识图谱问答
                        → 非中医问题 → LLM 兜底回答

技术选型理由：
    - 相比 LLM prompt 方案，微调模型在 4000 条标注数据上训练，
      响应更快（毫秒级）、成本更低（无需 API token）、
      结果稳定可复现（不依赖外部 API 可用性）、准确率更高。
    - 当模型加载失败或推理异常时，保守处理为非中医问题，
      交由 LLM 兜底链路给出有用回复，避免静默失败影响用户体验。
"""

from langgraph_workflow.agent_state import AgentState
from langgraph_workflow.tcm_predictor import (
    predict_tcm_intent,
)


def zhongyi_intent_node(state: AgentState):
    """
    中医意图识别节点。

    使用 LoRA 微调后的 Chinese-RoBERTa-wwm-ext 模型进行二分类，
    判断用户输入是否与中医相关。

    相比原先基于 LLM prompt 的方案，微调模型具备以下优势:
        - 响应速度: 本地模型推理毫秒级，无需等待 API 调用
        - 稳定性:   不受 LLM API 限流/波动影响，结果可复现
        - 成本:     无需消耗 API token
        - 准确率:   在 4000 条中医意图标注数据上微调，更贴近业务场景

    Args:
        state: AgentState，其中 input 字段为用户输入文本

    Returns:
        更新后的 AgentState，其中 is_zhongyi_intent 字段被设置为:
            - True  → 中医相关问题，走知识图谱问答链路
            - False → 非中医问题，走 LLM 兜底回答链路
    """
    # 阶段一：获取用户输入
    print("开始识别是否是中医的意图识别")
    user_input = state["input"]

    try:
        # 阶段二：调用 RoBERTa+LoRA 微调模型进行推理
        # predict_tcm_intent 内部会加载模型并进行前向推理，返回布尔值
        is_zhongyi = predict_tcm_intent(user_input)
        # 将识别结果写入 state，供下游路由节点判断走哪条链路
        state["is_zhongyi_intent"] = is_zhongyi
        print(f"🔍 中医意图识别结果（RoBERTa+LoRA）: {'是（中医）' if is_zhongyi else '否（非中医）'}")
    except Exception as e:
        # 阶段三（兜底）：模型不可用时保守处理
        print(f"❌ 中医意图识别 RoBERTa 模型调用失败: {e}")
        # 模型不可用时保守处理：当作非中医问题，走 LLM 兜底回答
        # 这样至少能给出有用的回复，而不是静默失败
        state["is_zhongyi_intent"] = False

    print("完成识别是否是中医的意图识别")
    return state
