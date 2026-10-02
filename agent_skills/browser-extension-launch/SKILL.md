---
name: browser-extension-launch
description: >-
  Builds, tests, packages, and prepares Chrome Manifest V3 extensions for store
  launch from a plain-language idea. Use when the user asks to create a browser
  extension, continue an existing extension, debug failures, prepare a release,
  or recover from Chrome Web Store review feedback.
license: MIT
compatibility: Requires local file and shell access plus a controlled browser capable of loading unpacked extensions; publishing requires the user's own Chrome Web Store account.
metadata:
  author: "xiehuan123"
  version: "1.0.0"
  source: "https://github.com/xiehuan123/browser-extension-launch"
---

# 浏览器插件一站式上线

你负责把插件做出来并推进交付，用户负责表达需要、体验结果及必要的本人操作。默认用户只经历：**说想法 → 试用第一版 → 说哪里要改 → 确认具体发布安排 → 获得安装入口**。

## When to Use

- Use when a user wants to turn a plain-language idea into a browser extension.
- Use when continuing, debugging, packaging, submitting, or releasing an existing extension.
- Do not use for ordinary website development or browser-extension knowledge questions that require no implementation.

本技能是宿主无关的共享 skill，负责编排子技能、受控浏览器工具和本地辅助工具。开始时按 [Agent 兼容说明](references/host-compatibility.md) 识别当前宿主并验证文件、终端、浏览器和子技能能力；不能把安装成功当成工具已可用。首次发布适配以 Chrome / Manifest V3 为基线。未指定浏览器时将 Chrome 记为可修改的建议并继续独立工作；用户指定其他浏览器时遵从选择，另核实该平台规则，不能宣称本包的 Chrome 检查器已覆盖它们。

## 执行约定

- 新项目默认正式本地任务，不要求 GitHub、服务器、付费域名或独立原型。已有项目先读其约定，保留现有任务系统和已确认设计。
- 主动选择可逆技术方案、检查环境、创建任务、制作、排错和验证。已有答案与授权沿用，不让用户逐步批准常规动作。
- 事实自己查；只有会改变用途、数据去向、费用或分发承诺的重要未知项才问。用日常场景解释影响，一轮只处理当前必要问题；等待时继续不依赖答案的工作。重要选择不以沉默当确认。
- 对用户说“内容留在这台电脑”“安装包”“已经检查哪些操作”。工单、Manifest、E2E、构建工具等留在后台；平台按钮名称可准确引用。
- 写代码、截图、静态检查、验收、上传、审核、上线各有独立证据。未运行的检查写“未验证”，不能以工具缺失、旧截图或用户没报错判通过。
- **真实验收是交付门槛。** 首次可用版、每张实施票和最终发布候选包，必须使用当前宿主中已核实能加载扩展并操作原生入口的受控浏览器工具，完成端到端核心操作及适用的关闭重开验证，保存证据并通过验收门禁，才能称为可用、交付完成或关闭任务。Playwright MCP 是首选参考实现；模拟 Chrome API、静态检查、单独打开弹窗 HTML 均不能替代。具体适配和证据见 [Agent 兼容说明](references/host-compatibility.md) 与 [独立验收](references/acceptance.md)。
- 当前宿主缺少可用浏览器通道或无法完成真实入口时，按 [依赖准备](references/dependencies.md) 给出具体原因，询问用户是否安装/启用或选择推荐的受控替代方案，等待选择；验收保持 `blocked`，不能静默改用日常浏览器或跳过此节点。已有明确选择沿用，不逐项重新请示。人工辅助后仍须接回真实验证。仅用户明确只要源码或要求中止时，可按该范围交出源码并标明未验收。
- 缺权限、等待本人操作或商店审核时保存状态，说明下一步；暂停依赖该条件的工作。没有实际持续跟踪能力，不承诺后台监控。

## 产品使用闭环

新建或改变用户流程时，必须实际执行 `product-designer`，先按 [产品使用闭环](references/product-loop.md) 把进入、核心动作、结果处理、继续使用、退出和恢复写入现有规格。基本操作由 AI 主动补齐，重要体验取舍信息不足时才询问用户。最终真实验收必须包含 `repeat_use` 连续两轮使用，产品体验复核与技术结果分别记录；缺基本闭环不能因技术用例通过而交付。

