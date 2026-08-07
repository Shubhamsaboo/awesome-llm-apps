"""
神农觅 — Streamlit 前端主入口
============================================

功能:
  - 💬 中医知识问答：通过 LangGraph 工作流查询 Neo4j 知识图谱
  - 📝 小红书生成器：AI 生成中医养生内容并自动发布
  - 🔍 知识图谱浏览：直接浏览 Neo4j 中的中医知识图谱

技术栈:
  - Streamlit: 前端框架，提供 Web UI
  - FastAPI: 后端服务，运行 LangGraph 工作流
  - Neo4j: 图数据库，存储中医知识图谱
  - DeepSeek v4: 大语言模型
  - FAISS + bge-large-zh-v1.5: 语义向量匹配

使用方式:
  1. 启动 FastAPI 服务: python __005__fastapi/__001__langgraph_fastapi.py
  2. 启动本前端: streamlit run __006__streamlit/app.py
"""

import sys
import os

# 确保项目根目录在 sys.path 中，以便导入 common 模块
# 向上三级: __006__streamlit/app.py → __006__streamlit → __006__ → 项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

# ============================================================
# Streamlit 页面配置（必须在任何 st.* 调用之前）
# ============================================================
st.set_page_config(
    page_title="神农觅",
    page_icon="🌿",
    layout="wide",           # 宽屏布局，充分利用大屏幕空间
    initial_sidebar_state="expanded",  # 侧边栏默认展开
)

# 导入自定义工具模块
from utils.style import inject_css, hero_section, section_title, COLORS, status_indicator
from utils.api import check_fastapi_health, clear_health_cache

# ============================================================
# 全局样式注入
# ============================================================

# 注入中医主题的全局 CSS（字体、颜色、卡片、按钮等样式）
inject_css()

# ============================================================
# 侧边栏 — 系统状态 & 导航
# ============================================================

