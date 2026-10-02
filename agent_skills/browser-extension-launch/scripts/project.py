#!/usr/bin/env python3
"""Create formal local records and inspect capabilities without changing a project.

Python standard library only. Detection never proves host activation, a browser
connection, a passing acceptance check, or a live store release.
"""

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import sys
from datetime import datetime, timezone


SCHEMA_VERSION = 1
RECORD_DIR = ".extension-launch"
DEFAULT_E2E_PROVIDER = "playwright-mcp"
REQUIRED_SKILLS = (
    ("product-designer", "product_experience", "new_or_changed_user_flow_and_experience_acceptance"),
    ("chrome-extensions", "architecture", "all_projects"),
    ("extension-create", "creation", "new_extension"),
    ("diagnosing-bugs", "debugging", "failure_or_regression"),
    ("code-review", "review", "each_implementation_and_final_candidate"),
    ("setup-matt-pocock-skills", "project_setup", "complex_project_first_use_or_missing_configuration"),
    ("to-spec", "specification", "complex_project"),
    ("to-tickets", "ticket_decomposition", "complex_project"),
    ("triage", "feedback_triage", "external_feedback_or_existing_tickets_need_triage"),
    ("implement", "ticket_implementation", "each_complex_project_ticket"),
)
PORTABLE_FALLBACKS = {
    "product-designer": "references/product-loop.md",
}
COMPLEX_CHAIN = ("setup-matt-pocock-skills", "to-spec", "publish-parent-ticket", "to-tickets", "implement")
METHODS = {
    "dependencies": "references/dependencies.md",
    "workflow": "references/workflow.md",
    "development": "references/development.md",
    "acceptance": "references/acceptance.md",
    "publishing": "references/publishing.md",
}
BROWSER_COMMANDS = {
    "chrome": ("google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser"),
    "edge": ("microsoft-edge", "microsoft-edge-stable", "msedge"),
    "firefox": ("firefox",),
}
TASK_DEFINITIONS = (
    ("T-001", "scope", "目标与首版范围", [], "needs_scope", "workflow",
     "记录用户、网页场景、首版范围、范围外事项、已确认决定和验收标准。",
     "范围内实施、独立验收、发布准备和上线跟踪全部满足各自关闭条件；未完成事项有明确处置。"),
    ("T-002", "implementation", "首条完整用户功能", [], "needs_scope", "development",
     "按 spec.md 做出从真实插件入口到可观察结果的一条完整路径。",
     "功能实现、相关测试、真实浏览器路径及规范/规格审查通过；保存可追溯且可恢复的版本。"),
    ("T-003", "acceptance", "独立完整体验检查", ["T-002"], "blocked", "acceptance",
     "用最终候选包独立检查跨功能主路径、异常恢复和适用的旧数据、界面及权限场景。",
     "所有必需场景均通过，失败已修复并复验；未验证不能算通过；证据与候选版本一致。"),
    ("T-004", "release-preparation", "发布材料准备", ["T-003"], "blocked", "publishing",
     "整理候选包、图标截图、商店文案、权限用途、数据说明、公开链接和具体账号待办。",
     "本票约定材料完整并对应已验收版本；清楚列出尚待提交或本人操作的项目。准备好不等于已上线。"),
    ("T-005", "launch-tracking", "提交与上线验证", ["T-004"], "blocked", "publishing",
     "记录分发决定、具体发布授权、提交记录、审核反馈、安装入口及发布后首次使用证据。",
     "目标用户可从所选渠道安装实际发布版本，核对版本并完成首条用户任务；有对应证据。"),
)
DELIVERY_GOALS = {
    "local": {
        "label": "在本机使用",
        "required_tasks": ["T-002", "T-003"],
        "outside_scope": ["T-004", "T-005"],
        "close": "实施 T-002 和独立验收 T-003 满足各自关闭条件，能够在本机安装并使用；发布准备与上线跟踪不属于本次交付。",
    },
    "materials": {
        "label": "做好插件和发布材料",
        "required_tasks": ["T-002", "T-003", "T-004"],
        "outside_scope": ["T-005"],
        "close": "实施 T-002、独立验收 T-003 和发布准备 T-004 满足各自关闭条件；提交与上线跟踪不属于本次交付。",
    },
    "live": {
        "label": "完成发布并验证可安装",
        "required_tasks": ["T-002", "T-003", "T-004", "T-005"],
        "outside_scope": [],
        "close": "实施 T-002、独立验收 T-003、发布准备 T-004 和上线跟踪 T-005 全部满足各自关闭条件；目标渠道可安装且首用验证有证据。",
    },
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def bundled_methods():
    skill_root = Path(__file__).resolve().parents[1]
    return {
        name: {
            "kind": "bundled_method",
            "source": relative_path,
            "source_base": "skill_root",
            "status": "available" if (skill_root / relative_path).is_file() else "missing",
            "host_activation": "not_applicable",
            "execution_proven": False,
        }
        for name, relative_path in METHODS.items()
    }


def make_task(definition, goal="live", complexity="undetermined"):
    task_id, task_type, title, dependencies, status, method, scope, close = definition
    goal_settings = DELIVERY_GOALS[goal]
    in_scope = task_id not in goal_settings["outside_scope"]
    if task_id == "T-001":
        close = goal_settings["close"]
    elif not in_scope:
        status = "not_in_scope"
    scope_note = "属于本次交付范围。" if in_scope else "本次范围外，未执行。保留模板供以后明确扩展目标时使用，不是当前阻塞项。"
    remaining = "本票范围尚未交付。" if in_scope else "本票不在本次范围内，无当前交付待办。"
    next_action = "核对前置条件，并替换与本票实际范围有关的待填项。" if in_scope else "无需执行；以后扩大目标时先更新规格、依赖和交付目标。"
    parent = "none" if task_id == "T-001" else "T-001"
    children = "T-002, T-003, T-004, T-005" if task_id == "T-001" else "none"
    precondition = (
        "读取用户原话和已有约定，明确当前阻塞范围的问题。"
        if task_id == "T-001" else
        "spec.md 中首版范围、首条成功路径及当前重要决定已明确。"
        if task_id == "T-002" else
        "前置任务已满足各自关闭条件，证据与当前候选版本一致。"
    )
    required_skills = {
        "scope": "优先由 product-designer 定义进入、操作、结果、再次使用、退出与恢复的体验 AC；当前宿主没有该技能时执行 references/product-loop.md portable fallback 并记录。使用 chrome-extensions；新建插件使用 extension-create；复杂项目首次或配置缺失使用 setup-matt-pocock-skills，使用 to-spec 发布正式主票后再使用 to-tickets；仅外部反馈或旧票待分流时使用 triage。",
        "implementation": "chrome-extensions；新建插件使用 extension-create；故障时使用 diagnosing-bugs；完成后使用 code-review；复杂项目每张实施票必须使用 implement。",
        "acceptance": "优先由 product-designer 复核真实连续两轮使用的闭环；缺失时执行 product-loop portable fallback。code-review 的 Spec 轴检查体验 AC 是否完整；验收发现故障先使用 diagnosing-bugs，修复后重验；必须通过已核实的受控浏览器工具实际加载插件完成端到端验证并记录 repeat_use。",
        "release-preparation": "code-review 审查最终候选；若构建文件变化，使用 Playwright MCP 重验受影响的真实插件路径。",
        "launch-tracking": "若发布或首用检查失败，使用 diagnosing-bugs；实际安装版本仍须完成端到端验证。",
    }[task_type]
    complexity_note = (
        "当前为复杂插件：主执行者自行使用 setup-matt-pocock-skills（首次/缺少配置）→ to-spec → 发布正式主票 → to-tickets → implement，"
        "按明确文件/模块所有权逐票开发和独立验收；未完成拆分与依赖检查不得开始实施。"
        "本目录任务仅为调度索引，须链接这些 skills 产生的 .scratch/<feature>/spec.md 和 issues/*.md；不得维护第二套权威规格或工单。"
        if complexity == "complex" else
        "当前为简单插件，保留精简本地工单；必须执行对应 skills、code-review 与真实端到端验收。"
        if complexity == "simple" else
        "复杂度尚未判定；主执行者根据需求自行记录 simple/complex 与理由，实施前必须完成判断；复杂时走正式主票和拆票流程。"
    )
    text = f"""# {task_id} {title}

本文件{'仅为复杂项目调度索引，正式规格和工单由对应 skills 生成并在此链接' if complexity == 'complex' else '是正式本地任务记录'}；下列待填项不代表功能已完成。由主执行者汇总更新，避免多个代理并发覆盖。

## 任务字段

- 编号：{task_id}
- 类型：{task_type}
- 状态：{status}
- 本次交付目标：{goal_settings['label']}（{goal}）
- 范围说明：{scope_note}
- 父任务：{parent}
- 子任务：{children}
- 前置依赖：{', '.join(dependencies) or 'none'}
- 开始条件：{precondition}
- 修改范围：待根据首版规格填写具体文件/模块；范围重叠时串行执行。
- 对应规格：../spec.md
- 已确认决定：../decisions.md（仅引用实际已确认条目）
- 所需方法：技能包中的 {METHODS[method]}
- 所需外部 skills：{required_skills}
- skills 来源、修订与实际可用证据：待填写；必须实际读取适用 SKILL.md 并执行，保存读取及执行证据。文件存在、同名方法或包内说明不能代替技能调用。
- 真实验收工具：默认 Playwright MCP；须在真实浏览器安装/加载插件并从原生入口完成用户路径。环境不支持时先记录原因并询问用户安装/启用或采用推荐替代，未获选择不得静默切换。

{complexity_note}

## 本票范围

{scope}

## 验收条目

| 编号 | 前置条件 | 用户操作 | 预期结果 | 验证方法 | 实际结果 | 证据 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| {task_id}-AC-01 | 待从规格填写 | 待填写 | 可观察结果待填写 | 真实环境或适用检查待填写 | 未执行 | 无 | 未验证 |

按功能增加失败、取消、重复操作、重开与升级场景；不适用项说明理由，不删除失败项。

## 版本与检查证据

- 候选版本/本地提交/可恢复快照：未保存
- 实际构建包及校验值：无
- 测试环境、浏览器版本、测试网页：待记录
- 用户路径证据：无
- 规范审查结论及证据：未审查
- 规格审查结论及证据：未审查
- 已执行 skills、源文件/修订、读取证据及按技能完成的产出：无
- Playwright MCP 加载/安装及端到端操作证据：无
- 工具不支持原因、推荐替代与用户选择证据（仅适用时填写）：无
- 失败复现、关联修复任务及复验结果：无
- 人工检查与尚待本人操作：按实际需要填写

## 关闭条件

{close}

{scope_note}

勾选或改变状态前核对原始证据；编写说明、检测到工具或生成包均不能代替真实检查。

## 未完成事项与下一步

- 未完成事项：{remaining}
- 下一步：{next_action}
- 发布准备状态：未开始
- 提交记录、审核反馈、商店/分发入口、安装验证：无（适用发布任务时逐项记录）

## 变更记录

- 初始化：建立正式本地任务，未执行开发、审查、验收或发布。
"""
    index = {
        "id": task_id, "type": task_type, "path": f"tasks/{task_id}.md",
        "parent": None if task_id == "T-001" else "T-001",
        "children": ["T-002", "T-003", "T-004", "T-005"] if task_id == "T-001" else [],
        "depends_on": dependencies, "status": status,
        "in_scope": in_scope,
        "closing_dependencies": goal_settings["required_tasks"] if task_id == "T-001" else [],
        "scope_ready": False, "version": None, "evidence": [],
    }
    return text, index


def initialize(project, name=None, idea="", browser=None, goal=None,
               complexity=None, complexity_reason=""):
    project = Path(project).expanduser().resolve()
    record = project / RECORD_DIR
    if record.exists() or record.is_symlink():
        raise ValueError(f"已有 {RECORD_DIR}，未覆盖任何记录。请运行 status 后读取已有任务继续。")
    name = (name or project.name).strip()
    if not name:
        raise ValueError("项目名称不能为空。")
    delivery_goal = goal or "live"
    if delivery_goal not in DELIVERY_GOALS:
        raise ValueError("交付目标须为 local、materials 或 live。")
    complexity_value = complexity or "undetermined"
    if complexity_value not in ("simple", "complex", "undetermined"):
        raise ValueError("复杂度须为 simple 或 complex，省略时待主执行者判断。")
    goal_settings = DELIVERY_GOALS[delivery_goal]
    goal_status = "provided" if goal else "assumption"
    project.mkdir(parents=True, exist_ok=True)
    task_files, tasks = {}, []
    for definition in TASK_DEFINITIONS:
        content, entry = make_task(definition, delivery_goal, complexity_value)
        task_files[entry["path"]] = content
        tasks.append(entry)
    target_browser = None if browser == "undecided" else (browser or "chrome")
    browser_status = "provided" if browser and browser != "undecided" else "undecided" if browser else "assumption"
    state = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now(), "updated_at": now(),
        "project": {
            "name": name, "root": "..", "idea": idea,
            "target_browser": {"value": target_browser, "status": browser_status,
                               "source": "explicit_cli_argument" if browser else "reversible_first_iteration_default"},
            "distribution": {"channel": None, "audience": None, "status": "undecided"},
            "delivery_goal": {
                "value": delivery_goal, "status": goal_status,
                "source": "explicit_cli_argument" if goal else "skill_default",
            },
        },
        "record_policy": {
            "authority": (["workflow.authoritative_artifacts", "decisions.md"] if complexity_value == "complex"
                          else ["spec.md", "decisions.md", "tasks/*.md"]),
            "state_role": "index_only", "paths_relative_to": RECORD_DIR,
            "updates": "single_writer; preserve last valid state before atomic replacement",
            "resume": "read authoritative documents; compare actual version and evidence before resuming",
        },
        "phase": "discovery",
        "workflow": {
            "complexity": {
                "value": complexity_value, "reason": complexity_reason,
                "status": "recorded" if complexity else "requires_agent_assessment",
                "source": "explicit_cli_argument" if complexity else "not_assessed",
                "decision_owner": "lead_agent",
            },
            "default_e2e_provider": DEFAULT_E2E_PROVIDER,
            "browser_choice": None,
            "required_skill_stages": [
                {"skill": skill, "stage": stage, "applies_when": condition,
                 "status": "not_executed", "source_path": None, "source_revision": None,
                 "read_evidence": [], "execution_evidence": []}
                for skill, stage, condition in REQUIRED_SKILLS
            ],
            "complex_chain": list(COMPLEX_CHAIN) if complexity_value == "complex" else [],
            "complex_chain_required_when": "complex_project",
            "parent_ticket": {"status": "not_published", "path_or_url": None, "evidence": []},
            "authoritative_artifacts": {"spec": None, "parent_ticket": None, "implementation_tickets": [],
                                        "paths_relative_to": "project_root", "produced_by_required_skills": True},
            "ticket_policy": "lead_agent_decides; native skill artifacts are authoritative; publish parent before decomposition; explicit file/module ownership; dependencies before implement; triage only for external feedback or existing tickets; independent review and real E2E",
        },
        "spec": {"path": "spec.md", "status": "awaiting_to_spec" if complexity_value == "complex" else "draft",
                 "role": "coordination_pointer" if complexity_value == "complex" else "authoritative_local_spec"},
        "decisions_path": "decisions.md", "progress_path": "progress.md",
        "tasks": tasks,
        "next_actions": [
            "读取已有要求与项目约定，补齐首版范围和可观察验收，沿用已明确的答案。",
            "运行 doctor 并用宿主工具验证当前步骤需要的实际执行能力。",
            "自行记录需求复杂度及理由；实际读取并执行适用的必需 skills，复杂时按项目配置、正式主票、拆票、implement 顺序推进。",
            "连接 Playwright MCP 并实测安装/加载插件能力；不支持时记录原因，请用户选择安装/启用或推荐的真实浏览器替代。",
            "仅对会影响当前实现的未定重要事项询问用户，再执行 T-002。",
        ],
        "needs_user": [],
        "capabilities": {
            "checked_at": None, "bundled_methods": bundled_methods(),
            "external_skills": [], "execution_tools": {"status": "unverified"},
            "development_software": {"status": "unverified"}, "doctor_report": None,
        },
        "milestones": {
            milestone: {"status": "not_started", "version": None, "evidence": []}
            for milestone in ("built", "accepted", "submitted", "live")
        },
        "release": {
            "status": "not_prepared", "candidate_version": None, "package": None,
            "publishing_intent": {"status": "not_established", "context_evidence": [],
                                  "readiness_notice": "not_shown"},
            "registration": {"status": "not_checked", "fee": None,
                             "payment_method_status": "not_checked"},
            "assets": {"status": "not_started", "required_missing": [],
                       "generation_status": "not_attempted", "waiting_for_user_upload": False},
            "preparation_in_scope": delivery_goal in ("materials", "live"),
            "submission_in_scope": delivery_goal == "live",
            "acceptance_task": "T-003", "preparation_task": "T-004", "tracking_task": "T-005",
            "channel": None, "submission": None, "store_url": None,
            "authorization_evidence": [], "first_use_evidence": [],
        },
    }
    browser_text = target_browser or "待确定"
    distribution_text = "本次仅本机使用，商店分发不在范围内" if delivery_goal == "local" else "未定，不自动公开发布"
    preparation_progress = "本次范围外（未执行）" if delivery_goal == "local" else "未准备"
    submission_progress = "未提交" if delivery_goal == "live" else "本次范围外（未执行）"
    live_progress = "未验证" if delivery_goal == "live" else "本次范围外（未执行）"
    documents = {
        "state.json": dump(state),
        "spec.md": f"""# {name}：首版说明

规格状态：draft。用户原话作为需求来源保存；初始化不会自动确认尚未明确的范围。此文件与正式任务共同作为依据。

## 用户原话

{idea or '尚未提供；先读取当前对话或请用户用一句话说明用途。'}

## 谁会用、在哪用、希望得到什么

- 使用者：待从用户已说明的要求填写
- 代表性网页/场景：待填写
- 首条完整用户故事：待填写
- 目标浏览器：{browser_text}（{browser_status}；默认只用于可逆的第一版建议）
- 本次交付目标：{goal_settings['label']}（{delivery_goal}；{goal_status}）
- 分发范围和渠道：{distribution_text}
- 复杂度：{complexity_value}；判断理由：{complexity_reason or '待主执行者根据需求自行记录'}

未明示的交付目标是 AI 暂定，不能当作用户已确认或发布授权；应沿用用户实际要求调整。保留未来发布任务模板不扩大本次范围。

## 首版范围与范围外事项

- 必须完成：待明确
- 暂缓事项：待明确
- 关键术语的实际含义：待明确
- 内容放在哪里、会不会发送出去、费用：按真实需要明确，不假定用户已同意

## 可观察验收

| 编号 | 前置条件 | 用户操作 | 预期结果 | 验证方法与证据 |
| --- | --- | --- | --- | --- |
| AC-01 | 待填写 | 待填写 | 待填写 | 待填写 |

## 重要决定及未决事项

决定和来源见 decisions.md；已由用户明确的要求直接沿用。只暂停依赖尚未回答的重要选择的步骤。

## 任务

主任务 T-001；实施 T-002；独立验收 T-003；发布准备 T-004；上线跟踪 T-005。
实施任务按完整用户功能继续拆分；本次主任务关闭条件：{goal_settings['close']}
范围外的任务保留并标为 not_in_scope，不要求执行或关闭它们。
复杂插件必须按 setup-matt-pocock-skills（首次/缺少配置）→ to-spec → 发布正式主票 → to-tickets → implement 推进，由主执行者自行安排独立模块与工单；triage 仅用于外部反馈或旧票分流。
本文件及初始任务仅为待完善记录，不证明已执行上述 skills、已发布正式主票或已完成拆分。
""",
        "decisions.md": """# 项目决定

按用户原话、已有记录或实际证据填写；区分用户已确认、AI 暂定、待决定。沉默不等于同意。

| 编号 | 要决定什么 | 答案 | 来源与日期 | 状态 | 影响规格/验收 | 替代旧决定 |
| --- | --- | --- | --- | --- | --- | --- |

初始化未添加任何用户确认。浏览器默认值仅记录在 state.json 与 spec.md 中作为暂定方案。
""",
        "progress.md": f"""# {name}：项目进度

当前：已建立项目记录，正在明确第一版。尚未开发、验收、提交或上线。

本次做到：{goal_settings['label']}（{goal_status}；暂定值不能替代用户已说明的目标或发布授权）。

接下来：从已有要求整理一条有用的功能和完成标准，再准备所需能力并开始制作。

待你处理：目前没有自动认定的待办；仅在实际遇到必要决定或本人操作时填写。

## 恢复说明

state.json 仅用于索引。继续前先阅读 spec.md、decisions.md 和当前任务，检查对应版本、构建包与证据是否还在。
文件存在仅证明有记录，须核对内容、版本和实际检查结果；不可仅凭旧进度文字报告完成。
每次变更由主执行者汇总，先保留上一次有效记录，再替换状态；不要存密码、验证码或密钥。

## 阶段结果

- 本地可试用：未开始
- 独立验收：未开始
- 发布材料：{preparation_progress}
- 提交审核：{submission_progress}
- 正式可安装及首用验证：{live_progress}
""",
        "evidence/README.md": """# 检查证据

这里只存本项目的检查结果和必要样例，不存密码、验证码、密钥或无关私人网页内容。
每份证据写明对应任务、候选版本/构建包、环境、操作、预期和实际结果、检查方式、时间和原始产出位置。
状态只能按事实填写：通过、失败、未验证、不适用（注明原因）。普通网页截图不能证明原生插件入口已打开。
在任务及 state.json 中使用相对 .extension-launch 的文件路径引用，例如 evidence/T-002-main-path.md。
""",
        **task_files,
    }
    if complexity_value == "complex":
        documents["spec.md"] = f"""# {name}：复杂项目规格入口

本文件仅为调度索引，不是另一份权威规格。尚未执行 to-spec，也未发布主票或创建独立模块工单。

- 需求来源：{idea or '读取当前对话中的用户原话'}
- 复杂度理由：{complexity_reason or '待主执行者记录'}
- 本次交付目标：{goal_settings['label']}（{delivery_goal}；{goal_status}）
- 正式规格：待 to-spec 生成 .scratch/<feature>/spec.md 后填入实际路径。
- 正式主票：待 to-spec 发布后记录实际路径/链接和发布证据。
- 子票：待 to-tickets 生成后记录 issues/*.md 的实际路径和模块所有权。

先使用 setup-matt-pocock-skills 完成首次/缺失配置，再执行 to-spec → 发布正式主票 → to-tickets → implement。
默认沿用这些 skills 的 Local Markdown 工作流，由主执行者自行做技术判断和拆分；更新 state.workflow.authoritative_artifacts 指向实际产物。
tasks/T-*.md 仅跟踪阶段依赖和验收证据，实施范围与验收标准以正式规格和子票为准。外部反馈或旧票需要分流时才使用 triage。
每票必须使用 code-review，并通过 Playwright MCP 实际加载插件完成端到端验证；发现问题必须使用 diagnosing-bugs。
"""
    # The exclusive directory creation also rejects concurrent initializers.
    record.mkdir(exist_ok=False)
    for relative, content in documents.items():
        destination = record / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as handle:
            handle.write(content)
    return {"status": "initialized", "record_directory": RECORD_DIR,
            "phase": "discovery", "spec_status": state["spec"]["status"], "created_files": list(documents),
            "delivery_goal": state["project"]["delivery_goal"],
            "message": "项目记录已建立；请核对要求后继续。未执行开发、验收或发布。"}