## 效率与收尾

规划、最终审查或返工时读取 [高效交付](references/efficient-delivery.md)：先验证开发环境和特殊浏览器能力，提前列出 AC 与硬规范；按风险拆票、按改动影响复验。同一候选的真实证据和双轴审查可明确覆盖多个就绪工单，最终跨模块验收仍必须实际执行。文档与归档未改变运行包时不重复产品测试；目标内验收、审查和交付文件齐全后一次收尾。用户要求独立 CLI 或完整会话时，按该参考保留实际输入、回复和原始记录。

## 必须执行的节点

“执行 skill”指定位并读取其真实入口及所需资源，按流程产生相应结果，记录来源、输入、输出和验证；只出现名字、文件存在或读过说明不算完成。优先执行下列命名子技能；宿主无法安装或调用时，只能采用 [Agent 兼容说明](references/host-compatibility.md) 中定义的等价实现，并明确记录 fallback，不能声称原技能已运行。

| 节点 | 必须执行 | 完成证据 |
| --- | --- | --- |
| 新建/改变用户流程及体验验收 | `product-designer` | 现有规格中的完整闭环、体验 AC、决策依据和真实连续使用复核 |
| 扩展设计、开发与发布 | `chrome-extensions` | 实际采用的 API/权限/发布规则及对应产物 |
| 新建插件 | `extension-create` | 已明确参数、实际脚手架和入口配置、基础构建结果；已有项目不重复初始化 |
| 发生故障或验收失败 | `diagnosing-bugs` | 可判定失败的复现、诊断、修复及原场景复验 |
| 每张实施票及版本审查 | `code-review` | 固定基线、实际变更、规格，以及规范/规格两个独立审查结果 |
| 首版、实施票、最终版本验收 | 受控浏览器工具；首选 Playwright MCP | 当前产物真实加载、原生入口、完整操作及重开证据；不支持时必须取得用户环境选择 |
| 复杂插件 | `setup-matt-pocock-skills` → `to-spec` → `to-tickets` → `implement` | 项目约定、已发布主工单、带依赖的子工单、按模块分工逐票实现；见 [复杂插件编排](references/complex-workflow.md) |

缺少必需 skill 时按已核实来源和当前 Agent 目标通过 Skill CLI 或宿主安装器补齐后执行，不以名字相近的未知 skill 代替。只有兼容说明明确允许的 portable fallback 才能替代，并必须记录真实执行方式。安装与技术拆分尽量自动完成；浏览器工具不支持时的替代选择、无法推断的产品承诺和真实账号费用仍由用户决定。来源清单见 [依赖准备](references/dependencies.md)。

## 从当前项目继续

1. 确定项目目录；已有 `.extension-launch/` 时先运行 `project.py status`，再读规格、任务和证据。已有其他任务系统则从那里恢复。不要凭聊天回忆重建或覆盖任务。
2. 按 [Agent 兼容说明](references/host-compatibility.md) 和 [依赖准备](references/dependencies.md) 检测必需技能、受控浏览器工具和开发软件，分别记录检测、读取及执行状态；缺什么补什么，不把文件存在当作能力已就绪。
3. 主代理自行判断复杂度并写明理由。简单插件走最小本地记录；复杂插件必须走 [复杂插件编排](references/complex-workflow.md)，由 AI 发布规格工单、拆票和分配独立模块。`project.py init --complexity simple|complex --complexity-reason <理由>` 建立调度记录，按 [任务与恢复](references/workflow.md) 关联真正的规格和工单。依据用户指定终点传 `--goal local`（先自己用）、`--goal materials`（仅材料）或 `--goal live`（上线）；默认值不当用户已确认。范围外发布任务保持不适用，不列为本人待办。草拟内容必须补实，不是已确认需求。
4. 按下表选择下一步；每阶段结束由主代理汇总进度、证据、未解决问题和下一动作。不要把整张表抛给新手。

