"""
小红书内容生成器 — AI 驱动的中医养生内容创作与发布（支持多会话管理）
=============================================

功能：
  - AI 驱动的小红书图文笔记生成（标题 + 正文）
  - 支持即梦 AI（火山引擎）自动配图
  - 支持 Playwright 浏览器自动化发布到小红书创作者平台
  - 多会话管理：新建、切换、删除会话，生成内容持久化存储
  - 流式 SSE 渲染：实时显示生成进度和 LLM token

技术流程（LangGraph 工作流）：
  1. 发布意图识别
  2. AI 文案生成（标题 + 正文，DeepSeek v4）
  3. AI 图片生成（即梦 AI / 火山引擎）
  4. 内容完整性校验
  5. Playwright 浏览器自动化发布
  6. 结果页面生成
"""

import sys
import os
import time

# 向上四级找到项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

# ============================================================
# Streamlit 页面配置（必须在任何 st.* 调用之前）
# ============================================================
st.set_page_config(
    page_title="小红书生成器 | 知识图谱智能助手",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.style import inject_css, section_title, COLORS, status_indicator
from utils.api import check_fastapi_health, stream_tcm_knowledge, strip_stream_progress
from common.session_manager import (
    SessionManager,
    ensure_current_session,
    switch_session,
)

# session_state 中存储当前会话 ID 的 key
SESSION_STATE_KEY = "xhs_current_session_id"

# ============================================================
# 全局样式
# ============================================================

inject_css()

# ============================================================
# Session State — 会话管理
# ============================================================

# 确保存在活跃会话
current_session_id = ensure_current_session(SESSION_STATE_KEY)


def _load_generated_content():
    """从当前会话的持久化存储加载已保存的生成内容。

    返回:
        dict | None: 生成内容字典 {"input", "output", "elapsed"}，无内容时返回 None
    """
    sid = st.session_state.get(SESSION_STATE_KEY)
    if not sid:
        return None
    return SessionManager.get_generated_content(sid)


def _save_generated_content(content_data: dict):
    """将生成内容保存到当前会话的持久化存储。

    参数:
        content_data: {"input": str, "output": str, "elapsed": float}
    """
    sid = st.session_state.get(SESSION_STATE_KEY)
    if not sid:
        return
    SessionManager.update_generated_content(sid, content_data)


def _clear_generated_content():
    """清除当前会话的生成内容（内存 + 持久化存储）。"""
    sid = st.session_state.get(SESSION_STATE_KEY)
    if not sid:
        return
    SessionManager.clear_generated_content(sid)


# 首次加载时从持久化存储恢复生成内容（如从其他页面切回）
if "xhs_generated_content" not in st.session_state:
    st.session_state.xhs_generated_content = _load_generated_content()

# 处理中/待处理的状态标记
if "xhs_generating" not in st.session_state:
    st.session_state.xhs_generating = False
if "xhs_pending_topic" not in st.session_state:
    st.session_state.xhs_pending_topic = ""


# ============================================================
# 侧边栏 — 会话管理 + 生成器引导
# ============================================================

with st.sidebar:
    # —— 页面 Logo ——
    st.markdown("""
    <div style="text-align:center; padding:1rem 0.5rem 0.5rem 0.5rem;">
        <div style="font-size:2.5rem;">📝</div>
        <div style="font-family:'Noto Serif SC',serif; font-size:1.1rem; font-weight:700; color:#8B3A3A;">
            小红书内容生成
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ============================
    # 会话管理区域
    # ============================

    st.markdown("""
    <div style="font-size:0.85rem; color:#6B5B4F; font-weight:600; margin-bottom:0.5rem;">
        💬 会话管理
    </div>
    """, unsafe_allow_html=True)

    # 新建会话
    if st.button("➕ 新建会话", width='stretch', key="xhs_new_session_btn"):
        new_id = SessionManager.create_session()
        switch_session(SESSION_STATE_KEY, new_id)
        st.session_state.xhs_generated_content = None
        st.rerun()

    # 获取所有持久化会话
    all_sessions = SessionManager.list_sessions()

    if all_sessions:
        # 构建会话名称映射
        session_names = {}
        for s in all_sessions:
            session_names[s["id"]] = s.get("name", "未命名")

        # —— 当前会话高亮显示 ——
        current_obj = SessionManager.get_session(current_session_id)
        cur_name = current_obj.get("name", "未命名") if current_obj else "?"
        st.markdown(f"""
        <div style="padding:0.5rem 0.8rem; background:#F5F0E8; border-radius:8px;
                    border-left:3px solid #8B3A3A; margin-bottom:0.5rem;">
            <div style="font-size:0.8rem; font-weight:600; color:#8B3A3A;">
                📌 当前会话
            </div>
            <div style="font-size:0.85rem; color:#4A3728; margin-top:0.2rem;">
                {cur_name}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # —— 其他会话列表（可切换） ——
        other_sessions = [s for s in all_sessions if s["id"] != current_session_id]
        if other_sessions:
            st.markdown("""
            <div style="font-size:0.78rem; color:#9B8B7F; margin-top:0.8rem; margin-bottom:0.3rem;">
                🔄 切换会话
            </div>
            """, unsafe_allow_html=True)
            for s in other_sessions:
                sid = s["id"]
                name = session_names.get(sid, "?")
                if st.button(f"📋 {name}", width='stretch', key=f"xhs_switch_{sid}"):
                    # 切换到目标会话，从持久化存储恢复生成内容
                    switch_session(SESSION_STATE_KEY, sid)
                    st.session_state.xhs_generated_content = _load_generated_content()
                    st.rerun()

        # 操作按钮（删除会话 + 清空内容）
        op_col1, op_col2 = st.columns(2, gap="small")
        with op_col1:
            if st.button("🗑️ 删除会话", width='stretch', key="xhs_delete_session_btn"):
                if len(all_sessions) <= 1:
                    # 最后一个会话：先创建新会话再删除旧会话，确保始终至少有一个会话
                    new_id = SessionManager.create_session()
                    SessionManager.delete_session(current_session_id)
                    switch_session(SESSION_STATE_KEY, new_id)
                    st.session_state.xhs_generated_content = None
                    st.rerun()
                else:
                    # 删除后自动切换到第一个剩余会话
                    SessionManager.delete_session(current_session_id)
                    remaining = SessionManager.list_sessions()
                    if remaining:
                        switch_session(SESSION_STATE_KEY, remaining[0]["id"])
                        st.session_state.xhs_generated_content = _load_generated_content()
                    st.rerun()
        with op_col2:
            if st.button("🗑️ 清空内容", width='stretch', key="xhs_clear_content_btn"):
                st.session_state.xhs_generated_content = None
                _clear_generated_content()
                st.rerun()

    st.markdown("---")

    # ============================
    # 服务状态
    # ============================

    online, status_msg = check_fastapi_health()
    st.markdown(f"""
    <div style="padding:0.6rem 1rem; background:#FFFFFF; border-radius:10px;
                border:1px solid #E8DDD0; margin-bottom:0.8rem; font-size:0.85rem;">
        🔌 {status_indicator(online)}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ============================
    # 内容创作指南
    # ============================

    st.markdown("""
    <div style="font-size:0.85rem; color:#6B5B4F; font-weight:600; margin-bottom:0.5rem;">
        ✨ 内容创作技巧
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.78rem; color:#6B5B4F; line-height:1.8;">
    📌 <b>主题选择</b><br>
    选择大众关心的养生话题<br><br>
    📌 <b>语言风格</b><br>
    亲切自然，有分享感<br><br>
    📌 <b>内容结构</b><br>
    引入 → 干货 → 小贴士 → 话题标签<br><br>
    📌 <b>发布建议</b><br>
    配图精美 + 标题吸引人 + 内容实用
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ============================
    # 工作流说明
    # ============================

    with st.expander("🔧 生成流程", expanded=False):
        st.markdown("""
        <div style="font-size:0.78rem; color:#6B5B4F; line-height:1.8;">
        <b>小红书发布链路：</b><br>
        1️⃣ 发布意图识别<br>
        2️⃣ AI 文案生成（标题+正文）<br>
        3️⃣ AI 图片生成（即梦AI）<br>
        4️⃣ 内容完整性校验<br>
        5️⃣ Playwright 自动发布<br>
        6️⃣ 结果页面生成
        </div>
        """, unsafe_allow_html=True)

    # ============================
    # 示例话题
    # ============================

    st.markdown("""
    <div style="font-size:0.85rem; color:#6B5B4F; font-weight:600; margin-bottom:0.5rem; margin-top:1rem;">
        💡 试试这些话题
    </div>
    """, unsafe_allow_html=True)

    # 预定义的养生话题示例
    example_topics = [
        "枸杞养生茶的做法和好处",
        "夏季祛湿的中医小妙招",
        "艾灸的好处和注意事项",
        "秋冬进补吃什么好",
        "玫瑰花茶的美容养颜功效",
        "中医教你调理脾胃",
        "失眠怎么办？中医安神小方",
        "日常养生穴位按摩指南",
    ]

    # 每个话题一个按钮，点击后填入输入框并触发生成
    for topic in example_topics:
        if st.button(f"📝 {topic}", width='stretch', key=f"xhs_example_{topic[:10]}"):
            st.session_state.xhs_pending_topic = topic
            st.rerun()


# ============================================================
# 主页面
# ============================================================

st.markdown(f"""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-family:'Noto Serif SC',serif; color:{COLORS['primary']};
               font-size:2rem; font-weight:700; margin-bottom:0.3rem;">
        📝 小红书内容生成器
    </h1>
    <p style="color:{COLORS['text_secondary']}; font-size:0.95rem;">
        AI 驱动的中医养生内容创作 · 一键生成 · 自动配图 · 智能发布
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 输入区域
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

# 左侧 3/4 宽度：文本输入区；右侧 1/4 宽度：生成按钮
col1, col2 = st.columns([3, 1], gap="medium")

with col1:
    # 主题输入文本域，支持多行输入
    topic_input = st.text_area(
        label="📝 描述您想要创作的内容主题",
        placeholder=(
            "描述您想要的养生内容，例如：\n"
            "「帮我写一篇小红书笔记，分享枸杞养生茶的做法和好处，要吸引人一点」\n"
            "「发一篇关于夏季祛湿的中医养生帖子，配上实用的小贴士」"
        ),
        height=120,
        key="xhs_topic_input",
        help="越具体越好，AI 会更好地理解您的需求",
    )

    # 处理示例话题点击：将话题填充到输入框并触发 rerun
    pending_topic = st.session_state.pop("xhs_pending_topic", None)
    if pending_topic:
        st.session_state.xhs_topic_input = (
            f"帮我写一篇小红书笔记，分享{pending_topic}，写得吸引人一点"
        )
        st.rerun()

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    # 生成按钮：生成过程中 disabled，防止重复提交
    generate_btn = st.button(
        "🚀 开始生成",
        width='stretch',
        type="primary",
        disabled=st.session_state.xhs_generating,
        key="xhs_generate_btn",
    )

    # 已有生成内容时，显示清空按钮
    if st.session_state.xhs_generated_content:
        if st.button("🗑️ 清空内容", width='stretch', key="xhs_clear_btn"):
            st.session_state.xhs_generated_content = None
            _clear_generated_content()
            st.rerun()

# ============================================================
# 处理生成请求 — 两阶段渲染模式
# ============================================================
#
# 阶段 1：用户点击生成按钮 → 设置 xhs_generating=True → rerun
# 阶段 2：xhs_generating=True → 消费流式生成器 → 展示结果

if generate_btn and topic_input.strip() and not st.session_state.xhs_generating:
    # —— 阶段 1：接收生成请求 ——
    st.session_state.xhs_generating = True
    st.rerun()

elif st.session_state.xhs_generating:
    # —— 阶段 2：执行流式生成 ——
    topic = (topic_input or "").strip()

    if not topic:
        st.error("请输入内容主题")
        st.session_state.xhs_generating = False
        st.stop()

    # 确保输入包含小红书发布意图关键词，帮助 LangGraph 正确路由
    # 如果没有这些关键词，LangGraph 可能将其路由到中医问答链路而非小红书发布链路
    if "小红书" not in topic and "发布" not in topic and "笔记" not in topic and "帖子" not in topic:
        topic = f"帮我写一篇小红书笔记，主题是：{topic}"

    # —— 流式渲染 ——
    # 记录开始时间，用于计算生成耗时
    start_time = time.time()

    # 占位符：用于打字机效果的渐进式渲染
    stream_placeholder = st.empty()
    accumulated = ""  # 累积的原始文本（含进度消息）
    output = ""       # 最终输出文本
    try:
        # 流式调用 FastAPI /process/stream 端点
        for chunk in stream_tcm_knowledge(topic):
            accumulated += chunk
            # 实时更新占位符，显示光标动画
            stream_placeholder.markdown(
                f"🤖 **AI 正在创作...**\n\n{accumulated} ▌"
            )
        output = accumulated
    finally:
        # 计算生成耗时
        elapsed = round(time.time() - start_time, 2)
        # 剥离进度消息得到干净正文
        clean_output = strip_stream_progress(output or "")
        # 最终渲染干净文本（去掉光标）
        stream_placeholder.markdown(clean_output or "*(未获取到内容)*")

        # 检测 SSE 错误事件（流式响应中包含 "❌ **错误**" 标记）
        has_stream_error = bool(output) and "❌ **错误**" in output
        is_empty_result = not clean_output

        if not has_stream_error and not is_empty_result:
            # 成功：保存生成内容到 session_state 和持久化存储
            content_data = {
                "input": topic,
                "output": clean_output,
                "elapsed": elapsed,
            }
            st.session_state.xhs_generated_content = content_data
            _save_generated_content(content_data)

            # 自动命名会话（如果仍为「新会话」，用第一句内容作为名称）
            current_sid = st.session_state.get(SESSION_STATE_KEY)
            if current_sid:
                session = SessionManager.get_session(current_sid)
                if session and session.get("name") == "新会话":
                    SessionManager.auto_name_session(current_sid)
        else:
            # 失败：展示错误信息
            error_msg = clean_output or "生成失败，请重试。"
            st.error(error_msg)
            st.session_state.xhs_generated_content = {
                "input": topic,
                "output": error_msg,
                "elapsed": elapsed,
                "error": True,
            }

    # 清除生成中标志
    st.session_state.xhs_generating = False
    st.rerun()

# ============================================================
# 展示生成结果
# ============================================================

if st.session_state.xhs_generated_content:
    content_data = st.session_state.xhs_generated_content
    is_error = content_data.get("error", False)

    st.markdown("<br>", unsafe_allow_html=True)
    section_title("📄 生成结果")

    # 耗时标签
    elapsed = content_data.get("elapsed", 0)
    st.caption(f"⏱️ 生成耗时: {elapsed} 秒")

    # 结果展示容器
    with st.container():
        if is_error:
            # 错误内容使用 error 组件展示
            st.error(content_data["output"])
        else:
            output_text = content_data["output"]

            # 如果输出是 HTML 格式（结果页面），直接渲染
            if output_text.strip().startswith("<html"):
                st.markdown(output_text, unsafe_allow_html=True)
            else:
                # 纯文本/Markdown 格式：HTML 转义后放入卡片展示
                # 先转义 HTML 特殊字符防止 XSS，再通过 unsafe_allow_html 渲染
                escaped = (
                    output_text
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                )
                st.markdown(
                    f'<div class="tcm-card" style="padding:1.5rem;">{escaped}</div>',
                    unsafe_allow_html=True,
                )

            # 操作按钮行：复制 / 下载 / 重新生成
            st.markdown("<br>", unsafe_allow_html=True)
            act_col1, act_col2, act_col3 = st.columns(3, gap="small")

            with act_col1:
                # 复制按钮（由于 Streamlit 限制，只能提示用户手动复制）
                st.button(
                    "📋 复制内容",
                    width='stretch',
                    key="xhs_copy_btn",
                    help="点击后在弹出框中复制",
                )
                if st.session_state.get("xhs_copy_btn"):
                    st.toast("请手动选中文本后使用 Ctrl+C / Cmd+C 复制", icon="📋")

            with act_col2:
                # 下载按钮：将生成内容导出为 Markdown 文件
                st.download_button(
                    label="💾 下载文本",
                    data=output_text,
                    file_name=f"小红书草稿_{content_data['input'][:20]}.md",
                    mime="text/markdown",
                    width='stretch',
                )

            with act_col3:
                # 重新生成按钮：清除当前结果，重新触发生成
                if st.button("🔄 重新生成", width='stretch', key="xhs_regenerate_btn"):
                    st.session_state.xhs_generated_content = None
                    st.session_state.xhs_generating = True
                    st.rerun()

# ============================================================
# 未激活时的功能引导展示
# ============================================================

# 无生成内容且有未在生成中时，展示功能介绍卡片
if not st.session_state.xhs_generated_content and not st.session_state.xhs_generating:
    st.markdown("<br>", unsafe_allow_html=True)

    # 三列等宽展示三大核心功能
    feature_col1, feature_col2, feature_col3 = st.columns(3, gap="medium")

    with feature_col1:
        st.markdown(f"""
        <div style="text-align:center; padding:1.5rem 1rem; background:#FFFFFF;
                    border-radius:14px; border:1px solid #E8DDD0;">
            <div style="font-size:2rem;">🤖</div>
            <div style="font-weight:600; color:{COLORS['text_primary']}; margin:0.5rem 0;">
                AI 智能文案
            </div>
            <div style="font-size:0.82rem; color:{COLORS['text_secondary']}; line-height:1.6;">
                DeepSeek 大模型驱动<br>
                标题+正文一键生成<br>
                风格自然亲切接地气
            </div>
        </div>
        """, unsafe_allow_html=True)

    with feature_col2:
        st.markdown(f"""
        <div style="text-align:center; padding:1.5rem 1rem; background:#FFFFFF;
                    border-radius:14px; border:1px solid #E8DDD0;">
            <div style="font-size:2rem;">🎨</div>
            <div style="font-weight:600; color:{COLORS['text_primary']}; margin:0.5rem 0;">
                即梦 AI 配图
            </div>
            <div style="font-size:0.82rem; color:{COLORS['text_secondary']}; line-height:1.6;">
                火山引擎即梦AI<br>
                中医养生主题配图<br>
                画面温和有疗愈感
            </div>
        </div>
        """, unsafe_allow_html=True)

    with feature_col3:
        st.markdown(f"""
        <div style="text-align:center; padding:1.5rem 1rem; background:#FFFFFF;
                    border-radius:14px; border:1px solid #E8DDD0;">
            <div style="font-size:2rem;">🚀</div>
            <div style="font-weight:600; color:{COLORS['text_primary']}; margin:0.5rem 0;">
                自动发布
            </div>
            <div style="font-size:0.82rem; color:{COLORS['text_secondary']}; line-height:1.6;">
                Playwright 浏览器自动化<br>
                模拟人工操作发布<br>
                一站式内容创作流程
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# 底部提示 — 自动发布的前提条件
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; padding:1.5rem 0; border-top:1px solid #F0EAE0; margin-top:1rem;">
    <span style="font-size:0.78rem; color:#9B8B7F;">
        ⚠️ 自动发布功能需要：1) 启动 FastAPI 服务 2) 预先登录小红书创作者平台 3) 已安装 Playwright Chromium
    </span>
</div>
""", unsafe_allow_html=True)
