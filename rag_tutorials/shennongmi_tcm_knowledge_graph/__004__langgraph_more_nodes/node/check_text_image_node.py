"""
内容完整性校验节点（发布守门人）
=====================================

角色定位:
    LangGraph 小红书发布链路的"守门人"节点。位于文案生成和图片生成之后、
    自动发布之前，负责校验发布所需的全部内容是否齐全有效。
    只有通过本节点校验的请求才能进入 auto_publish_xiaohongshu_node。

核心功能:
    1. 校验标题字段是否非空（含纯空格检测）
    2. 校验正文内容是否非空
    3. 校验图片路径列表是否非空
    4. 校验图片文件是否真实存在于文件系统
    5. 传播上游错误信息（如图片生成失败的详细原因）

校验逻辑:
    按优先级依次检查，一旦某项不满足条件立即短路返回失败:
      标题缺失 → 返回失败
      内容缺失 → 返回失败
      图片列表为空 → 返回失败（含上游错误传播）
      图片文件不存在 → 返回失败
      全部通过 → is_can_publish_xiaohongshu = True

上游错误传播机制:
    当检测到图片缺失时，会检查 xiaohongshu_tcm_tip 中是否包含
    上游节点的错误详情（如图片生成 API 失败原因），
    并将真实原因合并到提示信息中，便于用户了解根因。

数据流向:
    text_generate_node → image_generate_node → check_text_image_node
                                                    ↓ (校验通过)
                                        auto_publish_xiaohongshu_node
"""

import os

from __004__langgraph_more_nodes.agent_state import AgentState


def check_text_image_node(state: AgentState) -> AgentState:
    """
    检查是否可以发布小红书：校验标题、正文、图片是否齐全，且图片文件真实存在。

    本节点是小红书发布前的最后一道校验关卡，采用短路返回策略:
    一旦发现任何内容不满足条件，立即设置 is_can_publish_xiaohongshu=False
    并写入失败的 xiaohongshu_tcm_tip，终止发布流程。

    参数:
        state (AgentState): LangGraph 全局状态，包含:
            - xiaohongshu_tcm_post_title: 帖子标题（可能为空）
            - xiaohongshu_tcm_post_content: 帖子正文（可能为空）
            - xiaohongshu_image_path_list: 图片路径列表（可能为空）
            - xiaohongshu_tcm_tip: 上游节点的提示信息（用于错误传播）

    返回:
        AgentState: 更新后的状态，新增/修改字段:
            - is_can_publish_xiaohongshu: True（可发布）/ False（不可发布）
            - xiaohongshu_tcm_tip: 校验结果或失败原因
            - output: 失败时的错误提示（同步到 output 字段）
    """
    title = state.get("xiaohongshu_tcm_post_title", "").strip()
    content = state.get("xiaohongshu_tcm_post_content", "").strip()
    image_path_list = state.get("xiaohongshu_image_path_list", [])
    # 🔧 检查上游节点是否已有错误（如图片生成失败）
    # 如果上游 node 已写入错误信息，在下游校验失败时一并传播
    upstream_tip = state.get("xiaohongshu_tcm_tip", "")

    # —— 校验1: 标题非空（含纯空格检测） ——
    if not title:
        state["is_can_publish_xiaohongshu"] = False
        state["xiaohongshu_tcm_tip"] = "发布小红书失败，标题缺失！"
        state["output"] = state["xiaohongshu_tcm_tip"]
        return state

    # —— 校验2: 正文非空 ——
    if not content:
        state["is_can_publish_xiaohongshu"] = False
        state["xiaohongshu_tcm_tip"] = "发布小红书失败，内容缺失！"
        state["output"] = state["xiaohongshu_tcm_tip"]
        return state

    # —— 校验3: 图片路径列表非空 ——
    if not image_path_list:
        state["is_can_publish_xiaohongshu"] = False
        # 如果上游已有错误详情（如图片生成失败），在输出中附带原始错误
        # 例如: "发布小红书失败，图片缺失！（原因: 图片生成失败: API调用超时）"
        if upstream_tip and "失败" in upstream_tip:
            state["xiaohongshu_tcm_tip"] = f"发布小红书失败，图片缺失！（原因: {upstream_tip}）"
        else:
            state["xiaohongshu_tcm_tip"] = "发布小红书失败，图片缺失！"
        state["output"] = state["xiaohongshu_tcm_tip"]
        return state

    # —— 校验4: 图片文件真实存在于文件系统 ——
    # 遍历图片路径列表，检查每张图片是否真实存在（os.path.isfile）
    missing_images = [p for p in image_path_list if not os.path.isfile(p)]
    if missing_images:
        state["is_can_publish_xiaohongshu"] = False
        state["xiaohongshu_tcm_tip"] = f"发布小红书失败，以下图片文件不存在: {', '.join(missing_images)}"
        state["output"] = state["xiaohongshu_tcm_tip"]
        return state

    # —— 全部校验通过 ——
    # 代码能运行到这里，证明标题、内容、图片都是完整的，可以发布
    state["is_can_publish_xiaohongshu"] = True
    return state


if __name__ == "__main__":
    # ================================================================
    # 单元测试: 覆盖各种边界情况
    # ================================================================

    # 测试1：全部字段齐全，应该可以发布
    state1: AgentState = {
        "xiaohongshu_tcm_post_title": "测试标题",
        "xiaohongshu_tcm_post_content": "测试内容",
        "xiaohongshu_image_path_list": ["image1.png", "image2.png"],
    }
    result1 = check_text_image_node(state1)
    print("测试1 - 全部齐全:")
    print(f"  is_can_publish_xiaohongshu: {result1['is_can_publish_xiaohongshu']}")
    print(f"  xiaohongshu_tcm_tip: {result1.get('xiaohongshu_tcm_tip', '(无)')}")
    print()

    # 测试2：缺少标题
    state2: AgentState = {
        "xiaohongshu_tcm_post_title": "",
        "xiaohongshu_tcm_post_content": "测试内容",
        "xiaohongshu_image_path_list": ["image1.png"],
    }
    result2 = check_text_image_node(state2)
    print("测试2 - 缺少标题:")
    print(f"  is_can_publish_xiaohongshu: {result2['is_can_publish_xiaohongshu']}")
    print(f"  xiaohongshu_tcm_tip: {result2.get('xiaohongshu_tcm_tip', '(无)')}")
    print()

    # 测试3：纯空格标题（应被识别为缺失）
    # 验证 .strip() 处理逻辑是否正确
    state3: AgentState = {
        "xiaohongshu_tcm_post_title": "   ",
        "xiaohongshu_tcm_post_content": "测试内容",
        "xiaohongshu_image_path_list": ["image1.png"],
    }
    result3 = check_text_image_node(state3)
    print("测试3 - 纯空格标题（应判定为缺失）:")
    print(f"  is_can_publish_xiaohongshu: {result3['is_can_publish_xiaohongshu']}")
    print(f"  xiaohongshu_tcm_tip: {result3.get('xiaohongshu_tcm_tip', '(无)')}")