| 当前需要 | 读取并执行 | 前进依据 |
| --- | --- | --- |
| 想法或需求变化 | [任务与恢复](references/workflow.md) | 范围、数据承诺、成功路径可实施；必要答案已记录 |
| 制作、修复第一版 | [开发与排错](references/development.md) | 当前版本真实安装、原生入口及逐票功能通过，有证据和可恢复版本 |
| 整体检查、准备新版本 | [独立验收](references/acceptance.md) | 当前候选包必需真实场景通过，失败已修复复验，验收门禁通过 |
| 上架、被拒、上线或更新 | [发布与维护](references/publishing.md) | 实际后台记录及商店安装结果 |

## 本地辅助工具

路径相对本技能目录解析。以下供 AI 执行，替换占位参数并按宿主正确引用路径，不让用户拼命令。脚本需 Python 3.9+、标准库，无需第三方 Python 包。没有 Python 时依对应参考用宿主文件工具建立相同记录或检查，不能声称脚本已运行。

```text
python3 <skill-dir>/scripts/project.py doctor <project-dir>
python3 <skill-dir>/scripts/project.py init <project-dir> --name <项目名> --idea <用户原话>
python3 <skill-dir>/scripts/project.py status <project-dir>
python3 <skill-dir>/scripts/release_bundle.py check <build-dir> --report <新报告路径>
python3 <skill-dir>/scripts/release_bundle.py pack <build-dir> --output <新ZIP路径> --report <新报告路径>
python3 <skill-dir>/scripts/acceptance_gate.py fingerprint <build-dir>
python3 <skill-dir>/scripts/acceptance_gate.py check <build-dir> --evidence <真实验收JSON路径> --report <新的gate-report.json路径>
```

`doctor` 只证明检测到文件或软件，不能证明浏览器已连接。`check` / `pack` 只检查 Chrome 包的静态结构及部分风险；警告需逐项复核，成功退出不等于真实验收或商店批准。用 `--previous-version` 检查更新版本；报告及 ZIP 放在构建目录外，不覆盖旧成果。

交付前先用 `fingerprint` 取得当前构建的 `candidate` 指纹，再据实际操作填写真实验收 JSON，最后执行门禁 `check` 并在任务中保存新生成的 `gate-report.json` 路径。只有 `gate_passed: true` 且有可核对的真实操作记录才可关闭依赖交付；指纹计算和机器检查本身不证明操作发生。证据字段与调用方式见 [验收参考](references/acceptance.md)。

内置 [参考模板](assets/starter/chrome-mv3/manifest.json) 用于阅读或接手已有样例，不替代新建项目必须执行的 `extension-create`。已有项目不复制覆盖。

## 按上下文触发发布协助

只有上下文已明确用户要商店发布/上线时，才提醒 Google 账号、开发者注册、首次 5 美元注册费和付款页支持的国际线上支付卡等准备事项；不是固定开场阶段，不因技能名称或默认 goal=live 推断用户要注册付款。按 [发布与维护](references/publishing.md) 在内置浏览器协助填写用户已提供或已明确采用的名称、描述、图片和宣传资料。素材生成不可用时停在素材步骤，请用户上传后再继续，不能用占位图通过。

## 对用户的交付

交付经真实验收通过的结果及短操作说明，说清做到哪里、依据什么、还需本人做什么。已授权工作持续推进到指定终点；必需真实验收未通过时继续修复或补齐能力，实际外部阻塞时留下 `blocked` 状态及可恢复记录，不宣称可用交付完成。

- 第一版：已实际安装并从原生入口验收的目录、核心操作结果、适用的重开持久化证据及限制。反馈直接改这一版，无默认原型评审。
- 发布准备：最终 ZIP 解压后真实验收通过及门禁报告、真实截图和图标、可粘贴文案、权限数据说明、必要公开链接、具体分发及发布安排。材料做好再处理尚缺授权；不得以“想上线”代填未确认的身份声明或费用选择。
- 审核期间：实际提交记录、当前状态、下次由谁以何种方式检查。不把上传说成提交或上线。
- 上线完成：目标用户可安装的商店入口、匹配版本、从商店安装后首用通过的证据、使用说明与反馈入口。插件使用者不需要本技能或开发环境。

规则根据随需求提供的三份调研提炼，包内不依赖原作者电脑目录或 StyleSnip 私有工单。官方事实入口和核查日期见发布参考。
