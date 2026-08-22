"""
中医知识问答页面 — Chat 交互式知识图谱问答（支持多会话管理）
=============================================

功能：
  - 基于 Neo4j 知识图谱和 LangGraph 的中医知识问答
  - 支持多会话管理：新建、切换、重命名、删除会话
  - 流式 SSE 渲染：实时显示工作流进度和 LLM 生成 token
  - 对话历史持久化存储到磁盘

技术流程：
  1. 用户输入问题
  2. 通过 SSE 流式调用 FastAPI /process/stream 端点
  3. LangGraph 自动路由：意图识别 → 实体抽取 → FAISS 匹配 →
     Cypher 生成 → Neo4j 查询 → 答案生成
  4. 实时展示进度和 LLM token（打字机效果）
  5. 剥离进度消息后存入对话历史

两阶段渲染模式：
  阶段 1（用户输入到达）：
    - 保存用户消息，设置 tcm_processing=True，st.rerun()
  阶段 2（tcm_processing=True）：
    - 消费 stream_tcm_knowledge 生成器，逐 chunk 更新占位符
    - 完成后剥离进度消息，持久化助手回复，st.rerun() 展示最终结果

会话管理设计：
  - 使用 common.session_manager.SessionManager 进行持久化
  - _last_loaded_for_session 标志防止「跳到历史会话」
"""

import sys
import os

# 向上四级找到项目根目录（确保 common 模块可导入）
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

