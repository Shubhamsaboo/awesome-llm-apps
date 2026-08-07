"""
Streamlit 前端全局样式配置
=============================================
中医主题 — 温润、优雅、专业

设计理念：
  - 以中国传统色系为基础，营造温暖、专业的视觉氛围
  - 主色调为中国红/赭石色，强调色为琥珀金，辅助色为玉绿
  - 使用 Noto Serif SC（思源宋体）作为标题字体，Noto Sans SC（思源黑体）作为正文字体
  - 卡片、按钮等组件均带有柔和的圆角和微妙的悬停动效

提供的主要组件：
  - COLORS:           全局调色板字典
  - GLOBAL_CSS:       完整的 CSS 样式表
  - inject_css():     注入全局 CSS
  - status_indicator(): 在线/离线状态指示器
  - entity_badge():   实体类型彩色徽章（药材、方剂、症状等）
  - hero_section():   页面顶部 Hero 区域
  - feature_card():   功能卡片组件
  - section_title():  区域标题组件
"""

# ============================================================
# 调色板 — 中国传统色系
# ============================================================

COLORS = {
    # —— 主色调：中国红 / 赭石 ——
    # 用于标题、强调元素、主要按钮背景
    "primary": "#8B3A3A",
    "primary_light": "#A0524D",
    "primary_dark": "#6B2626",

    # —— 强调色：琥珀金 ——
    # 用于分隔线、卡片边框悬停、次要强调元素
    "accent": "#C8A45C",
    "accent_light": "#D4B896",
    "accent_dark": "#A07830",

    # —— 辅助色：玉绿 ——
    # 用于成功状态、健康/自然相关元素
    "jade": "#5B8C5A",
    "jade_light": "#7FAA7E",
    "jade_dark": "#3D6B3C",

    # —— 背景色 ——
    # 从暖色调到冷色调的渐变层次
    "bg_warm": "#FDF8F0",      # 暖色背景（主背景）
    "bg_cream": "#FFFCF7",      # 奶油色（渐变中间层）
    "bg_white": "#FFFFFF",      # 纯白（卡片背景）
    "bg_card": "#FFFFFF",       # 卡片背景（与纯白一致）

    # —— 文字颜色 ——
    # 从深到浅三个层次，用于不同重要级别的文本
    "text_primary": "#2C1810",      # 主要文字（深棕色）
    "text_secondary": "#6B5B4F",    # 次要文字（中棕色）
    "text_muted": "#9B8B7F",        # 弱化文字（浅棕色）
    "text_on_dark": "#FFF8F0",      # 深色背景上的文字（接近白色）

    # —— 状态色 ——
    # 用于成功/警告/错误/信息提示
    "success": "#5B8C5A",    # 成功（翠绿）
    "warning": "#D4943A",    # 警告（琥珀）
    "error": "#C0392B",      # 错误（朱红）
    "info": "#5B7F8C",       # 信息（灰蓝）

    # —— 边框颜色 ——
    # 两个层次，分别用于卡片边框和更微妙的区域分隔
    "border": "#E8DDD0",         # 默认边框（暖灰）
    "border_light": "#F0EAE0",   # 浅边框（更淡的暖灰）
}

# ============================================================
# 全局 CSS 样式表
# ============================================================
# 包含以下区域：
#   1. 字体导入（Google Fonts: 思源宋体 + 思源黑体）
#   2. CSS 自定义变量（对应 COLORS 调色板）
#   3. 基础排版（页面背景渐变）
#   4. 隐藏 Streamlit 默认元素（主菜单、页脚），Header 设为透明背景
#   5. 自定义组件样式（标题、卡片、按钮、聊天消息、徽章等）
#   6. Streamlit 组件覆盖（侧边栏、输入框、Expander、表格等）
# ============================================================

