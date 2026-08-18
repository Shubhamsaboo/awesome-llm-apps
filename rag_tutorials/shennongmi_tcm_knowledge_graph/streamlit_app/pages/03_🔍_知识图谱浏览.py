"""
知识图谱浏览 — 直接浏览 Neo4j 中医知识图谱
=============================================

功能：
  - 图谱总览统计：各实体类型数量柱状图 + 详细统计表格
  - 实体搜索：按名称模糊搜索 + 按类型筛选 + 限制结果数量
  - 实体详情查看：展示实体属性摘要
  - 关系浏览：查询实体的一阶正/反向关系

支持搜索的实体类型：
  - Herb(药材)、Formula(方剂)、Symptom(症状)、Disease(疾病)
  - Effect(功效)、EffectCategory(功效分类)、FormulaCategory(方剂分类)
  - Source(出处)、HerbNature(药性)、HerbFlavor(药味)、Meridian(归经)

关系类型：
  - HAS_INGREDIENT(组成成分)、HAS_EFFECT(具有功效)
  - TREATS_DISEASE(治疗疾病)、ALLEVIATES_SYMPTOM(缓解症状)
  - HAS_SYMPTOM(包含症状)、FROM_SOURCE(出自典籍)
"""

import sys
import os

# 向上四级找到项目根目录
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