# ============================================================
# Streamlit 页面配置（必须在任何 st.* 调用之前）
# ============================================================
st.set_page_config(
    page_title="中医问答 | 知识图谱智能助手",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.style import inject_css, section_title, COLORS, status_indicator
from utils.api import check_fastapi_health, stream_tcm_knowledge, strip_stream_progress
from common.session_manager import (
    SessionManager,
    ensure_current_session,
    load_current_messages,
    switch_session,
)

# session_state 中存储当前会话 ID 的 key
SESSION_STATE_KEY = "tcm_current_session_id"

# ============================================================
# 全局样式
# ============================================================

inject_css()

# ============================================================
# 初始化 Session State — 会话管理
# ============================================================

# 确保存在一个活跃的会话（首次访问自动创建）
current_session_id = ensure_current_session(SESSION_STATE_KEY)

# 追踪聊天历史是为哪个会话加载的。
# 如果与 current_session_id 不一致，说明会话被程序化切换了，
# 必须从磁盘重新加载正确会话的消息——这是防止「跳到历史会话」的最后防线。
_last_loaded_for_session = st.session_state.get("_tcm_last_loaded_for_session")


def _reload_chat_history():
    """从磁盘重新加载当前会话的消息到 session_state（强制同步）。

    调用场景：
      - 首次加载页面
      - 切换会话后
      - _last_loaded_for_session 与 current_session_id 不一致时
    """
    st.session_state.tcm_chat_history = load_current_messages(SESSION_STATE_KEY)
    st.session_state._tcm_last_loaded_for_session = st.session_state.get(SESSION_STATE_KEY)


def _add_message(role: str, content: str):
    """添加消息到会话历史，同时持久化到磁盘和内存缓存。

    参数:
        role:    消息角色（"user" 或 "assistant"）
        content: 消息正文（Markdown 格式）
    """
    sid = st.session_state.get(SESSION_STATE_KEY)
    if not sid:
        return
    # 持久化到磁盘（SessionManager 管理 JSON 文件存储）
    SessionManager.add_message(sid, role, content)
    # 同步内存缓存（session_state 中的聊天历史列表）
    st.session_state.tcm_chat_history.append((role, content))


# 核心保护逻辑：只要 current_session_id 和上次加载的不一致，就强制重新加载
# 这解决了多标签页切换、session_state 意外修改、跨页面跳转等场景
if (_last_loaded_for_session != current_session_id
        or "tcm_chat_history" not in st.session_state):
    _reload_chat_history()

# 处理中状态标记：当为 True 时，进入流式消费阶段
if "tcm_processing" not in st.session_state:
    st.session_state.tcm_processing = False


# ============================================================
# 侧边栏 — 会话管理 + 状态 + 示例问题
# ============================================================

with st.sidebar:
    # —— 页面 Logo ——
    st.markdown("""
    <div style="text-align:center; padding:1rem 0.5rem 0.5rem 0.5rem;">
        <div style="font-size:2.5rem;">💬</div>
        <div style="font-family:'Noto Serif SC',serif; font-size:1.1rem; font-weight:700; color:#8B3A3A;">
            中医知识问答
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

    # —— 新建会话按钮 ——
    # 创建新会话，自动切换到新会话，清空聊天历史
    if st.button("➕ 新建会话", width='stretch', key="tcm_new_session_btn"):
        new_id = SessionManager.create_session()
        switch_session(SESSION_STATE_KEY, new_id)
        st.session_state.tcm_chat_history = []
        st.toast(f"🆕 已创建新会话 ({new_id[:6]}...)", icon="➕")
        st.rerun()

    # —— 会话列表 ——
    # 获取所有持久化的会话（按创建时间倒序）
    all_sessions = SessionManager.list_sessions()

    if all_sessions:
        # 构建 session_id → session_name 的映射字典
        session_names = {}
        name_counts = {}
        for s in all_sessions:
            sid = s["id"]
            name = s.get("name", "未命名")
            name_counts[name] = name_counts.get(name, 0) + 1
        for s in all_sessions:
            sid = s["id"]
            name = s.get("name", "未命名")
            session_names[sid] = name

        # —— 当前会话高亮显示 ——
        current_obj = SessionManager.get_session(current_session_id)
        cur_name = current_obj.get("name", "未命名") if current_obj else "?"
        cur_count = current_obj.get("message_count", 0) if current_obj else 0
        cur_rounds = cur_count // 2  # 对话轮数 = 消息条数 / 2（每轮一问一答）
        st.markdown(f"""
        <div style="padding:0.5rem 0.8rem; background:#F5F0E8; border-radius:8px;
                    border-left:3px solid #8B3A3A; margin-bottom:0.5rem;">
            <div style="font-size:0.8rem; font-weight:600; color:#8B3A3A;">
                📌 当前会话
            </div>
            <div style="font-size:0.85rem; color:#4A3728; margin-top:0.2rem;">
                {cur_name} · {cur_rounds}轮
            </div>
        </div>
        """, unsafe_allow_html=True)

        # —— 其他会话列表（点击切换） ——
        other_sessions = [s for s in all_sessions if s["id"] != current_session_id]
        if other_sessions:
            st.markdown("""
            <div style="font-size:0.78rem; color:#9B8B7F; margin-top:0.8rem; margin-bottom:0.3rem;">
                🔄 切换会话
            </div>
            """, unsafe_allow_html=True)
            for s in other_sessions:
                sid = s["id"]
                count = s.get("message_count", 0)
                rounds = count // 2
                name = session_names.get(sid, "?")
                btn_label = f"📋 {name} ({rounds}轮)"
                if st.button(btn_label, width='stretch', key=f"tcm_switch_{sid}"):
                    # 切换到目标会话，从磁盘重新加载消息
                    switch_session(SESSION_STATE_KEY, sid)
                    _reload_chat_history()
                    st.rerun()

        # —— 当前会话操作按钮（删除 + 重命名） ——
        op_col1, op_col2 = st.columns(2, gap="small")

        with op_col1:
            # 删除当前会话
            if st.button("🗑️ 删除会话", width='stretch', key="tcm_delete_session_btn"):
                if len(all_sessions) <= 1:
                    # 最后一个会话不能删除，替换为新会话
                    st.toast("至少保留一个会话，已创建新会话", icon="⚠️")
                    new_id = SessionManager.create_session()
                    SessionManager.delete_session(current_session_id)
                    switch_session(SESSION_STATE_KEY, new_id)
                    st.session_state.tcm_chat_history = []
                    st.rerun()
                else:
                    # 删除后自动切换到剩余第一个会话
                    SessionManager.delete_session(current_session_id)
                    remaining = SessionManager.list_sessions()
                    if remaining:
                        switch_session(SESSION_STATE_KEY, remaining[0]["id"])
                        _reload_chat_history()
                    st.rerun()

        with op_col2:
            # 重命名会话：点击后展开输入框
            rename_key = f"tcm_rename_{current_session_id}"
            if st.button("✏️ 重命名", width='stretch', key="tcm_rename_btn"):
                st.session_state[rename_key] = True

        # 重命名输入区域（点击按钮后展开）
        if st.session_state.get(rename_key, False):
            current_name = session_names.get(current_session_id, "")
            new_name = st.text_input(
                "新名称",
                value=current_name,
                key=f"tcm_rename_input_{current_session_id}",
                label_visibility="collapsed",
            )
            rcol1, rcol2 = st.columns(2, gap="small")
            with rcol1:
                if st.button("✅ 确认", width='stretch', key="tcm_rename_confirm"):
                    if new_name.strip():
                        SessionManager.rename_session(current_session_id, new_name.strip())
                    st.session_state[rename_key] = False
                    st.rerun()
            with rcol2:
                if st.button("❌ 取消", width='stretch', key="tcm_rename_cancel"):
                    st.session_state[rename_key] = False
                    st.rerun()
    else:
        st.caption("暂无会话")

    st.markdown("---")

    # ============================
    # 服务状态
    # ============================

    # TCP Socket 快速检测 FastAPI 是否在线
    online, status_msg = check_fastapi_health()
    st.markdown(f"""
    <div style="padding:0.6rem 1rem; background:#FFFFFF; border-radius:10px;
                border:1px solid #E8DDD0; margin-bottom:0.8rem; font-size:0.85rem;">
        🔌 {status_indicator(online)}
    </div>
    """, unsafe_allow_html=True)

    # 清空当前对话：删除当前会话并创建新空会话，实现"重置对话"的效果
    if st.button("🗑️ 清空当前对话", width='stretch', key="tcm_clear_chat_btn"):
        SessionManager.delete_session(current_session_id)
        new_id = SessionManager.create_session()
        switch_session(SESSION_STATE_KEY, new_id)
        st.session_state.tcm_chat_history = []
        st.rerun()

    st.markdown("---")

    # ============================
    # 示例问题
    # ============================

    st.markdown("""
    <div style="font-size:0.85rem; color:#6B5B4F; font-weight:600; margin-bottom:0.5rem;">
        💡 试试这些问题
    </div>
    """, unsafe_allow_html=True)

    # 预定义示例问题，覆盖方剂组成、药材功效、疾病治疗等常见问法
    example_questions = [
        "四君子汤由哪些药材组成？",
        "人参有什么功效和禁忌？",
        "治疗风寒感冒有哪些方剂？",
        "咳嗽、发热可以用什么药材？",
        "《伤寒论》里记载了哪些方剂？",
        "当归补血汤出自哪里？",
        "藿香正气散的组成和功效是什么？",
        "什么药材可以清热解毒？",
    ]

    # 每个问题一个按钮，点击后通过 session_state 触发查询
    for q in example_questions:
        if st.button(q, width='stretch', key=f"tcm_example_{q[:15]}"):
            st.session_state.tcm_pending_question = q
            st.rerun()

    st.markdown("---")

    # ============================
    # 工作流说明 & 统计
    # ============================

    # 展开查看处理流程详情
    with st.expander("🔧 处理流程", expanded=False):
        st.markdown("""
        <div style="font-size:0.78rem; color:#6B5B4F; line-height:1.8;">
        <b>中医问题处理链路：</b><br>
        1️⃣ 意图识别（是否中医相关）<br>
        2️⃣ 实体抽取（症状/方剂/药材等）<br>
        3️⃣ FAISS 语义实体匹配<br>
        4️⃣ Cypher 图谱查询生成<br>
        5️⃣ Cypher 语法校验<br>
        6️⃣ 知识图谱查询执行<br>
        7️⃣ 自然语言答案生成
        </div>
        """, unsafe_allow_html=True)

    # 当前会话统计
    msg_count = len(st.session_state.tcm_chat_history)
    if msg_count > 0:
        current_session = SessionManager.get_session(current_session_id)
        session_name = current_session.get("name", "当前会话") if current_session else "当前会话"
        st.markdown(f"""
        <div style="font-size:0.75rem; color:#9B8B7F; text-align:center; margin-top:1rem;">
        📋 {session_name}<br>
        本次对话: {msg_count // 2} 轮
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 主页面 — 标题
# ============================================================

st.markdown(f"""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-family:'Noto Serif SC',serif; color:{COLORS['primary']};
               font-size:2rem; font-weight:700; margin-bottom:0.3rem;">
        💬 中医知识问答
    </h1>
    <p style="color:{COLORS['text_secondary']}; font-size:0.95rem;">
        基于 Neo4j 知识图谱 + LangGraph 智能工作流的交互式问答
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 欢迎提示（首次访问，无聊天历史时显示）
# ============================================================

if not st.session_state.tcm_chat_history:
    st.markdown(f"""
    <div style="max-width:650px; margin:1.5rem auto; padding:2rem;
                background:{COLORS['bg_warm']}; border-radius:16px;
                text-align:center; border:1px dashed {COLORS['border']};">
        <div style="font-size:3rem; margin-bottom:1rem;">🌿</div>
        <div style="font-family:'Noto Serif SC',serif; font-size:1.1rem;
                    color:{COLORS['text_primary']}; margin-bottom:0.5rem;">
            欢迎使用中医知识图谱问答
        </div>
        <div style="font-size:0.9rem; color:{COLORS['text_secondary']}; line-height:1.8;">
            您可以向我提问任何中医相关问题<br>
            方剂组成、药材功效、疾病治疗、经典出处……
        </div>
        <div style="margin-top:1rem; font-size:0.8rem; color:{COLORS['text_muted']};">
            在下方输入框输入您的问题，或点击左侧示例问题快速体验 👇<br>
            点击「➕ 新建会话」可以开始一段新的独立对话
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 聊天消息渲染
# ============================================================

# 使用 st.container() 包裹聊天区域，方便管理
chat_container = st.container()

with chat_container:
    # 遍历对话历史，逐条渲染聊天气泡
    for role, content in st.session_state.tcm_chat_history:
        if role == "user":
            # 用户消息：使用 👤 头像
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)
        else:
            # 助手消息：使用 🌿 头像，支持 Markdown/HTML 渲染
            with st.chat_message("assistant", avatar="🌿"):
                st.markdown(content, unsafe_allow_html=True)
                # 长消息显示字数统计
                if content and len(content) > 20:
                    st.caption(f"字数: {len(content)}")

# ============================================================
# 输入框
# ============================================================

# Streamlit 的 chat_input 组件，底部固定位置，支持回车发送
user_input = st.chat_input(
    placeholder="请输入您的中医问题，例如：四君子汤由哪些药材组成？",
    key="tcm_chat_input",
)

# 处理示例问题点击：将 tcm_pending_question 的值赋给 user_input
# pop 取出后立即清除，确保只在触发时执行一次
pending = st.session_state.pop("tcm_pending_question", None)
if pending:
    user_input = pending

# ============================================================
# 处理用户输入 — 两阶段渲染模式
# ============================================================
#
# Streamlit 的事件循环要求流式数据分两阶段处理：
#
# 阶段 1（user_input 不为空且未在处理中）：
#   - 保存用户消息到聊天历史
#   - 设置 tcm_processing = True
#   - st.rerun() 触发重新渲染，进入阶段 2
#
# 阶段 2（tcm_processing = True）：
#   - 找到最后一条用户消息
#   - 启动 stream_tcm_knowledge() 流式生成器
#   - 逐 chunk 更新 stream_placeholder，实现打字机效果
#   - 完成后剥离进度消息，存入聊天历史
#   - 设置 tcm_processing = False，st.rerun() 展示最终结果
#
# 分两阶段的原因：st.write_stream() 需要在其调用时才开始消费生成器；
# 先保存用户消息再立即消费生成器，用户消息不会立即显示。

if user_input and not st.session_state.tcm_processing:
    # —— 阶段 1：接收用户输入 ——
    user_input = user_input.strip()
    if not user_input:
        st.stop()

    # 设置处理中标志
    st.session_state.tcm_processing = True

    # 添加并持久化用户消息
    _add_message("user", user_input)

    # 检查是否首次对话，自动命名会话
    # （在 add_message 之后检查，此时消息列表中已有用户消息）
    current_sid = st.session_state.get(SESSION_STATE_KEY)
    if current_sid:
        session = SessionManager.get_session(current_sid)
        if session and session.get("name") == "新会话":
            SessionManager.auto_name_session(current_sid)

    # 刷新界面以显示用户消息，进入阶段 2
    st.rerun()

elif st.session_state.tcm_processing:
    # —— 阶段 2：流式处理 LangGraph 工作流 ——

    # 反向遍历找到最后一条用户消息作为触发输入
    last_user_msg = None
    for role, content in reversed(st.session_state.tcm_chat_history):
        if role == "user":
            last_user_msg = content
            break

    if last_user_msg:
        # —— 流式渲染 ——
        # 创建一个占位符，用于渐进式更新内容（打字机效果）
        stream_placeholder = st.empty()
        accumulated = ""  # 累积的原始文本（含进度消息）
        response = ""     # 最终响应文本
        try:
            # 构建对话历史（排除当前正在处理的用户消息，避免重复发送）
            # chat_history[:-1] 排除最后一条即刚添加的用户消息
            history_messages = []
            for role, content in st.session_state.tcm_chat_history[:-1]:
                history_messages.append({"role": role, "content": content})

            # 流式调用 FastAPI /process/stream，逐个 token 积累
            for chunk in stream_tcm_knowledge(last_user_msg, messages=history_messages if history_messages else None):
                accumulated += chunk
                # 实时更新占位符内容，显示光标动画 "▌"
                stream_placeholder.markdown(
                    f"🌿 **正在回答...**\n\n{accumulated} ▌"
                )
            response = accumulated
        finally:
            # 剥离进度消息得到干净正文
            # 进度消息如 "> 🔍 正在判断问题类型..." 不属于正文
            clean_response = strip_stream_progress(response or "")

            # 去掉 Markdown 代码块包裹（如果 LLM 输出被 ``` 包裹）
            if clean_response.startswith("```") and clean_response.endswith("```"):
                lines = clean_response.split("\n")
                # 去掉开头的 ``` (可能带语言标识如 ```markdown)
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # 去掉结尾的 ```
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_response = "\n".join(lines)

            # 持久化助手消息（磁盘 + 内存）
            _add_message("assistant", clean_response)
            # 最终渲染干净文本，清除光标
            stream_placeholder.markdown(clean_response or "*(未获取到回答)*")

    # 清除处理状态，触发最终渲染
    st.session_state.tcm_processing = False
    st.rerun()

# ============================================================
# 底部快捷栏 — 使用提示
# ============================================================

# 仅在有聊天历史时显示提示
if st.session_state.tcm_chat_history:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; padding:1rem 0; border-top:1px solid #F0EAE0; margin-top:1rem;">
        <span style="font-size:0.78rem; color:#9B8B7F;">
            💡 提示：提问时尽量具体，包含方剂名、药材名、症状或功效等关键词，可获得更精准的回答。
        </span>
    </div>
    """, unsafe_allow_html=True)