def detect_browser(name):
    candidates = [shutil.which(command) for command in BROWSER_COMMANDS[name]]
    system = platform.system()
    if system == "Darwin":
        app_names = {"chrome": "Google Chrome", "edge": "Microsoft Edge", "firefox": "Firefox"}
        executable = "firefox" if name == "firefox" else app_names[name]
        for root in (Path("/Applications"), Path.home() / "Applications"):
            candidates.append(str(root / f"{app_names[name]}.app" / "Contents" / "MacOS" / executable))
    elif system == "Windows":
        suffixes = {"chrome": "Google/Chrome/Application/chrome.exe",
                    "edge": "Microsoft/Edge/Application/msedge.exe",
                    "firefox": "Mozilla Firefox/firefox.exe"}
        for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            directory = os.environ.get(key)
            if directory:
                candidates.append(str(Path(directory) / suffixes[name]))
    detected = next((path for path in candidates if path and Path(path).is_file() and os.access(path, os.X_OK)), None)
    return {"status": "detected" if detected else "missing", "executable": detected,
            "version": None, "connection": "unverified", "extension_loading": "unverified"}


def inspect_skills(directories):
    """Inspect only case-insensitive SKILL.md names, never host configuration."""
    result = []
    for supplied in directories:
        directory = Path(supplied).expanduser()
        entry = {"directory": str(directory), "status": "missing", "skills": []}
        if directory.is_dir():
            entry["status"] = "detected"
            # Standard root/name/SKILL.md plus a directly supplied skill folder.
            paths = [path for pattern in ("*", "*/*", "*/*/*")
                     for path in directory.glob(pattern) if path.name.lower() == "skill.md"]
            for path in sorted(set(paths)):
                if path.is_file():
                    name = None
                    try:
                        with path.open(encoding="utf-8") as handle:
                            if handle.readline().strip() == "---":
                                for _ in range(100):
                                    line = handle.readline()
                                    if not line or line.strip() == "---":
                                        break
                                    match = re.fullmatch(r"name:\s*(.+?)\s*", line.rstrip("\n"))
                                    if match:
                                        name = match[1].strip().strip("\"'")
                    except (OSError, UnicodeError):
                        pass
                    entry["skills"].append({
                        "directory_name": path.parent.name,
                        "name": name, "source_path": str(path.resolve()),
                        "metadata": str(path.relative_to(directory)),
                        "status": "detected", "host_activation": "unverified",
                        "compatibility": "unverified", "source_revision": None,
                        "invocation": "unverified", "execution_evidence": [],
                    })
        result.append(entry)
    return result


