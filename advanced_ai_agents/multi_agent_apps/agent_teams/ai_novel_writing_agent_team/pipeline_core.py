#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""novel-agent-pipeline 流水线核心（除标准库外零依赖）。

7 个 Agent 接力写一章：检索 → 大纲 → 设计 → 场景 → 门禁 → 撰稿 → 评审，
中间用「四维记忆图谱」保证长篇一致性。所有阶段产物都是纯文本/dict，
便于单步重跑与离线检查。

本项目是 https://github.com/jiawood2006/novel-agent-pipeline 的精简版，
只依赖标准库即可跑 `--dry-run`（不调用任何 LLM）。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ─────────────────────────── 四维记忆图谱 ───────────────────────────
@dataclass
class MemoryGraph:
    """实体 / 时间 / 因果 / 语义 四张图，全部用普通 dict 表示，可 JSON 落盘。"""

    entity: Dict[str, dict] = field(default_factory=dict)      # 人名/地点/物件 → 属性
    temporal: List[dict] = field(default_factory=list)          # 按时间发生的事件
    causal: Dict[str, dict] = field(default_factory=dict)       # 线索/伏笔 → 开/收状态
    semantic: Dict[str, str] = field(default_factory=dict)      # 设定/规则/术语

    # —— 写：每章写完后由「吸收」阶段调用 ——
    def add_entity(self, name: str, **attrs) -> None:
        self.entity.setdefault(name, {}).update(attrs)

    def add_event(self, chapter: int, summary: str) -> None:
        self.temporal.append({"chapter": chapter, "summary": summary})

    def open_thread(self, key: str, note: str, chapter: int) -> None:
        self.causal[key] = {"state": "open", "note": note, "since": chapter}

    def resolve_thread(self, key: str, chapter: int) -> None:
        if key in self.causal:
            self.causal[key].update(state="resolved", resolved_at=chapter)

    # —— 读：每章动笔前由「检索」阶段调用 ——
    def digest(self, limit_events: int = 6) -> str:
        lines = []
        if self.entity:
            lines.append("【人物/物件】" + "；".join(
                f"{k}（{'、'.join(f'{a}={b}' for a, b in v.items())}）" for k, v in self.entity.items()))
        if self.temporal:
            lines.append("【最近事件】" + "；".join(
                f"第{e['chapter']}章 {e['summary']}" for e in self.temporal[-limit_events:]))
        open_threads = [f"{k}：{v['note']}" for k, v in self.causal.items() if v.get("state") == "open"]
        if open_threads:
            lines.append("【未收伏笔】" + "；".join(open_threads))
        if self.semantic:
            lines.append("【设定】" + "；".join(f"{k}={v}" for k, v in self.semantic.items()))
        return "\n".join(lines) or "（记忆为空，这是第一章）"

    def stats(self) -> Dict[str, int]:
        return {"entity": len(self.entity), "temporal": len(self.temporal),
                "causal_open": sum(1 for v in self.causal.values() if v.get("state") == "open"),
                "semantic": len(self.semantic)}

    def dump(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"entity": self.entity, "temporal": self.temporal,
                       "causal": self.causal, "semantic": self.semantic}, f,
                      ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str) -> "MemoryGraph":
        try:
            with open(path, encoding="utf-8") as f:
                d = json.load(f)
            return cls(**d)
        except FileNotFoundError:
            return cls()


# ─────────────────────────── Agent 定义 ───────────────────────────
@dataclass
class Agent:
    """一个职责单一的 Agent：只负责一个阶段，输入输出都是文本。"""

    key: str
    title: str
    instruction: str
    depends_on: List[str] = field(default_factory=list)
    artifact: str = ""

    def build_prompt(self, novel: dict, chapter: int, memory: MemoryGraph,
                     upstream: Dict[str, str]) -> str:
        parts = [
            f"【任务】{self.instruction}",
            f"【作品】《{novel['title']}》｜类型：{novel.get('genre', '未定')}"
            f"｜视角：{novel.get('pov', '第三人称有限视角')}",
            f"【本章】第 {chapter} 章｜目标：{novel['chapters'].get(str(chapter), '按主线推进')}",
            "【记忆图谱】\n" + memory.digest(),
        ]
        for dep in self.depends_on:
            if upstream.get(dep):
                parts.append(f"【上一阶段产出 · {dep}】\n{upstream[dep]}")
        parts.append("【输出要求】只输出该阶段的成果本身，不要解释、不要寒暄。")
        return "\n\n".join(parts)