GLOBAL_CSS = f"""
<style>
    /* ========== 字体导入 ========== */
    /* 思源宋体（Noto Serif SC）：用于标题，体现传统中医的典雅气质 */
    /* 思源黑体（Noto Sans SC）：用于正文，保证可读性 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

    /* ========== CSS 自定义变量 ========== */
    /* 将 COLORS 字典映射到 CSS 变量，方便在 CSS 中统一使用 */
    :root {{
        --primary: {COLORS["primary"]};
        --primary-light: {COLORS["primary_light"]};
        --accent: {COLORS["accent"]};
        --jade: {COLORS["jade"]};
        --bg-warm: {COLORS["bg_warm"]};
        --text-primary: {COLORS["text_primary"]};
        --text-secondary: {COLORS["text_secondary"]};
        --border: {COLORS["border"]};
    }}

    /* ========== 基础排版 ========== */
    /* 全局背景使用三层渐变：暖色 → 奶油 → 纯白，营造温润感 */
    .stApp {{
        background: linear-gradient(180deg, {COLORS["bg_warm"]} 0%, {COLORS["bg_cream"]} 50%, {COLORS["bg_white"]} 100%);
    }}

    /* ========== 隐藏 Streamlit 默认元素 ========== */
    /* 隐藏右上角主菜单、页脚，并将默认 Header 设为透明背景，保持界面整洁 */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header[data-testid="stHeader"] {{background: transparent;}}

    /* ========== 标题样式 ========== */
    /* 主标题：使用思源宋体，中国红配色，居中展示 */
    .tcm-title {{
        font-family: 'Noto Serif SC', serif;
        color: {COLORS["primary"]};
        font-size: 2.8rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: 0.04em;  /* 稍微增加字间距，提升标题质感 */
    }}
    /* 副标题：使用思源黑体，次要文字颜色，较轻字重 */
    .tcm-subtitle {{
        font-family: 'Noto Sans SC', sans-serif;
        color: {COLORS["text_secondary"]};
        font-size: 1.15rem;
        text-align: center;
        font-weight: 300;
        margin-bottom: 2rem;
        line-height: 1.8;
    }}
    /* 区域标题：使用思源宋体，底部有琥珀金分隔线 */
    .tcm-section-title {{
        font-family: 'Noto Serif SC', serif;
        color: {COLORS["primary"]};
        font-size: 1.5rem;
        font-weight: 600;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {COLORS["accent"]};
    }}

    /* ========== 卡片样式 ========== */
    /* 通用卡片：白色背景，圆角，细微阴影 */
    .tcm-card {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border"]};
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 12px rgba(139, 58, 58, 0.06);  /* 中国红调的微阴影 */
        transition: all 0.3s ease;  /* 悬停平滑过渡 */
    }}
    /* 卡片悬停：阴影加深，轻微上浮 */
    .tcm-card:hover {{
        box-shadow: 0 6px 24px rgba(139, 58, 58, 0.12);
        transform: translateY(-2px);
    }}
    /* 功能卡片：用于首页功能入口 */
    .tcm-feature-card {{
        background: {COLORS["bg_card"]};
        border: 1px solid {COLORS["border_light"]};
        border-radius: 20px;
        padding: 2rem 1.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.35s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    /* 功能卡片悬停：边框变色为琥珀金，上浮更多 */
    .tcm-feature-card:hover {{
        box-shadow: 0 8px 32px rgba(139, 58, 58, 0.12);
        transform: translateY(-4px);
        border-color: {COLORS["accent"]};
    }}
    .tcm-feature-icon {{
        font-size: 3rem;
        margin-bottom: 1rem;
    }}
    .tcm-feature-title {{
        font-family: 'Noto Serif SC', serif;
        font-size: 1.25rem;
        font-weight: 600;
        color: {COLORS["text_primary"]};
        margin-bottom: 0.5rem;
    }}
    .tcm-feature-desc {{
        font-size: 0.9rem;
        color: {COLORS["text_secondary"]};
        line-height: 1.6;
    }}

    /* ========== 按钮样式 ========== */
    /* 主要按钮：中国红渐变背景，带投影和悬停上浮效果 */
    .tcm-btn-primary {{
        background: linear-gradient(135deg, {COLORS["primary"]}, {COLORS["primary_dark"]});
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-family: 'Noto Sans SC', sans-serif;
        font-size: 1rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(139, 58, 58, 0.25);
    }}
    .tcm-btn-primary:hover {{
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(139, 58, 58, 0.35);
    }}

    /* ========== 聊天消息 ========== */
    /* 聊天容器居中，最大宽度 800px */
    .tcm-chat-container {{
        max-width: 800px;
        margin: 0 auto;
    }}

    /* ========== 状态指示器 ========== */
    /* 在线/离线圆点指示器，带发光效果 */
    .tcm-status-dot {{
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 6px;
    }}
    /* 在线：玉绿色，绿色发光 */
    .tcm-status-online {{
        background: {COLORS["jade"]};
        box-shadow: 0 0 8px rgba(91, 140, 90, 0.5);
    }}
    /* 离线：红色，红色发光 */
    .tcm-status-offline {{
        background: {COLORS["error"]};
        box-shadow: 0 0 8px rgba(192, 57, 43, 0.4);
    }}

    /* ========== 标签/徽章 ========== */
    /* 通用徽章样式：圆角药丸形状 */
    .tcm-badge {{
        display: inline-block;
        padding: 0.2rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 0.2rem 0.3rem;
    }}
    /* 药材徽章：浅绿色背景 + 深绿文字 */
    .tcm-badge-herb {{
        background: #E8F5E9;
        color: #2E7D32;
    }}
    /* 方剂徽章：浅橙色背景 + 深橙文字 */
    .tcm-badge-formula {{
        background: #FFF3E0;
        color: #E65100;
    }}
    /* 症状徽章：浅粉色背景 + 深红文字 */
    .tcm-badge-symptom {{
        background: #FCE4EC;
        color: #C62828;
    }}
    /* 功效徽章：浅蓝色背景 + 深蓝文字 */
    .tcm-badge-effect {{
        background: #E3F2FD;
        color: #1565C0;
    }}
    /* 疾病徽章：浅紫色背景 + 深紫文字 */
    .tcm-badge-disease {{
        background: #F3E5F5;
        color: #7B1FA2;
    }}

    /* ========== 分隔线 ========== */
    /* 使用琥珀金渐变的分隔线，两端透明中间实色 */
    .tcm-divider {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, {COLORS["accent"]}, transparent);
        margin: 2rem 0;
    }}

    /* ========== 例句标签 ========== */
    /* 示例问题的药丸形标签，可点击选择 */
    .tcm-example-chip {{
        display: inline-block;
        padding: 0.5rem 1rem;
        margin: 0.3rem;
        border: 1px solid {COLORS["border"]};
        border-radius: 20px;
        background: {COLORS["bg_white"]};
        color: {COLORS["text_secondary"]};
        font-size: 0.9rem;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    .tcm-example-chip:hover {{
        border-color: {COLORS["primary"]};
        color: {COLORS["primary"]};
        background: {COLORS["bg_warm"]};
    }}

    /* ========== 侧边栏优化 ========== */
    /* 侧边栏使用暖色渐变背景，与主区域协调 */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #FDF8F0 0%, #FFFCF7 100%);
        border-right: 1px solid {COLORS["border_light"]};
    }}
    /* 侧边栏内 Markdown h2 使用思源宋体和中国红配色 */
    [data-testid="stSidebar"] .stMarkdown h2 {{
        font-family: 'Noto Serif SC', serif;
        color: {COLORS["primary"]};
    }}

    /* ========== 输入框样式 ========== */
    /* 聚焦时边框变为中国红，带浅红色扩散阴影 */
    textarea:focus, input:focus {{
        border-color: {COLORS["primary"]} !important;
        box-shadow: 0 0 0 2px rgba(139, 58, 58, 0.1) !important;
    }}

    /* ========== Expander 展开组件样式 ========== */
    [data-testid="stExpander"] {{
        border: 1px solid {COLORS["border_light"]};
        border-radius: 12px;
        background: {COLORS["bg_white"]};
    }}

    /* ========== 表格样式 ========== */
    /* 表格圆角，表头使用暖色背景和中国红文字 */
    [data-testid="stTable"] {{
        border-radius: 12px;
        overflow: hidden;
    }}
    [data-testid="stTable"] th {{
        background: {COLORS["bg_warm"]};
        color: {COLORS["primary"]};
        font-family: 'Noto Serif SC', serif;
    }}

    /* ========== Toast / 通知样式 ========== */
    [data-testid="stToast"] {{
        border-radius: 12px;
    }}
</style>
"""

