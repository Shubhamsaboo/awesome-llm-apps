"""
LangGraph 工作流节点包。

本包包含全部 LangGraph 节点，按三条业务链路组织：

── 统一入口 ──
   1. xiaohongshu_publish_intent_node     — 小红书发布意图识别（fastText + LLM 兜底）

── 小红书发布链路（A 链路） ──
   2. text_generate_node                  — LLM 生成小红书标题和正文（Pydantic 结构化输出）
   3. image_generator_node                — 火山引擎即梦 AI 文生图（jimeng_t2i_v40）
   4. check_text_image_node               — 内容完整性校验（标题/正文/图片齐全性 + 文件存在性）
   5. auto_publish_xiaohongshu_node       — Playwright 浏览器自动化发布到小红书创作者平台
   6. generate_markdown_node              — 生成 HTML/Markdown 结果展示页面

── 中医知识图谱问答链路（B 链路） ──
   7. zhongyi_intent_node                 — 中医意图识别（RoBERTa+LoRA 二分类）
   8. extract_entity_from_user_input_node — LLM 实体抽取（六类中医实体）
   9. match_entity_from_neo4j_node        — FAISS 向量相似度匹配（实体名标准化）
  10. generate_neo4j_cypher_node          — LLM Cypher 查询生成（含重试修正）
  11. check_cypher_node                   — Cypher 语法校验（Neo4j EXPLAIN）
  12. run_cypher_node                     — Cypher 执行（Neo4j 查询）
  13. neo4j_answer_generate_node          — LLM 答案生成（图谱结果汇总为自然语言）

── 非中医兜底链路（C 链路） ──
  14. llm_direct_out_node                 — LLM 通用回答（非中医问题的直接兜底）

工作流路由逻辑（在 graph 层定义）：
    - 小红书发布意图 → 是 → 文案生成 → 图片生成 → 内容校验 → 自动发布 → Markdown 输出
    - 小红书发布意图 → 否 → 中医意图识别 → 是中医问题 → 实体抽取 → 实体匹配 → Cypher 生成 ⇄ Cypher 校验
        ├── 校验通过 → Cypher 执行 → LLM 答案生成
        ├── 校验失败 + 未超上限 → 返回 Cypher 生成节点重试（最多 MAX_CYPHER_RETRIES 次）
        └── 校验失败 + 已达上限 / Cypher 为空 → LLM 兜底回答
    - 中医意图识别 → 非中医问题 → 直接走 llm_direct_out_node（LLM 兜底回答）
"""
