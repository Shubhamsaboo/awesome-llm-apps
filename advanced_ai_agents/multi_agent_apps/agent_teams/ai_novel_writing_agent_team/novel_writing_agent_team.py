#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI Novel Writing Agent Team — 7 个 Agent 接力写一章（Streamlit 应用 + 离线 CLI）。

界面：填作品信息 → 选章节 → 点「生成章节」，逐阶段展开看每个 Agent 的产出与门禁结果。

离线预览（不需要 API key、不需要 streamlit，只要标准库）：

    python3 novel_writing_agent_team.py --dry-run

真实生成（需要一个 OpenAI 兼容的 key，如 DeepSeek / OpenAI / 本地 vLLM）：

    export DEEPSEEK_API_KEY=sk-...
    streamlit run novel_writing_agent_team.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from pipeline_core import MemoryGraph, default_agents, gate_score, rule_scan, run_chapter

DEMO_NOVEL = {
    "title": "临江夜航（示例）",
    "genre": "都市悬疑",
    "pov": "第三人称有限视角，始终跟主角沈砚",
    "chapters": {
        "1": "沈砚收到一份不该存在的航运单据，决定去码头查证",
        "2": "码头工人老陶说漏了嘴：那批货的名字三年前就注销了",
    },
}

DEMO_MEMORY = {
    "entity": {"沈砚": {"身份": "货运代理", "状态": "警觉"},
               "老陶": {"身份": "码头工人", "状态": "话多但知道分寸"},
               "临江码头": {"位置": "城东", "特点": "夜间只开三号闸"}},
    "temporal": [{"chapter": 1, "summary": "沈砚拿到废单"}],
    "causal": {"废单上的收货人": {"state": "open", "note": "名字与三年前注销的公司重合", "since": 1}},
    "semantic": {"世界观": "现代都市，无超自然设定", "叙事约定": "每章结尾必须留一个具体疑问"},
}


def load_memory(use_demo: bool = True) -> MemoryGraph:
    if use_demo:
        return MemoryGraph(**DEMO_MEMORY)
    return MemoryGraph()


# ─────────────────────────── CLI（离线预览 / 无头生成）───────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="AI Novel Writing Agent Team")
    ap.add_argument("--dry-run", action="store_true", help="只打印各阶段将发送的提示词，不调用 LLM（无需 key）")
    ap.add_argument("--chapter", type=int, default=1)
    ap.add_argument("--config", help="小说配置 JSON（默认用内置示例）")
    ap.add_argument("--save-memory", help="把记忆图谱写到该路径")
    args = ap.parse_args()

    novel = DEMO_NOVEL
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            novel = json.load(f)

    memory = load_memory()
    print("=" * 64)
    print(f" 作品：《{novel['title']}》｜{novel.get('genre', '')}｜第 {args.chapter} 章")
    print(f" 记忆图谱：{memory.stats()}")
    print(f" 模式：{'DRY-RUN（不调用 LLM）' if args.dry_run else '真实生成'}")
    print("=" * 64)

    llm = None
    if not args.dry_run:
        key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not key:
            print("\n[!] 未找到 DEEPSEEK_API_KEY / OPENAI_API_KEY。要离线看提示词请加 --dry-run。")
            sys.exit(1)

        def llm(prompt: str) -> str:  # noqa: ANN001
            from openai import OpenAI
            client = OpenAI(api_key=key,
                            base_url=os.environ.get("MODEL_BASE_URL", "https://api.deepseek.com/v1"))
            r = client.chat.completions.create(
                model=os.environ.get("MODEL_NAME", "deepseek-chat"),
                messages=[{"role": "user", "content": prompt}], temperature=0.8, max_tokens=4000)
            return r.choices[0].message.content

    result = run_chapter(novel, args.chapter, memory, llm=llm, dry_run=args.dry_run)

    print("\n" + "=" * 64)
    print(" 阶段产物清单")
    print(result["__plan__"])
    print(f" 门禁（规则口径）: {gate_score({'score': {'主线': 8, '人物': 8, '伏笔': 7, '节奏': 8}})}")
    if not args.dry_run and result.get("draft"):
        print(f" 规则初筛: {rule_scan(result['draft'])}")
    print(f" 记忆图谱（已吸收本章）: {memory.stats()}")
    if args.save_memory:
        memory.dump(args.save_memory)
        print(f" 记忆已写入 {args.save_memory}")
    print("=" * 64)


# ─────────────────────────── Streamlit UI ───────────────────────────
def ui() -> None:
    import streamlit as st  # 延迟导入：没有 streamlit 也能跑 --dry-run

    st.set_page_config(page_title="AI Novel Writing Agent Team", page_icon="📖", layout="wide")
    st.title("📖 AI Novel Writing Agent Team")
    st.caption("7 个职责单一的 Agent 接力写一章：检索 → 大纲 → 设计 → 场景 → 门禁 → 撰稿 → 评审，"
               "中间用四维记忆图谱（实体/时间/因果/语义）保证长篇一致性。")

    with st.sidebar:
        st.header("作品设定")
        title = st.text_input("书名", DEMO_NOVEL["title"])
        genre = st.text_input("类型", DEMO_NOVEL["genre"])
        pov = st.text_input("视角", DEMO_NOVEL["pov"])
        chapter = st.number_input("章节号", min_value=1, value=1, step=1)
        goal = st.text_area("本章目标", DEMO_NOVEL["chapters"]["1"], height=80)
        dry = st.checkbox("离线预览（不调用 LLM）", value=not bool(os.environ.get("DEEPSEEK_API_KEY")))
        run = st.button("生成章节", type="primary", use_container_width=True)
        st.caption("真实生成需要环境变量 DEEPSEEK_API_KEY（或 OPENAI_API_KEY）。")

    novel = {"title": title, "genre": genre, "pov": pov,
             "chapters": {**DEMO_NOVEL["chapters"], str(int(chapter)): goal}}

    if "memory" not in st.session_state:
        st.session_state.memory = load_memory()
    memory: MemoryGraph = st.session_state.memory

    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("流水线")
        for a in default_agents():
            st.markdown(f"- **{a.key}** · {a.title} → `{a.artifact.format(ch=str(int(chapter)))}`")
    with c2:
        st.subheader("记忆图谱")
        st.json(memory.stats())

    if run:
        llm = None
        if not dry:
            key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
            if not key:
                st.error("未找到 API key；请勾选「离线预览」或先设置环境变量。")
                st.stop()

            def llm(prompt: str) -> str:  # noqa: ANN001
                from openai import OpenAI
                client = OpenAI(api_key=key,
                                base_url=os.environ.get("MODEL_BASE_URL", "https://api.deepseek.com/v1"))
                r = client.chat.completions.create(
                    model=os.environ.get("MODEL_NAME", "deepseek-chat"),
                    messages=[{"role": "user", "content": prompt}], temperature=0.8, max_tokens=4000)
                return r.choices[0].message.content

        result = run_chapter(novel, int(chapter), memory, llm=llm, dry_run=dry, verbose=False)
        st.success("流水线跑完" + ("（离线预览，未调用 LLM）" if dry else ""))
        for a in default_agents():
            with st.expander(f"{a.key} · {a.title}", expanded=(a.key == "draft")):
                st.text(result.get(a.key, ""))
        if result.get("draft"):
            st.subheader("规则初筛")
            st.json(rule_scan(result["draft"]))
        st.session_state.memory = memory


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        ui()