# ============================================================
# 工具函数 — 样式渲染
# ============================================================


def inject_css():
    """注入全局 CSS 样式到当前 Streamlit 页面。

    注意：此函数不包含 set_page_config，各页面需要单独调用 set_page_config
    因为 Streamlit 要求 set_page_config 必须是第一个 st.* 调用。
    """
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def status_indicator(online: bool) -> str:
    """生成在线/离线状态指示器的 HTML 字符串。

    参数:
        online: 服务是否在线

    返回:
        str: 包含状态圆点和文字描述的 HTML 片段
             - 在线时：绿色发光圆点 + "服务已连接"
             - 离线时：红色发光圆点 + "服务未连接"
    """
    cls = "tcm-status-online" if online else "tcm-status-offline"
    text = "服务已连接" if online else "服务未连接"
    return f'<span class="tcm-status-dot {cls}"></span>{text}'


def entity_badge(entity_type: str, name: str) -> str:
    """根据实体类型生成对应的彩色徽章 HTML。

    用于知识图谱浏览页面中展示不同实体类型（药材、方剂、症状等）。

    参数:
        entity_type: 实体类型名称（如 "Herb", "Formula", "Symptom" 等）
        name:        实体名称（如 "人参", "四君子汤" 等）

    返回:
        str: 带颜色样式的徽章 HTML 片段
    """
    # 实体类型到 CSS class 的映射
    type_to_class = {
        "Herb": "tcm-badge-herb",           # 药材：绿色
        "Formula": "tcm-badge-formula",     # 方剂：橙色
        "Symptom": "tcm-badge-symptom",     # 症状：粉色
        "Effect": "tcm-badge-effect",       # 功效：蓝色
        "Disease": "tcm-badge-disease",     # 疾病：紫色
    }
    # 未知类型使用通用徽章样式
    cls = type_to_class.get(entity_type, "tcm-badge")
    return f'<span class="tcm-badge {cls}">{name}</span>'