with st.sidebar:
    # —— Logo 区域 ——
    # 使用自定义 HTML 展示应用 Logo、名称和副标题
    st.markdown("""
    <div style="text-align:center; padding: 1.5rem 0.5rem 1rem 0.5rem;">
        <div style="font-size:3.5rem; margin-bottom:0.5rem;">🌿</div>
        <div style="font-family:'Noto Serif SC',serif; font-size:1.3rem; font-weight:700; color:#8B3A3A;">
            神农觅
        </div>
        <div style="font-size:0.8rem; color:#9B8B7F; margin-top:0.2rem;">
            AI · 中医知识导航
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # —— 服务状态检测 ——
    # 使用 TCP Socket 快速检测 FastAPI 端口是否在监听（不触发 LangGraph 工作流）
    online, status_msg = check_fastapi_health()
    # 生成带颜色的状态指示器 HTML（在线=绿色圆点，离线=红色圆点）
    status_html = status_indicator(online)
    st.markdown(f"""
    <div style="padding:0.8rem 1rem; background:#FFFFFF; border-radius:12px;
                border:1px solid #E8DDD0; margin-bottom:1rem;">
        <div style="font-size:0.85rem; color:#6B5B4F; margin-bottom:0.3rem;">🔌 服务状态</div>
        <div style="font-size:0.9rem;">{status_html}</div>
        <div style="font-size:0.75rem; color:#9B8B7F; margin-top:0.3rem;">{status_msg}</div>
    </div>
    """, unsafe_allow_html=True)

    # —— 刷新连接状态按钮 ——
    # 点击后清除缓存并重新检测服务是否在线
    if st.button("🔄 刷新连接状态", width='stretch'):
        clear_health_cache()
        st.rerun()

    st.markdown("---")

    # —— 功能导航提示 ——
    # 列出所有可用页面及其功能概述
    st.markdown("""
    <div style="padding:0.5rem 1rem;">
        <div style="font-size:0.85rem; color:#6B5B4F; margin-bottom:0.8rem;">📋 功能导航</div>
        <div style="font-size:0.82rem; color:#9B8B7F; line-height:2.2;">
            🏠 <b>首页</b> — 当前页面<br>
            💬 <b>中医问答</b> — 知识图谱问答<br>
            📝 <b>小红书生成器</b> — 内容生成<br>
            🔍 <b>知识图谱浏览</b> — 图谱探索
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # —— 系统信息 ——
    # 显示当前系统各组件的连接状态和版本信息
    st.markdown(f"""
    <div style="padding:0.5rem 1rem; font-size:0.72rem; color:#9B8B7F;">
        <div>📍 FastAPI: <code>{'在线' if online else '离线'}</code></div>
        <div>🗄️ Neo4j: <code>bolt://localhost:7687</code></div>
        <div>🤖 LLM: <code>DeepSeek v4</code></div>
        <div>🧮 Embedding: <code>bge-large-zh-v1.5</code></div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 主页面 — 首页 Hero + 功能介绍
# ============================================================

# Hero 区域：大标题 + 副标题，给用户直观的应用定位
hero_section(
    title="神农觅",
    subtitle=(
        "融合知识图谱与大语言模型，探索千年中医智慧\n"
        "问答 · 方剂查询 · 药材溯源 · 智能内容生成"
    )
)

# ============================================================
# 功能卡片区
# ============================================================

# 使用最大宽度容器限制卡片区域宽度，保持视觉居中
st.markdown('<div style="max-width:1000px; margin:0 auto;">', unsafe_allow_html=True)

# 三列等宽布局，展示三个核心功能
col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    # 卡片 1：中医知识问答 — 使用 <a> 标签实现可点击的整卡跳转
    st.markdown("""
    <a href="/中医问答" target="_self" style="text-decoration:none; color:inherit;">
    <div class="tcm-feature-card">
        <div class="tcm-feature-icon">💬</div>
        <div class="tcm-feature-title">中医知识问答</div>
        <div class="tcm-feature-desc">
            基于 Neo4j 知识图谱和 LangGraph 智能工作流，
            精准回答方剂、药材、症状、功效等中医问题。
            支持实体识别、语义匹配、图谱查询。
        </div>
    </div>
    </a>
    """, unsafe_allow_html=True)

    # 卡片下方的处理流程说明
    st.markdown(
        '<div style="text-align:center;margin-top:0.5rem;">'
        '<span style="font-size:0.8rem;color:#8B3A3A;">📋 实体抽取 → 图谱查询 → 自然语言回答</span>'
        '</div>',
        unsafe_allow_html=True,
    )

with col2:
    # 卡片 2：小红书内容生成器
    st.markdown("""
    <a href="/小红书生成器" target="_self" style="text-decoration:none; color:inherit;">
    <div class="tcm-feature-card">
        <div class="tcm-feature-icon">📝</div>
        <div class="tcm-feature-title">小红书内容生成</div>
        <div class="tcm-feature-desc">
            AI 驱动的中医养生内容创作工具。一键生成专业、
            吸引人的小红书图文笔记，支持即梦 AI 配图生成
            和浏览器自动发布到小红书创作者平台。
        </div>
    </div>
    </a>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="text-align:center;margin-top:0.5rem;">'
        '<span style="font-size:0.8rem;color:#8B3A3A;">📋 文案生成 → AI配图 → 内容校验 → 自动发布</span>'
        '</div>',
        unsafe_allow_html=True,
    )

with col3:
    # 卡片 3：知识图谱浏览
    st.markdown("""
    <a href="/知识图谱浏览" target="_self" style="text-decoration:none; color:inherit;">
    <div class="tcm-feature-card">
        <div class="tcm-feature-icon">🔍</div>
        <div class="tcm-feature-title">知识图谱浏览</div>
        <div class="tcm-feature-desc">
            直接浏览和探索中医知识图谱。按功效、药材、方剂、
            疾病、症状等维度检索实体，查看关系网络，
            发现中药知识的深层关联。
        </div>
    </div>
    </a>
    """, unsafe_allow_html=True)

    st.markdown(
        '<div style="text-align:center;margin-top:0.5rem;">'
        '<span style="font-size:0.8rem;color:#8B3A3A;">📋 实体检索 → 关系浏览 → 图谱探索</span>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# 快速开始区域 — 示例问题 & 示例话题
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
section_title("🚀 快速开始")

qcol1, qcol2 = st.columns(2, gap="large")

with qcol1:
    # 中医问答示例问题列表
    st.markdown(f"""
    <div class="tcm-card">
        <h3 style="font-family:'Noto Serif SC',serif;color:{COLORS['primary']};margin-top:0;">
            💬 试试提问
        </h3>
        <div style="color:{COLORS['text_secondary']};line-height:2.2;font-size:0.95rem;">
            • 「四君子汤由哪些药材组成？」<br>
            • 「人参有什么功效和禁忌？」<br>
            • 「治疗风寒感冒有哪些方剂？」<br>
            • 「咳嗽、发热可以用什么药材？」<br>
            • 「《伤寒论》里记载了哪些方剂？」<br>
            • 「当归补血汤出自哪里？」
        </div>
    </div>
    """, unsafe_allow_html=True)

with qcol2:
    # 小红书内容生成示例话题
    st.markdown(f"""
    <div class="tcm-card">
        <h3 style="font-family:'Noto Serif SC',serif;color:{COLORS['primary']};margin-top:0;">
            📝 试试生成
        </h3>
        <div style="color:{COLORS['text_secondary']};line-height:2.2;font-size:0.95rem;">
            • 「帮我写一篇枸杞养生的小红书笔记」<br>
            • 「发一篇关于夏季祛湿的中医养生帖子」<br>
            • 「写一篇分享艾灸好处的小红书内容」<br>
            • 「生成一篇关于玫瑰花茶养生的笔记」<br>
            • 「帮我写一篇关于秋冬进补的养生文案」
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 启动指引
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)

# 如果 FastAPI 服务未连接，显示启动提示
if not online:
    st.warning("""
    ⚠️ **FastAPI 服务未连接**

    请先启动后端服务，在项目根目录执行：

    ```bash
    python __005__fastapi/__001__langgraph_fastapi.py
    ```

    服务启动后再刷新本页面。
    """, icon="⚠️")

# ============================================================
# 底部 — 版权信息 & 技术栈
# ============================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; padding:2rem 0; border-top:1px solid #F0EAE0; margin-top:2rem;">
    <div style="font-family:'Noto Serif SC',serif; font-size:1rem; color:#8B3A3A; margin-bottom:0.3rem;">
        🌿 神农觅 · 传承中医智慧
    </div>
    <div style="font-size:0.75rem; color:#9B8B7F;">
        Powered by Neo4j + LangGraph + DeepSeek + FAISS
    </div>
</div>
""", unsafe_allow_html=True)
