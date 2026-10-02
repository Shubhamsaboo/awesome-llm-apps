# 必需能力、子技能来源和浏览器工具

先读 [Agent 兼容说明](host-compatibility.md)。这是跨宿主依赖编排：优先执行下面的命名技能；缺失时按核实来源用 Skill CLI 或宿主安装器补齐。只有兼容说明明确允许的 portable fallback 或经核对覆盖同一能力的宿主原生技能可以替代，必须记录真实来源与差异，不能冒充命名技能已执行。

## 哪些节点必须用什么

| 节点 | 必需依赖 | 适用条件 |
| --- | --- | --- |
| 新建/改变用户流程及体验验收 | product-designer | 拆票前定义闭环与体验 AC，验收时复核连续使用和恢复路径 |
| 扩展设计、开发、修改和商店准备 | chrome-extensions | 对应阶段必须读取并执行相关部分 |
| 初始化插件 | extension-create | 每个新项目；已有项目记录已有脚手架，不重复初始化 |
| 可复现故障、运行或验收失败 | diagnosing-bugs | 一旦发生就进入完整诊断循环，不能用短排错段落替代 |
| 实施票与候选版本审查 | code-review | 提供真实比较基线与规格，执行两个独立审查维度 |
| 真实端到端验收 | 受控浏览器工具；首选 Playwright MCP | 必须加载实际插件并操作原生入口；不支持时必须询问安装/启用或替代选择 |
| 复杂项目配置及工单 | setup-matt-pocock-skills、to-spec、to-tickets、implement | 主代理自行判定复杂后强制，完整顺序见 complex-workflow.md |
| 工程链的条件依赖 | tdd、triage、domain-modeling 等 | 按实际子技能触发条件执行；triage 不加在每张新就绪票前 |

product-designer 在上表节点必需执行，具体见 [产品使用闭环](product-loop.md)；ui-designer 在界面节点按需调用，有动效再用 motion-designer、有新图像再用 imagegen。它们不替代上述必需技能。现代 Web API 等确实需要 modern-web-guidance 时按相关技能引用补齐，不一次安装无关技能。

## 已维护的来源清单

机器可读的 [required-skills.json](required-skills.json) 保存已核实仓库、精确子目录、固定修订、许可及入口哈希。先复用用户当前版本；本地文件与上游不相同并不意味着应该升级，先读真实内容，保留定制并记录兼容性。

- chrome-extensions：GoogleChrome/modern-web-guidance，skills/chrome-extensions，Apache-2.0。
- extension-create：quangpl/browser-extension-skills，skills/extension-create，MIT。
- 六个工程主链技能：mattpocock/skills，skills/engineering/<name>，MIT。本地部分技能与所记录上游版本不同，分别保存本地核查哈希与上游哈希，不伪称本地安装于该提交。
- product-designer：已核实部分宿主安装的实际入口及哈希，来源未核实为公开仓库，不能臆造下载地址。优先复用宿主版本；缺失时按兼容说明执行 `product-loop.md` portable fallback，并明确记录没有运行命名技能。
- Playwright MCP：microsoft/playwright-mcp / @playwright/mcp，固定参考版本及配置见 [Playwright MCP](playwright-mcp.md)。它是执行工具，不是安装一个同名 SKILL.md 就可用。

## 查找、安装、读取和执行分开

1. 获取宿主公开技能与工具清单，再检查其明确的技能目录及必需技能位置。用户提到与 diagnosing-bugs 同级时检查该目录，包括显式调用型技能、大小写入口和有权限读取的链接；不能因为未出现在自动列表就说没安装。不扫描凭据配置。
2. 运行 `project.py doctor PROJECT --skills-dir DIR` 查看必需技能的 detected/missing；它不证明已激活或已执行。阶段进入前解析真实入口、读取 SKILL.md 及该阶段引用文件，按宿主的显式调用机制执行。宿主没有专门调用命令时，显式读取并逐步执行真实技能，而非声称调用了不存在的命令。
3. 缺失时读取 skill-installer 并用其公开仓库安装器按清单固定来源补齐；宿主另有安装器时使用相应等效安装接口。参数形状为 `install-skill-from-github.py --repo <repo> --ref <ref> --path <path>`。安装的是完整技能目录及引用资源，不只下载入口。自动完成当前任务已授权的必要安装，不覆盖旧技能或把自己的私人目录当下载源。
4. 核对入口、资源和来源；需要宿主重载时保存 pending_reload 及恢复动作，重载后再查可用性。无法安装或来源无法核实时明确具体缺项并保持对应步骤阻塞，不用包内文字替代必需依赖。
5. 执行前准备输入，执行后保存真实输出及验证结果。`source_path` / `source_revision` / `read_evidence` / `execution_evidence` / `status` 写入 workflow.required_skill_stages。存在、已读取、已执行三个状态分开；子技能阶段有产物且核对完成才更新状态。