def hero_section(title: str, subtitle: str):
    """渲染页面顶部的 Hero 区域（大标题 + 副标题 + 分隔线）。

    典型用法：在 Streamlit 页面顶部展示应用名称和简介。

    参数:
        title:    主标题文本（显示为大号思源宋体）
        subtitle: 副标题文本（显示为灰色思源黑体，支持用 \\n 换行）
    """
    import streamlit as st
    st.markdown(f"""
    <div style="text-align:center; padding: 3rem 1rem 2rem 1rem;">
        <h1 class="tcm-title">{title}</h1>
        <p class="tcm-subtitle">{subtitle}</p>
    </div>
    <hr class="tcm-divider">
    """, unsafe_allow_html=True)


def feature_card(icon: str, title: str, description: str):
    """渲染功能卡片组件（图标 + 标题 + 描述文字）。

    用于展示功能特点，带悬停动效。

    参数:
        icon:        卡片图标（emoji 字符，如 "💬"）
        title:       卡片标题
        description: 卡片描述文字
    """
    import streamlit as st
    card_html = f"""
    <div class="tcm-feature-card">
        <div class="tcm-feature-icon">{icon}</div>
        <div class="tcm-feature-title">{title}</div>
        <div class="tcm-feature-desc">{description}</div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def section_title(title: str):
    """渲染带底部琥珀金分隔线的区域标题。

    参数:
        title: 区域标题文本
    """
    import streamlit as st
    st.markdown(f'<h2 class="tcm-section-title">{title}</h2>', unsafe_allow_html=True)