def default_agents() -> List[Agent]:
    """7 个写作 Agent + 最后的记忆吸收阶段（吸收由记忆引擎承担，不调 LLM）。"""
    return [
        Agent("context", "写前检索", "结合记忆图谱与上一章结尾，产出本章「上下文包」："
              "必须交代的前情、不能矛盾的事实、本章要推进的一条主线。",
              artifact="context_ch{ch}.md"),
        Agent("outline", "章节大纲", "产出本章大纲：3-5 个事件节点（含因果）、情绪温度曲线、"
              "结尾钩子。不要写正文。", ["context"], "outline_ch{ch}.md"),
        Agent("design", "创意设计", "为大纲里每个事件节点设计「展示方式」：用哪个场景、谁的动作、"
              "什么细节暴露信息；至少埋/收一条伏笔。", ["outline"], "design_ch{ch}.md"),
        Agent("scene", "场景拆分", "把设计稿拆成 3-5 个可写场景，标注地点/人物/时长权重，"
              "避免同一场景超过 800 字。", ["design"], "scene_ch{ch}.md"),
        Agent("gate", "创意门禁", "评审场景方案：主线推进、人物一致性、伏笔、节奏四项各 0-10 分。"
              "输出 JSON：{\"score\": 各维度分值, \"pass\": true/false, \"fix\": [\"具体修改建议\"]}。",
              ["scene"], "gate_ch{ch}.json"),
        Agent("draft", "撰稿", "依据场景方案写完整章节正文（1800-2500 字）。"
              "对话推进情节，不解释人物心理，不写总结句。", ["scene", "design"], "draft_ch{ch}.md"),
        Agent("editor", "评审", "对正文做两项检查：①规则项（错别字、重复词、AI 腔套话）"
              "②LLM 评审（人物是否走形、节奏是否塌、结尾是否有效）。"
              "输出 JSON：{\"issues\": [...], \"scores\": {...}, \"pass\": true/false}。",
              ["draft"], "editor_ch{ch}.json"),
    ]


# ─────────────────────────── 规则门禁 ───────────────────────────
AI_PHRASES = ["总而言之", "综上所述", "值得注意的是", "嘴角勾起", "眼中闪过一丝",
              "不禁", "仿佛", "宛如", "在这个瞬间", "与此同时"]
REPEAT_RE = re.compile(r"([\u4e00-\u9fa5]{2,4})\1")


def rule_scan(text: str) -> Dict[str, object]:
    """规则初筛：只统计可观测计数，不做主观打分（分数口径写在 README）。"""
    phrases = [p for p in AI_PHRASES if p in text]
    repeats = sorted({m.group(0) for m in REPEAT_RE.finditer(text)})
    lines = [l for l in text.splitlines() if l.strip()]
    return {"ai_phrases": phrases, "repeats": repeats,
            "chars": len(text), "lines": len(lines)}


def gate_score(gate_json: Optional[dict]) -> dict:
    """门禁阈值：四维平均分 ≥ 7.0 且无维度 < 5 才放行（口径固定，便于复现）。"""
    if not gate_json:
        return {"avg": 0.0, "pass": False, "reason": "门禁未产出结果"}
    scores = {k: v for k, v in (gate_json.get("score") or {}).items() if isinstance(v, (int, float))}
    if not scores:
        return {"avg": 0.0, "pass": False, "reason": "门禁 JSON 无分值"}
    avg = round(sum(scores.values()) / len(scores), 2)
    return {"avg": avg, "pass": avg >= 7.0 and min(scores.values()) >= 5,
            "reason": "通过" if avg >= 7.0 and min(scores.values()) >= 5 else "未达标"}


# ─────────────────────────── 编排 ───────────────────────────
def run_chapter(novel: dict, chapter: int, memory: MemoryGraph,
                llm: Optional[Callable[[str], str]] = None,
                dry_run: bool = True, verbose: bool = True) -> Dict[str, str]:
    """跑一章的完整流水线。dry_run=True 时不调用 LLM，只打印将发送的完整提示词。"""
    agents = default_agents()
    upstream: Dict[str, str] = {}
    plan: List[str] = []

    for a in agents:
        prompt = a.build_prompt(novel, chapter, memory, upstream)
        if verbose:
            print(f"\n{'=' * 62}\n[{a.key}] {a.title}  ← 依赖 {a.depends_on or '（无）'}\n{'=' * 62}")
        if dry_run or llm is None:
            if verbose:
                print(prompt)
            upstream[a.key] = f"(dry-run 未调用 LLM：{a.title})"
        else:
            out = llm(prompt)
            upstream[a.key] = out
            if verbose:
                print(out[:400] + ("…" if len(out) > 400 else ""))
        plan.append(f"{a.key:7} {a.title:<8} 产出 {a.artifact.format(ch=chapter)}")

    # 记忆吸收（不调 LLM）：把本章发生的事写回图谱
    memory.add_event(chapter, f"第{chapter}章完成：{novel['chapters'].get(str(chapter), '按主线推进')}")
    return {"__plan__": "\n".join(plan), **upstream}