用户已经明确授权这条自动主链。对关闭自动触发的 to-spec/to-tickets/implement 等进行显式编排，不修改其全局触发配置；新手不必手动输入每个技能。技术选型、拆分、依赖和本地发布等机械确认由主代理按授权提供给子技能，具体适配见 [复杂流程](complex-workflow.md)。

必需调用不等于照抄样例。extension-create 的框架问题由 AI 根据目标预先选定并传入；必须真正执行所选脚手架、配置入口和检查构建。已有项目不强行重建。示例的广泛网站权限不自动继承；遇技能样例与真实需求、当前官方 API 或用户明确约束冲突时，保留技能执行，记录有证据的局部适配，不能借此取消真实验收或跳过整项技能。付费推广或相关技能推荐不是强制购买/全量安装要求。

## Playwright MCP 是必须出现的决策节点

默认首先检查 Playwright MCP 的真实工具和当前支持能力：浏览器是否可启动、能否加载当前扩展、是否能观察并操作真实入口。必须在正式开发早期发现环境缺项，不能到交付时才把整张验收表给用户。

Playwright MCP 当前没有通用的“安装任意扩展”工具，不得捏造 extension_install。按照 [专用配置说明](playwright-mcp.md) 将实际构建加载到独立的持久 Chromium 上下文，再由 MCP 操作。普通页面能打开、桥接扩展已连接或直接打开 popup.html 都不足以说明端到端通道成立。

出现 MCP 未安装、未启用、浏览器不兼容、加载失败或原生入口无法受控时：先记录已查明原因和可行方案，**询问用户是否安装/启用 Playwright MCP，或选择推荐的其他受控方案**。可推荐 Chrome DevTools MCP 的扩展专用工具；若用户暂不处理则保持 waiting_user_environment_choice / blocked。等待期间继续独立工作，不能静默切换、跳过检查或标为可用。此前对相同环境的明确选择沿用，不重复询问。

推荐提问的内容应类似：“当前环境还不能通过 Playwright MCP 完成插件加载/入口操作。可安装或启用它，或使用已核实能真实加载插件的 Chrome DevTools MCP；请决定采用哪一种。”选项按当时事实提供，不能把尚未核实的替代说成已可用。实际用户选择和原因保存为原始证据。

选定后才配置和启用对应通道。优先项目专用配置和独立 profile，保留用户已配置服务；不得擅自切换日常浏览器。重新加载宿主后再次检查实际调用。只有不可自动化的原生步骤才由用户辅助，随后 AI 必须接回端到端检查。

验收 JSON 的 environment.automation_provider 默认必须为 playwright-mcp。若选择 chrome-devtools-mcp / browser-mcp / controlled-browser，按验收参考保存 browser_choice 和用户批准证据；门禁会拒绝缺失选择、遗漏 provider、模拟方法或过期文件指纹。门禁只检查记录，不负责安装或驱动浏览器。

## 失败和恢复

- 技能缺失与 MCP 不可用分别处理，不重复安装方法技能解决浏览器连接。
- 同一失败查明原因后至多原样重试一次，再按支持路径处理；不关闭工具限制。工具明确允许临时目录时可复制已授权构建并核对哈希，不能假定各 MCP 的目录策略相同。
- 软件版本按所选脚手架和官方文档核实；安装 extension-create 不代表其 Node/包管理器或项目构建已可运行。在实际执行 shell、工作目录和项目缓存下跑最小正式构建，并早测所需原生入口及特殊能力，按 [高效交付](efficient-delivery.md) 记录可复用环境结果。
- 固定来源失效先保留已有成果，再核实维护者的新修订。未知来源不能替代清单，已知定制不静默覆盖。
- 用户取消工作时按范围停止，保留未验收状态；不能因必需节点存在就继续运行用户已停止的例子。