# ============================================================
# Streamlit 页面配置
# ============================================================
st.set_page_config(
    page_title="知识图谱浏览 | 知识图谱智能助手",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

import pandas as pd

from utils.style import inject_css, section_title, COLORS, entity_badge

# ============================================================
# 全局样式
# ============================================================

inject_css()

# ============================================================
# Neo4j 连接（延迟初始化 + 缓存）
# ============================================================


@st.cache_resource(show_spinner="正在连接 Neo4j 数据库...")
def get_neo4j_client():
    """获取 Neo4j 客户端（使用 Streamlit 资源缓存，整个应用生命周期只初始化一次）。

    缓存策略：使用 st.cache_resource 而非 st.cache_data，
    因为 Neo4j 连接对象不可序列化，需要用资源缓存。

    返回:
        tuple[Neo4jClient | None, Config]:
          - Neo4jClient: 连接成功的客户端实例，失败时为 None
          - Config:      项目配置对象（始终返回，用于后续读取配置）
    """
    from common.neo4j_manager import neo4j_client
    from common.config import Config
    conf = Config()

    # 验证连接：执行一条简单查询确认连通性
    try:
        neo4j_client.run_cypher("MATCH (n) RETURN count(n) AS count LIMIT 1")
        return neo4j_client, conf
    except Exception as e:
        st.error(f"无法连接到 Neo4j: {e}")
        return None, conf


# 初始化 Neo4j 客户端
neo4j_client, conf = get_neo4j_client()

# ============================================================
# 知识图谱元数据定义
# ============================================================

# 实体类型配置：定义每种实体类型的中文标签、图标和 CSS 徽章样式
ENTITY_TYPES = {
    "Herb": {"label": "药材", "icon": "🌿", "color": "tcm-badge-herb"},
    "Formula": {"label": "方剂", "icon": "📜", "color": "tcm-badge-formula"},
    "Symptom": {"label": "症状", "icon": "🤒", "color": "tcm-badge-symptom"},
    "Disease": {"label": "疾病", "icon": "🏥", "color": "tcm-badge-disease"},
    "Effect": {"label": "功效", "icon": "✨", "color": "tcm-badge-effect"},
    "EffectCategory": {"label": "功效分类", "icon": "📂", "color": "tcm-badge"},
    "FormulaCategory": {"label": "方剂分类", "icon": "📁", "color": "tcm-badge"},
    "Source": {"label": "出处", "icon": "📖", "color": "tcm-badge"},
    "HerbNature": {"label": "药性", "icon": "🌡️", "color": "tcm-badge"},
    "HerbFlavor": {"label": "药味", "icon": "👅", "color": "tcm-badge"},
    "Meridian": {"label": "归经", "icon": "🧭", "color": "tcm-badge"},
}

# 关系类型的中文映射
RELATIONSHIP_TYPES = {
    "HAS_INGREDIENT": "组成成分",
    "HAS_EFFECT": "具有功效",
    "TREATS_DISEASE": "治疗疾病",
    "ALLEVIATES_SYMPTOM": "缓解症状",
    "HAS_SYMPTOM": "包含症状",
    "FROM_SOURCE": "出自典籍",
}

# ============================================================
# 侧边栏 — 图谱统计 + Schema 说明
# ============================================================

with st.sidebar:
    # —— 页面 Logo ——
    st.markdown("""
    <div style="text-align:center; padding:1rem 0.5rem 0.5rem 0.5rem;">
        <div style="font-size:2.5rem;">🔍</div>
        <div style="font-family:'Noto Serif SC',serif; font-size:1.1rem; font-weight:700; color:#8B3A3A;">
            知识图谱浏览
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ============================
    # Neo4j 连接状态 & 图谱统计
    # ============================

    if neo4j_client:
        try:
            # 查询总节点数
            count_result = neo4j_client.run_cypher(
                "MATCH (n) RETURN count(n) AS total_nodes"
            )
            total_nodes = count_result[0]["total_nodes"] if count_result else 0
            # 查询总关系数
            rel_result = neo4j_client.run_cypher(
                "MATCH ()-[r]->() RETURN count(r) AS total_rels"
            )
            total_rels = rel_result[0]["total_rels"] if rel_result else 0

            # 连接状态指示器 + 节点/关系计数
            st.markdown(f"""
            <div style="padding:0.6rem 1rem; background:#FFFFFF; border-radius:10px;
                        border:1px solid #E8DDD0; margin-bottom:0.8rem; font-size:0.85rem;">
                <span class="tcm-status-dot tcm-status-online"></span> Neo4j 已连接
            </div>
            <div style="display:flex; gap:0.5rem; margin-bottom:1rem;">
                <div style="flex:1; text-align:center; padding:0.6rem; background:#FFFFFF;
                            border-radius:10px; border:1px solid #E8DDD0;">
                    <div style="font-size:1.3rem; font-weight:700; color:{COLORS['primary']};">
                        {total_nodes:,}
                    </div>
                    <div style="font-size:0.7rem; color:{COLORS['text_muted']};">实体节点</div>
                </div>
                <div style="flex:1; text-align:center; padding:0.6rem; background:#FFFFFF;
                            border-radius:10px; border:1px solid #E8DDD0;">
                    <div style="font-size:1.3rem; font-weight:700; color:{COLORS['accent']};">
                        {total_rels:,}
                    </div>
                    <div style="font-size:0.7rem; color:{COLORS['text_muted']};">关系边</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        except Exception:
            st.warning("⚠️ 无法获取图谱统计")
    else:
        st.error("❌ 无法连接 Neo4j")

    st.markdown("---")

    # ============================
    # 图谱 Schema 查看
    # ============================

    with st.expander("📋 图谱 Schema", expanded=False):
        st.markdown("""
        <div style="font-size:0.78rem; color:#6B5B4F; line-height:1.6;">
        <b>节点标签：</b><br>
        Herb(药材) | Formula(方剂) | Symptom(症状)<br>
        Disease(疾病) | Effect(功效) | Source(出处)<br>
        HerbNature(药性) | HerbFlavor(药味)<br>
        Meridian(归经) | EffectCategory(功效分类)<br>
        FormulaCategory(方剂分类)<br><br>
        <b>关系类型：</b><br>
        HAS_INGREDIENT(组成) | HAS_EFFECT(功效)<br>
        TREATS_DISEASE(治疗) | HAS_SYMPTOM(症状)<br>
        ALLEVIATES_SYMPTOM(缓解) | FROM_SOURCE(出处)
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# 主页面 — 标题
# ============================================================

st.markdown(f"""
<div style="text-align:center; padding:1.5rem 0 0.5rem 0;">
    <h1 style="font-family:'Noto Serif SC',serif; color:{COLORS['primary']};
               font-size:2rem; font-weight:700; margin-bottom:0.3rem;">
        🔍 知识图谱浏览
    </h1>
    <p style="color:{COLORS['text_secondary']}; font-size:0.95rem;">
        浏览中医知识图谱中的实体与关系 · 发现中药知识的深层关联
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 图谱总览统计
# ============================================================

if neo4j_client:
    st.markdown("<br>", unsafe_allow_html=True)
    section_title("📊 图谱总览")

    try:
        # 查询各实体类型的数量（使用 UNWIND labels(n) 处理多标签节点）
        # 注意：UNWIND 会将多标签节点展开为多行，每个标签一行
        label_counts = neo4j_client.run_cypher(
            "MATCH (n) UNWIND labels(n) AS label "
            "RETURN label, count(*) AS cnt ORDER BY cnt DESC"
        )
        if label_counts:
            # 构建 Pandas DataFrame，添加中文名列
            df_labels = pd.DataFrame(label_counts)
            df_labels.columns = ["实体类型", "数量"]
            df_labels["中文名"] = df_labels["实体类型"].map(
                lambda x: ENTITY_TYPES.get(x, {}).get("label", x)
            )

            # 柱状图：按中文名展示各实体类型数量
            chart_df = df_labels.set_index("中文名")["数量"]
            st.bar_chart(chart_df, width='stretch', height=300)

            # 详细统计表格（折叠展示）
            with st.expander("📋 查看详细统计", expanded=False):
                st.dataframe(
                    df_labels[["中文名", "实体类型", "数量"]],
                    width='stretch',
                    hide_index=True,
                )
    except Exception as e:
        st.warning(f"获取图谱统计失败: {e}")

# ============================================================
# 实体搜索
# ============================================================

st.markdown("<br>", unsafe_allow_html=True)
section_title("🔎 实体搜索")

# 搜索栏：搜索框 + 类型筛选 + 结果数量限制
search_col1, search_col2, search_col3 = st.columns([2, 1, 1], gap="small")

with search_col1:
    # 实体名称搜索输入框（模糊匹配，使用 CONTAINS）
    search_query = st.text_input(
        "搜索实体名称",
        placeholder="输入药材名、方剂名、症状、功效等...",
        label_visibility="collapsed",
        key="graph_search_input",
    )

with search_col2:
    # 实体类型下拉筛选
    selected_type = st.selectbox(
        "实体类型",
        options=["全部"] + [info["label"] for info in ENTITY_TYPES.values()],
        label_visibility="collapsed",
        key="graph_search_type",
    )

with search_col3:
    # 结果数量限制
    search_limit = st.selectbox(
        "结果数量",
        options=[10, 20, 50, 100],
        index=1,  # 默认 20
        label_visibility="collapsed",
        key="graph_search_limit",
    )

# ============================================================
# 执行实体搜索 & 展示结果
# ============================================================

if search_query and neo4j_client:
    # —— 构造 Cypher 查询 ——
    # 建立中文标签到实体类型名称的反向映射
    label_to_type = {v["label"]: k for k, v in ENTITY_TYPES.items()}

    # 根据筛选类型添加标签过滤（如 :Herb）
    if selected_type != "全部" and selected_type in label_to_type:
        label_clause = f":{label_to_type[selected_type]}"
    else:
        label_clause = ""  # 不限制类型，搜索所有实体

    # 构建 Cypher 查询：
    #   - CONTAINS 做模糊匹配（子串包含）
    #   - 使用参数化查询防止 Cypher 注入
    #   - head(labels(n)) 返回第一个标签（多数节点只有一个标签）
    cypher = (
        f"MATCH (n{label_clause}) "
        f"WHERE n.name CONTAINS $query "
        f"RETURN head(labels(n)) AS type, n.name AS name, n "
        f"ORDER BY type, name "
        f"LIMIT $limit"
    )

    try:
        # 执行参数化查询
        results = neo4j_client.run_cypher(
            cypher, {"query": search_query, "limit": search_limit}
        )

        if results:
            # 显示匹配结果数量
            st.markdown(f"<div style='font-size:0.85rem; color:#6B5B4F; margin:0.5rem 0;'>"
                        f"找到 <b>{len(results)}</b> 个匹配实体</div>",
                        unsafe_allow_html=True)

            # 以卡片形式展示每个搜索结果
            for i, record in enumerate(results):
                entity_type = record.get("type", "Unknown")
                entity_name = record.get("name", "")
                entity_info = ENTITY_TYPES.get(entity_type, {})
                icon = entity_info.get("icon", "📌")
                label = entity_info.get("label", entity_type)

                # 获取实体属性摘要（排除 name 和 project 两个通用字段）
                node_data = record.get("n", {})
                props = {k: v for k, v in node_data.items()
                        if k not in ("name", "project") and v}

                # 构建属性摘要文本（最多展示前 5 个属性，每个值截断到 60 字符）
                props_summary = ""
                if props:
                    props_items = list(props.items())[:5]
                    props_summary = " | ".join(
                        f"<b>{k}</b>: {str(v)[:60]}" for k, v in props_items
                    )

                # 使用 Expander 展示每个实体，前 3 个默认展开
                with st.expander(f"{icon} [{label}] {entity_name}", expanded=(i < 3)):
                    if props_summary:
                        st.markdown(
                            f"<div style='font-size:0.85rem; color:#6B5B4F; line-height:1.8;'>{props_summary}</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("(无额外属性)")

                    # —— 关系查询按钮 ——
                    # 点击后查询该实体的一阶正/反向关系
                    if st.button(f"🔗 查看关系", key=f"rel_{i}_{entity_name[:10]}",
                                 width='content'):
                        # 正向关系查询：从当前实体出发 (n)-[r]->(m)
                        rel_query = (
                            f"MATCH (n:{entity_type} {{name: $name}})-[r]->(m) "
                            f"RETURN type(r) AS rel_type, head(labels(m)) AS target_type, "
                            f"m.name AS target_name LIMIT 30"
                        )
                        rel_results = neo4j_client.run_cypher(
                            rel_query, {"name": entity_name}
                        )

                        # 反向关系查询：指向当前实体 (m)-[r]->(n)
                        rev_query = (
                            f"MATCH (m)-[r]->(n:{entity_type} {{name: $name}}) "
                            f"RETURN type(r) AS rel_type, head(labels(m)) AS target_type, "
                            f"m.name AS target_name LIMIT 30"
                        )
                        rev_results = neo4j_client.run_cypher(
                            rev_query, {"name": entity_name}
                        )

                        # 展示关系列表
                        if rel_results or rev_results:
                            st.markdown("<div style='font-size:0.85rem; color:#6B5B4F; margin-top:0.5rem;'>"
                                        f"<b>关系列表：</b></div>",
                                        unsafe_allow_html=True)

                            # 正向关系：➡️ 箭头 + 关系中文名 + 目标实体徽章
                            for rel in rel_results:
                                rel_name = RELATIONSHIP_TYPES.get(
                                    rel["rel_type"], rel["rel_type"]
                                )
                                target_badge = entity_badge(
                                    rel["target_type"], rel["target_name"]
                                )
                                st.markdown(
                                    f"<span style='font-size:0.82rem;'>➡️ {rel_name}</span> "
                                    f"{target_badge}",
                                    unsafe_allow_html=True,
                                )

                            # 反向关系：⬅️ 箭头 + 关系中文名 + 源实体徽章
                            for rel in rev_results:
                                rel_name = RELATIONSHIP_TYPES.get(
                                    rel["rel_type"], rel["rel_type"]
                                )
                                source_badge = entity_badge(
                                    rel["target_type"], rel["target_name"]
                                )
                                st.markdown(
                                    f"<span style='font-size:0.82rem;'>⬅️ {rel_name}</span> "
                                    f"{source_badge}",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.caption("该实体暂无关系连接")
        else:
            # 无匹配结果
            st.info(f"未找到包含「{search_query}」的实体，请尝试其他关键词")
    except Exception as e:
        st.error(f"搜索失败: {e}")

elif not search_query and neo4j_client:
    # 无搜索词时显示引导提示
    st.markdown(f"""
    <div style="max-width:600px; margin:2rem auto; padding:2rem;
                background:{COLORS['bg_warm']}; border-radius:16px;
                text-align:center; border:1px dashed {COLORS['border']};">
        <div style="font-size:2.5rem; margin-bottom:1rem;">🔍</div>
        <div style="font-family:'Noto Serif SC',serif; font-size:1rem;
                    color:{COLORS['text_primary']}; margin-bottom:0.5rem;">
            输入关键词搜索知识图谱中的实体
        </div>
        <div style="font-size:0.85rem; color:{COLORS['text_secondary']}; line-height:1.8;">
            支持搜索：药材名（人参、黄芪）、方剂名（四君子汤、桂枝汤）<br>
            症状名（咳嗽、发热）、功效名（清热解毒、补气血）等
        </div>
    </div>
    """, unsafe_allow_html=True)

elif not neo4j_client:
    # Neo4j 连接失败时的排查指引
    st.error("""
    ❌ **无法连接到 Neo4j 数据库**

    请确认：
    1. Neo4j 数据库已启动（`brew services start neo4j` 或通过 Neo4j Desktop）
    2. `.env` 文件中的数据库连接配置正确
    3. 数据库包含已导入的中医知识图谱数据
    """)

# ============================================================
# 底部 — 数据来源 & 技术说明
# ============================================================

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; padding:1rem 0; border-top:1px solid #F0EAE0; margin-top:1rem;">
    <span style="font-size:0.75rem; color:#9B8B7F;">
        数据来源: Neo4j 中医知识图谱 | 实体匹配: FAISS + bge-large-zh-v1.5
    </span>
</div>
""", unsafe_allow_html=True)