def doctor(project, skills_dirs=()):
    software = {"python": {"status": "detected", "version": platform.python_version(),
                           "minimum_version_satisfied": sys.version_info >= (3, 9)}}
    for program in ("node", "npm", "git"):
        executable = shutil.which(program)
        software[program] = {"status": "detected" if executable else "missing",
                             "executable": executable, "version": None, "execution": "unverified"}
    browsers = {name: detect_browser(name) for name in BROWSER_COMMANDS}
    external_skills = inspect_skills(skills_dirs)
    found = [skill for directory in external_skills for skill in directory["skills"]]
    required_skills = []
    for name, stage, condition in REQUIRED_SKILLS:
        matches = [item for item in found if name.lower() in {
            item["directory_name"].lower(), (item["name"] or "").lower()}]
        required_skills.append({
            "skill": name, "stage": stage, "required_when": condition,
            "status": "detected" if matches else "missing",
            "source_paths": [item["source_path"] for item in matches],
            "host_activation": "unverified", "invocation": "unverified",
            "read_evidence": [], "execution_evidence": [],
            "bundled_substitute_allowed": name in PORTABLE_FALLBACKS,
            "portable_fallback": PORTABLE_FALLBACKS.get(name),
        })
    return {
        "schema_version": SCHEMA_VERSION, "checked_at": now(), "mode": "read_only_detection",
        "project_exists": Path(project).expanduser().is_dir(),
        "os": {"name": platform.system(), "release": platform.release(), "architecture": platform.machine()},
        "software": software, "browsers": browsers,
        "bundled_methods": bundled_methods(),
        "external_skills": external_skills,
        "required_skills": required_skills,
        "skill_discovery": "explicit_directories_only" if skills_dirs else "not_requested; use --skills-dir from the host",
        "execution_tools": {"default_e2e_provider": DEFAULT_E2E_PROVIDER,
                            "playwright_mcp": "unverified", "browser_connection": "unverified", "screenshot": "unverified",
                            "extension_installation": "unverified", "host_file_and_shell_tools": "unverified"},
        "overall": "requires_runtime_verification", "ready_to_develop": None,
        "notes": [
            "检测到命令或 SKILL.md 不代表软件可运行、技能已生效或浏览器已连接。",
            "适用的必需 skills 缺失时先通过当前宿主或 Skill CLI 补齐；只有 portable_fallback 非空时才能执行包内等价流程，并须记录。",
            "受控浏览器工具加载插件和操作原生入口的能力必须实测；Playwright MCP 不支持时请用户选择安装/启用或经核实的替代，不能静默换工具。",
            "Node/npm 是否必需取决于项目模板；纯 JavaScript 模板可以不需要。",
            "下一步由宿主验证当前任务所需能力；本检查不安装软件、不读取凭证、不改项目状态。",
        ],
    }


def inspect_status(project):
    record = Path(project).expanduser().resolve() / RECORD_DIR
    state = json.loads((record / "state.json").read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("不支持或缺少 state.json schema_version；请先审阅记录，不自动迁移。")
    errors, warnings, file_checks = [], [], []

    def check(relative, kind):
        if not isinstance(relative, str) or not relative:
            errors.append(f"{kind} 路径为空或格式错误")
            return
        path = (record / relative).resolve()
        try:
            path.relative_to(record.parent)
        except ValueError:
            errors.append(f"{kind} 路径超出项目：{relative}")
            return
        exists = path.is_file()
        file_checks.append({"path": relative, "kind": kind, "exists": exists, "content_verified": False})
        if not exists:
            errors.append(f"缺少 {kind}：{relative}")

    check(state.get("spec", {}).get("path"), "specification")
    check(state.get("decisions_path"), "decisions")
    check(state.get("progress_path"), "progress")
    for task in state.get("tasks", []):
        check(task.get("path"), "task")
        for evidence in task.get("evidence", []):
            check(evidence.get("path") if isinstance(evidence, dict) else evidence, "task_evidence")
        if task.get("status") in ("complete", "completed", "done", "closed") and not task.get("evidence"):
            warnings.append(f"{task.get('id')} 索引标为完成但没有证据索引；需阅读正式任务并核实关闭条件。")
    for milestone, data in state.get("milestones", {}).items():
        evidence = data.get("evidence", [])
        for pointer in evidence:
            check(pointer.get("path") if isinstance(pointer, dict) else pointer, f"{milestone}_evidence")
        if data.get("status") not in ("not_started", "pending", "unverified", "blocked") and not evidence:
            warnings.append(f"{milestone} 状态已推进但没有证据索引，不可据此宣称完成。")
    release = state.get("release", {})
    package = release.get("package")
    if package:
        check(package.get("path") if isinstance(package, dict) else package, "release_package")
    for field in ("authorization_evidence", "first_use_evidence"):
        for pointer in release.get(field, []):
            check(pointer.get("path") if isinstance(pointer, dict) else pointer, field)
    return {
        "schema_version": SCHEMA_VERSION, "phase_index": state.get("phase"),
        "release_status_index": state.get("release", {}).get("status"),
        "files": file_checks, "errors": errors, "warnings": warnings,
        "next_actions_index": state.get("next_actions", []), "needs_user_index": state.get("needs_user", []),
        "resume_requires_document_and_version_review": True,
        "message": "这是索引及文件存在性检查。继续前须阅读正式任务、核对当前版本与证据内容；本命令不会确认完成或推进阶段。",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="建立并检查浏览器插件项目的正式本地记录。")
    commands = parser.add_subparsers(dest="command", required=True)
    initialize_parser = commands.add_parser("init", help="创建记录；拒绝覆盖已有 .extension-launch")
    initialize_parser.add_argument("project")
    initialize_parser.add_argument("--name")
    initialize_parser.add_argument("--idea", default="")
    initialize_parser.add_argument("--browser", choices=("chrome", "edge", "firefox", "undecided"))
    initialize_parser.add_argument("--goal", choices=("local", "materials", "live"),
                                   help="本机使用、完成发布材料或上线；省略时 live 仅为未确认的暂定目标")
    initialize_parser.add_argument("--complexity", choices=("simple", "complex"),
                                   help="由主执行者判定需求复杂度；省略时记录 undetermined，实施前须判断")
    initialize_parser.add_argument("--complexity-reason", default="", help="主执行者判断需求复杂度的具体理由")
    doctor_parser = commands.add_parser("doctor", help="只读检测；不会宣称能力已连接")
    doctor_parser.add_argument("project")
    doctor_parser.add_argument("--skills-dir", action="append", default=[], help="宿主提供的技能目录；可重复")
    doctor_parser.add_argument("--report", type=Path, help="另存 JSON 报告（新文件；不会覆盖或更新 state）")
    status_parser = commands.add_parser("status", help="读取状态索引并核对文件是否存在")
    status_parser.add_argument("project")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = initialize(args.project, args.name, args.idea, args.browser, args.goal,
                                args.complexity, args.complexity_reason)
        elif args.command == "doctor":
            result = doctor(args.project, args.skills_dir)
            if args.report:
                with args.report.expanduser().open("x", encoding="utf-8") as handle:
                    handle.write(dump(result))
        else:
            result = inspect_status(args.project)
        print(dump(result), end="")
        return 1 if result.get("errors") else 0
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print(dump({"status": "error", "message": str(error)}), file=sys.stderr, end="")
        return 1


if __name__ == "__main__":
    sys.exit(main())
